<script setup lang="ts">
import { computed } from 'vue'

import { formatPercent, formatRelativeTime, formatToman } from '@/common/utils/format'
import { symbolLabels, type PriceQuote } from '../types'

const props = defineProps<{ quote: PriceQuote }>()

const label = computed(() => symbolLabels[props.quote.symbol] ?? props.quote.symbol)
const change = computed(() => props.quote.change_24h ?? null)
const changeClass = computed(() => {
  if (!change.value || change.value.percent === 0) return 'text-slate-400'
  return change.value.percent > 0 ? 'text-buy' : 'text-sell'
})
</script>

<template>
  <article class="card">
    <h3 class="card-title">{{ label }}</h3>

    <p class="num mt-2 text-2xl font-bold text-slate-800">{{ formatToman(quote.sell) }}</p>

    <div class="mt-1 flex items-center gap-2 text-xs">
      <span v-if="change" class="num font-medium" :class="changeClass">
        {{ formatPercent(change.percent) }}
      </span>
      <span class="text-slate-400">۲۴ ساعت</span>
    </div>

    <dl class="mt-4 space-y-1 text-xs text-slate-500">
      <div class="flex justify-between">
        <dt>خرید</dt>
        <dd class="num">{{ formatToman(quote.buy) }}</dd>
      </div>
      <div v-if="quote.premium != null" class="flex justify-between">
        <dt>حباب</dt>
        <dd class="num">{{ formatPercent(quote.premium) }}</dd>
      </div>
      <div class="flex justify-between">
        <dt>منبع</dt>
        <dd>{{ quote.source }}</dd>
      </div>
    </dl>

    <p class="mt-3 text-[11px] text-slate-400">
      به‌روزرسانی {{ formatRelativeTime(quote.observed_at) }}
    </p>
  </article>
</template>
