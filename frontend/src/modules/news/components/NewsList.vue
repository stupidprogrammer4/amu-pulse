<script setup lang="ts">
import { formatRelativeTime } from '@/common/utils/format'
import { sentimentLabels, type NewsItem, type Sentiment } from '../types'

defineProps<{ items: NewsItem[] }>()

const sentimentClasses: Record<Sentiment, string> = {
  positive: 'bg-emerald-50 text-emerald-700',
  neutral: 'bg-slate-100 text-slate-500',
  negative: 'bg-rose-50 text-rose-700',
}
</script>

<template>
  <ul class="divide-y divide-line">
    <li v-for="item in items" :key="item.id" class="py-3">
      <a
        :href="item.url"
        target="_blank"
        rel="noopener noreferrer"
        class="block hover:text-amber-700"
      >
        <div class="flex items-start justify-between gap-3">
          <h3 class="text-sm font-medium text-slate-800">{{ item.title }}</h3>
          <span
            v-if="item.sentiment"
            class="shrink-0 rounded-md px-2 py-0.5 text-[11px]"
            :class="sentimentClasses[item.sentiment]"
          >
            {{ sentimentLabels[item.sentiment] }}
          </span>
        </div>
        <p v-if="item.summary" class="mt-1 line-clamp-2 text-xs text-slate-500">
          {{ item.summary }}
        </p>
        <p class="mt-1 text-[11px] text-slate-400">
          {{ item.source }} · {{ formatRelativeTime(item.published_at) }}
        </p>
      </a>
    </li>
  </ul>
</template>
