import { api } from '@/infra/http'
import type { NewsItem, NewsQuery } from '../types'

const endpoints = {
  list: '/news',
} as const

export const newsService = {
  list: (query: NewsQuery = {}) => api.get<NewsItem[]>(endpoints.list, query),
}
