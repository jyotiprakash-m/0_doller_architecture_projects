import { render, screen } from '@testing-library/react'
import { expect, test, vi } from 'vitest'
import Sidebar from '@/components/Sidebar'

// Mock next/navigation
vi.mock('next/navigation', () => ({
  usePathname: () => '/',
}))

// Mock next/link to just render children
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode, href: string }) => (
    <a href={href}>{children}</a>
  ),
}))

test('renders logo and name', () => {
  render(<Sidebar />)
  expect(screen.getByText('Ghost-Editor')).toBeDefined()
  expect(screen.getByText('👻')).toBeDefined()
})

test('renders navigation items', () => {
  render(<Sidebar />)
  expect(screen.getByText('Dashboard')).toBeDefined()
  expect(screen.getByText('Repositories')).toBeDefined()
  expect(screen.getByText('Jobs')).toBeDefined()
  expect(screen.getByText('Settings')).toBeDefined()
})

test('renders status indicator', () => {
  render(<Sidebar />)
  expect(screen.getByText('Agent Ready')).toBeDefined()
})
