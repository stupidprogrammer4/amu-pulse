/** Mirrors `AdminOut` — the id arrives encrypted, so it is not a number here. */
export interface Admin {
  id: string | number
  username: string
  is_super_admin: boolean
  created_at?: string
  updated_at?: string
}

/** Mirrors `AdminAuthOut` from `/auth/admins/login`. */
export interface AdminAuth {
  access_token: string
  refresh_token: string
  token_type: string
  admin: Admin
}

export interface LoginPayload {
  username: string
  password: string
}
