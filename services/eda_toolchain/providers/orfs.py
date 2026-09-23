"""ORFS-backed implementation of the tool provider contract."""

from __future__ import annotations

import os
import re
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from fastapi import HTTPException

from .base import ToolRequestLike


@dataclass(frozen=True)
class ORFSConfig:
    pdk_root: Path
    design_root: Path
    workspace_root: Path
    orfs_root: Path
    yosys_bin: str
    sta_bin: str
    openroad_bin: str
    make_bin: str
    version_arguments: dict[str, list[str]]
    default_rtl: str
    default_sdc: str
    default_top: str
    platform: str
    pdn_tcl: str
    placement_site: str
    liberty: Path
    tech_lef: Path
    macro_lef: Path
    orfs_flow: dict[str, str | int | float]
    synthesis_timeout: int
    analysis_timeout: int
    physical_timeout: int


ORFS_TARGETS = {
    "run_synthesis": "synth",
    "run_floorplan": "floorplan",
    "run_placement": "place",
    "run_cts": "cts",
    "run_global_routing": "globalroute",
    "run_detailed_routing": "route",
    "run_finish": "finish",
    "run_gds": "gds",
    "run_drc": "drc",
    "run_lvs": "lvs",
    "run_full_orfs": "full",
    "run_orfs_flow": None,
}
ALIASES = {
    "compile_candidate": "run_synthesis",
    "synthesize": "run_synthesis",
    "yosys_synth": "run_synthesis",
    "run_global_placement": "run_placement",
    "global_placement": "run_placement",
    "openroad_place": "run_placement",
    "global_route": "run_global_routing",
    "detailed_route": "run_detailed_routing",
    "clock_tree_synthesis": "run_cts",
    "sta_report": "run_sta",
}
SCRIPT_OPS = {
    "run_yosys_script": ("yosys", "yosys.tcl"),
    "run_opensta_script": ("opensta", "opensta.tcl"),
    "run_openroad_script": ("openroad", "openroad.tcl"),
}
FORBIDDEN_TCL_COMMANDS = {"exec", "open", "socket", "load", "package", "source"}


class ORFSProvider:
    """Execute OpenROAD-flow-scripts stages and expert tool scripts."""

    def __init__(self, config: Mapping[str, Any]) -> None:
        self.config = self._parse_config(config)

    @staticmethod
    def _parse_config(raw: Mapping[str, Any]) -> ORFSConfig:
        try:
            paths = raw["paths"]
            design = raw["design"]
            collateral = raw["collateral"]
            limits = raw["limits"]
            pdk_root = Path(os.environ.get("PDK_ROOT", paths["pdk_root"])).resolve()
            design_root = Path(os.environ.get("DESIGN_ROOT", paths["design_root"])).resolve()
            return ORFSConfig(
                pdk_root=pdk_root,
                design_root=design_root,
                workspace_root=Path(
                    os.environ.get("WORKSPACE_ROOT", paths["workspace_root"])
                ).resolve(),
                orfs_root=Path(os.environ.get("ORFS_ROOT", paths["orfs_root"])).resolve(),
                yosys_bin=os.path.expanduser(os.environ.get("YOSYS_BIN", raw["binaries"]["yosys"])),
                sta_bin=os.path.expanduser(os.environ.get("STA_BIN", raw["binaries"]["opensta"])),
                openroad_bin=os.path.expanduser(
                    os.environ.get("OPENROAD_BIN", raw["binaries"]["openroad"])
                ),
                make_bin=os.path.expanduser(os.environ.get("MAKE_BIN", raw["binaries"]["make"])),
                version_arguments=raw["version_arguments"],
                default_rtl=design["rtl"],
                default_sdc=design["sdc"],
                default_top=design["top"],
                platform=design["platform"],
                pdn_tcl=design["pdn_tcl"],
                placement_site=design["placement_site"],
                liberty=pdk_root / collateral["liberty"],
                tech_lef=pdk_root / collateral["tech_lef"],
                macro_lef=pdk_root / collateral["macro_lef"],
                orfs_flow=raw["orfs_flow"],
                synthesis_timeout=int(limits["synthesis_timeout_seconds"]),
                analysis_timeout=int(limits["analysis_timeout_seconds"]),
                physical_timeout=int(limits["physical_timeout_seconds"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError(f"invalid ORFS provider configuration: {error}") from error

    def _ensure_pdk(self) -> None:
        missing = [
            path
            for path in (self.config.liberty, self.config.tech_lef, self.config.macro_lef)
            if not path.is_file()
        ]
        if missing:
            raise HTTPException(
                status_code=503,
                detail=f"PDK collateral missing: {[str(path) for path in missing]}",
            )

    def _rtl_path(self, params: dict[str, Any]) -> Path:
        raw = str(params.get("design_path", self.config.default_rtl))
        path = (self.config.design_root / raw).resolve()
        if path != self.config.design_root and self.config.design_root not in path.parents:
            raise HTTPException(status_code=400, detail="design_path escapes design root")
        if not path.is_file():
            raise HTTPException(status_code=404, detail=f"RTL not found: {raw}")
        return path

    def _sdc_path(self, params: dict[str, Any]) -> Path:
        raw = str(params.get("sdc_path", self.config.default_sdc))
        path = (self.config.design_root / raw).resolve()
        if path != self.config.design_root and self.config.design_root not in path.parents:
            raise HTTPException(status_code=400, detail="sdc_path escapes design root")
        if not path.is_file():
            raise HTTPException(status_code=404, detail=f"SDC not found: {raw}")
        return path

    def _top(self, params: dict[str, Any]) -> str:
        top = str(params.get("top", self.config.default_top))
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", top):
            raise HTTPException(status_code=400, detail="invalid top module name")
        return top

    @staticmethod
    def _run(
        command: list[str], *, cwd: Path | None = None, timeout: int = 600
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command, text=True, capture_output=True, timeout=timeout, cwd=cwd, check=False
        )

    @staticmethod
    def _float_metric(pattern: str, output: str, flags: int = 0) -> float | None:
        match = re.search(pattern, output, flags)
        return float(match.group(1)) if match else None

    def _workspace(self, prefix: str) -> tuple[str, Path]:
        job_id = f"{prefix}-{uuid.uuid4().hex[:12]}"
        workspace = self.config.workspace_root / job_id
        workspace.mkdir(parents=True, exist_ok=False)
        return job_id, workspace

    def _yosys_synth(self, rtl: Path, top: str, workspace: Path) -> tuple[Path, str, int]:
        synth_v = workspace / f"{top}.syn.v"
        script = workspace / "synth.ys"
        log = workspace / "yosys.log"
        script.write_text(
            f"read_liberty -ignore_miss_func {self.config.liberty}\n"
            f"read_verilog {rtl}\n"
            f"synth -top {top}\n"
            f"dfflibmap -liberty {self.config.liberty}\n"
            f"abc -liberty {self.config.liberty}\n"
            f"write_verilog {synth_v}\nstat\n",
            encoding="utf-8",
        )
        completed = self._run(
            [self.config.yosys_bin, "-s", str(script)], timeout=self.config.synthesis_timeout
        )
        output = completed.stdout + completed.stderr
        log.write_text(output, encoding="utf-8")
        return synth_v, output, completed.returncode

    def _opensta_report(
        self, synth_v: Path, top: str, sdc: Path, workspace: Path
    ) -> tuple[str, int, dict[str, Any]]:
        script = workspace / "sta.tcl"
        report = workspace / "sta.rpt"
        sta_is_openroad = Path(self.config.sta_bin).resolve() == Path(
            self.config.openroad_bin
        ).resolve()
        tech_setup = (
            f"read_lef {self.config.tech_lef}\nread_lef {self.config.macro_lef}\n"
            if sta_is_openroad
            else ""
        )
        script.write_text(
            tech_setup
            + f"read_liberty {self.config.liberty}\n"
            f"read_verilog {synth_v}\nlink_design {top}\nread_sdc {sdc}\n"
            "report_wns\nreport_tns\n"
            "report_checks -fields {slew cap fanout} -digits 3\nexit\n",
            encoding="utf-8",
        )
        completed = self._run(
            [self.config.sta_bin, str(script)], timeout=self.config.analysis_timeout
        )
        output = completed.stdout + completed.stderr
        report.write_text(output, encoding="utf-8")
        exit_code = completed.returncode if "[ERROR" not in output else 1
        return output, exit_code, {
            "exit_code": exit_code,
            "wns": self._float_metric(r"wns max\s+(-?\d+(?:\.\d+)?)", output),
            "tns": self._float_metric(r"tns max\s+(-?\d+(?:\.\d+)?)", output),
        }

    @staticmethod
    def _response(
        *, framework: str, operation: str, status: str, summary: str,
        metrics: dict[str, Any], artifacts: list[dict[str, str]], job_id: str,
        workspace: Path, manifest: str,
    ) -> dict[str, Any]:
        return {
            "framework": framework, "status": status, "summary": summary,
            "metrics": metrics, "artifacts": artifacts, "job_id": job_id,
            "workspace": str(workspace), "command_manifest": manifest,
            "state": status, "operation": operation,
        }

    def _orfs_target(self, operation: str, params: dict[str, Any]) -> str:
        target = ORFS_TARGETS[operation]
        if target is None:
            target = str(params.get("target", "all"))
        supported = set(ORFS_TARGETS.values()) - {None} | {"all"}
        if target not in supported:
            raise HTTPException(status_code=400, detail=f"unsupported ORFS target '{target}'")
        return target

    def _write_orfs_config(
        self, workspace: Path, job_id: str, rtl: Path, sdc: Path, top: str
    ) -> Path:
        pdn = self.config.design_root / self.config.pdn_tcl
        exports: dict[str, str | int | float] = {
            "DESIGN_NAME": top,
            "PLATFORM": self.config.platform,
            "VERILOG_FILES": str(rtl),
            "SDC_FILE": str(sdc),
            "FLOW_VARIANT": job_id,
        }
        exports.update(self.config.orfs_flow)
        if pdn.is_file():
            exports["PDN_TCL"] = str(pdn)
        config = workspace / "orfs.mk"
        config.write_text(
            "\n".join(f"export {name} = {value}" for name, value in exports.items()) + "\n",
            encoding="utf-8",
        )
        return config

    def _run_orfs(
        self, target: str, rtl: Path, sdc: Path, top: str, workspace: Path, job_id: str
    ) -> tuple[str, int, Path]:
        if not (self.config.orfs_root / "Makefile").is_file():
            raise HTTPException(
                status_code=503, detail=f"ORFS Makefile unavailable at {self.config.orfs_root}"
            )
        flow_config = self._write_orfs_config(workspace, job_id, rtl, sdc, top)
        targets = ["all", "gds", "drc", "lvs"] if target == "full" else [target]
        completed = self._run(
            [
                self.config.make_bin, "-C", str(self.config.orfs_root),
                f"DESIGN_CONFIG={flow_config}", f"YOSYS_EXE={self.config.yosys_bin}",
                f"OPENSTA_EXE={self.config.sta_bin}",
                f"OPENROAD_EXE={self.config.openroad_bin}", *targets,
            ],
            timeout=self.config.physical_timeout,
        )
        output = completed.stdout + completed.stderr
        (workspace / "orfs.log").write_text(output, encoding="utf-8")
        return output, completed.returncode, flow_config

    @staticmethod
    def _validated_script(params: dict[str, Any]) -> str:
        script = str(params.get("script", ""))
        if not script.strip():
            raise HTTPException(status_code=400, detail="script is required")
        commands = set(re.findall(r"(?m)^\s*([A-Za-z_][A-Za-z0-9_:]*)", script))
        disallowed = sorted(command for command in commands if command in FORBIDDEN_TCL_COMMANDS)
        if disallowed:
            raise HTTPException(
                status_code=400, detail=f"disallowed Tcl commands: {', '.join(disallowed)}"
            )
        return script

    def _run_script(
        self, operation: str, params: dict[str, Any], workspace: Path
    ) -> tuple[str, int, Path, str]:
        framework, filename = SCRIPT_OPS[operation]
        script_path = workspace / filename
        script_path.write_text(self._validated_script(params), encoding="utf-8")
        command = {
            "yosys": [self.config.yosys_bin, "-s", str(script_path)],
            "opensta": [self.config.sta_bin, str(script_path)],
            "openroad": [self.config.openroad_bin, "-exit", str(script_path)],
        }[framework]
        completed = self._run(command, cwd=workspace, timeout=self.config.physical_timeout)
        output = completed.stdout + completed.stderr
        (workspace / f"{framework}.log").write_text(output, encoding="utf-8")
        return output, completed.returncode, script_path, framework

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "frameworks": ["yosys", "opensta", "openroad"],
            "pdk_mounted": self.config.liberty.is_file(),
            "design_mounted": (self.config.design_root / self.config.default_rtl).is_file(),
        }

    def capabilities(self) -> dict[str, Any]:
        binaries = {}
        for name, binary in {
            "yosys": self.config.yosys_bin, "opensta": self.config.sta_bin,
            "openroad": self.config.openroad_bin,
        }.items():
            try:
                binaries[name] = self._run(
                    [binary, *self.config.version_arguments[name]], timeout=30
                ).returncode == 0
            except OSError:
                binaries[name] = False
        return {
            "operations": sorted(set(ORFS_TARGETS) | set(ALIASES) | {"run_sta"} | set(SCRIPT_OPS)),
            "orfs_targets": sorted(set(ORFS_TARGETS.values()) - {None} | {"all"}),
            "script_contracts": sorted(SCRIPT_OPS),
            "binaries": binaries,
            "pdk_collateral": {
                name: str(path)
                for name, path in {
                    "liberty": self.config.liberty, "tech_lef": self.config.tech_lef,
                    "macro_lef": self.config.macro_lef,
                }.items()
            },
            "orfs_root": str(self.config.orfs_root),
        }

    def run(self, request: ToolRequestLike) -> dict[str, Any]:
        operation = ALIASES.get(request.operation, request.operation)
        self._ensure_pdk()
        rtl = self._rtl_path(request.params)
        top = self._top(request.params)
        if operation in SCRIPT_OPS:
            job_id, workspace = self._workspace("script")
            _, code, manifest, framework = self._run_script(operation, request.params, workspace)
            return self._response(
                framework=framework, operation=operation,
                status="succeeded" if code == 0 else "failed",
                summary=f"{framework} expert script {'completed' if code == 0 else 'failed'}",
                metrics={"exit_code": code},
                artifacts=[{"uri": f"file://{workspace / f'{framework}.log'}", "type": f"{framework}-log"}],
                job_id=job_id, workspace=workspace, manifest=str(manifest),
            )
        if operation == "run_synthesis" and request.operation in {
            "compile_candidate", "synthesize", "yosys_synth",
        }:
            job_id, workspace = self._workspace("yosys")
            synth_v, yosys_out, code = self._yosys_synth(rtl, top, workspace)
            cells_match = re.search(r"Number of cells:\s+(\d+)", yosys_out)
            cells = int(cells_match.group(1)) if cells_match else None
            return self._response(
                framework="yosys", operation=request.operation,
                status="succeeded" if code == 0 and synth_v.is_file() else "failed",
                summary=f"Yosys mapped {top} to {self.config.platform} ({cells or '?'} cells)",
                metrics={"exit_code": code, "cell_count": cells, "top": top},
                artifacts=[
                    {"uri": f"file://{workspace / 'yosys.log'}", "type": "yosys-log"},
                    {"uri": f"file://{synth_v}", "type": "verilog-netlist"},
                ],
                job_id=job_id, workspace=workspace, manifest=str(workspace / "synth.ys"),
            )
        if operation == "run_sta":
            job_id, workspace = self._workspace("sta")
            synth_v, _, code = self._yosys_synth(rtl, top, workspace)
            if code != 0 or not synth_v.is_file():
                raise HTTPException(status_code=500, detail="Yosys synthesis failed before OpenSTA")
            _, _, metrics = self._opensta_report(
                synth_v, top, self._sdc_path(request.params), workspace
            )
            return self._response(
                framework="opensta", operation=request.operation,
                status="succeeded" if metrics.get("exit_code") == 0 else "failed",
                summary=f"OpenSTA WNS={metrics.get('wns')} TNS={metrics.get('tns')} on {top}",
                metrics=metrics,
                artifacts=[
                    {"uri": f"file://{workspace / 'sta.rpt'}", "type": "opensta-report"},
                    {"uri": f"file://{synth_v}", "type": "verilog-netlist"},
                ],
                job_id=job_id, workspace=workspace, manifest=str(workspace / "sta.tcl"),
            )
        if operation in ORFS_TARGETS:
            job_id, workspace = self._workspace("orfs")
            target = self._orfs_target(operation, request.params)
            _, code, manifest = self._run_orfs(
                target, rtl, self._sdc_path(request.params), top, workspace, job_id
            )
            return self._response(
                framework="openroad", operation=request.operation,
                status="succeeded" if code == 0 else "failed",
                summary=f"ORFS {target} {'completed' if code == 0 else 'failed'} for {top}",
                metrics={"exit_code": code, "target": target, "top": top},
                artifacts=[
                    {"uri": f"file://{workspace / 'orfs.log'}", "type": "orfs-log"},
                    {"uri": f"file://{manifest}", "type": "orfs-config"},
                ],
                job_id=job_id, workspace=workspace, manifest=str(manifest),
            )
        supported = set(ORFS_TARGETS) | set(ALIASES) | {"run_sta"} | set(SCRIPT_OPS)
        raise HTTPException(
            status_code=400,
            detail=f"unsupported operation '{operation}'; supported: " + ", ".join(sorted(supported)),
        )
