#!/usr/bin/env python3
"""Click CLI entrypoint for fleet operator commands (``agentctl``).

Provides a command tree over ``FleetManagerClient`` gRPC: agent
register/unregister/list/status, and nested ``goal``, ``task``, and ``plan``
groups. YAML agent configs are validated via ``YAMLValidator`` before
registration. Pretty-printing is delegated to ``printer``. Deploy/undeploy
commands remain commented out (not yet implemented on the server).

Invoke as ``agentctl …`` (console script) or ``python -m cli.agentctl``.
Requires a reachable fleet_server; gRPC and generic errors exit with code 1.
"""

# Click builds the nested command groups and options.
import click
# grpc.RpcError for typed error reporting on some commands.
import grpc
# sys.exit on fatal operator errors.
import sys
# os retained for historical import surface compatibility.
import os
# Regex extracts numeric suffixes when bulk-registering agent ids.
import re
# Optional/List typing retained for annotations and historical callers.
from typing import Optional, List
# Protobuf symbols used when decoding agent status state names.
from packages.proto import fleet_manager_pb2
# Validates agent YAML against the agentfleet/v1 schema.
from packages.agent_sdk.src.schema.yaml_validator import YAMLValidator
# Shared stdout formatters and strategy Choice lists.
from .printer import (
    print_task, print_all_tasks,
    print_goal, print_all_goals,
    print_agent, print_all_agents,
    print_response, print_plan, print_all_plans,
    PLANNING_STRATEGY_ENUMS,
    PLANNING_STRATEGY_CHOICES,
    PLANNING_STRATEGY_STRINGS,
    ALLOCATION_STRATEGY_ENUMS,
    ALLOCATION_STRATEGY_CHOICES,
    ALLOCATION_STRATEGY_STRINGS,
)
# gRPC client wrapper around FleetManager.
from packages.fleet_sdk.src.grpc_client import FleetManagerClient
# yaml.YAMLError caught around config load failures.
import yaml
# asyncio retained for historical import surface (commands are sync today).
import asyncio


def load_agent_config(config_file: str) -> dict:
    """Load and validate an agent configuration YAML file.

    Raises ``click.UsageError`` when *config_file* is empty/falsy. On any
    validator failure, echoes the error to stderr and exits with code 1.
    Returns the validated config dict on success for register to consume.
    """
    # Guard against missing path arguments from callers.
    if not config_file:
        raise click.UsageError("You must provide a config file path. Example: agentctl register my_agent.yaml")
    try:
        # Construct the schema validator used across the fleet.
        validator = YAMLValidator()
        # Parse + validate; returns a dict-like config structure.
        return validator.validate_file(config_file)
    except Exception as e:
        # Surface validation/IO errors to the operator and abort.
        click.echo(f"Error loading config file: {str(e)}", err=True)
        sys.exit(1)


@click.group()
def cli():
    """Agent fleet management CLI

    Example usage:
      agentctl register my_agent.yaml
      agentctl plan create dag llm 1
    """
    # Click group body is intentionally empty; subcommands attach below.
    pass


@cli.command()
@click.argument('config_file')
@click.argument('agent_id', required=False)
@click.option('--num', '-n', default=1, show_default=True, type=int, help="Number of agents to register")
@click.option('--host', type=str, help="Override the task server host from YAML")
@click.option('--port', type=int, help="Override the task server port from YAML")
def register(config_file, agent_id, num, host, port):
    """Register a new agent. Optionally register multiple agents with --num.

    Example:
      agentctl register my_agent.yaml my_agent_id
      agentctl register my_agent.yaml --num 3
      agentctl register my_agent.yaml --host localhost --port 8001
    """
    # Redundant guard for empty config path (Click usually requires the arg).
    if not config_file:
        raise click.UsageError("You must provide a config file. Example: agentctl register my_agent.yaml")
    try:
        # Load and schema-validate the YAML agent package config.
        config = load_agent_config(config_file)
        # Open a fleet manager gRPC client (closed in finally).
        client = FleetManagerClient()
        # Agent type is the metadata.name from the YAML.
        agent_type = config['metadata']['name']
        # Optional human description for the registry.
        description = config['metadata'].get('description', '')
        # Normalize capabilities to a list of string ids/descriptions.
        capabilities = [
            c if isinstance(c, str) else c.get('id', c.get('description', ''))
            for c in config.get('capabilities', [])
        ]

        # Prefer connection block; fall back to legacy taskServer key.
        conn = config.get('connection') or config.get('taskServer', {})
        # CLI --host/--port override YAML when provided.
        task_server_host = host if host is not None else conn.get('host', 'localhost')
        task_server_port = port if port is not None else conn.get('port', 8001)

        # Deployment hints for future container orchestration.
        deployment = config.get('deployment', {})
        container = config.get('container', {})
        docker_host = deployment.get('docker_host', 'localhost')
        docker_port = deployment.get('docker_port', 2375)
        container_image = deployment.get('image') or container.get('image', '')
        container_env = deployment.get('environment') or container.get('environment', {})

        if num == 1:
            # Single registration: explicit id or "{type}-1".
            rid = agent_id if agent_id else f"{agent_type}-1"
            response = client.register_agent(
                agent_id=rid,
                agent_type=agent_type,
                description=description,
                capabilities=capabilities,
                task_server_host=task_server_host,
                task_server_port=task_server_port,
                docker_host=docker_host,
                docker_port=docker_port,
                container_image=container_image,
                container_env=container_env
            )
            # Print success/failure and exit on failure.
            print_response(response)
        else:
            # Bulk mode: discover existing "{type}-N" ids to pick next suffixes.
            existing_agents = client.list_agents().agents
            existing_ids = [r.agent_id for r in existing_agents if r.agent_id.startswith(f"{agent_type}-")]
            # Extract the numeric suffix for this agent_type (preserve exact regex).
            suffixes = [int(re.match(rf"{agent_type}-(\\d+)", rid).group(1)) for rid in existing_ids if re.match(rf"{agent_type}-(\\d+)", rid)]
            # Start after the highest existing suffix (or at 1).
            start_idx = max(suffixes) + 1 if suffixes else 1
            # Always skip IDs that already exist.
            num_registered = 0
            i = start_idx
            while num_registered < num:
                rid = f"{agent_type}-{i}"
                # Skip ids that somehow already exist in the snapshot.
                if rid in existing_ids:
                    i += 1
                    continue
                response = client.register_agent(
                    agent_id=rid,
                    agent_type=agent_type,
                    description=description,
                    capabilities=capabilities,
                    task_server_host=task_server_host,
                    task_server_port=task_server_port,
                    docker_host=docker_host,
                    docker_port=docker_port,
                    container_image=container_image,
                    container_env=container_env
                )
                print_response(response)
                num_registered += 1
                i += 1

    except FileNotFoundError:
        click.echo(f"Config file {config_file} not found", err=True)
        sys.exit(1)
    except yaml.YAMLError as e:
        click.echo(f"Error parsing config file: {str(e)}", err=True)
        sys.exit(1)
    except grpc.RpcError as e:
        click.echo(f"gRPC error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        # Always close the channel when client was constructed.
        client.close()

# @cli.command()
# @click.argument('agent_id')
# def deploy(agent_id):
#     """Deploy a agent container to a agent (NOT YET IMPLEMENTED)
#
#     Example:
#       agentctl deploy my_agent_id
#     """
#     if not agent_id:
#         raise click.UsageError("You must provide a agent_id. Example: agentctl deploy my_agent_id")
#     try:
#         client = FleetManagerClient()
#         response = client.deploy_agent(agent_id)
#         print_response(response)
#     except Exception as e:
#         click.echo(f"Error: {str(e)}", err=True)
#         sys.exit(1)
#     finally:
#         client.close()

# @cli.command()
# @click.argument('agent_id')
# def undeploy(agent_id):
#     """Undeploy a agent container from a agent (NOT YET IMPLEMENTED)
#
#     Example:
#       agentctl undeploy my_agent_id
#     """
#     if not agent_id:
#         raise click.UsageError("You must provide a agent_id. Example: agentctl undeploy my_agent_id")
#     try:
#         client = FleetManagerClient()
#         response = client.undeploy_agent(agent_id)
#         print_response(response)
#     except Exception as e:
#         click.echo(f"Error: {str(e)}", err=True)
#         sys.exit(1)
#     finally:
#         client.close()

@cli.command()
@click.argument('agent_id')
def unregister(agent_id):
    """Unregister a agent

    Example:
      agentctl unregister my_agent_id
    """
    # Guard empty ids (Click normally requires the argument).
    if not agent_id:
        raise click.UsageError("You must provide a agent_id. Example: agentctl unregister my_agent_id")
    try:
        # Open client for the RPC.
        client = FleetManagerClient()
        # Ask fleet_server to drop the agent registration.
        response = client.unregister_agent(agent_id)
        # Pretty-print and exit on failure.
        print_response(response)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        client.close()

@cli.command()
@click.option('--filter', 'filter_type', type=click.Choice(['all', 'deployed', 'registered'], case_sensitive=False),
              default='all', help="Filter agent list")
@click.option('-v', '--verbose', is_flag=True, help="Show detailed agent and task info")
def list(filter_type, verbose):
    """List all agents

    Example:
      agentctl list
      agentctl list --filter deployed
    """
    try:
        client = FleetManagerClient()
        # Fetch agents according to the filter enum string.
        response = client.list_agents(filter_type)
        agents = response.agents
        # Optionally hydrate tasks for verbose tree printing.
        tasks_by_agent = {}
        if verbose:
            for agent in agents:
                tasks = []
                for tid in getattr(agent, 'task_ids', []):
                    try:
                        t = client.get_task(tid).task
                        tasks.append(t)
                    except Exception:
                        click.echo(f"[Warning] Task ID {tid} not found for agent {agent.agent_id}", err=True)
                tasks_by_agent[agent.agent_id] = tasks
        # Render the agent list (with optional tasks).
        print_all_agents(agents, tasks_by_agent if verbose else None, verbose)
    except Exception as e:
        click.echo(f"Error listing agents: {str(e)}", err=True)
        sys.exit(1)
    finally:
        client.close()

@cli.command()
@click.argument('agent_id')
@click.option('-v', '--verbose', is_flag=True, help="Show detailed agent and task info")
def status(agent_id, verbose):
    """Get detailed status of a agent

    Example:
      agentctl status my_agent_id
    """
    if not agent_id:
        raise click.UsageError("You must provide a agent_id. Example: agentctl status my_agent_id")
    try:
        client = FleetManagerClient()
        # Fetch AgentStatus protobuf.
        status = client.get_agent_status(agent_id)
        # Decode enum to a readable name.
        state_name = fleet_manager_pb2.AgentStatus.State.Name(status.state)
        click.echo(f"\nAgent Status: {state_name}")
        if status.message:
            click.echo(f"Status Message: {status.message}")
        # Verbose: list tasks referenced on the status object.
        if verbose and getattr(status, 'task_ids', []):
            tasks = []
            for tid in status.task_ids:
                try:
                    t = client.get_task(tid).task
                    tasks.append(t)
                except Exception:
                    click.echo(f"[Warning] Task ID {tid} not found for agent {agent_id}", err=True)
            print_all_tasks(tasks, verbose=True)
    except Exception as e:
        click.echo(f"Error getting agent status: {str(e)}", err=True)
        sys.exit(1)
    finally:
        client.close()

@cli.group()
def goal():
    """Goal management commands"""
    # Nested Click group; subcommands registered via decorators below.
    pass

@goal.command()
@click.argument('description')
@click.option('--planning-strategy', '-p', type=click.Choice(['monolithic', 'dag', 'big_dag'], case_sensitive=False),
              default='monolithic', help='Planning strategy to use (monolithic, dag, or big_dag)')
def add(description, planning_strategy):
    """Add a new goal with specified planning strategy"""
    try:
        # Context-manager form closes the client automatically.
        with FleetManagerClient() as client:
            # Map the strategy string to the string expected by the client
            # (planning_strategy is currently unused by create_goal; retained for CLI API).
            response = client.create_goal(description)
            if response.goal:
                print_goal(response.goal)
            else:
                click.echo(f"Error: {response.error}", err=True)
    except grpc.RpcError as e:
        status_code = e.code()
        status_details = e.details()
        click.echo(f"gRPC error: {status_code.name} - {status_details}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error adding goal: {str(e)}", err=True)
        sys.exit(1)

@goal.command()
@click.argument('goal_id', type=int)
@click.option('-v', '--verbose', is_flag=True, help="Show detailed goal, plan, and task info")
def get(goal_id, verbose):
    """Get details of a specific goal"""
    try:
        client = FleetManagerClient()
        goal_resp = client.get_goal(goal_id)
        goal = goal_resp.goal
        # Empty goal_id field means not found.
        if not goal.goal_id:
            click.echo(f"[Warning] Goal ID {goal_id} not found", err=True)
            return
        # Load associated plans and tasks for this goal
        plans = client.list_plans().plans
        tasks = client.list_tasks(goal_ids=[goal.goal_id]).tasks
        print_goal(goal, plans=plans, tasks=tasks, verbose=verbose)
    except Exception as e:
        click.echo(f"Error getting goal: {str(e)}", err=True)
        sys.exit(1)
    finally:
        client.close()

@goal.command()
@click.option('-v', '--verbose', is_flag=True, help="Show detailed info for all goals")
def list(verbose):
    """List all goals"""
    try:
        client = FleetManagerClient()
        goals = client.list_goals().goals
        plans = client.list_plans().plans
        tasks = client.list_tasks().tasks
        for goal in goals:
            # Filter plans that reference this goal id.
            goal_plans = [p for p in plans if goal.goal_id in getattr(p, 'goal_ids', [])]
            goal_tasks = [t for t in tasks if t.goal_id == goal.goal_id]
            print_goal(goal, plans=goal_plans, tasks=goal_tasks, verbose=verbose)
    except Exception as e:
        click.echo(f"Error listing goals: {str(e)}", err=True)
        sys.exit(1)
    finally:
        client.close()

@goal.command()
@click.argument('goal_id', type=int)
def delete(goal_id):
    """Delete a goal"""
    try:
        # Validate goal_id is an integer
        try:
            goal_id_int = int(goal_id)
        except ValueError:
            click.echo(f"Error: Goal ID must be an integer, got '{goal_id}'", err=True)
            sys.exit(1)

        client = FleetManagerClient()
        response = client.delete_goal(goal_id_int)
        if response.goal:
            click.echo(f"Goal {goal_id_int} deleted successfully")
        else:
            click.echo(f"Error: {response.error}", err=True)
    except grpc.RpcError as e:
        status_code = e.code()
        status_details = e.details()
        click.echo(f"gRPC error: {status_code.name} - {status_details}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        client.close()

@cli.group()
def task():
    """Task management commands"""
    pass

@task.command()
@click.argument('description', type=str)
@click.option('--goal-id', type=int, required=True, help="Goal ID for the task")
@click.option('--plan-id', type=int, required=True, help="Plan ID for the task")
@click.option('--agent-id', type=str, required=True, default=None, help="Agent ID to assign (optional)")
@click.option('--agent-type', type=str, required=True, default=None, help="Agent type to assign (optional)")
@click.option('--dependencies', required=False, type=str, default=None, help="Comma-separated list of task IDs this task depends on (optional)")
def add(description, goal_id, plan_id, agent_id, agent_type, dependencies):
    """Add a new task to a goal and plan, with optional agent assignment and dependencies."""
    try:
        client = FleetManagerClient()
        # Parse dependencies string into a list of ints, if provided
        if dependencies:
            dependencies_list = [int(x.strip()) for x in dependencies.split(',') if x.strip()]
        else:
            dependencies_list = []
        # Create the task via gRPC.
        resp = client.create_task(description, agent_id, agent_type, goal_id, plan_id, dependencies_list)
        if resp.task:
            click.echo(f"Task added: {resp.task.task_id}")
        else:
            click.echo(f"Error adding task: {resp.error}", err=True)
    except Exception as e:
        click.echo(f"Error adding task: {str(e)}", err=True)
        sys.exit(1)
    finally:
        client.close()

# Example usage:
# r task add "Fry eggs" --goal-id 1 --plan-id 1
# r task add "Pour coffee" --goal-id 1 --plan-id 2 --agent-id rob
# r task add "Put plates" --goal-id 2 --plan-id 1 --dependencies 5 --dependencies 6

@task.command()
@click.option('--goal-id', help='Filter tasks by goal ID')
@click.option('--agent-id', help='Filter tasks by agent ID')
@click.option('-v', '--verbose', is_flag=True, help="Show detailed task info")
def list(goal_id, agent_id, verbose):
    """List tasks with optional filtering"""
    try:
        # Convert goal_id to int if provided
        goal_ids = None
        if goal_id:
            try:
                goal_ids = [int(goal_id)]
            except ValueError:
                click.echo(f"Error: Goal ID must be an integer, got '{goal_id}'", err=True)
                sys.exit(1)

        # Convert agent_id to list if provided
        agent_ids = None
        if agent_id:
            agent_ids = [agent_id]

        client = FleetManagerClient()
        response = client.list_tasks(goal_ids=goal_ids, agent_ids=agent_ids)
        tasks = response.tasks
        print_all_tasks(tasks, verbose=verbose)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        client.close()

@task.command()
@click.argument('task_id', type=int)
@click.option('-v', '--verbose', is_flag=True, help="Show detailed task info")
def get(task_id, verbose):
    """Get details of a specific task"""
    try:
        # Validate task_id is an integer
        try:
            task_id_int = int(task_id)
        except ValueError:
            click.echo(f"Error: Task ID must be an integer, got '{task_id}'", err=True)
            sys.exit(1)

        client = FleetManagerClient()
        response = client.get_task(task_id_int)

        if response.task:
            task = response.task
            if verbose:
                # Attach related goal onto the task object for printers.
                if getattr(task, 'goal_id', None):
                    try:
                        g = client.get_goal(task.goal_id).goal
                        task._goal = g
                    except Exception:
                        click.echo(f"[Warning] Goal ID {task.goal_id} not found for task {task.task_id}", err=True)
                # Attach agent status when assigned.
                if getattr(task, 'agent_id', None):
                    try:
                        r = client.get_agent_status(task.agent_id)
                        task._agent = r
                    except Exception:
                        click.echo(f"[Warning] Agent ID {task.agent_id} not found for task {task.task_id}", err=True)
                # Find plans that list this task id.
                plans = [p for p in client.list_plans().plans if task.task_id in getattr(p, 'task_ids', [])]
                task._plans = plans
                task._tasks = []
                for plan in plans:
                    for tid in getattr(plan, 'task_ids', []):
                        try:
                            t = client.get_task(tid).task
                            task._tasks.append(t)
                        except Exception:
                            click.echo(f"[Warning] Task ID {tid} not found for plan {plan.plan_id}", err=True)
            print_task(task)
        else:
            click.echo(f"Error: {response.error}", err=True)
            sys.exit(1)
    except grpc.RpcError as e:
        status_code = e.code()
        status_details = e.details()
        click.echo(f"gRPC error: {status_code.name} - {status_details}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        client.close()

@task.command()
@click.argument('task_id', type=int)
def delete(task_id):
    """Delete a task"""
    try:
        # Validate task_id is an integer
        try:
            task_id_int = int(task_id)
        except ValueError:
            click.echo(f"Error: Task ID must be an integer, got '{task_id}'", err=True)
            sys.exit(1)

        client = FleetManagerClient()
        response = client.delete_task(task_id_int)
        if getattr(response, "success", False):
            click.echo(f"Task {task_id_int} deleted successfully")
            if getattr(response, "updated_task_ids", None):
                click.echo(f"Unlinked dependencies from tasks: {list(response.updated_task_ids)}")
        else:
            click.echo(f"Error: {response.error}", err=True)
    except grpc.RpcError as e:
        status_code = e.code()
        status_details = e.details()
        click.echo(f"gRPC error: {status_code.name} - {status_details}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        client.close()

@cli.group()
def plan():
    """Plan management commands"""
    pass

@plan.command()
@click.argument('planning_strategy', type=click.Choice(PLANNING_STRATEGY_CHOICES, case_sensitive=False))
@click.argument('allocation_strategy', type=click.Choice(ALLOCATION_STRATEGY_CHOICES, case_sensitive=False))
@click.argument('goal_ids', required=True, type=str)
@click.option('-v', '--verbose', is_flag=True, help="Show detailed plan, goal, and task info")
def create(planning_strategy, allocation_strategy, goal_ids, verbose):
    """Create a new plan with planning strategy, allocator, and goal IDs

    Example:
      agentctl plan create dag llm 1
      agentctl plan create monolithic llm 1,2,3
    """
    if not planning_strategy or not allocation_strategy or not goal_ids:
        raise click.UsageError("You must provide planning_strategy, allocation_strategy, and goal_ids. Example: agentctl plan create dag llm 1")
    client = None
    try:
        # Parse the comma-separated string into a list of ints
        try:
            goal_ids_list = [int(x.strip()) for x in goal_ids.split(',') if x.strip()]
        except Exception:
            click.echo(f"Error: Could not parse goal IDs from '{goal_ids}'", err=True)
            sys.exit(1)
        client = FleetManagerClient()
        # Add allocator info to the plan creation request if supported
        response = client.create_plan(planning_strategy, goal_ids_list, allocation_strategy)
        plan = response.plan
        if not plan.plan_id:
            click.echo(f"[Warning] Plan creation failed", err=True)
            return
        # Hydrate goals and tasks for pretty printing.
        goals = [client.get_goal(gid).goal for gid in getattr(plan, 'goal_ids', [])]
        tasks = []
        for tid in getattr(plan, 'task_ids', []):
            try:
                t = client.get_task(tid).task
                tasks.append(t)
            except Exception:
                click.echo(f"[Warning] Task ID {tid} not found for plan {plan.plan_id}", err=True)
        print_plan(plan, goals, tasks, verbose)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        if client is not None:
            client.close()

@plan.command()
@click.argument('plan_id', type=int)
@click.option('-a', '--analyze-idle', is_flag=True, help="Analyze idle time and display task grid for the plan")
@click.option('-v', '--verbose', is_flag=True, help="Show detailed plan, goal, and task info")
def get(plan_id, analyze_idle, verbose):
    """Get details of a specific plan"""
    client = None
    try:
        client = FleetManagerClient()
        plan_resp = client.get_plan(plan_id)
        plan = plan_resp.plan
        if not plan.plan_id:
            click.echo(f"[Warning] Plan ID {plan_id} not found", err=True)
            return
        goals = [client.get_goal(gid).goal for gid in getattr(plan, 'goal_ids', [])]
        tasks = client.list_tasks(plan_ids=[plan.plan_id]).tasks
        print_plan(plan, goals=goals, tasks=tasks, verbose=verbose)
        if analyze_idle:
            # Perform idle analysis and print the grid
            report = client.analyze_idle_time(plan_id)
            click.echo(report)
            return
    except Exception as e:
        click.echo(f"Error getting plan: {str(e)}", err=True)
        sys.exit(1)
    finally:
        client.close()

@plan.command()
@click.option('-v', '--verbose', is_flag=True, help="Show detailed info for all plans")
def list(verbose):
    """List all plans"""
    try:
        client = FleetManagerClient()
        plans_resp = client.list_plans()
        plans = plans_resp.plans
        goals = client.list_goals().goals
        tasks = client.list_tasks().tasks
        print_all_plans(plans, goals=goals, tasks_by_plan=tasks, verbose=verbose)
    except Exception as e:
        click.echo(f"Error listing plans: {str(e)}", err=True)
        sys.exit(1)
    finally:
        client.close()

@plan.command()
@click.argument('plan_id', type=int)
def delete(plan_id):
    """Delete a plan"""
    try:
        client = FleetManagerClient()
        response = client.delete_plan(plan_id)
        if response.plan:
            click.echo(f"Plan {plan_id} deleted successfully")
        else:
            click.echo(f"Error: {response.error}", err=True)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        client.close()

@plan.command()
@click.argument('plan_id', type=int)
def start(plan_id):
    """Start a plan"""
    try:
        client = FleetManagerClient()
        response = client.start_plan(plan_id)
        # Empty error string means success (message historically says "completed").
        if response.error == "":
            click.echo(f"Plan {plan_id} completed successfully")
        else:
            click.echo(f"Error: {response.error}", err=True)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    finally:
        client.close()

cli.add_command(goal)  # Add goal command group to main CLI
cli.add_command(task)  # Add task command group to main CLI
cli.add_command(plan)  # Add plan command group to main CLI

def main():
    """Entry point for the CLI console script.

    Invokes the Click ``cli`` group and converts unexpected exceptions into
    stderr messages with exit code 1.
    """
    try:
        cli()
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    # Allow `python cli/agentctl.py` during local development.
    main()
