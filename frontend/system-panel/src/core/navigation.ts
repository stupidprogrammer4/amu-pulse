/**
 * The sidebar map. Every entry named here is a section of the backend's
 * `/panel/*` surface; `ready: false` means the route is not built yet, so the
 * item renders as a disabled placeholder rather than a link into nowhere.
 */
export interface NavItem {
  label: string
  /** Named route, once it exists. */
  to?: string
  /** The backend prefix this section drives — shown as the item's subtitle. */
  endpoint?: string
  icon: string
  ready: boolean
  superAdminOnly?: boolean
}

export interface NavSection {
  title: string
  items: NavItem[]
}

export const navigation: NavSection[] = [
  {
    title: 'Operations',
    items: [
      { label: 'Overview', to: 'overview', icon: 'LayoutDashboard', ready: true },
      { label: 'Logs', endpoint: '/panel/logs', icon: 'ScrollText', ready: false },
      { label: 'Traces', endpoint: '/panel/logs/traces', icon: 'Waypoints', ready: false },
    ],
  },
  {
    title: 'Market catalog',
    items: [
      { label: 'Assets', endpoint: '/panel/assets', icon: 'Boxes', ready: false },
      { label: 'Sources', endpoint: '/panel/sources', icon: 'Antenna', ready: false },
      { label: 'Symbols', endpoint: '/panel/symbols', icon: 'Tags', ready: false },
      { label: 'Bubbles', endpoint: '/panel/bubbles', icon: 'CircleDot', ready: false },
      { label: 'Candles', endpoint: '/panel/candles', icon: 'ChartCandlestick', ready: false },
    ],
  },
  {
    title: 'Identity',
    items: [
      {
        label: 'Admins',
        endpoint: '/panel/admins',
        icon: 'UsersRound',
        ready: false,
        superAdminOnly: true,
      },
    ],
  },
  {
    title: 'Developer',
    items: [
      {
        label: 'API explorer',
        to: 'explorer',
        endpoint: '/openapi.json',
        icon: 'Terminal',
        ready: true,
      },
    ],
  },
]
