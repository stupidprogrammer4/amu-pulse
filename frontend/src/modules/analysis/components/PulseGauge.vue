<script setup lang="ts">
import { computed } from 'vue'

import { formatNumber } from '@/common/utils/format'
import {
  confidenceLabel,
  scoreToAngle,
  toVerdict,
  verdictColors,
  verdictLabels,
} from '../utils/score'

const props = defineProps<{
  /** Directional score in [-1, 1]. */
  score: number
  /** How much weight the score deserves, in [0, 1]. */
  confidence: number
}>()

const RADIUS = 80
const CENTER = { x: 100, y: 100 }

const verdict = computed(() => toVerdict(props.score))

/** Needle tip, sitting slightly inside the arc. */
const needle = computed(() => {
  const radians = (scoreToAngle(props.score) * Math.PI) / 180
  const length = RADIUS - 12
  return {
    x: CENTER.x - length * Math.cos(radians),
    y: CENTER.y - length * Math.sin(radians),
  }
})
</script>

<template>
  <figure class="flex flex-col items-center">
    <!-- The gauge axis runs sell→buy left-to-right regardless of page direction,
         so it is pinned to LTR and labelled explicitly underneath. -->
    <svg
      viewBox="0 0 200 120"
      class="w-full max-w-xs"
      dir="ltr"
      role="img"
      :aria-label="`امتیاز ${formatNumber(score, 2)} — ${verdictLabels[verdict]}`"
    >
      <defs>
        <linearGradient id="pulse-gauge-track" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%" stop-color="var(--color-sell)" />
          <stop offset="50%" stop-color="var(--color-hold)" />
          <stop offset="100%" stop-color="var(--color-buy)" />
        </linearGradient>
      </defs>

      <path
        d="M 20 100 A 80 80 0 0 1 180 100"
        fill="none"
        stroke="url(#pulse-gauge-track)"
        stroke-width="14"
        stroke-linecap="round"
      />

      <line
        :x1="CENTER.x"
        :y1="CENTER.y"
        :x2="needle.x"
        :y2="needle.y"
        stroke="currentColor"
        class="text-slate-700"
        stroke-width="3"
        stroke-linecap="round"
      />
      <circle :cx="CENTER.x" :cy="CENTER.y" r="6" class="fill-slate-700" />
    </svg>

    <div class="-mt-3 flex w-full max-w-xs justify-between text-[11px]" dir="ltr">
      <span class="text-sell">فروش</span>
      <span class="text-slate-400">نگه‌داری</span>
      <span class="text-buy">خرید</span>
    </div>

    <figcaption class="mt-3 text-center">
      <p class="num text-3xl font-bold" :class="verdictColors[verdict]">
        {{ formatNumber(score, 2) }}
      </p>
      <p class="mt-1 text-sm font-medium" :class="verdictColors[verdict]">
        {{ verdictLabels[verdict] }}
      </p>
      <p class="num mt-2 text-xs text-slate-400">
        {{ confidenceLabel(confidence) }} ({{ formatNumber(confidence * 100, 0) }}٪)
      </p>
    </figcaption>
  </figure>
</template>
