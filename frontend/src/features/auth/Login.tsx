import { ArrowRight, ShieldCheck } from 'lucide-react';
import { useState, type FormEvent } from 'react';

export function Login({ onLogin }: { onLogin: (email: string, password: string) => Promise<void> }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); if (pending) return;
    setPending(true); setError('');
    try { await onLogin(email, password); }
    catch (err) { setError((err as Error).message); }
    finally { setPending(false); }
  }
  return <main className="login-page">
    <section className="login-story" aria-label="About Aster">
      <div className="brand"><span className="brand-symbol">a</span><strong>aster</strong></div>
      <div><p className="eyebrow">SUPPORT, WITH CLARITY</p><h1>Good answers.<br />Grounded in knowledge.</h1>
        <p className="story-copy">One calm workspace to understand customer requests, inspect the evidence, and stay in control.</p></div>
      <div className="story-footer"><ShieldCheck size={18} /><span>Knowledge. Context. Human judgment.</span></div>
    </section>
    <section className="login-panel"><div className="login-card">
      <p className="eyebrow">YOUR WORKSPACE</p><h2>Welcome back</h2><p className="muted">Sign in to your support workspace.</p>
      <form onSubmit={submit} aria-label="Sign in">
        <label htmlFor="email">Email address</label><input id="email" type="email" autoComplete="username" required
          value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" />
        <label htmlFor="password">Password</label><input id="password" type="password" autoComplete="current-password" required
          value={password} onChange={e => setPassword(e.target.value)} />
        {error && <p className="error" role="alert">{error}</p>}
        <button className="primary" disabled={pending} type="submit">{pending ? 'Signing in…' : 'Sign in'}<ArrowRight size={17} /></button>
      </form>
      <p className="access-note">Need access? Contact your workspace administrator.</p>
      <span className="mode-badge">Local support workbench</span>
    </div></section>
  </main>;
}
