import type { RouteRecordRaw } from 'vue-router'

import type { AppModule } from './module'

/**
 * Discovers every `src/modules/<name>/index.ts` at build time — the frontend's
 * answer to the backend bootstrapper. Adding a module is a matter of creating
 * the directory; nothing here or in the router needs editing.
 */
const moduleFiles = import.meta.glob<{ default: AppModule }>('../modules/*/index.ts', {
  eager: true,
})

export function bootModules(): AppModule[] {
  return Object.entries(moduleFiles)
    .map(([path, loaded]) => {
      if (!loaded.default?.name) {
        throw new Error(`Module at ${path} must default-export a defineModule({ ... }) result.`)
      }
      return loaded.default
    })
    .sort((a, b) => a.name.localeCompare(b.name))
}

/** True for `/:pathMatch(.*)*`-style catch-alls, which must be registered last. */
function isCatchAll(route: RouteRecordRaw): boolean {
  return route.path.includes(':pathMatch')
}

export function bootRoutes(modules: AppModule[] = bootModules()): RouteRecordRaw[] {
  const routes = modules.flatMap((module) => module.routes)
  return [...routes.filter((r) => !isCatchAll(r)), ...routes.filter(isCatchAll)]
}

/** Navigation entries, ordered by each route's `meta.nav.order`. */
export function bootNavigation(routes: RouteRecordRaw[] = bootRoutes()) {
  return routes
    .filter((route) => route.meta?.nav)
    .sort((a, b) => a.meta!.nav!.order - b.meta!.nav!.order)
    .map((route) => ({ name: route.name as string, label: route.meta!.nav!.label }))
}
