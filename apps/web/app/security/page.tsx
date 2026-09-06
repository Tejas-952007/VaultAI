"use client";

import { useEffect, useState } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  Lock,
  FileKey,
  Info,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
} from "lucide-react";

type ModelProvenance = {
  model: string;
  role: string;
  provider: string;
  sha256: string | null;
  expected_sha256: string | null;
  verification: string;
  status: string;
};

type SecurityStatus = {
  timestamp: string;
  hostname: string;
  network_isolation: {
    status: string;
    firewall: {
      status: string;
      profiles: { name: string; enabled: boolean }[];
    };
    airgap_rules: {
      status: string;
      rule_count: number;
      active_rules: number;
      rules: {
        name: string;
        direction: number;
        action: number;
        enabled: boolean;
      }[];
    };
  };
  local_services: {
    status: string;
    services: Record<
      string,
      { port: number; local_only: boolean | null }
    >;
  };
  claims: {
    physical_air_gap: string;
    gpu_memory_encryption: string;
    packet_telemetry: string;
    model_checksum: string;
  };
  model_provenance: {
    status: string;
    configured_models: number;
    verified_models: number;
    verification: string;
    model: string;
    role: string;
    provider: string;
    sha256: string | null;
    expected_sha256: string | null;
    models: ModelProvenance[];
  };
};

const API_BASE = (
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toUpperCase();

  if (normalized === "PASS" || normalized === "VERIFIED") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-[9px] font-black bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
        <CheckCircle2 size={11} />
        {normalized}
      </span>
    );
  }

  if (
    normalized === "FAIL" ||
    normalized === "ERROR" ||
    normalized === "NOT_IMPLEMENTED"
  ) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-[9px] font-black bg-red-500/10 text-red-400 border border-red-500/30">
        <XCircle size={11} />
        {normalized.replaceAll("_", " ")}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-[9px] font-black bg-slate-700/50 text-slate-400 border border-slate-700">
      {normalized.replaceAll("_", " ")}
    </span>
  );
}

function formatTimestamp(timestamp: string) {
  try {
    return new Date(timestamp).toLocaleString();
  } catch {
    return timestamp;
  }
}

export default function SecurityHub() {
  const [data, setData] = useState<SecurityStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadStatus() {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `${API_BASE}/api/v1/security/status`,
        {
          credentials: "include",
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(
          `Security endpoint returned ${response.status}`
        );
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load security status."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadStatus();

    const interval = setInterval(loadStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return (
      <div className="p-8 h-full overflow-y-auto bg-transparent">
        <div className="flex items-center gap-3 text-slate-400">
          <RefreshCw size={18} className="animate-spin" />
          <span className="text-sm font-mono">
            Loading live security instrumentation...
          </span>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="p-8 h-full overflow-y-auto bg-transparent">
        <div className="max-w-2xl rounded-xl border border-red-500/30 bg-red-500/5 p-6">
          <div className="flex items-center gap-3 text-red-400 mb-3">
            <ShieldAlert size={20} />
            <span className="font-bold">
              SECURITY STATUS UNAVAILABLE
            </span>
          </div>

          <p className="text-sm text-slate-400 font-mono">
            {error}
          </p>

          <button
            onClick={loadStatus}
            className="mt-5 px-4 py-2 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 text-xs font-bold hover:bg-slate-700 transition"
          >
            RETRY
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const networkPass =
    data.network_isolation.status === "PASS";

  const localPass =
    data.local_services.status === "PASS";

  const modelPass =
    data.model_provenance.status === "PASS" &&
    data.model_provenance.verified_models ===
      data.model_provenance.configured_models;

  const models = data.model_provenance.models || [];

  return (
    <div className="p-8 h-full overflow-y-auto space-y-8 bg-transparent">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tighter uppercase">
            Sovereignty Hub
          </h1>

          <p className="text-slate-500 text-sm">
            Live Model Provenance &amp; Air-Gap Compliance Status
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono">
            <Clock size={12} />
            {formatTimestamp(data.timestamp)}
          </div>

          <button
            onClick={loadStatus}
            disabled={loading}
            className="p-2 rounded-lg border border-slate-700 bg-slate-800/60 text-slate-400 hover:text-slate-200 hover:bg-slate-700 transition"
            title="Refresh security status"
          >
            <RefreshCw
              size={15}
              className={loading ? "animate-spin" : ""}
            />
          </button>
        </div>
      </div>

      <div
        className={`flex items-start gap-3 px-5 py-4 rounded-xl border ${
          networkPass && localPass && modelPass
            ? "bg-emerald-500/5 border-emerald-500/30 text-emerald-300"
            : "bg-amber-500/5 border-amber-500/30 text-amber-300"
        }`}
      >
        {networkPass && localPass && modelPass ? (
          <ShieldCheck
            size={18}
            className="mt-0.5 flex-shrink-0"
          />
        ) : (
          <Info
            size={18}
            className="mt-0.5 flex-shrink-0"
          />
        )}

        <div className="text-sm leading-relaxed">
          <span className="font-bold block mb-1">
            Live security instrumentation is active.
          </span>

          Firewall profiles, VaultAI air-gap rules, local service
          bindings, and all configured model checksums are read
          directly from the backend. Unsupported capabilities remain
          explicitly marked as unverified or not implemented.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-navy/80 border border-slate-700 rounded-xl p-6">
          <h2 className="text-xs font-bold text-slate-300 mb-6 flex items-center gap-2">
            <ShieldAlert
              size={16}
              className={
                networkPass
                  ? "text-emerald-400"
                  : "text-red-400"
              }
            />

            NETWORK ISOLATION

            <span className="ml-auto">
              <StatusBadge
                status={data.network_isolation.status}
              />
            </span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-bold text-slate-500 uppercase">
                  Windows Firewall
                </span>

                <StatusBadge
                  status={
                    data.network_isolation.firewall.status
                  }
                />
              </div>

              <div className="space-y-2">
                {data.network_isolation.firewall.profiles.map(
                  (profile) => (
                    <div
                      key={profile.name}
                      className="flex items-center justify-between text-xs"
                    >
                      <span className="text-slate-400">
                        {profile.name}
                      </span>

                      <span
                        className={
                          profile.enabled
                            ? "text-emerald-400 font-bold"
                            : "text-red-400 font-bold"
                        }
                      >
                        {profile.enabled
                          ? "ENABLED"
                          : "DISABLED"}
                      </span>
                    </div>
                  )
                )}
              </div>
            </div>

            <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-bold text-slate-500 uppercase">
                  VaultAI Air-Gap Rules
                </span>

                <StatusBadge
                  status={
                    data.network_isolation.airgap_rules.status
                  }
                />
              </div>

              <div className="text-3xl font-black text-slate-100">
                {
                  data.network_isolation.airgap_rules
                    .active_rules
                }

                <span className="text-slate-600 text-lg">
                  /
                  {
                    data.network_isolation.airgap_rules
                      .rule_count
                  }
                </span>
              </div>

              <p className="text-[10px] text-slate-500 mt-1 font-mono">
                ACTIVE BLOCK RULES
              </p>
            </div>
          </div>

          <div className="mt-4 rounded-lg border border-slate-700 bg-slate-900/40 p-4">
            <div className="text-[10px] font-bold text-slate-500 uppercase mb-3">
              Local Service Bindings
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(
                data.local_services.services
              ).map(([name, service]) => (
                <div
                  key={name}
                  className="flex items-center justify-between rounded border border-slate-800 px-3 py-2"
                >
                  <div>
                    <span className="text-xs text-slate-300 font-bold uppercase">
                      {name}
                    </span>

                    <span className="ml-2 text-[10px] text-slate-600 font-mono">
                      :{service.port}
                    </span>
                  </div>

                  {service.local_only ? (
                    <span className="text-[9px] font-black text-emerald-400">
                      LOCAL ONLY
                    </span>
                  ) : (
                    <span className="text-[9px] font-black text-red-400">
                      NOT LOCAL
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-navy/80 border border-slate-700 rounded-xl p-6 space-y-6">
          <h2 className="text-xs font-bold text-slate-300 flex items-center gap-2">
            <Lock size={16} className="text-slate-500" />
            CONTAINMENT STATUS
          </h2>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-400">
                Physical Air Gap
              </span>

              <StatusBadge
                status={data.claims.physical_air_gap}
              />
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-400">
                GPU Memory Encryption
              </span>

              <StatusBadge
                status={
                  data.claims.gpu_memory_encryption
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-400">
                Packet Telemetry
              </span>

              <StatusBadge
                status={data.claims.packet_telemetry}
              />
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-400">
                Model Checksum
              </span>

              <StatusBadge
                status={data.claims.model_checksum}
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800">
            <div className="text-[10px] text-slate-600 font-mono leading-relaxed">
              Host: {data.hostname}
              <br />
              Backend security endpoint: LIVE
              <br />
              Refresh interval: 15 seconds
            </div>
          </div>
        </div>
      </div>

      <div className="bg-navy/80 border border-slate-700 rounded-xl overflow-hidden">
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h2 className="text-xs font-bold text-slate-300 flex items-center gap-2">
                <FileKey
                  size={16}
                  className="text-cyan-500"
                />
                MODEL PROVENANCE
              </h2>

              <p className="text-[11px] text-slate-600 mt-1 font-mono">
                SHA-256 is calculated from each local Ollama model
                blob and compared against its expected content hash.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-[10px] text-slate-500 font-mono">
                {data.model_provenance.verified_models}/
                {data.model_provenance.configured_models} VERIFIED
              </span>

              <StatusBadge
                status={data.model_provenance.status}
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-6 border-b border-slate-800">
          {models.map((model) => (
            <div
              key={model.model}
              className="rounded-xl border border-slate-700 bg-slate-900/40 p-5"
            >
              <div className="flex items-start justify-between gap-3 mb-4">
                <div>
                  <div className="text-sm font-black text-slate-200">
                    {model.model}
                  </div>

                  <div className="text-[10px] text-cyan-400 font-bold uppercase mt-1">
                    {model.role}
                  </div>
                </div>

                <StatusBadge
                  status={model.verification}
                />
              </div>

              <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">
                Provider
              </div>

              <div className="text-[11px] text-slate-400 font-mono mb-4">
                {model.provider}
              </div>

              <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">
                SHA-256
              </div>

              <div className="text-[9px] text-cyan-400 font-mono break-all leading-relaxed">
                {model.sha256 || "NOT AVAILABLE"}
              </div>
            </div>
          ))}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-[11px]">
            <thead>
              <tr className="bg-obsidian/50 text-slate-500 uppercase tracking-widest border-b border-slate-700">
                <th className="px-6 py-3 font-bold">
                  Model Name
                </th>

                <th className="px-6 py-3 font-bold">
                  Role
                </th>

                <th className="px-6 py-3 font-bold">
                  Provider
                </th>

                <th className="px-6 py-3 font-bold">
                  SHA-256 Checksum
                </th>

                <th className="px-6 py-3 font-bold">
                  Verification
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-800">
              {models.map((model) => (
                <tr
                  key={model.model}
                  className="hover:bg-slate-700/20 transition"
                >
                  <td className="px-6 py-4 font-bold text-slate-200">
                    {model.model}
                  </td>

                  <td className="px-6 py-4 text-cyan-400">
                    {model.role}
                  </td>

                  <td className="px-6 py-4 text-slate-400 font-mono">
                    {model.provider}
                  </td>

                  <td className="px-6 py-4 font-mono text-cyan-400 break-all">
                    {model.sha256 || "NOT AVAILABLE"}
                  </td>

                  <td className="px-6 py-4">
                    <StatusBadge
                      status={model.verification}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/20">
          <div className="text-[9px] text-slate-600 font-mono">
            CONFIGURED MODELS:{" "}
            {data.model_provenance.configured_models}
            {" | "}
            VERIFIED:{" "}
            {data.model_provenance.verified_models}
            {" | "}
            ALL MODEL CHECKSUMS MUST MATCH
          </div>
        </div>
      </div>
    </div>
  );
}