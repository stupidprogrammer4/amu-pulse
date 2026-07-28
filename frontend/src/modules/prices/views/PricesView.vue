<script setup lang="ts">
import { onMounted } from 'vue'

import { BaseCard, BaseSpinner, EmptyState, ErrorState } from '@/common/components'
import PriceTable from '../components/PriceTable.vue'
import { usePricesStore } from '../stores/prices.store'

const prices = usePricesStore()

onMounted(() => void prices.fetchQuotes())
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-xl font-bold text-slate-800">قیمت‌ها</h1>

    <BaseCard>
      <BaseSpinner v-if="prices.isLoading && !prices.hasQuotes" />
      <ErrorState v-else-if="prices.error" :error="prices.error" @retry="prices.fetchQuotes()" />
      <EmptyState v-else-if="!prices.hasQuotes" message="هنوز قیمتی ثبت نشده است." />
      <PriceTable v-else :quotes="prices.quotes" />
    </BaseCard>
  </div>
</template>
