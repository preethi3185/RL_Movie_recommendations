import type { Page } from '../types'

const items: { label: Page; marker?: string }[] = [
  { label: 'Recommendations' },
  { label: 'Watchlist' },
  { label: 'History' },
  { label: 'Dashboard' },
  { label: 'Profile' },
]

type Props = { page: Page; username: string; isDemo: boolean; onNavigate: (page: Page) => void; onLogout: () => void }

export default function TopNav({ page, username, isDemo, onNavigate, onLogout }: Props) {
  return <header className="sticky top-4 z-10 mx-auto flex w-[calc(100%-2rem)] max-w-[1400px] flex-wrap items-center gap-4 rounded-[22px] border border-white/10 bg-[#0c121e]/85 p-2.5 shadow-2xl shadow-black/20 backdrop-blur-xl sm:w-[calc(100%-3rem)] lg:flex-nowrap">
    <button className="flex min-w-0 flex-1 items-center gap-3 text-left text-white lg:min-w-[210px] lg:flex-none" onClick={() => onNavigate('Recommendations')} aria-label="Go to recommendations">
      <span className="grid h-11 w-11 shrink-0 place-items-center rounded-[14px] bg-gradient-to-br from-[#8066ff] to-[#16c8ee] text-sm font-bold shadow-lg shadow-cyan-500/20">MV</span>
      <span><strong className="block font-['Space_Grotesk'] text-[1.06rem]">MovieVerse</strong><small className="block text-[.62rem] tracking-[.15em] text-[#aebbd7]">PERSONAL CINEMA</small></span>
    </button>
    <nav className="order-3 flex w-full gap-1 overflow-x-auto lg:order-none lg:w-auto lg:flex-1" aria-label="Primary navigation">
      {[...items, { label: 'Search' as Page, marker: '⌕' }].map((item) => <button key={item.label} className={`flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-xl border px-3.5 text-sm whitespace-nowrap transition duration-200 hover:-translate-y-px hover:bg-white/[.06] ${page === item.label ? 'border-[#8066ff]/40 bg-gradient-to-br from-[#8066ff]/45 to-[#16c8ee]/20 text-white' : 'border-transparent text-[#aebbd7]'}`} onClick={() => onNavigate(item.label)}>{item.marker && <span className="font-['Space_Grotesk'] text-[.68rem] text-[#7889b1]">{item.marker}</span>}{item.label}</button>)}
    </nav>
    <div className="flex items-center gap-2"><button className="flex items-center gap-2 p-1 text-[#dce5ff]" onClick={() => onNavigate('Profile')}><span className="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-[#8066ff] to-[#16c8ee] text-xs font-bold">{username.slice(0, 2).toUpperCase()}</span><small className="hidden max-w-28 truncate text-xs sm:block">{isDemo ? 'Demo user' : username}</small></button><button className="rounded-lg border border-white/10 px-2 py-1 text-xs text-[#aebbd7] transition hover:border-[#8066ff]/50 hover:text-white" onClick={onLogout}>Log out</button></div>
  </header>
}
