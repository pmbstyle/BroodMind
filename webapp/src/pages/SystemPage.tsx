import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";

import { fetchSystem } from "../api/dashboardClient";
import type { components } from "../api/types";
import type { AppShellOutletContext } from "../ui/AppShell";

type SystemPayload = components["schemas"]["DashboardSystemV2"];
type ServiceItem = { id?: string; name?: string; status?: string; reason?: string; updated_at?: string };
type LogItem = { timestamp?: string; level?: string; event?: string; service?: string };
type Connectivity = {
  mcp_servers?: Record<
    string,
    {
      status?: string;
      tool_count?: number;
      name?: string;
      reason?: string;
      transport?: string;
      reconnect_attempts?: number;
      connected?: boolean;
      reconnecting?: boolean;
      configured?: boolean;
      error?: string | null;
    }
  >;
};

function statusTone(status?: string): string {
  const v = String(status ?? "").toLowerCase();
  if (v === "ok" || v === "connected" || v === "running") {
    return "border-emerald-400/30 bg-emerald-500/10 text-emerald-300";
  }
  if (v === "warning" || v === "reconnecting" || v === "configured") {
    return "border-amber-300/30 bg-amber-500/10 text-amber-300";
  }
  return "border-rose-300/30 bg-rose-500/10 text-rose-300";
}

export function SystemPage() {
  const { filters } = useOutletContext<AppShellOutletContext>();
  const [data, setData] = useState<SystemPayload | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");

    void fetchSystem({
      windowMinutes: filters.windowMinutes,
      service: filters.service,
      environment: filters.environment,
      token: filters.token || undefined,
    })
      .then((payload) => {
        if (active) {
          setData(payload);
        }
      })
      .catch((err: unknown) => {
        if (!active) {
          return;
        }
        setError(err instanceof Error ? err.message : "Unknown request error");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [filters.environment, filters.service, filters.token, filters.windowMinutes]);

  if (loading) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8 text-slate-300">
        <h2 className="text-2xl font-semibold text-slate-100">System</h2>
        <p className="mt-2">Loading system diagnostics...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="rounded-2xl border border-rose-500/40 bg-rose-950/30 p-8 text-rose-200">
        <h2 className="text-2xl font-semibold text-rose-100">System</h2>
        <p className="mt-2">Failed to load system diagnostics: {error}</p>
      </section>
    );
  }

  const system = (data?.system ?? {}) as { running?: boolean; pid?: number; uptime?: string; active_channel?: string };
  const services = ((data?.services ?? []) as ServiceItem[]).slice(0, 10);
  const logs = ((data?.logs ?? []) as LogItem[]).slice(0, 10);
  const connectivity = (data?.connectivity ?? {}) as Connectivity;
  const mcpServers = connectivity.mcp_servers ?? {};

  return (
    <section className="grid gap-5">
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl shadow-slate-950/60">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">System</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-100">
              {system.running ? "Runtime is healthy" : "Runtime is degraded"}
            </h2>
            <p className="mt-2 text-sm text-slate-400">
              PID {system.pid ?? "n/a"} | Channel {system.active_channel ?? "n/a"} | Uptime {system.uptime ?? "n/a"}
            </p>
          </div>
          <div className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${statusTone(system.running ? "running" : "critical")}`}>
            {system.running ? "running" : "down"}
          </div>
        </div>
      </section>

      <div className="grid gap-5 xl:grid-cols-2">
        <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-xl shadow-slate-950/60">
          <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-300">Service Health</h3>
          <div className="mt-4 space-y-3">
            {services.length === 0 ? (
              <p className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-slate-400">No services.</p>
            ) : (
              services.map((service) => (
                <article key={service.id ?? service.name} className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h4 className="text-base font-semibold text-slate-100">{service.name ?? "Service"}</h4>
                      <p className="mt-1 text-sm text-slate-400">{service.reason ?? "No reason"}</p>
                    </div>
                    <div className={`rounded-full border px-2.5 py-1 text-xs uppercase tracking-wide ${statusTone(service.status)}`}>
                      {String(service.status ?? "unknown")}
                    </div>
                  </div>
                </article>
              ))
            )}
          </div>
        </article>

        <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-xl shadow-slate-950/60">
          <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-300">MCP Connectivity</h3>
          <div className="mt-4 space-y-3">
            {Object.keys(mcpServers).length === 0 ? (
              <p className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-slate-400">
                No MCP servers configured.
              </p>
            ) : (
              Object.entries(mcpServers).map(([key, value]) => (
                <article key={key} className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h4 className="text-base font-semibold text-slate-100">{value.name ?? key}</h4>
                      <p className="mt-1 text-sm text-slate-400">
                        Available tools: {value.tool_count ?? 0} | Transport: {value.transport ?? "auto"}
                      </p>
                      <p className="mt-1 text-sm text-slate-500">
                        {value.reason ?? "No detail available"}
                        {typeof value.reconnect_attempts === "number" && value.reconnect_attempts > 0
                          ? ` | Retry attempts: ${value.reconnect_attempts}`
                          : ""}
                      </p>
                      {value.error ? <p className="mt-1 text-sm text-rose-300/80">{value.error}</p> : null}
                    </div>
                    <div className={`rounded-full border px-2.5 py-1 text-xs uppercase tracking-wide ${statusTone(value.status)}`}>
                      {String(value.status ?? "unknown")}
                    </div>
                  </div>
                </article>
              ))
            )}
          </div>
        </article>
      </div>

      <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-xl shadow-slate-950/60">
        <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-300">Recent Logs</h3>
        {logs.length === 0 ? (
          <p className="mt-4 rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-slate-400">
            No logs in current filter window.
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="border-b border-slate-800 px-3 py-2">Time</th>
                  <th className="border-b border-slate-800 px-3 py-2">Level</th>
                  <th className="border-b border-slate-800 px-3 py-2">Service</th>
                  <th className="border-b border-slate-800 px-3 py-2">Event</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={`${log.timestamp ?? ""}-${log.event ?? ""}`} className="border-b border-slate-900">
                    <td className="px-3 py-3 text-slate-400">{log.timestamp ?? "n/a"}</td>
                    <td className="px-3 py-3">
                      <span className={`rounded-full border px-2 py-1 text-xs uppercase tracking-wide ${statusTone(log.level)}`}>
                        {String(log.level ?? "info")}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-slate-300">{log.service ?? "gateway"}</td>
                    <td className="px-3 py-3 text-slate-300">{log.event ?? ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  );
}
