import { describe, expect, it } from 'vitest'

import { formatNumber, formatPercent, formatToman } from './format'

describe('Persian formatting', () => {
  it('renders numbers with Persian digits', () => {
    expect(formatNumber(1234)).toMatch(/[۰-۹]/)
  })

  it('appends the Toman unit', () => {
    expect(formatToman(3450000)).toContain('تومان')
  })

  it('always shows the sign on a percentage so direction is unambiguous', () => {
    expect(formatPercent(0.031)).toContain('+')
    expect(formatPercent(-0.031)).toMatch(/[-−]/)
  })
})
