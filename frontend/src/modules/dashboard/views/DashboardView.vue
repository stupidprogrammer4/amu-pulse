<script setup lang="ts">
import { onMounted } from 'vue'

import { BaseCard, BaseSpinner, EmptyState, ErrorState } from '@/common/components'
import { useAsyncData } from '@/common/composables/useAsyncData'
import { formatRelativeTime } from '@/common/utils/format'
import PulseGauge from '@/modules/analysis/components/PulseGauge.vue'
import { useAnalysisStore } from '@/modules/analysis/stores/analysis.store'
import NewsList from '@/modules/news/components/NewsList.vue'
import { newsService } from '@/modules/news/services/news.service'
import PriceCard from '@/modules/prices/components/PriceCard.vue'
import { usePricesStore } from '@/modules/prices/stores/prices.store'

/** The instrument the headline read-out is about. */
const PRIMARY_SYMBOL = 'GOLD_18K'

const prices = usePricesStore()
const analysis = useAnalysisStore()
const news = useAsyncData(() => newsService.list({ symbol: PRIMARY_SYMBOL, limit: 5 }))

function loadAll() {
  void prices.fetchQuotes()
  void analysis.fetchLatest(PRIMARY_SYMBOL)
  void news.execute()
}

onMounted(loadAll)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold text-slate-800">نبض بازار</h1>
        <p class="mt-1 text-sm text-slate-500">خوانش لحظه‌ای قیمت‌ها، اخبار و جهت‌گیری بازار طلا</p>
      </div>
      <p v-if="prices.lastUpdatedAt" class="text-xs text-slate-400">
        آخرین به‌روزرسانی {{ formatRelativeTime(prices.lastUpdatedAt) }}
      </p>
    </div>

    <ErrorState v-if="prices.error" :error="prices.error" @retry="loadAll" />
    <BaseSpinner v-else-if="prices.isLoading && !prices.hasQuotes" />
    <div v-else-if="prices.hasQuotes" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <PriceCard v-for="quote in prices.quotes" :key="quote.symbol" :quote="quote" />
    </div>
    <EmptyState v-else message="هنوز قیمتی ثبت نشده است." />

    <div class="grid gap-6 lg:grid-cols-5">
      <BaseCard
        title="خوانش بازار"
        subtitle="امتیاز بین ۱- (فروش) تا ۱+ (خرید)"
        class="lg:col-span-2"
      >
        <BaseSpinner v-if="analysis.isLoading" />
        <ErrorState
          v-else-if="analysis.error"
          :error="analysis.error"
          @retry="analysis.fetchLatest(PRIMARY_SYMBOL)"
        />
        <template v-else-if="analysis.current">
          <PulseGauge :score="analysis.current.score" :confidence="analysis.current.confidence" />
          <p class="mt-5 border-t border-line pt-4 text-sm text-slate-600">
            {{ analysis.current.reason }}
          </p>
        </template>
        <EmptyState v-else message="تحلیلی برای این بازه موجود نیست." />
      </BaseCard>

      <BaseCard title="اخبار مرتبط" class="lg:col-span-3">
        <BaseSpinner v-if="news.isLoading.value" />
        <ErrorState
          v-else-if="news.error.value"
          :error="news.error.value"
          @retry="news.execute()"
        />
        <NewsList v-else-if="news.data.value?.length" :items="news.data.value" />
        <EmptyState v-else message="خبری یافت نشد." />
      </BaseCard>
    </div>
  </div>
</template>
