<script setup lang="ts">
import { formatPercent, formatRelativeTime, formatToman } from '@/common/utils/format'
import { symbolLabels, type PriceQuote } from '../types'

defineProps<{ quotes: PriceQuote[] }>()
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead class="text-xs text-slate-400">
        <tr class="border-b border-line">
          <th class="py-2 text-start font-medium">نماد</th>
          <th class="py-2 text-start font-medium">خرید</th>
          <th class="py-2 text-start font-medium">فروش</th>
          <th class="py-2 text-start font-medium">حباب</th>
          <th class="py-2 text-start font-medium">تغییر ۲۴ ساعت</th>
          <th class="py-2 text-start font-medium">به‌روزرسانی</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-line">
        <tr v-for="quote in quotes" :key="quote.symbol">
          <td class="py-3 font-medium text-slate-700">
            {{ symbolLabels[quote.symbol] ?? quote.symbol }}
          </td>
          <td class="num py-3">{{ formatToman(quote.buy) }}</td>
          <td class="num py-3">{{ formatToman(quote.sell) }}</td>
          <td class="num py-3">{{ quote.premium != null ? formatPercent(quote.premium) : '—' }}</td>
          <td
            class="num py-3"
            :class="(quote.change_24h?.percent ?? 0) >= 0 ? 'text-buy' : 'text-sell'"
          >
            {{ quote.change_24h ? formatPercent(quote.change_24h.percent) : '—' }}
          </td>
          <td class="py-3 text-xs text-slate-400">{{ formatRelativeTime(quote.observed_at) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
