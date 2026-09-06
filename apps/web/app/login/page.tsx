'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { LockKeyhole, ShieldCheck, Sparkles } from 'lucide-react';
import { useAuth } from '@/components/AuthProvider';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { employee, loading, login } = useAuth();
  const [employeeId, setEmployeeId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!loading && employee) router.replace('/workbench');
  }, [employee, loading, router]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(employeeId.trim(), password);
      setPassword('');
      router.replace(searchParams.get('next') || '/workbench');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Authentication failed.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#070B12] px-5 py-10 text-slate-100">
      <section className="w-full max-w-md rounded-xl border border-white/[0.1] bg-[#0B111D]/95 p-8 shadow-2xl shadow-cyan-950/30">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-600 to-emerald-400 p-[1px]">
            <div className="flex h-full w-full items-center justify-center rounded-[11px] bg-[#090D16]">
              <Sparkles className="h-6 w-6 text-cyan-400" />
            </div>
          </div>
          <div className="font-mono text-xl font-bold tracking-widest text-white">VAULT<span className="text-cyan-400">AI</span></div>
          <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">Sovereign AI Workbench • SIH 2026 • MRPL</p>
        </div>
        <div className="mb-5 flex items-center gap-2 border-b border-white/[0.08] pb-3">
          <LockKeyhole className="h-4 w-4 text-cyan-400" />
          <h1 className="font-mono text-sm font-semibold uppercase tracking-wider text-slate-200">Employee Authentication</h1>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block font-mono text-xs text-slate-400">
            Employee ID
            <input value={employeeId} onChange={(event) => setEmployeeId(event.target.value)} required autoComplete="username" className="mt-2 w-full rounded border border-white/10 bg-black/20 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-400" />
          </label>
          <label className="block font-mono text-xs text-slate-400">
            Password
            <input value={password} onChange={(event) => setPassword(event.target.value)} required type="password" autoComplete="current-password" className="mt-2 w-full rounded border border-white/10 bg-black/20 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-400" />
          </label>
          {error && <p className="rounded border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">{error}</p>}
          <button disabled={busy} className="flex w-full items-center justify-center gap-2 rounded bg-cyan-500 px-3 py-2.5 font-mono text-xs font-bold tracking-wider text-slate-950 transition hover:bg-cyan-400 disabled:cursor-wait disabled:opacity-50">
            <ShieldCheck className="h-4 w-4" /> {busy ? 'AUTHENTICATING...' : 'AUTHENTICATE'}
          </button>
        </form>
        <p className="mt-6 text-center font-mono text-[10px] uppercase tracking-wider text-slate-500">LOCAL-ONLY • ON-PREMISE • SESSION PROTECTED</p>
      </section>
    </main>
  );
}
