import { describe, expect, it } from 'vitest'

import { bootModules, bootNavigation, bootRoutes } from './bootstrap'

describe('module bootstrapper', () => {
  it('discovers every module under src/modules', () => {
    const names = bootModules().map((module) => module.name)
    expect(names).toEqual(['analysis', 'dashboard', 'news', 'prices', 'system'])
  })

  it('registers the catch-all last, so real routes still match', () => {
    const paths = bootRoutes().map((route) => route.path)
    expect(paths.at(-1)).toContain(':pathMatch')
    expect(paths.filter((path) => path.includes(':pathMatch'))).toHaveLength(1)
  })

  it('orders navigation by each route meta.nav.order', () => {
    expect(bootNavigation().map((item) => item.name)).toEqual([
      'dashboard',
      'prices',
      'analysis',
      'news',
    ])
  })

  it('keeps the catch-all out of the navigation', () => {
    expect(bootNavigation().map((item) => item.name)).not.toContain('not-found')
  })
})
