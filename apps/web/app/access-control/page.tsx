"use client";

import { useEffect, useState } from "react";
import { ShieldAlert } from "lucide-react";
import { AdminEmployee, AdminPermission, AdminPosition, VaultAPI } from "@/lib/api";

export default function AccessControlPage() {
  const [employees, setEmployees] = useState<AdminEmployee[]>([]);
  const [positions, setPositions] = useState<AdminPosition[]>([]);
  const [permissions, setPermissions] = useState<AdminPermission[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [currentPassword, setCurrentPassword] = useState("");
  const [selectedEmployee, setSelectedEmployee] = useState("");
  const [selectedPosition, setSelectedPosition] = useState("");
  const [selectedPermission, setSelectedPermission] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([VaultAPI.listAdminEmployees(), VaultAPI.listAdminPositions(), VaultAPI.listAdminPermissions()])
      .then(([employeeData, positionData, permissionData]) => {
        setEmployees(employeeData);
        setPositions(positionData);
        setPermissions(permissionData);
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Access-control data unavailable."));
  }, []);

  async function updateEmployeeStatus(is_active: boolean) {
    setStatus(null);
    try {
      const updated = await VaultAPI.updateAdminEmployee(Number(selectedEmployee), currentPassword, is_active);
      setEmployees((items) => items.map((item) => item.id === updated.id ? updated : item));
      setStatus(`Employee ${updated.employee_id} updated.`);
    } catch (reason) {
      setStatus(reason instanceof Error ? reason.message : "Employee update failed.");
    }
  }

  async function updatePositionPermission(allowed: boolean) {
    setStatus(null);
    try {
      const result = await VaultAPI.setPositionPermission(Number(selectedPosition), Number(selectedPermission), currentPassword, allowed);
      setStatus(`${result.permission} ${allowed ? "granted to" : "revoked from"} ${result.position}.`);
    } catch (reason) {
      setStatus(reason instanceof Error ? reason.message : "Permission update failed.");
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6 font-sans">
      <div className="border-b border-vault-border pb-4">
        <h1 className="text-xl font-bold font-mono text-slate-100 flex items-center gap-2"><ShieldAlert className="w-6 h-6 text-amber-400" />ACCESS CONTROL STATUS</h1>
        <p className="text-xs text-slate-400 font-mono mt-2">Server-side authentication and position-based RBAC.</p>
      </div>
      {error ? <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4 text-rose-300 text-sm">{error}</div> : (
        <div className="grid gap-4 sm:grid-cols-3">
          <section className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
            <h2 className="font-mono text-xs text-cyan-300">EMPLOYEES</h2>
            <div className="mt-3 space-y-2">{employees.map((item) => <div key={item.employee_id} className="text-sm text-slate-200"><span className="font-mono text-cyan-400">{item.employee_id}</span><br />{item.full_name} <span className="text-xs text-slate-500">({item.position || "unassigned"})</span></div>)}</div>
          </section>
          <section className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
            <h2 className="font-mono text-xs text-cyan-300">POSITIONS</h2>
            <div className="mt-3 space-y-2">{positions.map((item) => <div key={item.id} className="text-sm text-slate-200">{item.name}<span className="ml-2 text-xs text-slate-500">{item.is_active ? "ACTIVE" : "INACTIVE"}</span></div>)}</div>
          </section>
          <section className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
            <h2 className="font-mono text-xs text-cyan-300">PERMISSIONS</h2>
            <div className="mt-3 max-h-64 space-y-1 overflow-auto">{permissions.map((item) => <div key={item.id} className="font-mono text-xs text-slate-300">{item.code}</div>)}</div>
          </section>
        </div>
      )}
      {!error && (
        <section className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
          <h2 className="font-mono text-xs text-cyan-300">ADMINISTRATION (STEP-UP REQUIRED)</h2>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            <input value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} type="password" placeholder="Current password" className="rounded border border-white/10 bg-black/20 px-3 py-2 text-sm text-white" />
            <select value={selectedEmployee} onChange={(event) => setSelectedEmployee(event.target.value)} className="rounded border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white">
              <option value="">Select employee</option>{employees.map((item) => <option key={item.id} value={item.id}>{item.employee_id}</option>)}
            </select>
            <div className="flex gap-2"><button disabled={!selectedEmployee || !currentPassword} onClick={() => updateEmployeeStatus(false)} className="rounded border border-rose-500/30 px-3 py-2 text-xs text-rose-300 disabled:opacity-40">DISABLE EMPLOYEE</button><button disabled={!selectedEmployee || !currentPassword} onClick={() => updateEmployeeStatus(true)} className="rounded border border-emerald-500/30 px-3 py-2 text-xs text-emerald-300 disabled:opacity-40">ENABLE EMPLOYEE</button></div>
            <select value={selectedPosition} onChange={(event) => setSelectedPosition(event.target.value)} className="rounded border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white">
              <option value="">Select position</option>{positions.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
            <select value={selectedPermission} onChange={(event) => setSelectedPermission(event.target.value)} className="rounded border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white">
              <option value="">Select permission</option>{permissions.map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}
            </select>
            <div className="flex gap-2"><button disabled={!selectedPosition || !selectedPermission || !currentPassword} onClick={() => updatePositionPermission(false)} className="rounded border border-rose-500/30 px-3 py-2 text-xs text-rose-300 disabled:opacity-40">REVOKE POSITION PERMISSION</button><button disabled={!selectedPosition || !selectedPermission || !currentPassword} onClick={() => updatePositionPermission(true)} className="rounded border border-cyan-500/30 px-3 py-2 text-xs text-cyan-300 disabled:opacity-40">GRANT POSITION PERMISSION</button></div>
          </div>
          {status && <p className="mt-3 text-xs text-slate-300">{status}</p>}
        </section>
      )}
      <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 text-xs text-amber-300">Demo organization mappings are representative VaultAI data, not an official MRPL authorization matrix. Authorization is enforced by the backend.</div>
    </div>
  );
}
