import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Activity } from 'lucide-react'
import { MetricCard } from '../components/MetricCard'

describe('MetricCard', () => {
  it('displays a metric with three decimal places', () => {
    render(
      <MetricCard
        label="Precision"
        value={0.881234}
        icon={Activity}
        description="Precision on held-out test data"
      />
    )

    expect(screen.getByText('Precision')).toBeInTheDocument()
    expect(screen.getByText('0.881')).toBeInTheDocument()
    expect(
      screen.getByText('Precision on held-out test data')
    ).toBeInTheDocument()
  })

  it('displays zero correctly', () => {
    render(
      <MetricCard
        label="Recall"
        value={0}
        icon={Activity}
        description="Recall metric"
      />
    )

    expect(screen.getByText('0.000')).toBeInTheDocument()
  })
})
