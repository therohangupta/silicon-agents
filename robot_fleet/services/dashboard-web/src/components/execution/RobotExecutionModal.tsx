import {
  CheckCircle,
  Clock,
  AlertCircle,
  Circle,
  Video,
  Activity,
  Terminal,
  ChevronDown,
  ChevronRight,
  MessageSquare,
  Wifi,
  WifiOff,
} from 'lucide-react'
import { useState } from 'react'
import { Modal } from '../common/Modal'
import { StatusBadge } from '../common/StatusBadge'
import { LiveVideoCanvas } from '../common/LiveVideoCanvas'
import { TaskIdChip } from './TaskIdChip'
import { cn } from '../../lib/utils'
import { useTelemetryStream } from '../../hooks/useTelemetryStream'
import type { Task } from '../../types'

interface RobotExecutionModalProps {
  isOpen: boolean
  onClose: () => void
  robotId: string
  robotType: string
  tasks: Task[]
  allTasks: Task[]
  elapsedTimes: Map<number, number>
  taskServerInfo?: { host: string; port: number } | null
}

const statusIcon: Record<string, React.ReactNode> = {
  completed: <CheckCircle className="w-4 h-4 text-emerald-700" />,
  in_progress: <Clock className="w-4 h-4 text-amber-700 animate-pulse" />,
  failed: <AlertCircle className="w-4 h-4 text-red-700" />,
  pending: <Circle className="w-4 h-4 text-[var(--color-text-secondary)]" />,
}

function formatElapsed(ms: number): string {
  const secs = Math.floor(ms / 1000)
  if (secs < 60) return `${secs}s`
  const mins = Math.floor(secs / 60)
  const remainder = secs % 60
  return `${mins}m ${remainder}s`
}

export function RobotExecutionModal({
  isOpen,
  onClose,
  robotId,
  robotType,
  tasks,
  allTasks,
  elapsedTimes,
  taskServerInfo,
}: RobotExecutionModalProps) {
  const [expandedResults, setExpandedResults] = useState<Set<number>>(new Set())
  const telemetryRobotId = taskServerInfo
    ? `${taskServerInfo.host}:${taskServerInfo.port}`
    : robotId
  const telemetry = useTelemetryStream(isOpen ? telemetryRobotId : null)

  const taskMap = new Map(allTasks.map(t => [t.task_id, t]))

  const currentTask = tasks.find(t => t.status === 'in_progress')
  const completedTasks = tasks.filter(t => t.status === 'completed' || t.status === 'failed')
  const pendingTasks = tasks.filter(t => t.status === 'pending')

  const toggleResult = (taskId: number) => {
    const next = new Set(expandedResults)
    if (next.has(taskId)) next.delete(taskId)
    else next.add(taskId)
    setExpandedResults(next)
  }

  const depsReady = (task: Task) =>
    task.dependency_task_ids.every(depId => {
      const dep = taskMap.get(depId)
      return dep && dep.status === 'completed'
    })

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`@${robotId} (${robotType})`} size="wide">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_0.8fr] gap-6 max-h-[75vh] overflow-y-auto pr-1">
        {/* Left column: task info */}
        <div className="space-y-5">
          {/* Current task */}
          <div>
            <h4 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">
              Current Task
            </h4>
            {currentTask ? (
              <div className="p-4 rounded-lg border-2 border-amber-400 bg-amber-50">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="w-4 h-4 text-amber-700 animate-pulse" />
                  <span className="text-xs font-mono text-amber-950">#{currentTask.task_id}</span>
                  <StatusBadge status="in_progress" />
                  {elapsedTimes.has(currentTask.task_id) && (
                    <span className="text-xs font-mono text-amber-900 ml-auto">
                      {formatElapsed(elapsedTimes.get(currentTask.task_id)!)}
                    </span>
                  )}
                </div>
                <p className="text-[var(--color-text)] text-sm leading-relaxed">{currentTask.description}</p>
                {currentTask.dependency_task_ids.length > 0 && (
                  <div className="flex items-center gap-1.5 mt-2 text-xs text-[var(--color-text-secondary)]">
                    <span>Deps:</span>
                    {currentTask.dependency_task_ids.map(depId => (
                      <TaskIdChip key={depId} taskId={depId} task={taskMap.get(depId)} />
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/40 text-center text-sm text-[var(--color-text-muted)]">
                {completedTasks.length === tasks.length ? 'All tasks complete' : 'Idle — waiting for dependencies'}
              </div>
            )}
          </div>

          {/* Pending tasks */}
          {pendingTasks.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">
                Queued ({pendingTasks.length})
              </h4>
              <div className="space-y-2">
                {pendingTasks.map(task => (
                  <div
                    key={task.task_id}
                    className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 bg-slate-50/30"
                  >
                    {statusIcon.pending}
                    <span className="text-xs font-mono text-[var(--color-text-muted)]">#{task.task_id}</span>
                    <p className="text-sm text-[var(--color-text-secondary)] flex-1 truncate">{task.description}</p>
                    <span className={cn(
                      'text-xs px-1.5 py-0.5 rounded',
                      depsReady(task)
                        ? 'bg-emerald-100 text-emerald-950 border border-emerald-300'
                        : 'bg-slate-100 text-[var(--color-text-muted)]'
                    )}>
                      {depsReady(task) ? 'Ready' : 'Blocked'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Completed tasks */}
          {completedTasks.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">
                Completed ({completedTasks.length})
              </h4>
              <div className="space-y-2">
                {[...completedTasks].reverse().map(task => (
                  <div
                    key={task.task_id}
                    className={cn(
                      'rounded-lg border bg-slate-50/30',
                      task.status === 'failed' ? 'border-red-500/25' : 'border-slate-200'
                    )}
                  >
                    <div
                      className="flex items-center gap-3 p-3 cursor-pointer"
                      onClick={() => task.result && toggleResult(task.task_id)}
                    >
                      {statusIcon[task.status] || statusIcon.pending}
                      <span className={cn(
                        'text-xs font-mono font-medium',
                        task.status === 'failed' ? 'text-red-950' : 'text-slate-900'
                      )}>
                        #{task.task_id}
                      </span>
                      <p className="text-sm text-[var(--color-text-secondary)] flex-1 truncate">{task.description}</p>
                      <StatusBadge status={task.status} />
                      {task.result && (
                        expandedResults.has(task.task_id)
                          ? <ChevronDown className="w-3.5 h-3.5 text-[var(--color-text-secondary)]" />
                          : <ChevronRight className="w-3.5 h-3.5 text-[var(--color-text-secondary)]" />
                      )}
                    </div>
                    {expandedResults.has(task.task_id) && task.result && (
                      <div className="px-3 pb-3">
                        <div className="bg-surface/80 rounded p-3 border border-slate-200">
                          <div className="flex items-center gap-1.5 mb-1.5">
                            <MessageSquare className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                            <span className="text-xs font-medium text-[var(--color-text-muted)]">Result</span>
                          </div>
                          <pre className="text-xs text-[var(--color-text-secondary)] whitespace-pre-wrap font-mono leading-relaxed">
                            {task.result}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right column: live telemetry */}
        <div className="space-y-4">
          {/* Connection indicator */}
          <div className="flex items-center gap-2 text-xs">
            {telemetry.connected ? (
              <>
                <Wifi className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-700 font-medium">Telemetry connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-slate-400">Telemetry disconnected</span>
              </>
            )}
          </div>

          {/* Video feed — MJPEG stream from telemetry server media plane */}
          <div className="rounded-lg border border-slate-200 bg-slate-50/60 overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-slate-200">
              <Video className="w-4 h-4 text-[var(--color-text-muted)]" />
              <span className="text-sm font-medium text-[var(--color-text-secondary)]">Live Video Feed</span>
              <span className="text-xs text-[var(--color-text-muted)] ml-auto font-mono">MJPEG</span>
            </div>
            {telemetryRobotId ? (
              <div className="aspect-video bg-black flex items-center justify-center">
                <LiveVideoCanvas robotId={telemetryRobotId} className="w-full h-full" />
              </div>
            ) : (
              <div className="aspect-video flex flex-col items-center justify-center text-[var(--color-text-muted)] bg-surface/50">
                <Video className="w-10 h-10 mb-3 opacity-40" />
                <p className="text-sm">No video feed available</p>
              </div>
            )}
          </div>

          {/* Joint states */}
          <div className="rounded-lg border border-slate-200 bg-slate-50/60 overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-slate-200">
              <Activity className="w-4 h-4 text-[var(--color-text-muted)]" />
              <span className="text-sm font-medium text-[var(--color-text-secondary)]">Joint States</span>
            </div>
            <div className="p-4">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-[var(--color-text-muted)] border-b border-slate-200">
                    <th className="text-left pb-2 font-medium">Joint</th>
                    <th className="text-right pb-2 font-medium">Position</th>
                    <th className="text-right pb-2 font-medium">Velocity</th>
                    <th className="text-right pb-2 font-medium">Effort</th>
                  </tr>
                </thead>
                <tbody className="text-[var(--color-text)]">
                  {telemetry.jointStates.length > 0 ? (
                    telemetry.jointStates.map((joint) => (
                      <tr key={joint.name} className="border-b border-slate-200">
                        <td className="py-1.5 font-mono text-slate-700">{joint.name}</td>
                        <td className="py-1.5 text-right font-mono">{joint.position.toFixed(4)}</td>
                        <td className="py-1.5 text-right font-mono">{joint.velocity.toFixed(4)}</td>
                        <td className="py-1.5 text-right font-mono">{joint.effort.toFixed(4)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="py-4 text-center text-[var(--color-text-muted)]">
                        No joint data received
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Action command log */}
          <div className="rounded-lg border border-slate-200 bg-slate-50/60 overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-slate-200">
              <Terminal className="w-4 h-4 text-[var(--color-text-muted)]" />
              <span className="text-sm font-medium text-[var(--color-text-secondary)]">Action Commands</span>
              {telemetry.actionLog.length > 0 && (
                <span className="text-xs text-[var(--color-text-muted)] ml-auto">{telemetry.actionLog.length} entries</span>
              )}
            </div>
            <div className="max-h-40 overflow-y-auto">
              {telemetry.actionLog.length > 0 ? (
                <div className="divide-y divide-slate-200">
                  {telemetry.actionLog.slice(0, 20).map((entry, i) => (
                    <div key={i} className="px-4 py-2 text-xs">
                      <div className="flex items-center gap-2">
                        {entry.attributes?.cmd_type && (
                          <span className="font-mono text-cyan-700 bg-cyan-50 px-1.5 py-0.5 rounded">
                            {entry.attributes.cmd_type}
                          </span>
                        )}
                        <span className="text-[var(--color-text-muted)] font-mono">
                          {entry.signals.map(s => `${s.name}: ${s.values[0]?.toFixed(3)}`).join(', ')}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-24 flex flex-col items-center justify-center text-[var(--color-text-muted)]">
                  <Terminal className="w-8 h-8 mb-2 opacity-40" />
                  <p className="text-xs">No commands received</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Modal>
  )
}
