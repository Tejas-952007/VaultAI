'use client';
import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ShieldCheck, Terminal, FileText, Cpu, LayoutDashboard, History, ShieldAlert, Sparkles, LogOut } from 'lucide-react';
import { useAuth } from '@/components/AuthProvider';

const NAV_ITEMS = [
  { name: 'Workbench', href: '/', icon: LayoutDashboard },
  { name: 'Documents', href: '/documents', icon: FileText },
  { name: 'RBAC Policy', href: '/access-control', icon: ShieldCheck },
  { name: 'Audit History', href: '/audit-history', icon: History },
  { name: 'Air-Gap Hub', href: '/security', icon: ShieldAlert },
  { name: 'Sandbox', href: '/sandbox', icon: Terminal },
  { name: 'Telemetry', href: '/telemetry', icon: Cpu },
];

export default function Navbar() {
  const pathname = usePathname();
  const { employee, logout } = useAuth();

  if (!employee) return null;

  return (
    <header className="h-14 border-b border-white/[0.08] bg-[#090D16]/80 backdrop-blur-xl sticky top-0 z-40 flex items-center justify-between px-5 font-sans">
      {/* Brand & Tagline */}
      <div className="flex items-center space-x-6">
        <Link href="/" className="flex items-center space-x-2.5 group">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-cyan-600 to-emerald-400 p-[1px] shadow-lg shadow-cyan-500/20">
            <div className="w-full h-full bg-[#090D16] rounded-[7px] flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400 group-hover:rotate-12 transition-transform" />
            </div>
          </div>
          <div>
            <span className="font-mono font-bold text-sm tracking-wider text-white">VAULT<span className="text-cyan-400">AI</span></span>
            <span className="hidden sm:inline-block ml-2 text-[10px] font-mono text-slate-400 uppercase tracking-widest bg-white/[0.05] px-1.5 py-0.5 rounded border border-white/[0.05]">
              SIH 2026 • MRPL
            </span>
          </div>
        </Link>

        {/* Modern Nav Tabs */}
        <nav className="hidden lg:flex items-center space-x-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  active
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm shadow-cyan-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Right Telemetry & Role Badges */}
      <div className="flex items-center space-x-3 text-xs font-mono">
        <div className="flex items-center space-x-2 px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-400 shadow-sm shadow-emerald-500/10">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-[11px] font-semibold tracking-wide">LOCAL-ONLY MODE</span>
        </div>

        {employee && (
          <div className="hidden sm:flex items-center gap-2">
            <Link href="/access-control" className="flex items-center space-x-1.5 px-3 py-1 bg-slate-800/60 hover:bg-slate-800 border border-white/[0.08] rounded-full text-slate-300 transition-colors">
              <span className="text-slate-500 text-[10px]">POSITION:</span>
              <span className="text-cyan-400 font-semibold text-[11px]">{employee.position || 'UNASSIGNED'}</span>
            </Link>
            <button onClick={() => void logout()} className="text-slate-400 hover:text-white" title="Sign out">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}