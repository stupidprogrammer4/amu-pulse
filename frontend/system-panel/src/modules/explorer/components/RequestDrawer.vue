<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { Check, Clipboard, Clock, LoaderCircle, Play, RotateCcw, X } from '@/common/icons'
import { ApiError, rawRequest, type RawResponse } from '@/infra/http'

import type { OpenApiParameter, Operation } from '../types'
import {
  defaultValueFor,
  describeSchema,
  enumOptionsFor,
  resolveSchema,
  sampleFor,
  unwrapNullable,
} from '../utils/schema'
import { useExplorerStore } from '../stores/explorer.store'
import GuardChip from './GuardChip.vue'
import MethodChip from './MethodChip.vue'

const props = defineProps<{ operation: Operation }>()
const emit = defineEmits<{ close: [] }>()

const explorer = useExplorerStore()

const pathValues = ref<Record<string, string>>({})
const queryValues = ref<Record<string, string>>({})
const headerValues = ref<Record<string, string>>({})
const bodyText = ref('')
const mediaType = ref('')
const files = ref<Record<string, File | null>>({})
const formFields = ref<Record<string, string>>({})

const sending = ref(false)
const response = ref<RawResponse | null>(null)
const failure = ref<string | null>(null)
const copied = ref(false)
const showHeaders = ref(false)

const pathParams = computed(() => paramsIn('path'))
const queryParams = computed(() => paramsIn('query'))
const headerParams = computed(() => paramsIn('header'))

function paramsIn(location: OpenApiParameter['in']): OpenApiParameter[] {
  return props.operation.parameters.filter((parameter) => parameter.in === location)
}

const mediaTypes = computed(() => Object.keys(props.operation.requestBody?.content ?? {}))
const isMultipart = computed(() => mediaType.value.includes('multipart/form-data'))
const isJsonBody = computed(() => mediaType.value.includes('json'))

/** Properties of a multipart body, split into files and plain fields. */
const multipartFields = computed(() => {
  if (!isMultipart.value) return []
  const schema = resolveSchema(
    explorer.document,
    props.operation.requestBody?.content?.[mediaType.value]?.schema,
  )
  return Object.entries(schema?.properties ?? {}).map(([name, property]) => {
    const resolved = resolveSchema(explorer.document, unwrapNullable(property).schema)
    return {
      name,
      isFile: resolved?.format === 'binary',
      required: schema?.required?.includes(name) ?? false,
      hint: describeSchema(explorer.document, property),
    }
  })
})

/** The path with `{id}` replaced, ready to send. */
const resolvedPath = computed(() =>
  props.operation.path.replace(/\{([^}]+)\}/g, (match, name: string) => {
    const value = pathValues.value[name]
    return value ? encodeURIComponent(value) : match
  }),
)

const missingPathParams = computed(() =>
  pathParams.value.filter((parameter) => !pathValues.value[parameter.name]).map((p) => p.name),
)

/** Pretty-printed when the answer is JSON, verbatim otherwise. */
const prettyBody = computed(() => {
  const body = response.value?.body ?? ''
  if (!body) return ''
  try {
    return JSON.stringify(JSON.parse(body), null, 2)
  } catch {
    return body
  }
})

const statusTone = computed(() => {
  const status = response.value?.status ?? 0
  if (status >= 200 && status < 300) return 'bg-signal-ok/14 text-signal-ok'
  if (status >= 300 && status < 400) return 'bg-accent-500/14 text-accent-300'
  if (status === 0) return 'bg-surface-700 text-content-400'
  return 'bg-signal-error/14 text-signal-error'
})

// A different operation is a different form; nothing carries over.
watch(
  () => props.operation.id,
  () => reset(),
  { immediate: true },
)

function reset(): void {
  const operation = props.operation
  pathValues.value = Object.fromEntries(paramsIn('path').map((p) => [p.name, '']))
  queryValues.value = Object.fromEntries(
    paramsIn('query').map((p) => [p.name, defaultValueFor(explorer.document, p.schema)]),
  )
  headerValues.value = Object.fromEntries(paramsIn('header').map((p) => [p.name, '']))

  const types = Object.keys(operation.requestBody?.content ?? {})
  mediaType.value = types.find((type) => type.includes('json')) ?? types[0] ?? ''

  const schema = operation.requestBody?.content?.[mediaType.value]?.schema
  bodyText.value =
    mediaType.value && !mediaType.value.includes('multipart')
      ? JSON.stringify(sampleFor(explorer.document, schema), null, 2)
      : ''

  files.value = {}
  formFields.value = {}
  response.value = null
  failure.value = null
  copied.value = false
  showHeaders.value = false
}

function optionsFor(parameter: OpenApiParameter): string[] {
  return enumOptionsFor(explorer.document, parameter.schema)
}

function typeLabel(parameter: OpenApiParameter): string {
  return describeSchema(explorer.document, parameter.schema)
}

function onFile(name: string, event: Event): void {
  const input = event.target as HTMLInputElement
  files.value[name] = input.files?.[0] ?? null
}

/** Empty query fields are left out entirely rather than sent as `?x=`. */
function buildQuery(): Record<string, string> {
  return Object.fromEntries(Object.entries(queryValues.value).filter(([, value]) => value !== ''))
}

function buildHeaders(): Record<string, string> {
  const headers = Object.fromEntries(
    Object.entries(headerValues.value).filter(([, value]) => value !== ''),
  )
  if (mediaType.value && !isMultipart.value) headers['Content-Type'] = mediaType.value
  return headers
}

/** Throws with a readable message when the editor holds broken JSON. */
function buildBody(): unknown {
  if (!mediaType.value) return undefined

  if (isMultipart.value) {
    const form = new FormData()
    for (const [name, file] of Object.entries(files.value)) if (file) form.append(name, file)
    for (const [name, value] of Object.entries(formFields.value)) {
      if (value !== '') form.append(name, value)
    }
    return form
  }

  const text = bodyText.value.trim()
  if (!text) return undefined
  if (!isJsonBody.value) return text
  try {
    return JSON.parse(text)
  } catch (cause) {
    throw new Error(`Request body is not valid JSON — ${(cause as Error).message}`)
  }
}

async function send(): Promise<void> {
  if (sending.value) return
  failure.value = null

  if (missingPathParams.value.length) {
    failure.value = `Fill the path parameter${
      missingPathParams.value.length > 1 ? 's' : ''
    }: ${missingPathParams.value.join(', ')}.`
    return
  }

  let body: unknown
  try {
    body = buildBody()
  } catch (cause) {
    failure.value = (cause as Error).message
    return
  }

  sending.value = true
  try {
    response.value = await rawRequest({
      method: props.operation.method,
      path: resolvedPath.value,
      query: buildQuery(),
      headers: buildHeaders(),
      body,
    })
  } catch (cause) {
    response.value = null
    failure.value =
      cause instanceof ApiError ? cause.message : ((cause as Error).message ?? 'Request failed.')
  } finally {
    sending.value = false
  }
}

async function copyResponse(): Promise<void> {
  if (!prettyBody.value) return
  try {
    await navigator.clipboard.writeText(prettyBody.value)
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  } catch {
    /* clipboard is blocked outside a secure context; the text is selectable anyway */
  }
}
</script>

<template>
  <div class="fixed inset-0 z-100 bg-black/60 backdrop-blur-[3px]" @click.self="emit('close')">
    <aside
      class="absolute inset-y-0 right-0 flex w-full max-w-[44rem] flex-col border-l border-line bg-surface-900"
    >
      <!-- Head -->
      <header class="flex items-start gap-3 border-b border-line bg-surface-850 px-5 py-4">
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <MethodChip :method="operation.method" />
            <code class="font-mono text-[0.72rem] break-all text-content-100">
              {{ operation.path }}
            </code>
            <GuardChip :guard="operation.guard" label />
          </div>
          <p class="mt-1.5 text-[0.62rem] text-content-400">{{ operation.summary }}</p>
        </div>
        <button
          type="button"
          class="grid size-8 shrink-0 place-items-center rounded-lg border border-line text-content-400 transition hover:text-content-100"
          aria-label="Close"
          @click="emit('close')"
        >
          <X :size="15" />
        </button>
      </header>

      <!-- Form -->
      <div class="flex-1 overflow-y-auto p-4">
        <p
          v-if="operation.description"
          class="mb-3 rounded-xl border border-line bg-surface-850 px-3.5 py-3 text-[0.63rem] leading-relaxed text-content-400"
        >
          {{ operation.description }}
        </p>

        <section
          v-for="group in [
            { title: 'Path parameters', items: pathParams },
            { title: 'Query parameters', items: queryParams },
            { title: 'Headers', items: headerParams },
          ].filter((entry) => entry.items.length)"
          :key="group.title"
          class="mb-3 overflow-hidden rounded-xl border border-line bg-surface-850"
        >
          <h3
            class="border-b border-line px-3.5 py-2.5 text-[0.62rem] font-bold tracking-wide text-content-200"
          >
            {{ group.title }}
          </h3>
          <label
            v-for="parameter in group.items"
            :key="`${group.title}:${parameter.name}`"
            class="grid items-center gap-2 border-b border-line/60 px-3.5 py-2.5 last:border-0 sm:grid-cols-[minmax(9rem,0.8fr)_1.2fr]"
          >
            <span class="min-w-0">
              <b class="block font-mono text-[0.62rem] font-semibold text-content-200">
                {{ parameter.name }}
                <i v-if="parameter.required" class="text-signal-error not-italic">*</i>
              </b>
              <small class="mt-0.5 block truncate font-mono text-[0.52rem] text-content-500">
                {{ typeLabel(parameter) }}
              </small>
            </span>

            <select
              v-if="group.title === 'Query parameters' && optionsFor(parameter).length"
              v-model="queryValues[parameter.name]"
              class="h-9 w-full rounded-lg border border-line bg-surface-800 px-2.5 font-mono text-[0.63rem] text-content-100 outline-none focus:border-accent-500"
            >
              <option value="">—</option>
              <option v-for="option in optionsFor(parameter)" :key="option" :value="option">
                {{ option }}
              </option>
            </select>
            <input
              v-else-if="group.title === 'Path parameters'"
              v-model="pathValues[parameter.name]"
              type="text"
              spellcheck="false"
              class="h-9 w-full rounded-lg border border-line bg-surface-800 px-2.5 font-mono text-[0.63rem] text-content-100 outline-none focus:border-accent-500"
            />
            <input
              v-else-if="group.title === 'Query parameters'"
              v-model="queryValues[parameter.name]"
              type="text"
              spellcheck="false"
              class="h-9 w-full rounded-lg border border-line bg-surface-800 px-2.5 font-mono text-[0.63rem] text-content-100 outline-none focus:border-accent-500"
            />
            <input
              v-else
              v-model="headerValues[parameter.name]"
              type="text"
              spellcheck="false"
              class="h-9 w-full rounded-lg border border-line bg-surface-800 px-2.5 font-mono text-[0.63rem] text-content-100 outline-none focus:border-accent-500"
            />
          </label>
        </section>

        <!-- Body -->
        <section
          v-if="mediaTypes.length"
          class="mb-3 overflow-hidden rounded-xl border border-line bg-surface-850"
        >
          <header class="flex items-center justify-between gap-3 border-b border-line px-3.5 py-2">
            <h3 class="text-[0.62rem] font-bold tracking-wide text-content-200">
              Request body
              <i v-if="operation.requestBody?.required" class="text-signal-error not-italic">*</i>
            </h3>
            <select
              v-model="mediaType"
              class="h-7 max-w-56 rounded-lg border border-line bg-surface-800 px-2 font-mono text-[0.55rem] text-content-300 outline-none focus:border-accent-500"
            >
              <option v-for="type in mediaTypes" :key="type" :value="type">{{ type }}</option>
            </select>
          </header>

          <div v-if="isMultipart" class="p-3.5">
            <label
              v-for="field in multipartFields"
              :key="field.name"
              class="mb-2.5 block last:mb-0"
            >
              <span class="mb-1.5 block font-mono text-[0.6rem] text-content-300">
                {{ field.name }}
                <i v-if="field.required" class="text-signal-error not-italic">*</i>
                <small class="ml-1 text-content-500">{{ field.hint }}</small>
              </span>
              <input
                v-if="field.isFile"
                type="file"
                class="w-full rounded-lg border border-line bg-surface-800 p-2 text-[0.6rem] text-content-300 file:mr-2 file:rounded file:border-0 file:bg-accent-500 file:px-2 file:py-1 file:text-[0.58rem] file:text-surface-950"
                @change="onFile(field.name, $event)"
              />
              <input
                v-else
                v-model="formFields[field.name]"
                type="text"
                class="h-9 w-full rounded-lg border border-line bg-surface-800 px-2.5 font-mono text-[0.63rem] text-content-100 outline-none focus:border-accent-500"
              />
            </label>
          </div>

          <textarea
            v-else
            v-model="bodyText"
            rows="10"
            spellcheck="false"
            class="block w-full resize-y bg-surface-950 p-3.5 font-mono text-[0.63rem] leading-relaxed text-content-200 outline-none"
          />
        </section>

        <p
          v-if="failure"
          class="mb-3 rounded-xl border border-signal-error/35 bg-signal-error/10 px-3.5 py-2.5 text-[0.63rem] text-signal-error"
        >
          {{ failure }}
        </p>

        <!-- Response -->
        <section
          v-if="response"
          class="overflow-hidden rounded-xl border border-line bg-surface-950"
        >
          <header class="flex flex-wrap items-center gap-2 border-b border-line px-3.5 py-2.5">
            <span
              class="rounded px-1.5 py-0.5 font-mono text-[0.58rem] font-bold"
              :class="statusTone"
            >
              {{ response.status }} {{ response.statusText }}
            </span>
            <small class="flex items-center gap-1 font-mono text-[0.55rem] text-content-500">
              <Clock :size="11" />
              {{ response.durationMs }} ms
            </small>
            <small class="font-mono text-[0.55rem] text-content-500">
              {{ response.bytes.toLocaleString('en-US') }} B
            </small>
            <button
              type="button"
              class="ml-auto flex items-center gap-1 text-[0.55rem] text-content-400 transition hover:text-content-100"
              @click="showHeaders = !showHeaders"
            >
              {{ showHeaders ? 'Hide headers' : 'Headers' }}
            </button>
            <button
              type="button"
              class="flex items-center gap-1 text-[0.55rem] text-content-400 transition hover:text-content-100"
              @click="copyResponse"
            >
              <Check v-if="copied" :size="11" class="text-signal-ok" />
              <Clipboard v-else :size="11" />
              {{ copied ? 'Copied' : 'Copy' }}
            </button>
          </header>

          <div v-if="showHeaders" class="border-b border-line px-3.5 py-2.5">
            <p class="mb-1.5 font-mono text-[0.55rem] break-all text-content-500">
              {{ response.url }}
            </p>
            <div
              v-for="(value, name) in response.headers"
              :key="name"
              class="grid grid-cols-[minmax(7rem,auto)_1fr] gap-2 py-0.5 font-mono text-[0.55rem]"
            >
              <span class="text-content-500">{{ name }}</span>
              <span class="break-all text-content-300">{{ value }}</span>
            </div>
          </div>

          <pre
            class="max-h-96 overflow-auto p-3.5 font-mono text-[0.62rem] leading-relaxed whitespace-pre-wrap text-content-200"
            >{{ prettyBody || '(empty body)' }}</pre>
        </section>
      </div>

      <!-- Footer -->
      <footer class="flex items-center gap-2 border-t border-line bg-surface-850 px-4 py-3">
        <code class="min-w-0 flex-1 truncate font-mono text-[0.58rem] text-content-500">
          {{ resolvedPath }}
        </code>
        <button
          type="button"
          class="flex h-9 items-center gap-1.5 rounded-lg border border-line px-3 text-[0.63rem] text-content-300 transition hover:text-content-100"
          @click="reset"
        >
          <RotateCcw :size="13" />
          Reset
        </button>
        <button
          type="button"
          :disabled="sending"
          class="flex h-9 min-w-28 items-center justify-center gap-1.5 rounded-lg bg-accent-500 px-4 text-[0.66rem] font-bold text-surface-950 transition hover:bg-accent-400 disabled:cursor-wait disabled:opacity-60"
          @click="send"
        >
          <LoaderCircle v-if="sending" :size="14" class="animate-spin" />
          <Play v-else :size="13" />
          {{ sending ? 'Sending…' : 'Send' }}
        </button>
      </footer>
    </aside>
  </div>
</template>
