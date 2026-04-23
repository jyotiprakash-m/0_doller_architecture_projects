import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import DashboardStats from '@/components/DashboardStats'

test('renders all three stat cards', () => {
  render(<DashboardStats />)
  
  expect(screen.getByText('Tracked Repositories')).toBeDefined()
  expect(screen.getByText('Active PRs Analysed')).toBeDefined()
  expect(screen.getByText('Docs Auto-Updated')).toBeDefined()
})

test('renders correct values', () => {
  render(<DashboardStats />)
  
  expect(screen.getByText('12')).toBeDefined()
  expect(screen.getByText('34')).toBeDefined()
  expect(screen.getByText('156')).toBeDefined()
})

test('renders trend icons and meta text', () => {
  render(<DashboardStats />)
  
  expect(screen.getByText(/98% success rate/i)).toBeDefined()
  expect(screen.getByText(/\+2 this week/i)).toBeDefined()
})
