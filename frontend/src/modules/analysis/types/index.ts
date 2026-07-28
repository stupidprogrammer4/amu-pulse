import type { ChartWindow } from '@/modules/prices/types'
import type { NewsItem } from '@/modules/news/types'

/**
 * The directional read-out. `score` lives in [-1, 1]:
 * +1 leans buy, -1 leans sell, ~0 is hold. `confidence` is [0, 1]
 * and says how much weight the score deserves.
 */
export interface Analysis {
  id: string
  symbol: string
  score: number
  confidence: number
  /** Why the model landed on this score — always present, by design. */
  reason: string
  window: ChartWindow
  /** The exact inputs the read-out was produced from. */
  inputs?: AnalysisInputs | null
  created_at: string
}

export interface AnalysisInputs {
  chart_window: ChartWindow
  news: NewsItem[]
}

export type Verdict = 'buy' | 'hold' | 'sell'

export interface AnalysisFeedback {
  analysis_id: string
  accurate: boolean
  note?: string
}
