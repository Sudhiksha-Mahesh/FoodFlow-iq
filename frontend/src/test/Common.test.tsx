import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KpiCard, EmptyState, UnavailableState, StatusBadge } from '../components/Common'

describe('KpiCard', () => {
  it('renders label and value', () => {
    render(<KpiCard label="Total Revenue" value="₹1,234" />)
    expect(screen.getByText('Total Revenue')).toBeInTheDocument()
    expect(screen.getByText('₹1,234')).toBeInTheDocument()
  })
})

describe('EmptyState', () => {
  it('renders the title and optional description', () => {
    render(<EmptyState title="No dataset loaded" description="Upload a CSV to begin." />)
    expect(screen.getByText('No dataset loaded')).toBeInTheDocument()
    expect(screen.getByText('Upload a CSV to begin.')).toBeInTheDocument()
  })
})

describe('UnavailableState', () => {
  it('explains why a module is unavailable rather than showing fabricated data', () => {
    render(<UnavailableState reason="Delivery time columns missing" />)
    expect(screen.getByText(/isn't available/i)).toBeInTheDocument()
    expect(screen.getByText('Delivery time columns missing')).toBeInTheDocument()
  })
})

describe('StatusBadge', () => {
  it('shows the correct label for each status', () => {
    const { rerender } = render(<StatusBadge status="available" />)
    expect(screen.getByText(/Available/)).toBeInTheDocument()
    rerender(<StatusBadge status="partial" />)
    expect(screen.getByText(/Partial/)).toBeInTheDocument()
    rerender(<StatusBadge status="unavailable" />)
    expect(screen.getByText(/Unavailable/)).toBeInTheDocument()
  })
})
