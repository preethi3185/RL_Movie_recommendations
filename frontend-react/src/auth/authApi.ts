import { apiRequest } from '../lib/api'

export type AuthUser = { user_id: string; email: string; username: string; is_demo: boolean }
export type AuthResponse = { access_token: string; token_type: string; user: AuthUser }

export const authApi = {
  /**
   * Creates a new user account.
   * Returns a JWT access token and the user's profile.
   */
  register: (email: string, username: string, password: string) => apiRequest<AuthResponse>('/auth/register', { method: 'POST', body: JSON.stringify({ email, username, password }) }),

  /**
   * Authenticates an existing user.
   * Validates credentials and returns a JWT access token.
   */
  login: (email: string, password: string) => apiRequest<AuthResponse>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),

  /**
   * Provides instant access via a pre-configured guest account.
   * Useful for first-time visitors to explore recommendations without signing up.
   */
  demo: () => apiRequest<AuthResponse>('/auth/demo', { method: 'POST' }),

  /**
   * Fetches the currently authenticated user's profile based on the JWT in storage.
   */
  me: () => apiRequest<AuthUser>('/auth/me'),
}
