'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useEffect, useMemo, useState } from 'react'
import { useGoal } from '@/hooks/useGoals'
import { GoalSocket, GoalSocketMessage } from '@/lib/websocket'
import { useAuth } from '@/hooks/useAuth'

export default function GoalDetailPage() {
  const router = useRouter()
  const params = useParams<{ id: string }>()
  const goalId = params.id
  const { user, init, initialized, backendOnline, error: authError } = useAuth()
  const goalQuery = useGoal(goalId)
  const [events, setEvents] = useState<GoalSocketMessage[]>([])

  useEffect(() => {
    void init()
  }, [init])

  useEffect(() => {
    if (initialized && !user) {
      router.push('/login')
    }
  }, [initialized, user, router])

  const socket = useMemo(() => {
    if (!goalId) return null
    return new GoalSocket(goalId, (message) => {
      setEvents((prev) => [message, ...prev].slice(0, 15))
    })
  }, [goalId])

  useEffect(() => {
    socket?.connect()
    return () => socket?.disconnect()
  }, [socket])

  if (!initialized || !user) {
    return <main className="min-h-screen bg-slate-950 p-8 text-slate-100">Loading...</main>
  }

  if (goalQuery.isLoading) {
    return <main className="min-h-screen bg-slate-950 p-8 text-slate-100">Loading goal...</main>
  }

  if (goalQuery.isError || !goalQuery.data) {
    return (
      <main className="min-h-screen bg-slate-950 p-8 text-slate-100">
        {!backendOnline && (
          <div className="mb-4 rounded-lg border border-rose-500/50 bg-rose-500/10 p-4">
            <p className="text-rose-400">
              <span className="font-semibold">Backend Offline:</span> Cannot load goal details.
              Please start the backend server on port 8000.
            </p>
          </div>
        )}
        <p className="text-rose-300">{authError || 'Failed to load goal details.'}</p>
        <Link href="/dashboard" className="mt-4 inline-block text-cyan-300 underline">
          Back to dashboard
        </Link>
      </main>
    )
  }

  const { goal, agents, checkpoints } = goalQuery.data

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl px-6 py-10">
        <Link href="/dashboard" className="text-sm text-cyan-300 underline">
          Back to dashboard
        </Link>
        <h1 className="mt-3 text-3xl font-semibold text-white">Goal Details</h1>
        <p className="mt-2 rounded-lg border border-slate-800 bg-slate-900/80 p-4 text-slate-200">{goal.description}</p>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <StatCard label="Status" value={goal.status} />
          <StatCard label="Progress" value={`${goal.progress_percent.toFixed(0)}%`} />
          <StatCard label="Budget" value={goal.budget_usd ? `$${goal.budget_usd}` : 'N/A'} />
        </div>

        <section className="mt-8 grid gap-4 md:grid-cols-2">
          <article className="rounded-xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-medium text-white">Agent execution</h2>
            <div className="mt-3 space-y-2">
              {agents.map((agent) => (
                <div key={`${agent.name}-${agent.status}`} className="rounded-md border border-slate-800 bg-slate-950/60 p-3">
                  <p className="text-sm text-cyan-300">{agent.status.toUpperCase()}</p>
                  <p className="font-medium text-white">{agent.name}</p>
                  {agent.current_step && <p className="text-sm text-slate-300">{agent.current_step}</p>}
                </div>
              ))}
              {agents.length === 0 && <p className="text-sm text-slate-300">No agent states yet.</p>}
            </div>
          </article>

          <article className="rounded-xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-medium text-white">Checkpoints</h2>
            <div className="mt-3 space-y-2">
              {checkpoints.map((checkpoint) => (
                <div key={checkpoint.id} className="rounded-md border border-slate-800 bg-slate-950/60 p-3">
                  <p className="text-sm text-cyan-300">{checkpoint.status.toUpperCase()}</p>
                  <p className="font-medium text-white">{checkpoint.title}</p>
                </div>
              ))}
              {checkpoints.length === 0 && <p className="text-sm text-slate-300">No checkpoints yet.</p>}
            </div>
          </article>
        </section>

        <section className="mt-8 rounded-xl border border-slate-800 bg-slate-900/70 p-5">
          <h2 className="text-lg font-medium text-white">Real-time events</h2>
          <div className="mt-3 space-y-2">
            {events.map((event, idx) => (
              <div key={`${event.timestamp || idx}-${idx}`} className="rounded-md border border-slate-800 bg-slate-950/60 p-3">
                <p className="text-sm text-cyan-300">{event.type}</p>
                <pre className="mt-1 overflow-x-auto text-xs text-slate-300">{JSON.stringify(event, null, 2)}</pre>
              </div>
            ))}
            {events.length === 0 && <p className="text-sm text-slate-300">Waiting for websocket updates...</p>}
          </div>
        </section>
      </div>
    </main>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-xl border border-slate-800 bg-slate-900/70 p-5">
      <p className="text-sm text-slate-300">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-white">{value}</p>
    </article>
  )
}
