import { useState } from 'react'
import { authApi, type AuthResponse } from '../auth/authApi'

type Props = { onAuthenticated: (response: AuthResponse, isNewAccount: boolean) => void }

export default function AuthScreen({ onAuthenticated }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const response = mode === 'login' ? await authApi.login(email, password) : await authApi.register(email, username, password)
      onAuthenticated(response, mode === 'register')
    } catch (requestError) {
      /**
       * Backend Error Parsing:
       * FastAPI returns error details in a JSON format: {"detail": "Error message"}.
       * These regex replacements strip the JSON metadata to display only the
       * human-readable error message to the user.
       */
      setError(requestError instanceof Error ? requestError.message.replace(/^\{.*"detail":"?/, '').replace(/"?\}$/, '') : 'Authentication failed.')
    } finally {
      setBusy(false)
    }
  }

  const demoLogin = async () => {
    setBusy(true)
    setError('')
    try { onAuthenticated(await authApi.demo(), false) } catch { setError('Demo access is temporarily unavailable.') } finally { setBusy(false) }
  }

  return <main className="grid min-h-screen place-items-center bg-[#0b1020] px-5 py-10 text-[#edf2ff]"><section className="w-full max-w-[460px] rounded-[26px] border border-white/10 bg-[#121926]/90 p-7 shadow-2xl shadow-black/30 sm:p-9"><div className="mb-8 flex items-center gap-3"><span className="grid h-12 w-12 place-items-center rounded-[15px] bg-gradient-to-br from-[#8066ff] to-[#16c8ee] font-bold">MV</span><span><strong className="block font-['Space_Grotesk'] text-xl">MovieVerse</strong><small className="text-[.65rem] tracking-[.16em] text-[#aebbd7]">PERSONAL CINEMA</small></span></div><div className="text-[.7rem] font-bold tracking-[.14em] text-[#cad3ee]">{mode === 'login' ? 'WELCOME BACK' : 'CREATE YOUR ACCOUNT'}</div><h1 className="mt-2 font-['Space_Grotesk'] text-3xl font-semibold">{mode === 'login' ? 'Enter your cinema.' : 'Start your cinema.'}</h1><p className="mt-2 text-sm text-[#aebbd7]">{mode === 'login' ? 'Sign in to continue your personalized movie journey.' : 'Create a profile and begin building your taste.'}</p><form className="mt-7 grid gap-4" onSubmit={submit}>{mode === 'register' && <label className="grid gap-1.5 text-sm text-[#aebbd7]">Username<input className="rounded-xl border border-white/10 bg-[#080d17] px-3.5 py-3 text-white outline-none focus:border-[#8066ff]" value={username} onChange={(event) => setUsername(event.target.value)} required /></label>}<label className="grid gap-1.5 text-sm text-[#aebbd7]">Email<input type="email" className="rounded-xl border border-white/10 bg-[#080d17] px-3.5 py-3 text-white outline-none focus:border-[#8066ff]" value={email} onChange={(event) => setEmail(event.target.value)} required /></label><label className="grid gap-1.5 text-sm text-[#aebbd7]">Password<input type="password" minLength={mode === 'register' ? 8 : 1} className="rounded-xl border border-white/10 bg-[#080d17] px-3.5 py-3 text-white outline-none focus:border-[#8066ff]" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>{error && <p className="rounded-xl border border-[#ffb86c]/30 bg-[#2c2117] p-3 text-sm text-[#ffd6a0]">{error}</p>}<button className="rounded-xl bg-gradient-to-br from-[#8066ff] to-[#16c8ee] px-4 py-3 font-bold text-white transition hover:brightness-110 disabled:opacity-60" disabled={busy}>{busy ? 'Please wait...' : mode === 'login' ? 'Log in' : 'Create account'}</button></form><div className="my-5 flex items-center gap-3 text-xs text-[#7081a8]"><span className="h-px flex-1 bg-white/10" />OR<span className="h-px flex-1 bg-white/10" /></div><button className="w-full rounded-xl border border-[#8066ff]/35 bg-[#8066ff]/10 px-4 py-3 text-sm font-semibold text-[#dcd7ff] transition hover:bg-[#8066ff]/20" onClick={() => void demoLogin()} disabled={busy}>Login as demo user</button><button className="mt-5 w-full text-sm text-[#aebbd7] hover:text-white" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>{mode === 'login' ? 'Need an account? Create one' : 'Already have an account? Log in'}</button></section></main>
}
