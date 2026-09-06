"use client";

import { useEffect, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type GPU = {
  name: string;
  utilization_percent: number;
  memory_total_mb: number;
  memory_used_mb: number;
  memory_free_mb: number;
  temperature_c: number;
  power_watts: number;
};

type TelemetryData = {
  timestamp: string;
  system: {
    cpu_percent: number;
    memory_percent: number;
    memory_used_bytes: number;
    memory_total_bytes: number;
    uptime_seconds: number;
  };
  disk: {
    usage_percent: number;
    used_bytes: number;
    total_bytes: number;
    free_bytes: number;
  };
  backend_process: {
    cpu_percent: number;
    memory_bytes: number;
  };
  gpu: {
    available: boolean;
    count?: number;
    gpus?: GPU[];
    reason?: string;
  };
};

type Sample = {
  cpu: number;
  memory: number;
  gpu: number;
  vram: number;
};

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1
  );

  return `${(bytes / Math.pow(1024, index)).toFixed(1)} ${units[index]}`;
}

function formatUptime(seconds: number): string {
  const totalSeconds = Math.max(0, Math.floor(seconds));

  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);

  if (days > 0) {
    return `${days}d ${hours}h ${minutes}m`;
  }

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }

  return `${minutes}m`;
}

function MiniGraph({
  values,
  label,
  suffix = "%",
}: {
  values: number[];
  label: string;
  suffix?: string;
}) {
  const width = 520;
  const height = 110;
  const padding = 8;

  if (!values.length) {
    return (
      <div className="rounded-xl border border-cyan-400/10 bg-slate-950/40 p-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-cyan-300/60">
            {label}
          </span>

          <span className="text-sm font-semibold text-cyan-100">
            --
          </span>
        </div>

        <div className="mt-3 h-24" />
      </div>
    );
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(max - min, 1);

  const points = values
    .map((value, index) => {
      const x =
        padding +
        (index / Math.max(values.length - 1, 1)) *
          (width - padding * 2);

      const y =
        height -
        padding -
        ((value - min) / range) *
          (height - padding * 2);

      return `${x},${y}`;
    })
    .join(" ");

  const current = values[values.length - 1];

  return (
    <div className="rounded-xl border border-cyan-400/10 bg-slate-950/40 p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-cyan-300/60">
          {label}
        </span>

        <span className="text-sm font-semibold text-cyan-100">
          {current.toFixed(1)}
          {suffix}
        </span>
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="mt-2 h-24 w-full"
        preserveAspectRatio="none"
      >
        <line
          x1="0"
          y1={height - 1}
          x2={width}
          y2={height - 1}
          className="stroke-cyan-400/10"
          strokeWidth="1"
        />

        <polyline
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
          className="text-cyan-300"
        />
      </svg>
    </div>
  );
}

function MetricCard({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: string;
  subtitle: string;
}) {
  return (
    <div className="rounded-2xl border border-cyan-400/10 bg-slate-950/40 p-5 transition-colors hover:border-cyan-400/20">
      <p className="text-xs font-semibold uppercase tracking-widest text-cyan-300/60">
        {title}
      </p>

      <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-100">
        {value}
      </p>

      <p className="mt-1 text-xs text-slate-500">
        {subtitle}
      </p>
    </div>
  );
}

export default function TelemetryPage() {
  const [telemetry, setTelemetry] =
    useState<TelemetryData | null>(null);

  const [history, setHistory] = useState<Sample[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);

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
          throw new Error(
            `Telemetry API returned ${response.status}`
          );
        }

        const data =
          (await response.json()) as TelemetryData;

        if (cancelled) {
          return;
        }

        const gpu =
          data.gpu.available &&
          data.gpu.gpus &&
          data.gpu.gpus.length > 0
            ? data.gpu.gpus[0]
            : null;

        const vramPercent = gpu
          ? (gpu.memory_used_mb /
              Math.max(gpu.memory_total_mb, 1)) *
            100
          : 0;

        setTelemetry(data);
        setError(null);
        setLoading(false);

        setHistory((previous) => {
          const next = [
            ...previous,
            {
              cpu: data.system.cpu_percent,
              memory: data.system.memory_percent,
              gpu: gpu?.utilization_percent ?? 0,
              vram: vramPercent,
            },
          ];

          return next.slice(-60);
        });
      } catch (err) {
        if (cancelled) {
          return;
        }

        setLoading(false);

        setError(
          err instanceof Error
            ? err.message
            : "Unable to read telemetry"
        );
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

  const gpu =
    telemetry?.gpu.available &&
    telemetry.gpu.gpus &&
    telemetry.gpu.gpus.length > 0
      ? telemetry.gpu.gpus[0]
      : null;

  return (
    <main className="min-h-full w-full overflow-y-auto px-4 py-8 text-slate-100 sm:px-6 lg:px-10">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-cyan-400/60">
              VaultAI
            </p>

            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-100 sm:text-4xl">
              Control Manager
            </h1>

            <p className="mt-2 text-sm text-slate-500">
              Live local system telemetry and resource monitoring.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span
              className={`h-2 w-2 rounded-full ${
                error
                  ? "bg-red-400"
                  : telemetry
                    ? "bg-emerald-400"
                    : "bg-amber-400"
              }`}
            />

            <span className="text-slate-500">
              {error
                ? "Telemetry Offline"
                : telemetry
                  ? "Live"
                  : "Connecting..."}
            </span>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Main metrics */}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <MetricCard
            title="CPU Load"
            value={
              telemetry
                ? `${telemetry.system.cpu_percent.toFixed(1)}%`
                : "--"
            }
            subtitle="System CPU utilization"
          />

          <MetricCard
            title="Memory"
            value={
              telemetry
                ? `${telemetry.system.memory_percent.toFixed(
                    1
                  )}%`
                : "--"
            }
            subtitle={
              telemetry
                ? `${formatBytes(
                    telemetry.system.memory_used_bytes
                  )} / ${formatBytes(
                    telemetry.system.memory_total_bytes
                  )}`
                : "Waiting for telemetry"
            }
          />

          <MetricCard
            title="GPU Load"
            value={
              gpu
                ? `${gpu.utilization_percent.toFixed(1)}%`
                : "--"
            }
            subtitle={
              gpu
                ? gpu.name
                : "NVIDIA telemetry unavailable"
            }
          />
        </div>

        {/* History */}
        <section className="mt-5 grid gap-4 lg:grid-cols-2">
          <MiniGraph
            label="CPU History"
            values={history.map(
              (sample) => sample.cpu
            )}
          />

          <MiniGraph
            label="Memory History"
            values={history.map(
              (sample) => sample.memory
            )}
          />

          <MiniGraph
            label="GPU History"
            values={history.map(
              (sample) => sample.gpu
            )}
          />

          <MiniGraph
            label="VRAM Usage"
            values={history.map(
              (sample) => sample.vram
            )}
          />
        </section>

        {/* New sections */}
        <section className="mt-5 grid gap-4 lg:grid-cols-2">
          {/* GPU Thermals */}
          <div className="rounded-2xl border border-cyan-400/10 bg-slate-950/40 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-cyan-300/60">
                  GPU Thermals
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Live NVIDIA hardware telemetry
                </p>
              </div>

              <div className="rounded-lg border border-cyan-400/10 bg-cyan-400/5 px-3 py-1 text-xs text-cyan-300">
                NVIDIA SMI
              </div>
            </div>

            {gpu ? (
              <div className="mt-6 grid grid-cols-2 gap-x-8 gap-y-6">
                <div>
                  <p className="text-xs text-slate-500">
                    Temperature
                  </p>

                  <p className="mt-1 text-2xl font-semibold text-slate-100">
                    {gpu.temperature_c.toFixed(1)}°C
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    Power
                  </p>

                  <p className="mt-1 text-2xl font-semibold text-slate-100">
                    {gpu.power_watts.toFixed(1)} W
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    VRAM Used
                  </p>

                  <p className="mt-1 text-2xl font-semibold text-slate-100">
                    {formatBytes(
                      gpu.memory_used_mb * 1024 * 1024
                    )}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    VRAM Total
                  </p>

                  <p className="mt-1 text-2xl font-semibold text-slate-100">
                    {formatBytes(
                      gpu.memory_total_mb * 1024 * 1024
                    )}
                  </p>
                </div>
              </div>
            ) : (
              <p className="mt-6 text-sm text-slate-500">
                NVIDIA GPU telemetry is unavailable.
              </p>
            )}
          </div>

          {/* VaultAI Process */}
          <div className="rounded-2xl border border-cyan-400/10 bg-slate-950/40 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-cyan-300/60">
                  VaultAI Process
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Backend process resource usage
                </p>
              </div>

              <div className="rounded-lg border border-emerald-400/10 bg-emerald-400/5 px-3 py-1 text-xs text-emerald-300">
                Active
              </div>
            </div>

            {telemetry ? (
              <div className="mt-6 grid grid-cols-2 gap-x-8 gap-y-6">
                <div>
                  <p className="text-xs text-slate-500">
                    CPU
                  </p>

                  <p className="mt-1 text-2xl font-semibold text-slate-100">
                    {telemetry.backend_process.cpu_percent.toFixed(
                      1
                    )}
                    %
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    Memory
                  </p>

                  <p className="mt-1 text-2xl font-semibold text-slate-100">
                    {formatBytes(
                      telemetry.backend_process.memory_bytes
                    )}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    System Uptime
                  </p>

                  <p className="mt-1 text-2xl font-semibold text-slate-100">
                    {formatUptime(
                      telemetry.system.uptime_seconds
                    )}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    Polling
                  </p>

                  <p className="mt-1 text-2xl font-semibold text-slate-100">
                    2s
                  </p>
                </div>
              </div>
            ) : (
              <p className="mt-6 text-sm text-slate-500">
                Waiting for backend telemetry.
              </p>
            )}
          </div>
        </section>

        {/* Footer */}
        <div className="mt-8 flex flex-col gap-2 border-t border-cyan-400/10 py-5 text-[11px] uppercase tracking-wider text-slate-600 sm:flex-row sm:items-center sm:justify-between">
          <span>
            Local Host Telemetry · PSUTIL · NVIDIA SMI
          </span>

          <span>
            Rolling Window: 60 Samples · Hardware Poll: 2s
          </span>
        </div>

        {loading && !telemetry && (
          <div className="py-4 text-center text-xs text-slate-600">
            Initializing local telemetry...
          </div>
        )}
      </div>
    </main>
  );
}