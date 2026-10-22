import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, within } from '@testing-library/react'
import { BatchCSV, type BatchResult } from '../components/BatchCSV'

const result: BatchResult = {
  result_id: 'demo-123',
  rows_received: 3,
  rows_processed: 2,
  rows_rejected: 1,
  predicted_positive: 0,
  duration_ms: 120,
  score_semantics: 'Uncalibrated model score',
  model_version: 'test-model',
  download_url: '/predict/batch/demo-123/download',
  results: [
    { row: 2, status: 'scored', predicted_label: 0, model_score: 0.00026 },
    { row: 3, status: 'scored', predicted_label: 0, model_score: 0.01234 },
    {
      row: 4,
      status: 'rejected',
      error: 'Amount: float_parsing: invalid numeric value',
    },
  ],
}

const defaultProps = {
  batch: null,
  loading: false,
  error: null,
  disabled: false,
  apiUrl: '/api',
  onUpload: vi.fn(),
}

describe('BatchCSV', () => {
  it('shows the CSV upload field', () => {
    render(<BatchCSV {...defaultProps} />)

    expect(screen.getByText('Batch Fraud Analysis')).toBeInTheDocument()
    expect(screen.getByText('Choose a CSV file')).toBeInTheDocument()
  })

  it('calls onUpload when a CSV is selected', () => {
    const onUpload = vi.fn()

    const { container } = render(
      <BatchCSV {...defaultProps} onUpload={onUpload} />
    )

    const input = container.querySelector('input[type="file"]')
    expect(input).not.toBeNull()

    const file = new File(['Time,Amount\n0,10'], 'demo.csv', {
      type: 'text/csv',
    })

    fireEvent.change(input!, { target: { files: [file] } })

    expect(onUpload).toHaveBeenCalledOnce()
  })

  it('displays processing statistics and rejected rows', () => {
    render(<BatchCSV {...defaultProps} batch={result} />)

    for (const [label, count] of [
      ['Received', '3'],
      ['Processed', '2'],
      ['Rejected', '1'],
      ['Flagged', '0'],
    ]) {
      const labelElement = screen.getByText(label)
      const card = labelElement.parentElement!
      expect(within(card).getByText(count)).toBeInTheDocument()
    }

    expect(
      screen.getByText('Invalid Amount: expected a numeric value')
    ).toBeInTheDocument()
  })

  it('builds the correct report download URL', () => {
    render(<BatchCSV {...defaultProps} batch={result} />)

    expect(
      screen.getByRole('link', { name: /Download enriched CSV/i })
    ).toHaveAttribute(
      'href',
      '/api/predict/batch/demo-123/download'
    )
  })

  it('shows API errors and disables upload when unavailable', () => {
    const { container } = render(
      <BatchCSV
        {...defaultProps}
        error="Unable to process CSV"
        disabled={true}
      />
    )

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Unable to process CSV'
    )

    expect(container.querySelector('input[type="file"]')).toBeDisabled()
  })
})
