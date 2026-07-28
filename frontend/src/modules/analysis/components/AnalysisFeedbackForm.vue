<script setup lang="ts">
import { ref } from 'vue'

import { useAnalysisStore } from '../stores/analysis.store'

const analysis = useAnalysisStore()
const sent = ref(false)

async function rate(accurate: boolean) {
  sent.value = await analysis.submitFeedback(accurate)
}

defineExpose({ reset: () => (sent.value = false) })
</script>

<template>
  <div>
    <p v-if="sent" class="text-sm text-emerald-600">
      بازخوردتان ثبت شد. ممنون — همین داده‌ها دقت تحلیل‌های بعدی را می‌سنجند.
    </p>
    <template v-else-if="analysis.canRate">
      <p class="text-sm text-slate-600">این خوانش با واقعیت بازار هم‌خوان بود؟</p>
      <div class="mt-3 flex gap-2">
        <button
          type="button"
          class="rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-medium text-white hover:bg-emerald-700"
          @click="rate(true)"
        >
          درست بود
        </button>
        <button
          type="button"
          class="rounded-lg bg-rose-600 px-4 py-1.5 text-xs font-medium text-white hover:bg-rose-700"
          @click="rate(false)"
        >
          نادرست بود
        </button>
      </div>
    </template>
    <p v-else class="text-sm text-slate-400">برای این تحلیل قبلاً بازخورد ثبت کرده‌اید.</p>
  </div>
</template>
