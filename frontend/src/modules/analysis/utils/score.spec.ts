import { describe, expect, it } from 'vitest'

import { clampScore, scoreToAngle, toVerdict } from './score'

describe('toVerdict', () => {
  it('reads a strong positive score as buy', () => {
    expect(toVerdict(0.8)).toBe('buy')
  })

  it('reads a strong negative score as sell', () => {
    expect(toVerdict(-0.8)).toBe('sell')
  })

  it('treats scores inside the dead zone as hold', () => {
    expect(toVerdict(0.1)).toBe('hold')
    expect(toVerdict(-0.1)).toBe('hold')
    expect(toVerdict(0)).toBe('hold')
  })
})

describe('scoreToAngle', () => {
  it('maps the [-1, 1] range onto a 0-180 degree sweep', () => {
    expect(scoreToAngle(-1)).toBe(0)
    expect(scoreToAngle(0)).toBe(90)
    expect(scoreToAngle(1)).toBe(180)
  })

  it('clamps out-of-range scores so the needle stays on the arc', () => {
    expect(scoreToAngle(2)).toBe(180)
    expect(scoreToAngle(-2)).toBe(0)
  })
})

describe('clampScore', () => {
  it('leaves in-range scores untouched', () => {
    expect(clampScore(0.42)).toBe(0.42)
  })
})
