<script setup lang="ts">
import { useId } from 'vue'

/**
 * The wide-banner motif — gold ribbons sweeping over a dark ground — rebuilt as
 * motion instead of a 1.4 MB photograph, and with the banner's navy dropped for
 * the console's black. Each ribbon carries a dashed highlight travelling its
 * length, which is what reads as the moving gold light in the pack.
 */
const uid = useId()
const gold = `${uid}-gold`
const deep = `${uid}-deep`
const glow = `${uid}-glow`

const ribbons = [
  { d: 'M-120 392C264 300 392 128 728 156S1236 336 1780 204', w: 7, dash: 300, dur: 17, delay: 0 },
  {
    d: 'M-120 300C300 428 528 196 868 252S1300 152 1780 328',
    w: 4,
    dash: 220,
    dur: 13,
    delay: 2.4,
  },
  {
    d: 'M-120 452C348 384 604 300 908 364S1376 428 1780 386',
    w: 9,
    dash: 380,
    dur: 21,
    delay: 1.1,
  },
  { d: 'M-120 176C240 204 468 56 884 112S1324 244 1780 116', w: 3, dash: 180, dur: 11, delay: 3.6 },
  {
    d: 'M-120 254C404 120 704 388 1052 304S1452 248 1780 262',
    w: 5,
    dash: 260,
    dur: 15,
    delay: 0.8,
  },
]

const dust = [
  { cx: 236, cy: 214, r: 2.4, dur: 4.2, delay: 0 },
  { cx: 512, cy: 356, r: 1.6, dur: 5.8, delay: 1.3 },
  { cx: 744, cy: 128, r: 2, dur: 3.6, delay: 2.1 },
  { cx: 968, cy: 288, r: 1.4, dur: 6.4, delay: 0.6 },
  { cx: 1188, cy: 176, r: 2.6, dur: 4.8, delay: 3.2 },
  { cx: 1364, cy: 396, r: 1.8, dur: 5.2, delay: 1.9 },
  { cx: 1508, cy: 246, r: 1.5, dur: 3.9, delay: 2.7 },
]
</script>

<template>
  <svg
    class="ribbons pointer-events-none absolute inset-0 size-full"
    viewBox="0 0 1600 500"
    preserveAspectRatio="xMidYMid slice"
    aria-hidden="true"
    focusable="false"
  >
    <defs>
      <linearGradient :id="gold" x1="0" y1="0" x2="1600" y2="500" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#D4AF37" stop-opacity="0" />
        <stop offset="0.22" stop-color="#D4AF37" />
        <stop offset="0.5" stop-color="#F7C24D" />
        <stop offset="0.78" stop-color="#D4AF37" />
        <stop offset="1" stop-color="#D4AF37" stop-opacity="0" />
      </linearGradient>

      <radialGradient :id="deep" cx="0.3" cy="0.15" r="0.95">
        <stop offset="0" stop-color="#262218" />
        <stop offset="1" stop-color="#080705" />
      </radialGradient>

      <filter :id="glow" x="-20%" y="-40%" width="140%" height="180%">
        <feGaussianBlur stdDeviation="7" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>

    <rect width="1600" height="500" :fill="`url(#${deep})`" />

    <g :stroke="`url(#${gold})`" fill="none" stroke-linecap="round">
      <path
        v-for="(ribbon, index) in ribbons"
        :key="`base-${index}`"
        :d="ribbon.d"
        :stroke-width="ribbon.w"
        opacity="0.16"
      />
      <path
        v-for="(ribbon, index) in ribbons"
        :key="`lit-${index}`"
        class="ribbon-lit"
        :d="ribbon.d"
        :stroke-width="ribbon.w"
        :stroke-dasharray="`${ribbon.dash} 2400`"
        :filter="`url(#${glow})`"
        :style="{ animationDuration: `${ribbon.dur}s`, animationDelay: `${ribbon.delay}s` }"
      />
    </g>

    <g fill="#F7C24D">
      <circle
        v-for="(mote, index) in dust"
        :key="index"
        class="dust"
        :cx="mote.cx"
        :cy="mote.cy"
        :r="mote.r"
        :style="{ animationDuration: `${mote.dur}s`, animationDelay: `${mote.delay}s` }"
      />
    </g>
  </svg>
</template>

<style scoped>
.ribbon-lit {
  animation-name: ribbon-travel;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
}

.dust {
  animation-name: dust-twinkle;
  animation-timing-function: ease-in-out;
  animation-iteration-count: infinite;
}

@keyframes ribbon-travel {
  from {
    stroke-dashoffset: 2700;
  }
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes dust-twinkle {
  0%,
  100% {
    opacity: 0.15;
    transform: translateY(0);
  }
  50% {
    opacity: 0.85;
    transform: translateY(-6px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .ribbon-lit,
  .dust {
    animation: none;
  }
  .ribbon-lit {
    stroke-dasharray: none;
    opacity: 0.5;
  }
}
</style>
