import { anonymousRequest, request } from '@/infra/http'

import type { Admin, AdminAuth, LoginPayload } from '../types'

/** The three routes under `/auth/admins` the panel signs in through. */
export const authService = {
  login(payload: LoginPayload): Promise<AdminAuth> {
    return anonymousRequest<AdminAuth>({
      method: 'post',
      url: '/auth/admins/login',
      data: payload,
    })
  },

  me(): Promise<Admin> {
    return request<Admin>({ method: 'get', url: '/auth/admins/me' })
  },
}
