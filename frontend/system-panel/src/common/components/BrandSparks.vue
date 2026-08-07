<script setup lang="ts">
/**
 * The hero banner's other half: the trail of gold motes the butterfly leaves
 * behind. Every mote rides the same bezier via `offset-path`, staggered by a
 * negative delay, so the stream reads as one continuous spray on first paint
 * rather than a row of dots that fills in over the first few seconds.
 */
const motes = Array.from({ length: 26 }, (_, index) => ({
  size: 1.5 + ((index * 7) % 5) * 0.9,
  dur: 6 + ((index * 5) % 9),
  delay: -((index * 13) % 90) / 6,
  drift: (((index * 11) % 7) - 3) * 9,
  bright: index % 4 === 0,
}))
</script>

<template>
  <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
    <div class="trail">
      <span
        v-for="(mote, index) in motes"
        :key="index"
        class="mote"
        :style="{
          width: `${mote.size}px`,
          height: `${mote.size}px`,
          background: mote.bright ? '#F7C24D' : '#D4AF37',
          animationDuration: `${mote.dur}s`,
          animationDelay: `${mote.delay}s`,
          '--drift': `${mote.drift}px`,
        }"
      />
    </div>
  </div>
</template>

<style scoped>
/* The bezier below is authored in this box's coordinates, so the box is a
   fixed size and gets centred rather than stretched. */
.trail {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 1200px;
  height: 340px;
  translate: -50% -50%;
}

.mote {
  position: absolute;
  top: 0;
  left: 0;
  border-radius: 9999px;
  opacity: 0;
  offset-path: path('M40 210C220 236 420 300 640 268S920 150 1160 96');
  offset-rotate: 0deg;
  animation-name: mote-ride;
  animation-timing-function: cubic-bezier(0.32, 0.12, 0.44, 1);
  animation-iteration-count: infinite;
  box-shadow: 0 0 7px 1px rgb(212 175 55 / 0.75);
}

@keyframes mote-ride {
  0% {
    offset-distance: 0%;
    opacity: 0;
    translate: 0 var(--drift);
  }
  12% {
    opacity: 0.95;
  }
  78% {
    opacity: 0.55;
  }
  100% {
    offset-distance: 100%;
    opacity: 0;
    translate: 0 calc(var(--drift) * -1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .mote {
    animation: none;
    opacity: 0.4;
  }
}
</style>
