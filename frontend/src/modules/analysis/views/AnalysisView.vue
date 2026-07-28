<script setup lang="ts">
import { onMounted, ref, useTemplateRef, watch } from 'vue'

import { BaseCard, BaseSpinner, EmptyState, ErrorState } from '@/common/components'
import { formatDateTime } from '@/common/utils/format'
import { chartWindowLabels, type ChartWindow } from '@/modules/prices/types'
import AnalysisFeedbackForm from '../components/AnalysisFeedbackForm.vue'
import PulseGauge from '../components/PulseGauge.vue'
import { useAnalysisStore } from '../stores/analysis.store'

const SYMBOL = 'GOLD_18K'
const windows: ChartWindow[] = ['1d', '7d', '30d', '90d']

const analysis = useAnalysisStore()
const selectedWindow = ref<ChartWindow>('7d')
const feedbackForm = useTemplateRef('feedbackForm')

function load() {
  feedbackForm.value?.reset()
  void analysis.fetchLatest(SYMBOL, selectedWindow.value)
}

watch(selectedWindow, load)
onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-xl font-bold text-slate-800">تحلیل بازار</h1>

      <div class="flex gap-1 rounded-xl bg-slate-100 p-1 text-xs">
        <button
          v-for="option in windows"
          :key="option"
          type="button"
          class="rounded-lg px-3 py-1.5 transition"
          :class="
            selectedWindow === option
              ? 'bg-white font-medium text-slate-800 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
          "
          @click="selectedWindow = option"
        >
          {{ chartWindowLabels[option] }}
        </button>
      </div>
    </div>

    <BaseSpinner v-if="analysis.isLoading" />
    <ErrorState v-else-if="analysis.error" :error="analysis.error" @retry="load" />
    <EmptyState v-else-if="!analysis.current" message="تحلیلی برای این بازه موجود نیست." />

    <div v-else class="grid gap-6 lg:grid-cols-5">
      <BaseCard class="lg:col-span-2">
        <PulseGauge :score="analysis.current.score" :confidence="analysis.current.confidence" />
      </BaseCard>

      <div class="space-y-6 lg:col-span-3">
        <BaseCard title="دلیل این خوانش">
          <p class="text-sm text-slate-600">{{ analysis.current.reason }}</p>
          <p class="mt-4 text-[11px] text-slate-400">
            تولید شده در {{ formatDateTime(analysis.current.created_at) }}
          </p>
        </BaseCard>

        <BaseCard title="بازخورد شما">
          <AnalysisFeedbackForm ref="feedbackForm" />
        </BaseCard>
      </div>
    </div>
  </div>
</template>
