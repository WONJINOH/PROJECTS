/**
 * Test Utilities
 *
 * Provides:
 * - Custom render function with all providers
 * - Mock data factories
 * - Common test helpers
 */

import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import userEvent from '@testing-library/user-event'

// Create a new QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

interface WrapperProps {
  children: React.ReactNode
}

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  route?: string
  queryClient?: QueryClient
}

/**
 * Custom render function that wraps components with necessary providers
 */
function customRender(
  ui: ReactElement,
  {
    route = '/',
    queryClient = createTestQueryClient(),
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  // Set initial route
  window.history.pushState({}, 'Test page', route)

  function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>{children}</BrowserRouter>
      </QueryClientProvider>
    )
  }

  return {
    user: userEvent.setup(),
    queryClient,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  }
}

/**
 * Render with MemoryRouter for testing specific routes
 */
function renderWithRouter(
  ui: ReactElement,
  {
    initialEntries = ['/'],
    queryClient = createTestQueryClient(),
    ...renderOptions
  }: CustomRenderOptions & { initialEntries?: string[] } = {}
) {
  function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>
      </QueryClientProvider>
    )
  }

  return {
    user: userEvent.setup(),
    queryClient,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  }
}

// ===== Mock Data Factories =====

export const mockUser = {
  qpsStaff: {
    id: 1,
    username: 'qps_test',
    email: 'qps@test.hospital.kr',
    fullName: 'QPS 담당자',
    role: 'qps_staff',
    department: '환자안전팀',
  },
  reporter: {
    id: 2,
    username: 'reporter_test',
    email: 'reporter@test.hospital.kr',
    fullName: '김간호',
    role: 'reporter',
    department: '내과',
  },
  director: {
    id: 3,
    username: 'director_test',
    email: 'director@test.hospital.kr',
    fullName: '원장',
    role: 'director',
    department: '경영진',
  },
}

export const mockIncident = {
  basic: {
    id: 1,
    category: 'fall',
    grade: 'moderate',
    occurredAt: '2026-01-15T10:00:00Z',
    location: '3층 301호',
    description: '환자가 침대에서 낙상함',
    immediateAction: '의료진 호출, 환자 상태 확인',
    reportedAt: '2026-01-15T10:30:00Z',
    reporterName: '김간호',
    reporterId: 2,
    department: '내과',
    status: 'submitted',
    createdAt: '2026-01-15T10:30:00Z',
    updatedAt: '2026-01-15T10:30:00Z',
  },
  severe: {
    id: 2,
    category: 'fall',
    grade: 'severe',
    occurredAt: '2026-01-15T14:00:00Z',
    location: '2층 ICU',
    description: '중환자실 환자 낙상으로 골절 발생',
    immediateAction: '응급 처치, X-ray 촬영',
    reportedAt: '2026-01-15T14:30:00Z',
    reporterName: '박간호',
    reporterId: 2,
    department: '중환자실',
    status: 'submitted',
    createdAt: '2026-01-15T14:30:00Z',
    updatedAt: '2026-01-15T14:30:00Z',
  },
}

export const mockRisk = {
  basic: {
    id: 1,
    riskCode: 'R-2026-001',
    title: '낙상 위험 - 내과 병동',
    description: '내과 병동에서 반복적인 낙상 발생',
    sourceType: 'psr',
    category: 'fall',
    currentControls: '낙상 예방 교육, 침대 난간 확인',
    probability: 3,
    severity: 4,
    riskScore: 12,
    riskLevel: 'high',
    status: 'identified',
    ownerId: 1,
    createdById: 1,
    createdAt: '2026-01-15T10:00:00Z',
    updatedAt: '2026-01-15T10:00:00Z',
  },
  critical: {
    id: 2,
    riskCode: 'R-2026-002',
    title: '투약 오류 위험',
    description: '고위험 약물 투여 오류 위험',
    sourceType: 'psr',
    category: 'medication',
    currentControls: '더블체크 시스템',
    probability: 4,
    severity: 5,
    riskScore: 20,
    riskLevel: 'critical',
    status: 'treating',
    ownerId: 1,
    createdById: 1,
    createdAt: '2026-01-14T10:00:00Z',
    updatedAt: '2026-01-14T10:00:00Z',
  },
}

export const mockIndicator = {
  basic: {
    id: 1,
    code: 'PSR-001',
    name: '환자안전사건 보고율',
    category: 'psr',
    description: '월별 환자안전사건 보고 건수',
    unit: '건/월',
    periodType: 'monthly',
    chartType: 'line',
    isKeyIndicator: true,
    status: 'active',
    displayOrder: 1,
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-01-01T00:00:00Z',
  },
}

// ===== Test Helpers =====

/**
 * Set mock auth state in localStorage
 */
export function setMockAuth(user: typeof mockUser.qpsStaff, token = 'test-token') {
  const authState = {
    state: {
      user,
      token,
      isAuthenticated: true,
      isLoading: false,
    },
    version: 0,
  }
  localStorage.setItem('auth-storage', JSON.stringify(authState))
}

/**
 * Clear auth state
 */
export function clearAuth() {
  localStorage.removeItem('auth-storage')
}

/**
 * Wait for loading to complete
 */
export async function waitForLoadingToFinish() {
  await new Promise((resolve) => setTimeout(resolve, 0))
}

// Re-export everything from @testing-library/react
export * from '@testing-library/react'
export { customRender as render, renderWithRouter }
export { userEvent }
