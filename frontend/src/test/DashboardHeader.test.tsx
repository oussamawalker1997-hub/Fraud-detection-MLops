import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DashboardHeader } from '../components/DashboardHeader'

describe('DashboardHeader', () => {
  it('shows the checking state', () => {
    render(<DashboardHeader ready={false} checking={true} />)

    expect(screen.getByRole('status')).toHaveTextContent('Checking model')
    expect(screen.getByRole('heading', { name: 'Fraud Intelligence' })).toBeInTheDocument()
  })

  it('shows model ready', () => {
    render(<DashboardHeader ready={true} checking={false} />)

    expect(screen.getByRole('status')).toHaveTextContent('Model ready')
  })

  it('shows model unavailable', () => {
    render(<DashboardHeader ready={false} checking={false} />)

    expect(screen.getByRole('status')).toHaveTextContent('Model unavailable')
  })
})
