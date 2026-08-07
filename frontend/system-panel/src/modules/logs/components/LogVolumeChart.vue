<script setup lang="ts">
import type { ApexOptions } from 'apexcharts'
import { computed, defineAsyncComponent, onMounted, watch } from 'vue'

import BaseSpinner from '@/common/components/BaseSpinner.vue'
import ErrorState from '@/common/components/ErrorState.vue'
import { baseChartOptions, chartInk } from '@/common/charts/theme'
import { formatNumber } from '@/common/utils/format'

import { useLogsStore } from '../stores/logs.store'
import { logBuckets, logLevels } from '../types'

// ApexCharts is half a megabyte; keeping it behind an async component means the
// log table paints without waiting for a library only the chart needs.
const VueApexCharts = defineAsyncComponent(() => import('vue3-apexcharts'))

const logs = useLogsStore()

const buckets = computed(() => (logs.chartBuckets.length ? logs.chartBuckets : [...logBuckets]))
const containers = computed(() =>
  logs.chartContainers.length
    ? logs.chartContainers
    : logs.containerFacets.map((facet) => facet.value),
)

/** Buckets are minutes-to-days apart, so the axis label has to follow the span. */
const timeFormat = computed(() => (logs.chartBucket === '1d' ? 'dd MMM' : 'HH:mm'))

const series = computed(() => [
  {
    name: 'Lines written',
    data: (logs.chart?.points ?? []).map((point) => ({
      x: new Date(point.timestamp).getTime(),
      y: point.count,
    })),
  },
])

// One series, so no legend: the heading names it and the stat row carries the
// numbers. Gold is the console's only accent and does not encode a category.
const options = computed<ApexOptions>(() => ({
  ...baseChartOptions(),
  chart: { ...baseChartOptions().chart, type: 'area', height: 220, sparkline: { enabled: false } },
  colors: [chartInk.gold],
  stroke: { curve: 'smooth', width: 2, lineCap: 'round' },
  fill: {
    type: 'gradient',
    gradient: { shadeIntensity: 0, opacityFrom: 0.34, opacityTo: 0, stops: [0, 100] },
  },
  markers: { size: 0, strokeWidth: 0, hover: { size: 5 } },
  xaxis: {
    ...baseChartOptions().xaxis,
    type: 'datetime',
    labels: {
      style: { fontSize: '9px', colors: chartInk.text },
      datetimeUTC: false,
      format: timeFormat.value,
    },
  },
  yaxis: {
    ...baseChartOptions().yaxis,
    min: 0,
    forceNiceScale: true,
    labels: {
      style: { fontSize: '9px', colors: chartInk.text },
      formatter: (value: number) => formatNumber(Math.round(value)),
    },
  },
  tooltip: {
    ...baseChartOptions().tooltip,
    x: { format: 'dd MMM · HH:mm' },
    y: { formatter: (value: number) => `${formatNumber(value)} lines` },
  },
}))

const stats = computed(() => [
  { label: 'min', value: logs.chart?.min },
  { label: 'mean', value: logs.chart ? Math.round(logs.chart.mean) : undefined },
  { label: 'max', value: logs.chart?.max },
])

onMounted(() => void logs.loadChart())
watch(
  () => [logs.chartBucket, logs.chartContainer, logs.chartLevel],
  () => void logs.loadChart(),
)
</script>

<template>
  <section class="overflow-hidden rounded-2xl border border-line bg-surface-800">
    <header class="flex flex-wrap items-center gap-x-4 gap-y-2.5 border-b border-line px-4 py-3">
      <div class="mr-auto">
        <h2 class="text-[0.76rem] font-bold text-content-100">Log volume</h2>
        <p class="mt-0.5 text-[0.6rem] text-content-400">
          Lines per bucket for one container — <code class="font-mono">/panel/logs/chart</code>
        </p>
      </div>

      <label class="flex items-center gap-1.5 text-[0.6rem] text-content-400">
        <span class="sr-only">Container</span>
        <select
          v-model="logs.chartContainer"
          class="h-8 max-w-44 rounded-lg border border-line bg-surface-850 px-2 font-mono text-[0.62rem] text-content-200 outline-none focus:border-accent-500"
        >
          <option v-if="!containers.length" value="">no containers</option>
          <option v-for="name in containers" :key="name" :value="name">{{ name }}</option>
        </select>
      </label>

      <label class="flex items-center gap-1.5 text-[0.6rem] text-content-400">
        <span class="sr-only">Level</span>
        <select
          v-model="logs.chartLevel"
          class="h-8 rounded-lg border border-line bg-surface-850 px-2 font-mono text-[0.62rem] text-content-200 outline-none focus:border-accent-500"
        >
          <option value="">all levels</option>
          <option v-for="level in logLevels" :key="level" :value="level">{{ level }}</option>
        </select>
      </label>

      <div class="flex overflow-hidden rounded-lg border border-line">
        <button
          v-for="bucket in buckets"
          :key="bucket"
          type="button"
          :aria-pressed="logs.chartBucket === bucket"
          class="h-8 px-2.5 font-mono text-[0.62rem] transition"
          :class="
            logs.chartBucket === bucket
              ? 'bg-accent-500 font-bold text-surface-950'
              : 'bg-surface-850 text-content-400 hover:text-content-100'
          "
          @click="logs.chartBucket = bucket"
        >
          {{ bucket }}
        </button>
      </div>
    </header>

    <div class="px-2 pt-3 pb-1">
      <ErrorState
        v-if="logs.chartError"
        class="m-2"
        :message="logs.chartError"
        :retrying="logs.chartLoading"
        @retry="logs.loadChart()"
      />
      <div v-else-if="logs.chartLoading && !logs.chart" class="grid h-55 place-items-center">
        <BaseSpinner label="Reading the chart" />
      </div>
      <p
        v-else-if="!logs.chartContainer"
        class="grid h-55 place-items-center text-[0.66rem] text-content-500"
      >
        Pick a container to chart.
      </p>
      <VueApexCharts v-else :options="options" :series="series" height="220" type="area" />
    </div>

    <dl class="flex gap-6 border-t border-line px-4 py-2.5">
      <div v-for="stat in stats" :key="stat.label" class="flex items-baseline gap-1.5">
        <dt class="font-mono text-[0.55rem] tracking-[0.1em] text-content-500 uppercase">
          {{ stat.label }}
        </dt>
        <dd class="font-mono text-[0.72rem] font-bold text-content-100">
          {{ formatNumber(stat.value) }}
        </dd>
      </div>
    </dl>
  </section>
</template>
