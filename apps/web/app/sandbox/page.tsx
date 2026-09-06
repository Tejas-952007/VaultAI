"use client";
import { useState } from "react";
import { Terminal, Play, RefreshCw, AlertTriangle } from "lucide-react";
import { VaultAPI, SandboxResponse } from "@/lib/api";

const DEFAULT_CODE = "value = 1\nfor number in range(1, 11):\n    value *= number\nprint(value)";

/**
 * Isolated Sandbox page.
 *
 * Code is executed by the backend inside the network-disabled Docker sandbox.
 */
export default function Sandbox() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [result, setResult] = useState<SandboxResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  const runCode = async () => {
    setRunning(true);
    setError(null);
    try {
      setResult(await VaultAPI.executeSandbox(code));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Sandbox request failed.");
      setResult(null);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="p-8 h-full flex flex-col gap-6 bg-transparent overflow-y-auto">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-black text-slate-100 tracking-tighter uppercase">Isolated Sandbox</h1>
          <p className="text-slate-500 text-sm mt-1">Live backend execution through the network-disabled Docker boundary</p>
        </div>
        <button onClick={runCode} disabled={running || !code.trim()} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-xs font-bold">
          {running ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
          {running ? "Running…" : "Run in sandbox"}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
        <section className="bg-navy/80 border border-slate-700 rounded-xl p-5 flex flex-col gap-3">
          <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">Python source</label>
          <textarea value={code} onChange={e => setCode(e.target.value)} spellCheck={false} className="flex-1 min-h-[280px] resize-none rounded-lg bg-black/60 border border-slate-800 p-4 text-sm text-cyan-200 font-mono focus:outline-none focus:border-cyan-500/50" />
          <p className="text-[10px] text-slate-600 font-mono">Execution is performed by the backend sandbox. Browser JavaScript never executes this source.</p>
        </section>
        <section className="bg-navy/80 border border-slate-700 rounded-xl p-5 flex flex-col gap-4">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-widest"><Terminal size={15} className="text-cyan-400" /> Execution result</div>
          {error && <div className="flex gap-2 text-sm text-red-400"><AlertTriangle size={16} />{error}</div>}
          {!result && !error && <p className="text-sm text-slate-600 font-mono">No execution result yet.</p>}
          {result && <>
            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <span className="text-slate-500">Exit code <b className={result.exit_code === 0 ? "text-emerald-400" : "text-red-400"}>{result.exit_code}</b></span>
              <span className="text-slate-500">Duration <b className="text-cyan-300">{result.duration_seconds.toFixed(3)}s</b></span>
              <span className="text-slate-500">Timeout <b className={result.timed_out ? "text-red-400" : "text-emerald-400"}>{result.timed_out ? "YES" : "NO"}</b></span>
              <span className="text-slate-500">Request <b className="text-slate-300">{result.request_id.slice(0, 8)}…</b></span>
            </div>
            <Output label="stdout" value={result.stdout} />
            <Output label="stderr" value={result.stderr} error />
          </>}
        </section>
      </div>
    </div>
  );
}

function Output({ label, value, error = false }: { label: string; value: string; error?: boolean }) {
  return <div className="space-y-1"><p className={`text-[10px] uppercase font-bold ${error ? "text-red-400" : "text-slate-500"}`}>{label}</p><pre className={`min-h-16 whitespace-pre-wrap rounded bg-black/60 border border-slate-800 p-3 text-xs font-mono ${error ? "text-red-300" : "text-emerald-300"}`}>{value || "(none)"}</pre></div>;
}