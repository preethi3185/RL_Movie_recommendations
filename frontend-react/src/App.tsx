import { useEffect, useMemo, useState } from 'react'
import { apiRequest, movieApi } from './lib/api'
import type { Dashboard, Movie, Page, Profile } from './types'
import TopNav from './components/TopNav'
import HeroPanel from './components/HeroPanel'
import PageHeading from './components/PageHeading'
import { ApiAlert, EmptyState, LoadingState } from './components/FeedbackStates'
import LibraryPage from './pages/LibraryPage'
import DashboardPage from './pages/DashboardPage'
import ProfilePage from './pages/ProfilePage'
import AuthScreen from './components/AuthScreen'
import OnboardingPage from './pages/OnboardingPage'
import { authApi, type AuthResponse, type AuthUser } from './auth/authApi'

const pageTitles: Record<Page, string> = {
  Recommendations: 'Curated for your next watch',
  Search: 'Find something worth watching',
  Watchlist: 'Your saved cinema',
  History: 'Your viewing trail',
  Dashboard: 'Taste, measured',
  Profile: 'Shape your cinema profile',
}

const pageStorageKey = 'movieverse_current_page'
const pages: Page[] = ['Recommendations', 'Search', 'Watchlist', 'History', 'Dashboard', 'Profile']

function getStoredPage(): Page {
  const storedPage = localStorage.getItem(pageStorageKey) as Page | null
  return storedPage && pages.includes(storedPage) ? storedPage : 'Recommendations'
}

function App() {
  const [authUser, setAuthUser] = useState<AuthUser | null>(null)
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [initialPage] = useState(getStoredPage)
  const [page, setPage] = useState<Page>(initialPage)
  const [query, setQuery] = useState('')
  const [offset, setOffset] = useState(0)
  const [movies, setMovies] = useState<Movie[]>([])
  const [profile, setProfile] = useState<Profile | null>(null)
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')

  const loadPage = async (nextPage: Page, nextQuery = query, nextOffset = offset) => {
    setLoading(true)
    setError('')
    try {
      if (nextPage === 'Recommendations') setMovies(await movieApi.recommendations(25, nextOffset))
      if (nextPage === 'Search' && nextQuery.trim()) setMovies((await movieApi.search(nextQuery)).items)
      if (nextPage === 'Watchlist') setMovies(await movieApi.watchlist())
      if (nextPage === 'History') setMovies(await movieApi.history())
      if (nextPage === 'Profile') setProfile(await movieApi.profile())
      if (nextPage === 'Dashboard') setDashboard(await movieApi.dashboard())
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not connect to MovieVerse API.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    localStorage.setItem(pageStorageKey, page)
  }, [page])

  useEffect(() => {
    if (!sessionStorage.getItem('movieverse_access_token')) {
      return
    }
    void Promise.all([authApi.me(), movieApi.profile()])
      .then(async ([user, prof]) => {
        setAuthUser(user)
        setProfile(prof)
        if (initialPage === 'Recommendations') setMovies(await movieApi.recommendations(25, 0))
        if (initialPage === 'Watchlist') setMovies(await movieApi.watchlist())
        if (initialPage === 'History') setMovies(await movieApi.history())
        if (initialPage === 'Dashboard') setDashboard(await movieApi.dashboard())
      })
      .catch((requestError: unknown) => setError(requestError instanceof Error ? requestError.message : 'Could not connect to MovieVerse API.'))
      .finally(() => setLoading(false))
  }, [initialPage])

  const handleAuthenticated = async (response: AuthResponse, isNewAccount: boolean) => {
    sessionStorage.setItem('movieverse_access_token', response.access_token)
    setAuthUser(response.user)
    setShowOnboarding(isNewAccount)
    setPage('Recommendations')
    setOffset(0)
    if (!isNewAccount) {
      try {
        const [prof, recs] = await Promise.all([
          movieApi.profile(),
          movieApi.recommendations(25, 0)
        ])
        setProfile(prof)
        setMovies(recs)
      } catch {
        setError('Could not load your profile.')
      }
    }
  }

  const logout = () => {
    sessionStorage.removeItem('movieverse_access_token')
    setAuthUser(null)
    setMovies([])
    setProfile(null)
    setDashboard(null)
  }

  const navigate = (nextPage: Page) => {
    setPage(nextPage)
    setOffset(0)
    if (nextPage !== 'Search') setQuery('')
    void loadPage(nextPage, query, 0)
  }

  const performAction = async (path: string, method = 'POST', body?: object) => {
    // Store the current profile state before making the API call.
    // This allows us to "roll back" the UI if the server request fails.
    const previousProfile = profile
    try {
      const movieId = parseInt(path.split('/').filter(Boolean).pop() || '0')

      /**
       * Optimistic UI Update:
       * To make the app feel instantaneous, we update the local state
       * BEFORE the API call completes. The user sees their action
       * reflected immediately, rather than waiting for a network round-trip.
       */
      setProfile(prev => {
        if (!prev) return null
        // If marking as watched, immediately add to the local history.
        if (path.includes('/watched') && method === 'POST') {
          return { ...prev, watched_movies: [...(prev.watched_movies ?? []), movieId] }
        }
        // If toggling watchlist, add or remove based on the HTTP method.
        if (path.includes('/watchlist')) {
          const newWatchlist = method === 'POST'
            ? [...(prev.watchlist ?? []), movieId]
            : (prev.watchlist ?? []).filter(id => id !== movieId)
          return { ...prev, watchlist: newWatchlist }
        }
        return prev
      })

      // Execute the actual network request.
      await apiRequest(path, { method, body: body ? JSON.stringify(body) : undefined })
      setToast('Your cinema profile has been updated.')
      window.setTimeout(() => setToast(''), 2400)
    } catch (requestError) {
      // ROLLBACK: If the server returns an error, we revert the local state
      // to the previousProfile to maintain consistency with the backend.
      setProfile(previousProfile)
      setError(requestError instanceof Error ? requestError.message : 'That action could not be completed.')
    }
  }

  const watchlistIds = useMemo(() => new Set(profile?.watchlist ?? []), [profile])
  const watchedIds = useMemo(() => new Set(profile?.watched_movies ?? []), [profile])
  const hasLibraryPage = page === 'Recommendations' || page === 'Search' || page === 'Watchlist' || page === 'History'
  const searchIsEmpty = page === 'Search' && !query

  if (!authUser && !sessionStorage.getItem('movieverse_access_token')) return <AuthScreen onAuthenticated={handleAuthenticated} />
  if (showOnboarding && authUser) return <OnboardingPage username={authUser.username} onComplete={() => { setShowOnboarding(false); void loadPage('Recommendations') }} />

  return <div className="min-h-screen bg-[#0b1020] text-[#edf2ff]">
    <TopNav page={page} username={authUser?.username ?? 'Viewer'} isDemo={authUser?.is_demo ?? false} onNavigate={navigate} onLogout={logout} />
    <main className="mx-auto mb-20 mt-8 w-[calc(100%-2rem)] max-w-[1400px] sm:w-[calc(100%-3rem)]">
      <HeroPanel />
      <PageHeading page={page} title={pageTitles[page]} query={query} onQueryChange={setQuery} onSearch={() => void loadPage('Search', query)} />
      {error && <ApiAlert message={error} />}
      {toast && <div className="fixed bottom-6 right-6 z-20 rounded-[15px] border border-[#48dcb8]/30 bg-[#0f2c2b]/95 px-5 py-4 text-sm text-[#dffdf4] shadow-2xl">{toast}</div>}
      {loading && <LoadingState />}
      {!loading && searchIsEmpty && <EmptyState title="Start with a title or genre." message="Search the full movie catalog to find your next watch." />}
      {!loading && hasLibraryPage && !searchIsEmpty && (
        <>
          <LibraryPage page={page as 'Recommendations' | 'Search' | 'Watchlist' | 'History'} movies={movies} watchlistIds={watchlistIds} watchedIds={watchedIds} onWatched={(id) => void performAction(`/interactions/${id}/watched`)} onToggleWatchlist={(id) => void performAction(`/interactions/${id}/watchlist`, watchlistIds.has(id) ? 'DELETE' : 'POST')} onRate={(id, rating) => void performAction(`/interactions/${id}/rating`, 'POST', { rating })} />
          {page === 'Recommendations' && (
            <div className="mt-8 flex justify-center gap-4">
              <button disabled={offset === 0} className="rounded-xl border border-white/10 bg-white/[.05] px-6 py-2 text-sm text-[#aebbd7] transition hover:border-[#8066ff]/50 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed" onClick={() => { const nextOffset = Math.max(0, offset - 25); setOffset(nextOffset); void loadPage('Recommendations', query, nextOffset); }}>Previous</button>
              <button disabled={movies.length < 25} className="rounded-xl border border-white/10 bg-white/[.05] px-6 py-2 text-sm text-[#aebbd7] transition hover:border-[#8066ff]/50 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed" onClick={() => { const nextOffset = offset + 25; setOffset(nextOffset); void loadPage('Recommendations', query, nextOffset); }}>Next</button>
            </div>
          )}
        </>
      )}
      {!loading && page === 'Dashboard' && dashboard && <DashboardPage data={dashboard} />}
      {!loading && page === 'Profile' && profile && authUser && <ProfilePage profile={profile} user={authUser} onSaved={() => { setToast('Preferences saved. Recommendations will adapt from here.'); navigate('Recommendations') }} />}
    </main>
  </div>
}

export default App
