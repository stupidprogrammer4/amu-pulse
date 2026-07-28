export type Sentiment = 'positive' | 'neutral' | 'negative'

export interface NewsItem {
  id: string
  title: string
  summary?: string | null
  url: string
  source: string
  sentiment?: Sentiment | null
  published_at: string
}

export interface NewsQuery {
  symbol?: string
  limit?: number
}

export const sentimentLabels: Record<Sentiment, string> = {
  positive: 'مثبت',
  neutral: 'خنثی',
  negative: 'منفی',
}
