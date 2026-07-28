<script setup lang="ts">
import { onMounted } from 'vue'

import { BaseCard, BaseSpinner, EmptyState, ErrorState } from '@/common/components'
import { useAsyncData } from '@/common/composables/useAsyncData'
import NewsList from '../components/NewsList.vue'
import { newsService } from '../services/news.service'

const news = useAsyncData(() => newsService.list({ limit: 30 }))

onMounted(() => void news.execute())
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-xl font-bold text-slate-800">اخبار بازار</h1>

    <BaseCard>
      <BaseSpinner v-if="news.isLoading.value" />
      <ErrorState v-else-if="news.error.value" :error="news.error.value" @retry="news.execute()" />
      <NewsList v-else-if="news.data.value?.length" :items="news.data.value" />
      <EmptyState v-else message="خبری یافت نشد." />
    </BaseCard>
  </div>
</template>
