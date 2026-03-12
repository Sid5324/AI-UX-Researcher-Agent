'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { FormEvent, useEffect, useState } from 'react'
import { workspacesApi } from '@/lib/api'
import { useAuth } from '@/hooks/useAuth'

type Workspace = {
  id: string
  name: string
  description?: string
}

export default function WorkspacesPage() {
  const router = useRouter()
  const { user, init, initialized, backendOnline } = useAuth()
  const [items, setItems] = useState<Workspace[]>([])
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    void init()
  }, [init])

  useEffect(() => {
    if (initialized && !user) {
      router.push('/login')
    }
  }, [initialized, user, router])

  const load = async () => {
    setLoading(true)
    try {
      setItems(await workspacesApi.list())
      setError(null)
    } catch {
      setError('Unable to load workspaces. Ensure you are authenticated.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (initialized && user) {
      void load()
    }
  }, [initialized, user])

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!backendOnline) {
      setError('Cannot create workspace: Backend server is offline')
      return
    }
    try {
      await workspacesApi.create(name, description || undefined)
      setName('')
      setDescription('')
      await load()
    } catch {
      setError('Failed to create workspace.')
    }
  }

  if (!initialized || !user) {
    return <main className="min-h-screen bg-slate-950 p-8 text-slate-100">Loading...</main>
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-semibold text-white">Workspaces</h1>
          <Link href="/dashboard" className="text-cyan-300 underline">
            Back to dashboard
          </Link>
        </div>

        {!backendOnline && (
          <div className="mb-6 rounded-lg border border-rose-500/50 bg-rose-500/10 p-4">
            <p className="text-rose-400">
              <span className="font-semibold">Backend Offline:</span> Cannot create workspaces or load data.
              Please start the backend server on port 8000.
            </p>
          </div>
        )}

        <form className="mb-8 rounded-xl border border-slate-800 bg-slate-900/70 p-5" onSubmit={onSubmit}>
          <h2 className="text-lg font-medium text-white">Create workspace</h2>
          <input
            className="mt-3 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-white disabled:opacity-50"
            placeholder="Workspace name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            disabled={!backendOnline}
          />
          <textarea
            className="mt-3 h-24 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-white disabled:opacity-50"
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={!backendOnline}
          />
          <button
            className="mt-3 rounded-md bg-cyan-500 px-4 py-2 font-semibold text-slate-950 disabled:opacity-60 disabled:cursor-not-allowed"
            type="submit"
            disabled={!backendOnline}
            title={!backendOnline ? 'Backend server is offline' : ''}
          >
            {!backendOnline ? 'Backend Offline' : 'Create'}
          </button>
        </form>

        {loading && <p className="text-slate-300">Loading...</p>}
        {error && <p className="mb-3 text-rose-300">{error}</p>}
        <div className="grid gap-3">
          {items.map((item) => (
            <article key={item.id} className="rounded-lg border border-slate-800 bg-slate-900/70 p-4">
              <h3 className="font-medium text-white">{item.name}</h3>
              <p className="mt-1 text-sm text-slate-300">{item.description || 'No description provided.'}</p>
            </article>
          ))}
        </div>
      </div>
    </main>
  )
}
