'use client';
import React from 'react';
import { Cpu } from 'lucide-react';

interface ModelStatusProps {
  name: string;
  role: string;
  status: 'active' | 'ready' | 'standby' | 'idle' | 'error';
}

export default function ModelStatusPill({ name, role, status }: ModelStatusProps) {
  const isActive = status === 'active';
  const isError = status === 'error';
  const isIdle = status === 'idle' || status === 'standby';

  const containerCls = isActive
    ? 'bg-cyan-500/[0.08] border-cyan-500/30 shadow-sm shadow-cyan-500/10'
    : isError
    ? 'bg-red-500/[0.06] border-red-500/20'
    : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.04]';

  const iconCls = isActive
    ? 'bg-cyan-500/20 text-cyan-400'
    : isError
    ? 'bg-red-500/20 text-red-400'
    : 'bg-slate-800 text-slate-500';

  const badgeCls = isActive
    ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30 animate-pulse'
    : isError
    ? 'bg-red-500/10 text-red-400 border-red-500/20'
    : isIdle
    ? 'bg-slate-700/40 text-slate-500 border-slate-700'
    : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';

  return (
    <div className={`p-2.5 rounded-lg border transition-all flex items-center justify-between font-mono ${containerCls}`}>
      <div className="flex items-center space-x-2.5 truncate">
        <div className={`w-7 h-7 rounded-md flex items-center justify-center ${iconCls}`}>
          <Cpu className="w-3.5 h-3.5" />
        </div>
        <div className="truncate">
          <span className="text-xs font-semibold text-slate-200 block truncate">{name}</span>
          <span className="text-[10px] text-slate-400 block truncate">{role}</span>
        </div>
      </div>
      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${badgeCls}`}>
        {status.toUpperCase()}
      </span>
    </div>
  );
}