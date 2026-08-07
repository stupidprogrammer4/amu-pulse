<script setup lang="ts">
/**
 * The mark is the pack's own artwork, not a redraw — the same butterfly the
 * favicon and the PWA icons are cut from (see scripts/generate-brand-icons.mjs).
 * The motion is a two-stage gold beat behind it, which is the "pulse" half of
 * the name.
 */
const props = withDefaults(defineProps<{ size?: number; animated?: boolean }>(), {
  size: 36,
  animated: true,
})
</script>

<template>
  <span
    class="brand-mark relative block shrink-0"
    :class="props.animated && 'is-animated'"
    :style="{ width: `${props.size}px`, height: `${props.size}px` }"
  >
    <span class="beat" aria-hidden="true" />
    <img
      src="/brand/logo-tile-128.png"
      srcset="/brand/logo-tile-64.png 64w, /brand/logo-tile-128.png 128w"
      :sizes="`${props.size}px`"
      :width="props.size"
      :height="props.size"
      alt="AMU Pulse"
      class="relative block size-full"
      decoding="async"
    />
  </span>
</template>

<style scoped>
.beat {
  position: absolute;
  inset: -18%;
  border-radius: 9999px;
  background: radial-gradient(circle, rgb(212 175 55 / 0.55), transparent 68%);
  opacity: 0;
}

.is-animated .beat {
  animation: mark-beat 3.2s ease-in-out infinite;
}

@keyframes mark-beat {
  0%,
  100% {
    opacity: 0;
    transform: scale(0.86);
  }
  8% {
    opacity: 0.9;
    transform: scale(1.06);
  }
  18% {
    opacity: 0.25;
    transform: scale(0.94);
  }
  28% {
    opacity: 0.7;
    transform: scale(1.02);
  }
  46% {
    opacity: 0;
    transform: scale(0.88);
  }
}

@media (prefers-reduced-motion: reduce) {
  .is-animated .beat {
    animation: none;
  }
}
</style>
