import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { describe, expect, it, vi } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'

import App from './App.vue'
import { bootRoutes } from './core/bootstrap'

// The dashboard fires requests on mount; the shell is what's under test here.
vi.mock('@/infra/http', async () => {
  const actual = await vi.importActual<typeof import('@/infra/http')>('@/infra/http')
  return {
    ...actual,
    api: {
      get: vi.fn().mockResolvedValue([]),
      post: vi.fn().mockResolvedValue(undefined),
      patch: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    },
  }
})

async function mountApp(path: string) {
  const router = createRouter({ history: createMemoryHistory(), routes: bootRoutes() })
  await router.push(path)
  await router.isReady()
  return mount(App, { global: { plugins: [createPinia(), router] } })
}

describe('App shell', () => {
  it('renders the navigation built from the discovered modules', async () => {
    const wrapper = await mountApp('/')
    const links = wrapper.findAll('nav a').map((link) => link.text())
    expect(links).toEqual(['نبض بازار', 'قیمت‌ها', 'تحلیل', 'اخبار'])
  })

  it('renders the matched module view inside the shell', async () => {
    const wrapper = await mountApp('/prices')
    expect(wrapper.find('h1').text()).toBe('قیمت‌ها')
  })

  it('falls through to the system module for an unknown path', async () => {
    const wrapper = await mountApp('/no-such-page')
    expect(wrapper.text()).toContain('این صفحه پیدا نشد')
  })
})
