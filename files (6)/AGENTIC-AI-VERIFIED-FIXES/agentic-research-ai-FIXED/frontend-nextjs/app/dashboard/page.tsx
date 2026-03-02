'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { FormEvent, useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useCreateGoal, useGoals } from '@/hooks/useGoals'

export default function DashboardPage() {
  const router = useRouter()
  const { user, init, initialized, logout } = useAuth()
  const goalsQuery = useGoals()
  const createGoal = useCreateGoal()
  const [description, setDescription] = useState(
    'Analyze onboarding drop-off and generate prioritized UX + PRD recommendations for activation lift.',
  )
  const [budget, setBudget] = useState('2000')
  const [timeline, setTimeline] = useState('7')

  useEffect(() => {
    void init()
  }, [init])

  useEffect(() => {
    if (initialized && !user) {
      router.push('/login')
    }
  }, [initialized, user, router])

  const onCreateGoal = async (e: FormEvent) => {
    e.preventDefault()
    const goal = await createGoal.mutateAsync({
      description,
      budget_usd: Number.isFinite(Number(budget)) ? Number(budget) : undefined,
      timeline_days: Number.isFinite(Number(timeline)) ? Number(timeline) : undefined,
    })
    router.push(`/goals/${goal.id}`)
  }

  if (!initialized || !user) {
    return <main className="min-h-screen bg-slate-950 p-8 text-slate-100">Loading dashboard...</main>
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-semibold text-white">Research Dashboard</h1>
            <p className="text-sm text-slate-300">
              Logged in as {user.name} ({user.email})
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/workspaces" className="rounded-md border border-slate-700 px-4 py-2 text-sm hover:bg-slate-900">
              Workspaces
            </Link>
            <button
              onClick={logout}
              className="rounded-md border border-slate-700 px-4 py-2 text-sm hover:bg-slate-900"
              type="button"
            >
              Sign out
            </button>
          </div>
        </div>

        <section className="mb-8 rounded-xl border border-slate-800 bg-slate-900/70 p-6">
          <h2 className="text-xl font-medium text-white">Start new autonomous research</h2>
          <form className="mt-4 grid gap-4" onSubmit={onCreateGoal}>
            <label className="text-sm text-slate-300">
              Goal description
              <textarea
                className="mt-2 h-28 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-white"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                minLength={10}
                required
              />
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-sm text-slate-300">
                Budget (USD)
                <input
                  className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-white"
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  type="number"
                  min={0}
                />
              </label>
              <label className="text-sm text-slate-300">
                Timeline (days)
                <input
                  className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-white"
                  value={timeline}
                  onChange={(e) => setTimeline(e.target.value)}
                  type="number"
                  min={1}
                />
              </label>
            </div>
            <button
              type="submit"
              disabled={createGoal.isPending}
              className="rounded-md bg-cyan-500 px-4 py-2 font-semibold text-slate-950 disabled:opacity-60"
            >
              {createGoal.isPending ? 'Starting agents...' : 'Create and run'}
            </button>
          </form>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/70 p-6">
          <h2 className="text-xl font-medium text-white">Recent goals</h2>
          {goalsQuery.isLoading && <p className="mt-3 text-sm text-slate-300">Loading goals...</p>}
          {goalsQuery.isError && <p className="mt-3 text-sm text-rose-300">Unable to load goals.</p>}
          <div className="mt-4 grid gap-3">
            {(goalsQuery.data || []).map((goal) => (
              <Link
                key={goal.id}
                href={`/goals/${goal.id}`}
                className="rounded-lg border border-slate-800 bg-slate-950/60 p-4 transition hover:border-cyan-500/40"
              >
                <p className="text-sm text-cyan-300">{goal.status.toUpperCase()}</p>
                <p className="mt-1 font-medium text-white">{goal.description}</p>
                <p className="mt-2 text-sm text-slate-300">
                  Progress: {goal.progress_percent.toFixed(0)}% • Mode: {goal.mode}
                </p>
              </Link>
            ))}
            {!goalsQuery.isLoading && (goalsQuery.data || []).length === 0 && (
              <p className="text-sm text-slate-300">No goals yet. Create your first one above.</p>
            )}
          </div>
        </section>
      </div>
    </main>
  )
}
