import { useEffect, useState } from 'react'

type Row = { region: string; ingreso: number }
type State = { status: 'loading' } | { status: 'error'; message: string } | { status: 'ok'; rows: Row[] }

export default function App({ url = '/data.json' }: { url?: string }) {
  const [state, setState] = useState<State>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false
    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<Row[]>
      })
      .then((rows) => !cancelled && setState({ status: 'ok', rows }))
      .catch((e: Error) => !cancelled && setState({ status: 'error', message: e.message }))
    return () => {
      cancelled = true
    }
  }, [url])

  if (state.status === 'loading') return <p role="status">Cargando…</p>
  if (state.status === 'error') return <p role="alert">Error al cargar: {state.message}</p>
  const total = state.rows.reduce((a, r) => a + r.ingreso, 0)
  return (
    <main>
      <h1>Ingresos por región</h1>
      <ul>
        {state.rows.map((r) => (
          <li key={r.region}>
            {r.region}: {r.ingreso}
          </li>
        ))}
      </ul>
      <p>Total: {total}</p>
    </main>
  )
}
