import type { RouteRecordRaw } from 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    /** Shown in the browser tab and the page header. */
    title: string
    /** Present when the route should appear in the main navigation. */
    nav?: { label: string; order: number }
    requiresAuth?: boolean
  }
}

/**
 * What a feature module exposes to the app shell. Mirrors the backend's
 * per-module `routers` package: a module owns its own routes, and the
 * bootstrapper collects them without the shell knowing any module by name.
 */
export interface AppModule {
  /** Must be unique; used for route-name prefixing and debugging. */
  name: string
  routes: RouteRecordRaw[]
}

export function defineModule(module: AppModule): AppModule {
  return module
}
