import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Globe, Plus, Trash2, MessageSquare } from 'lucide-react'
import { Card } from '../components/common/Card'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/common/Button'
import { Modal } from '../components/common/Modal'
import { EmptyState } from '../components/common/EmptyState'
import { worldApi } from '../lib/api'
import { formatDate } from '../lib/utils'

function AddStatementModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [statement, setStatement] = useState('')
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: worldApi.add,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['world'] })
      onClose()
      setStatement('')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate({ statement })
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add World Statement">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
            Statement
          </label>
          <textarea
            value={statement}
            onChange={(e) => setStatement(e.target.value)}
            placeholder="Describe a fact about the world state..."
            rows={4}
            className="w-full px-4 py-3 bg-white/90 ring-1 ring-slate-200/70 rounded-xl text-[var(--color-text)] placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 resize-none"
            required
          />
          <p className="text-xs text-[var(--color-text-muted)] mt-2">
            Examples: "There is a kitchen and a living room", "The kitchen has 2 cups", "The robot is at the entrance"
          </p>
        </div>

        {mutation.error && (
          <p className="text-sm text-red-400">{(mutation.error as Error).message}</p>
        )}

        <div className="flex justify-end gap-3 pt-4">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Adding...' : 'Add Statement'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

export function World() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: statements = [], isLoading } = useQuery({
    queryKey: ['world'],
    queryFn: worldApi.list,
  })

  const deleteMutation = useMutation({
    mutationFn: worldApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['world'] })
    },
  })

  if (isLoading) {
    return <div className="text-[var(--color-text-secondary)]">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="World State"
        meta={<>{statements.length} statements defined</>}
        actions={
          <Button onClick={() => setIsModalOpen(true)}>
            <Plus className="w-4 h-4" />
            Add Statement
          </Button>
        }
      />

      {/* Info Card */}
      <Card className="border-l-[3px] border-l-cyan-500 bg-[var(--color-surface-raised)]">
        <div className="flex items-start gap-3">
          <Globe className="w-5 h-5 text-cyan-800 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-[var(--color-text)] mb-1">About World State</h3>
            <p className="text-sm text-[var(--color-text-secondary)]">
              World statements describe the current state of the environment. The planner uses these 
              statements to understand the context and generate appropriate task plans. Be descriptive 
              about locations, objects, and their relationships.
            </p>
          </div>
        </div>
      </Card>

      {/* Statements List */}
      {statements.length > 0 ? (
        <div className="space-y-3">
          {statements.map((ws) => (
            <Card key={ws.id} className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 ring-1 ring-emerald-200/60 flex items-center justify-center flex-shrink-0">
                <MessageSquare className="w-5 h-5 text-emerald-600" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-[var(--color-text)]">{ws.statement}</p>
                    <p className="text-xs text-[var(--color-text-muted)] mt-1 font-mono">
                      ID: {ws.id.substring(0, 8)}... • {formatDate(ws.created_at)}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteMutation.mutate(ws.id)}
                    className="text-red-400 hover:text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<Globe className="w-8 h-8" />}
          title="No world statements"
          description="Add statements to describe the current state of your environment for the planner."
          action={
            <Button onClick={() => setIsModalOpen(true)}>
              <Plus className="w-4 h-4" />
              Add Statement
            </Button>
          }
        />
      )}

      <AddStatementModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </div>
  )
}
