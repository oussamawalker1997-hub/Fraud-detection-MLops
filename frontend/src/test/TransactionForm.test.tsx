import { describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { TransactionForm } from '../components/TransactionForm'

const features = [
  'Time',
  'Amount',
  ...Array.from({ length: 28 }, (_, i) => `V${i + 1}`),
]

const createValues = () =>
  Object.fromEntries(features.map((feature) => [feature, 0]))

describe('TransactionForm', () => {
  it('renders all 30 required features', () => {
    render(
      <TransactionForm
        values={createValues()}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        disabled={false}
        loading={false}
      />
    )

    expect(screen.getAllByRole('spinbutton')).toHaveLength(30)

    for (const feature of features) {
      expect(screen.getByRole('spinbutton', { name: feature }))
        .toBeInTheDocument()
    }
  })

  it('converts numeric input into a number', () => {
    const onChange = vi.fn()

    render(
      <TransactionForm
        values={createValues()}
        onChange={onChange}
        onSubmit={vi.fn()}
        disabled={false}
        loading={false}
      />
    )

    fireEvent.change(
      screen.getByRole('spinbutton', { name: 'Amount' }),
      { target: { value: '149.75' } }
    )

    expect(onChange).toHaveBeenCalledWith('Amount', 149.75)
  })

  it('preserves an empty value when a field is cleared', () => {
    const onChange = vi.fn()

    render(
      <TransactionForm
        values={createValues()}
        onChange={onChange}
        onSubmit={vi.fn()}
        disabled={false}
        loading={false}
      />
    )

    fireEvent.change(
      screen.getByRole('spinbutton', { name: 'Amount' }),
      { target: { value: '' } }
    )

    expect(onChange).toHaveBeenCalledWith('Amount', '')
  })

  it('disables fields and submission when unavailable', () => {
    render(
      <TransactionForm
        values={createValues()}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        disabled={true}
        loading={false}
      />
    )

    expect(screen.getByRole('button', { name: /Analyze transaction/i }))
      .toBeDisabled()

    for (const input of screen.getAllByRole('spinbutton')) {
      expect(input).toBeDisabled()
    }
  })
})
