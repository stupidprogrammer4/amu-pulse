import type { Verdict } from '../types'

/** Below this the score reads as "hold" rather than a direction. */
export const HOLD_THRESHOLD = 0.15

export function toVerdict(score: number): Verdict {
  if (score > HOLD_THRESHOLD) return 'buy'
  if (score < -HOLD_THRESHOLD) return 'sell'
  return 'hold'
}

export const verdictLabels: Record<Verdict, string> = {
  buy: 'متمایل به خرید',
  hold: 'نگه‌داری',
  sell: 'متمایل به فروش',
}

/** Tailwind text colour per verdict — sell-red through buy-green. */
export const verdictColors: Record<Verdict, string> = {
  buy: 'text-buy',
  hold: 'text-hold',
  sell: 'text-sell',
}

export function clampScore(score: number): number {
  return Math.min(1, Math.max(-1, score))
}

/** Maps a [-1, 1] score onto the gauge's 0–180° sweep. */
export function scoreToAngle(score: number): number {
  return (clampScore(score) + 1) * 90
}

/** A bare ۰٫۶۲ tells users little, so confidence is shown as a band. */
export function confidenceLabel(confidence: number): string {
  if (confidence >= 0.75) return 'اطمینان بالا'
  if (confidence >= 0.45) return 'اطمینان متوسط'
  return 'اطمینان پایین'
}
