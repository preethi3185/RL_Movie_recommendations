import type { Dashboard } from '../types'

export default function DashboardPage({ data }: { data: Dashboard }) {
  return (
    <section className="grid gap-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <Metric label="Movies watched" value={data.movies_watched} />
        <Metric label="Movies rated" value={data.movies_rated} />
        <Metric label="Average rating" value={data.average_rating.toFixed(1)} />
      </div>
      <div className="rounded-[20px] border border-white/10 bg-[#121926]/85 p-6 shadow-xl shadow-black/15">
        <div className="text-[.7rem] font-bold tracking-[.14em] text-[#cad3ee]">LEARNED TASTE</div>
        <h3 className="mb-5 mt-2 font-['Space_Grotesk'] text-xl font-semibold text-white">What your feedback is teaching the agent</h3>
        {data.genre_preferences.length === 0 ? (
          <p className="text-sm text-[#aebbd7]">Rate a few movies to reveal preference signals.</p>
        ) : (
          data.genre_preferences.map((item) => (
            <div className="grid grid-cols-[90px_1fr_38px] items-center gap-2 border-b border-white/[.08] py-3 text-sm text-[#aebbd7] sm:grid-cols-[120px_1fr_44px] sm:gap-3.5" key={item.genre}>
              <span>{item.genre}</span>
              <div className="h-[5px] overflow-hidden rounded-full bg-white/[.07]">
                {/**
                 * Score Normalization for UI:
                 * The RL Agent's Q-values typically range from -1.0 (disliked) to 1.0 (liked).
                 * To represent this as a percentage for the progress bar:
                 * 1. (item.score + 1) maps -1.0..1.0 to 0.0..2.0.
                 * 2. Multiplying by 50 maps it to 0%..100%.
                 * 3. Math.max(8, ...) ensures the bar is always visible, even for highly disliked genres.
                 */}
                <i className="block h-full rounded-full bg-gradient-to-r from-[#8066ff] to-[#16c8ee]" style={{ width: `${Math.max(8, Math.min(100, (item.score + 1) * 50))}%` }} />
              </div>
              <strong className="text-right text-[#dce5ff]">{item.score.toFixed(2)}</strong>
            </div>
          ))
        )}
      </div>
    </section>
  )
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-[#121926]/85 p-[22px] shadow-xl shadow-black/15">
      <span className="text-xs text-[#aebbd7]">{label}</span>
      <strong className="mt-3 block font-['Space_Grotesk'] text-4xl font-bold text-white">{value}</strong>
    </div>
  )
}
