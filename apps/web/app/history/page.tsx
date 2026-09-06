"use client";

import { useEffect, useState } from "react";
import { History, RefreshCw, AlertTriangle } from "lucide-react";
import { AuditEvent, VaultAPI } from "@/lib/api";

export default function HistoryPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await VaultAPI.getAudit();
      setEvents(response.events);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Audit data unavailable.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6 font-sans">
      <div className="border-b border-vault-border pb-4 flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2"><History className="w-6 h-6 text-cyan-400" />WORKFLOW &amp; AUDIT TRAIL HISTORY</h1>
          <p className="text-xs text-slate-400 font-mono">Local audit metadata only. Sensitive payloads are minimized.</p>
        </div>
        <button onClick={load} title="Refresh audit events" className="p-2 border border-vault-border rounded text-slate-400 hover:text-cyan-400"><RefreshCw size={16} className={loading ? "animate-spin" : ""} /></button>
      </div>
      {error && <div className="flex items-center gap-2 text-red-400 text-sm"><AlertTriangle size={16} />{error}</div>}
      <div className="bg-vault-card border border-vault-border rounded-lg overflow-auto font-mono text-xs">
        {!loading && !error && events.length === 0 && <p className="p-10 text-center text-slate-500">No audit events available.</p>}
        {events.length > 0 && <table className="w-full text-left"><thead className="bg-vault-surface/60 text-slate-400"><tr><th className="p-3">TIME</th><th className="p-3">ACTOR</th><th className="p-3">POSITION</th><th className="p-3">ACTION</th><th className="p-3">TARGET</th><th className="p-3">RESULT</th></tr></thead><tbody className="divide-y divide-slate-800">{events.map((event) => <tr key={event.id} className="text-slate-300"><td className="p-3 text-slate-400">{new Date(event.timestamp).toLocaleString()}</td><td className="p-3">{event.employee_id ? `${event.employee_id} — ${event.employee_name}` : "SYSTEM"}</td><td className="p-3">{event.position || "-"}</td><td className="p-3 text-cyan-400">{event.action}</td><td className="p-3">{event.resource_id || event.resource_type || "-"}</td><td className="p-3">{event.result}</td></tr>)}</tbody></table>}
      </div>
    </div>
  );
}
