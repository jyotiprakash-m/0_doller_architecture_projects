import { render, screen } from '@testing-library/react'
import { expect, test, vi } from 'vitest'
import Home from '@/app/page'

// Mock components
vi.mock('@/components/DashboardStats', () => ({
  default: () => <div data-testid="dashboard-stats">Dashboard Stats</div>
}))

vi.mock('@/components/RepoList', () => ({
  default: () => <div data-testid="repo-list">Repo List</div>
}))

test('renders dashboard heading', () => {
  render(<Home />)
  const heading = screen.getByRole('heading', { level: 1, name: /dashboard/i })
  expect(heading).toBeDefined()
})

test('renders agent active message', () => {
  render(<Home />)
  expect(screen.getByText(/Agent is Active and Listening/i)).toBeDefined()
})

test('renders subcomponents', () => {
  render(<Home />)
  expect(screen.getByTestId('dashboard-stats')).toBeDefined()
  expect(screen.getByTestId('repo-list')).toBeDefined()
})
