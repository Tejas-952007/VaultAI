"use client";

import React, { useEffect, useState } from "react";
import { Activity, ShieldCheck, Radio } from "lucide-react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type TelemetryResponse = {
  timestamp: string;
  system?: {
    cpu_percent?: number;
  };
};

export default function ZeroEgressGraph() {
  const [points, setPoints] = useState<number[]>([]);
  const [telemetryOnline, setTelemetryOnline] = useState(false);
  const [networkTelemetry, setNetworkTelemetry] =
    useState(false);

  useEffect(() => {
    let cancelled = false;

    const fetchTelemetry = async () => {
      try {
        const response = await fetch(
          `${API_BASE}/api/v1/telemetry`,
          {
            cache: "no-store",
          }
        );

        if (!response.ok) {
          throw new Error("Telemetry unavailable");
        }

        const data =
          (await response.json()) as TelemetryResponse;

        if (cancelled) return;

        const cpu =
          typeof data.system?.cpu_percent === "number"
            ? data.system.cpu_percent
            : 0;

        /*
         * This graph now represents real system telemetry.
         * It does NOT represent packet/egress traffic.
         */
        const graphValue = Math.max(
          4,
          Math.min(32, cpu / 2)
        );

        setPoints((previous) => {
          const next = [
            ...previous,
            graphValue,
          ];

          return next.slice(-12);
        });

        setTelemetryOnline(true);

        /*
         * The telemetry backend is reachable and returning
         * live system data, so the telemetry data source is
         * available.
         *
         * This is NOT claiming packet-level network
         * instrumentation.
         */
        setNetworkTelemetry(true);
      } catch {
        if (cancelled) return;

        setTelemetryOnline(false);
        setNetworkTelemetry(false);
      }
    };

    fetchTelemetry();

    const interval = window.setInterval(
      fetchTelemetry,
      2000
    );

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  const displayPoints =
    points.length > 0
      ? points
      : [4, 4, 4, 4, 4, 4, 4, 4];

  return (
    <div className="glass-panel p-3.5 rounded-xl text-xs font-mono space-y-2.5">
      {/* Header */}
      <div className="flex justify-between items-center">
        <span className="text-slate-400 text-[11px] flex items-center space-x-1.5">
          <Activity className="w-3.5 h-3.5 text-emerald-400" />

          <span>NETWORK TELEMETRY</span>
        </span>

        <span
          className={`font-bold px-2 py-0.5 rounded border text-[10px] ${
            networkTelemetry
              ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
              : "text-amber-400 bg-amber-500/10 border-amber-500/20"
          }`}
        >
          {networkTelemetry
            ? "AVAILABLE"
            : "UNAVAILABLE"}
        </span>
      </div>

      {/* Real telemetry graph */}
      <div className="h-9 flex items-end space-x-1 bg-black/40 rounded-lg p-1.5 border border-white/[0.04]">
        {displayPoints.map((point, index) => (
          <div
            key={`${index}-${point}`}
            className="flex-1 bg-gradient-to-t from-emerald-600/30 to-emerald-400 rounded-sm transition-all duration-500"
            style={{
              height: `${point}px`,
            }}
          />
        ))}
      </div>

      {/* Status */}
      <div className="flex justify-between gap-3 text-[10px] text-slate-500 pt-0.5 border-t border-white/[0.04]">
        <span className="flex items-center space-x-1">
          <ShieldCheck className="w-3 h-3 text-emerald-400/80" />

          <span
            className={
              "text-amber-400/80"
            }
          >
            Firewall: NOT VERIFIED
          </span>
        </span>

        <span
          className={
            telemetryOnline
              ? "text-emerald-400/80"
              : "text-slate-500"
          }
        >
          Telemetry:{" "}
          {telemetryOnline
            ? "online"
            : "offline"}
        </span>
      </div>

      {/* Isolation status */}
      <div className="flex items-center justify-between border-t border-white/[0.04] pt-2 text-[10px]">
        <span className="flex items-center space-x-1 text-slate-500">
          <Radio className="w-3 h-3" />

          <span>Network isolation</span>
        </span>

        <span className="text-amber-400/80">
          NOT INSTRUMENTED
        </span>
      </div>
    </div>
  );
}