import { useEffect, useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";

import { fetchOverview } from "../api/dashboardClient";
import type { components } from "../api/types";
import type { AppShellOutletContext } from "../ui/AppShell";

type OverviewPayload = components["schemas"]["DashboardOverviewV2"];
type KpiItem = { value?: unknown; unit?: string; status?: string };
type HealthView = { status?: string; summary?: string; reasons?: string[] };
type ServiceView = { id?: string; name?: string; status?: string; reason?: string; updated_at?: string };

function statusTone(status?: string): string {
  const value = String(status ?? "").toLowerCase();
  if (value === "ok") {
    return "border-emerald-400/30 bg-emerald-500/10 text-emerald-300";
  }
  if (value === "warning") {
    return "border-amber-300/30 bg-amber-500/10 text-amber-300";
  }
  return "border-rose-300/30 bg-rose-500/10 text-rose-300";
}

function formatKpi(value: unknown, unit?: string): string {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }
  return unit ? `${String(value)} ${unit}` : String(value);
}

export function OverviewPage() {
  const { filters } = useOutletContext<AppShellOutletContext>();
  const [data, setData] = useState<OverviewPayload | null>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let active = true;
    let source: EventSource | null = null;

    const query = new URLSearchParams();
    query.set("window_minutes", String(filters.windowMinutes));
    query.set("service", filters.service);
    query.set("environment", filters.environment);
    query.set("topic", "overview");
    query.set("interval_seconds", "2");
    if (filters.token) {
      query.set("token", filters.token);
    }

    const loadOnce = async () => {
      setLoading(true);
      setError("");
      try {
        const payload = await fetchOverview({
          windowMinutes: filters.windowMinutes,
          service: filters.service,
          environment: filters.environment,
          token: filters.token || undefined,
        });
        if (active) {
          setData(payload);
        }
      } catch (err: unknown) {
        if (active) {
          setError(err instanceof Error ? err.message : "Unknown request error");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void loadOnce();
    const pollTimer = window.setInterval(() => {
      void loadOnce();
    }, 15000);

    if (typeof EventSource !== "undefined") {
      source = new EventSource(`/api/dashboard/v2/stream?${query.toString()}`);
      source.addEventListener("overview", (event: MessageEvent) => {
        if (!active) {
          return;
        }
        try {
          const payload = JSON.parse(event.data) as OverviewPayload;
          setData(payload);
          setError("");
          setLoading(false);
        } catch (_error) {
          // Keep current data when stream payload is malformed.
        }
      });
    }

    return () => {
      active = false;
      if (source) {
        source.close();
      }
      window.clearInterval(pollTimer);
    };
  }, [filters.environment, filters.service, filters.token, filters.windowMinutes]);

  const incidentsSummary = useMemo(() => {
    if (!data) {
      return { open: 0, critical: 0, warning: 0 };
    }
    return data.incidents_summary;
  }, [data]);

  const health = (data?.health ?? {}) as HealthView;
  const kpis = (data?.kpis ?? {}) as Record<string, KpiItem>;
  const services = ((data?.services ?? []) as ServiceView[]).slice(0, 6);

  if (loading) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8 text-slate-300">
        <h2 className="text-2xl font-semibold text-slate-100">Overview</h2>
        <p className="mt-2">Loading operational snapshot...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="rounded-2xl border border-rose-500/40 bg-rose-950/30 p-8 text-rose-200">
        <h2 className="text-2xl font-semibold text-rose-100">Overview</h2>
        <p className="mt-2">Failed to load overview: {error}</p>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8 text-slate-300">
        <h2 className="text-2xl font-semibold text-slate-100">Overview</h2>
        <p className="mt-2">No data returned.</p>
      </section>
    );
  }

  return (
    <section className="grid gap-5">
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl shadow-slate-950/60">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Overview</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-100">
              {health.summary ?? "Operational summary"}
            </h2>
            <p className="mt-2 max-w-3xl text-sm text-slate-400">
              {(health.reasons ?? []).join(" | ") || "No degradation reasons."}
            </p>
          </div>
          <div
            className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${statusTone(health.status)}`}
          >
            {String(health.status ?? "unknown")}
          </div>
        </div>
      </section>

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Latency p95</p>
          <p className="mt-2 text-2xl font-semibold text-slate-100">
            {formatKpi(kpis.latency_ms_p95?.value, kpis.latency_ms_p95?.unit)}
          </p>
          <span className={`mt-3 inline-flex rounded-full border px-2 py-1 text-xs ${statusTone(kpis.latency_ms_p95?.status)}`}>
            {String(kpis.latency_ms_p95?.status ?? "unknown")}
          </span>
        </article>
        <article className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Error rate</p>
          <p className="mt-2 text-2xl font-semibold text-slate-100">
            {formatKpi(kpis.error_rate_5m?.value, kpis.error_rate_5m?.unit)}
          </p>
          <span className={`mt-3 inline-flex rounded-full border px-2 py-1 text-xs ${statusTone(kpis.error_rate_5m?.status)}`}>
            {String(kpis.error_rate_5m?.status ?? "unknown")}
          </span>
        </article>
        <article className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Queue depth</p>
          <p className="mt-2 text-2xl font-semibold text-slate-100">
            {formatKpi(kpis.queue_depth?.value, kpis.queue_depth?.unit)}
          </p>
          <span className={`mt-3 inline-flex rounded-full border px-2 py-1 text-xs ${statusTone(kpis.queue_depth?.status)}`}>
            {String(kpis.queue_depth?.status ?? "unknown")}
          </span>
        </article>
        <article className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Active workers</p>
          <p className="mt-2 text-2xl font-semibold text-slate-100">
            {formatKpi(kpis.active_workers?.value, kpis.active_workers?.unit)}
          </p>
          <span className={`mt-3 inline-flex rounded-full border px-2 py-1 text-xs ${statusTone(kpis.active_workers?.status)}`}>
            {String(kpis.active_workers?.status ?? "unknown")}
          </span>
        </article>
      </section>

      <div className="grid gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
        <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-xl shadow-slate-950/60">
          <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-300">Incident Summary</h3>
          <div className="mt-4 space-y-3">
            <div className="rounded-xl border border-slate-800 bg-slate-950/70 px-4 py-3">
              <div className="text-xs uppercase tracking-wide text-slate-500">Open</div>
              <div className="mt-1 text-2xl font-semibold text-slate-100">{incidentsSummary.open}</div>
            </div>
            <div className="rounded-xl border border-rose-400/20 bg-rose-500/5 px-4 py-3">
              <div className="text-xs uppercase tracking-wide text-rose-300/80">Critical</div>
              <div className="mt-1 text-2xl font-semibold text-rose-300">{incidentsSummary.critical}</div>
            </div>
            <div className="rounded-xl border border-amber-300/20 bg-amber-500/5 px-4 py-3">
              <div className="text-xs uppercase tracking-wide text-amber-300/80">Warning</div>
              <div className="mt-1 text-2xl font-semibold text-amber-300">{incidentsSummary.warning}</div>
            </div>
          </div>
        </article>

        <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-xl shadow-slate-950/60">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-300">Service Health</h3>
            <p className="text-xs text-slate-500">Generated at {data.generated_at}</p>
          </div>
          <div className="space-y-3">
            {services.length === 0 ? (
              <p className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-slate-400">
                No services returned.
              </p>
            ) : (
              services.map((service) => (
                <article
                  key={String(service.id ?? service.name ?? "service")}
                  className="rounded-xl border border-slate-800 bg-slate-950/70 p-4"
                >
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
      </div>
    </section>
  );
}
