import type { Dashboard, Movie, Profile } from '../types'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

export async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(sessionStorage.getItem('movieverse_access_token') ? { Authorization: `Bearer ${sessionStorage.getItem('movieverse_access_token')}` } : {}),
      ...options?.headers,
    },
  })
  if (response.status === 401 && !path.startsWith('/auth/')) {
    sessionStorage.removeItem('movieverse_access_token')
    window.location.reload()
  }
  if (!response.ok) throw new Error(await response.text() || 'The API request failed.')
  return response.json() as Promise<T>
}

export const movieApi = {
  recommendations: (limit = 25, offset = 0) => apiRequest<Movie[]>(`/recommendations?limit=${limit}&offset=${offset}`),
  search: (query: string) => apiRequest<{ items: Movie[] }>(`/movies/search?q=${encodeURIComponent(query)}&limit=30`),
  watchlist: () => apiRequest<Movie[]>('/interactions/watchlist'),
  history: () => apiRequest<Movie[]>('/interactions/history'),
  profile: () => apiRequest<Profile>('/profile'),
  dashboard: () => apiRequest<Dashboard>('/dashboard'),
  watched: (movieId: number) => apiRequest(`/interactions/${movieId}/watched`, { method: 'POST' }),
  addToWatchlist: (movieId: number) => apiRequest(`/interactions/${movieId}/watchlist`, { method: 'POST' }),
  removeFromWatchlist: (movieId: number) => apiRequest(`/interactions/${movieId}/watchlist`, { method: 'DELETE' }),
  rate: (movieId: number, rating: number) => apiRequest(`/interactions/${movieId}/rating`, { method: 'POST', body: JSON.stringify({ rating }) }),
  updatePreferences: (genres: string[]) => apiRequest<Profile>('/profile/preferences', { method: 'PUT', body: JSON.stringify({ preferred_genres: genres }) }),
}
