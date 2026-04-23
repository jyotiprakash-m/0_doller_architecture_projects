import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import RepoList from '@/components/RepoList'

test('renders tracked repositories title', () => {
  render(<RepoList />)
  expect(screen.getByText('Tracked Repositories')).toBeDefined()
})

test('renders list of repositories', () => {
  render(<RepoList />)
  
  expect(screen.getByText('ghost-editor-core')).toBeDefined()
  expect(screen.getByText('legal-auditor-frontend')).toBeDefined()
  expect(screen.getByText('data-generator-api')).toBeDefined()
})

test('renders status badges correctly', () => {
  render(<RepoList />)
  const activeStatuses = screen.getAllByText('Active')
  const syncingStatuses = screen.getAllByText('Syncing')
  
  expect(activeStatuses.length).toBe(2)
  expect(syncingStatuses.length).toBe(1)
})

test('renders action buttons', () => {
  render(<RepoList />)
  const buttons = screen.getAllByRole('button', { name: /force sync/i })
  expect(buttons.length).toBe(3)
})
