/**
 * What this console is, in the words the UI shows. Kept in one place so the
 * login screen and the overview never drift into describing two products.
 */
export const project = {
  name: 'AMU Pulse',
  panel: 'System Panel',

  /** One line, for the tightest spots. */
  tagline: 'Precious-metals pricing, history and market analysis.',

  /** What the service does — shown on the login screen and the overview. */
  about:
    'AMU Pulse collects gold and precious-metal prices from many sources — market boards, ' +
    'wholesalers, world XAU feeds, the USD rate and the published premium — normalizes them ' +
    'into one database, folds each asset’s readings into a single price, keeps the history ' +
    'as tickers and candles, and pairs that with news to produce a directional read-out of the ' +
    'market: the pulse.',

  /** What *this* frontend is, as opposed to the client app. */
  role:
    'This is the system panel of AMU Pulse — the console the project’s own developers and ' +
    'operators run the service from. It is not the app end users see; that one is the client ' +
    'panel.',

  /** The three things an operator comes here to do. */
  capabilities: [
    {
      icon: 'ScrollText',
      title: 'Logs and reports',
      body: 'Every request and task run the backend ships to Elasticsearch, searchable, with the full trace behind a request id.',
    },
    {
      icon: 'Boxes',
      title: 'The guarded surface',
      body: 'Every /panel route: the source catalogue and its config, assets and their pricing order, symbols, bubbles, candles, and the admin accounts themselves.',
    },
    {
      icon: 'Terminal',
      title: 'An API explorer',
      body: "Read from the backend's own openapi.json — build and send any request by hand with the current session's token. A new route needs no frontend change.",
    },
  ],
} as const
