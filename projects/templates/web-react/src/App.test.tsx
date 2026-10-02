import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

afterEach(() => vi.restoreAllMocks())

describe('App', () => {
  it('muestra carga y luego los datos con el total', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => [{ region: 'Norte', ingreso: 5 }, { region: 'Sur', ingreso: 7 }] }))
    render(<App />)
    expect(screen.getByRole('status')).toHaveTextContent('Cargando')
    expect(await screen.findByText('Total: 12')).toBeInTheDocument()
  })

  it('muestra error si la petición falla', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500 }))
    render(<App />)
    expect(await screen.findByRole('alert')).toHaveTextContent('HTTP 500')
  })
})
