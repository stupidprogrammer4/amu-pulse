import { ref, shallowRef, type Ref } from 'vue'

import { ApiRequestError } from '@/infra/http/api-error'

export interface UseAsyncDataOptions {
  /** Run the fetcher as soon as the composable is created. */
  immediate?: boolean
}

export interface UseAsyncData<T, A extends unknown[]> {
  data: Ref<T | null>
  error: Ref<ApiRequestError | null>
  isLoading: Ref<boolean>
  execute: (...args: A) => Promise<T | null>
}

/**
 * Wraps a service call in loading/error state. Stale responses are dropped, so
 * a slow request that resolves after a newer one never overwrites fresh data.
 */
export function useAsyncData<T, A extends unknown[] = []>(
  fetcher: (...args: A) => Promise<T>,
  options: UseAsyncDataOptions = {},
): UseAsyncData<T, A> {
  const data = shallowRef<T | null>(null)
  const error = ref<ApiRequestError | null>(null)
  const isLoading = ref(false)

  let requestId = 0

  async function execute(...args: A): Promise<T | null> {
    const currentId = ++requestId
    isLoading.value = true
    error.value = null

    try {
      const result = await fetcher(...args)
      if (currentId !== requestId) return null
      data.value = result
      return result
    } catch (caught) {
      if (currentId !== requestId) return null
      error.value =
        caught instanceof ApiRequestError
          ? caught
          : new ApiRequestError(caught instanceof Error ? caught.message : 'خطای غیرمنتظره')
      return null
    } finally {
      if (currentId === requestId) isLoading.value = false
    }
  }

  if (options.immediate) void execute(...([] as unknown as A))

  return { data, error, isLoading, execute }
}
