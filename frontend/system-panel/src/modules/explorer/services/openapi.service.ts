import axios from 'axios'

import { apiUrl, env } from '@/core/config/env'
import { ApiError } from '@/infra/http'

import type { OpenApiDocument } from '../types'

/**
 * The contract is fetched raw rather than through the envelope client: FastAPI
 * serves `/openapi.json` as a bare document, not wrapped in `APIResponse`.
 */
export const openApiService = {
  async load(): Promise<OpenApiDocument> {
    try {
      const response = await axios.get<OpenApiDocument>(apiUrl('/openapi.json'), {
        timeout: env.requestTimeout,
        headers: { Accept: 'application/json' },
      })
      if (!response.data?.paths) {
        throw new ApiError('The contract came back without a paths object.', response.status)
      }
      return response.data
    } catch (cause) {
      if (cause instanceof ApiError) throw cause
      if (axios.isAxiosError(cause)) {
        throw new ApiError(
          cause.response
            ? `The backend answered ${cause.response.status} for /openapi.json.`
            : 'The backend could not be reached for /openapi.json.',
          cause.response?.status ?? 0,
        )
      }
      throw cause
    }
  },
}
