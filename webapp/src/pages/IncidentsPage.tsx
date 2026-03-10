import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";

import { fetchIncidents } from "../api/dashboardClient";
import type { components } from "../api/types";
import type { AppShellOutletContext } from "../ui/AppShell";

type IncidentsPayload = components["schemas"]["DashboardIncidentsV2"];
type IncidentItem = {
  id?: string;
  service?: string;
  severity?: string;
  impact?: number;
  title?: string;
  summary?: string;
  count?: number;
  latest_at?: string;
};

function severityTone(value?: string): string {
  const v = String(value ?? "").toLowerCase();
  if (v === "critical") {
    return "border-rose-300/30 bg-rose-500/10 text-rose-300";
  }
  if (v === "warning") {
    return "border-amber-300/30 bg-amber-500/10 text-amber-300";
  }
  return "border-emerald-400/30 bg-emerald-500/10 text-emerald-300";
}

export function IncidentsPage() {
  const { filters, setFilters } = useOutletContext<AppShellOutletContext>();
  const [data, setData] = useState<IncidentsPayload | null>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");

    void fetchIncidents({
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
        <h2 className="text-2xl font-semibold text-slate-100">Incidents</h2>
        <p className="mt-2">Loading incident stream...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="rounded-2xl border border-rose-500/40 bg-rose-950/30 p-8 text-rose-200">
        <h2 className="text-2xl font-semibold text-rose-100">Incidents</h2>
        <p className="mt-2">Failed to load incidents: {error}</p>
      </section>
    );
  }

  const incidentsNode = (data?.incidents ?? {}) as {
    summary?: { open?: number; critical?: number; warning?: number };
    items?: IncidentItem[];
  };

  const summary = incidentsNode.summary ?? {};
  const items = incidentsNode.items ?? [];

  return (
    <section className="grid gap-5">
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl shadow-slate-950/60">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Incidents</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-100">Incident Groups</h2>
            <p className="mt-2 text-sm text-slate-400">
              Deduped warnings and critical signals for the current filter set.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="rounded-xl border border-slate-800 bg-slate-950/70 px-3 py-2 text-center">
              <div className="text-xs uppercase tracking-wide text-slate-500">Open</div>
              <div className="mt-1 text-xl font-semibold text-slate-100">{summary.open ?? 0}</div>
            </div>
            <div className="rounded-xl border border-rose-300/20 bg-rose-500/5 px-3 py-2 text-center">
              <div className="text-xs uppercase tracking-wide text-rose-300/80">Critical</div>
              <div className="mt-1 text-xl font-semibold text-rose-300">{summary.critical ?? 0}</div>
            </div>
            <div className="rounded-xl border border-amber-300/20 bg-amber-500/5 px-3 py-2 text-center">
              <div className="text-xs uppercase tracking-wide text-amber-300/80">Warning</div>
              <div className="mt-1 text-xl font-semibold text-amber-300">{summary.warning ?? 0}</div>
            </div>
          </div>
        </div>
      </section>

      {items.length === 0 ? (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl shadow-slate-950/60">
          <p className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-slate-400">
            No incident groups for current filters.
          </p>
        </section>
      ) : (
        <section className="grid gap-4 xl:grid-cols-2">
          {items.map((item) => (
            <article
              key={item.id ?? item.title}
              className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-xl shadow-slate-950/60"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className={`rounded-full border px-2.5 py-1 text-xs uppercase tracking-wide ${severityTone(item.severity)}`}>
                  {String(item.severity ?? "unknown")}
                </div>
                <div className="text-xs text-slate-500">Impact {item.impact ?? 0}</div>
              </div>
              <h3 className="mt-4 text-lg font-semibold text-slate-100">{item.title ?? "Incident"}</h3>
              <p className="mt-2 text-sm text-slate-400">{item.summary ?? "No summary"}</p>
              <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-500">
                <span>Service: {item.service ?? "unknown"}</span>
                <span>Count: {item.count ?? 0}</span>
                <span>Latest: {item.latest_at ?? "n/a"}</span>
              </div>
              <button
                type="button"
                className="mt-4 rounded-full border border-cyan-400/40 bg-cyan-400/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-200 transition hover:border-cyan-300/60 hover:bg-cyan-400/15"
                onClick={() =>
                  setFilters({
                    ...filters,
                    service: (item.service as AppShellOutletContext["filters"]["service"]) || "all",
                  })
                }
              >
                Drill by service
              </button>
            </article>
          ))}
        </section>
      )}
    </section>
  );
}
