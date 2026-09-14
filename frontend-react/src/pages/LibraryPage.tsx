import MovieCard from '../components/MovieCard'
import { EmptyState } from '../components/FeedbackStates'
import type { Movie } from '../types'

type Props = { movies: Movie[]; page: 'Recommendations' | 'Search' | 'Watchlist' | 'History'; watchlistIds: Set<number>; watchedIds: Set<number>; onWatched: (id: number) => void; onToggleWatchlist: (id: number) => void; onRate: (id: number, rating: number) => void }

export default function LibraryPage({ movies, page, watchlistIds, watchedIds, onWatched, onToggleWatchlist, onRate }: Props) {
  if (!movies.length) return <EmptyState title={page === 'Watchlist' ? 'Your watchlist is empty.' : page === 'History' ? 'No viewing history yet.' : 'No films found.'} message="There is always another great story to discover." />
  return <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-[18px]">{movies.map((movie, index) => <MovieCard key={movie.movie_id} movie={movie} index={index} isWatchlisted={watchlistIds.has(movie.movie_id)} isWatched={watchedIds.has(movie.movie_id)} onWatched={() => onWatched(movie.movie_id)} onToggleWatchlist={() => onToggleWatchlist(movie.movie_id)} onRate={(rating) => onRate(movie.movie_id, rating)} />)}</div>
}
