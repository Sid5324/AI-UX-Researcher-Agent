import Link from 'next/link'

const steps = [
  'Capture a natural-language research goal',
  'Run autonomous multi-agent analysis',
  'Review checkpoints and findings',
  'Export implementation-ready outputs',
]

export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl px-6 py-16">
        <header className="mb-16">
          <p className="mb-4 inline-block rounded-full border border-cyan-400/40 bg-cyan-500/10 px-4 py-1 text-sm text-cyan-200">
            Agentic Research Platform
          </p>
          <h1 className="max-w-3xl text-5xl font-semibold leading-tight text-white">
            Product research from goal to decision package in one workflow
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-slate-300">
            This app orchestrates data, PRD, design, validation, competitor, interview, and feedback agents and tracks
            progress in real time.
          </p>
          <div className="mt-8 flex gap-4">
            <Link href="/register" className="rounded-lg bg-cyan-500 px-5 py-3 font-medium text-slate-950 hover:bg-cyan-400">
              Create account
            </Link>
            <Link href="/login" className="rounded-lg border border-slate-700 px-5 py-3 font-medium hover:bg-slate-900">
              Sign in
            </Link>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-2">
          {steps.map((step, idx) => (
            <article key={step} className="rounded-xl border border-slate-800 bg-slate-900/70 p-5">
              <p className="text-sm text-cyan-300">Step {idx + 1}</p>
              <h2 className="mt-2 text-xl font-medium text-white">{step}</h2>
            </article>
          ))}
        </section>
      </div>
    </main>
  )
}
