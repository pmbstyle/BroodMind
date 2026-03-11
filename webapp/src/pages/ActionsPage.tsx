import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useOutletContext } from "react-router-dom";

import { fetchActions, runDashboardAction } from "../api/dashboardClient";
import type { components } from "../api/types";
import type { AppShellOutletContext } from "../ui/AppShell";
import { formatLocalDateTime } from "../utils/dateTime";

type ActionsPayload = components["schemas"]["DashboardActionsV2"];
type ActionHistoryItem = {
  timestamp?: string;
  action?: string;
  requested_by?: string;
  worker_id?: string;
  result?: { status?: string; message?: string };
};

function statusTone(value?: string): string {
  const v = String(value ?? "").toLowerCase();
  if (v === "ok") {
    return "border-emerald-400/30 bg-emerald-500/10 text-emerald-300";
  }
  if (v === "warning") {
    return "border-amber-300/30 bg-amber-500/10 text-amber-300";
  }
  return "border-rose-300/30 bg-rose-500/10 text-rose-300";
}

export function ActionsPage() {
  const { filters } = useOutletContext<AppShellOutletContext>();
  const [data, setData] = useState<ActionsPayload | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [workerId, setWorkerId] = useState<string>("");
  const [resultMessage, setResultMessage] = useState<string>("No actions yet.");

  const loadActions = () => {
    setLoading(true);
    setError("");
    void fetchActions({
      windowMinutes: filters.windowMinutes,
      service: filters.service,
      environment: filters.environment,
      token: filters.token || undefined,
    })
      .then((payload) => {
        setData(payload);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Unknown request error");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    loadActions();
  }, [filters.environment, filters.service, filters.token, filters.windowMinutes]);

  const runAction = async (action: "restart_worker" | "retry_failed" | "clear_control_queue") => {
    try {
      setResultMessage("Running action...");
      const payload =
        action === "restart_worker"
          ? { action, worker_id: workerId.trim(), confirm: true }
          : action === "clear_control_queue"
            ? { action, confirm: true }
            : { action };
      const response = await runDashboardAction(payload, filters.token || undefined);
      setResultMessage(String(response.message ?? response.status ?? "Action completed."));
      loadActions();
    } catch (err: unknown) {
      setResultMessage(err instanceof Error ? err.message : "Action failed.");
    }
  };

  const onRestartSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!workerId.trim()) {
      setResultMessage("Enter worker ID before restart.");
      return;
    }
    void runAction("restart_worker");
  };

  const actionsNode = (data?.actions ?? {}) as { history?: ActionHistoryItem[] };
  const history = actionsNode.history ?? [];

  return (
    <section className="grid gap-5">
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl shadow-slate-950/60">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Actions</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-100">Operational Controls</h2>
            <p className="mt-2 text-sm text-slate-400">
              Manual controls for worker recovery and queue cleanup, with audit history below.
            </p>
          </div>
          <div className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${error ? statusTone("error") : statusTone("ok")}`}>
            {error ? "load error" : "ready"}
          </div>
        </div>
      </section>

      <div className="grid gap-5 xl:grid-cols-[minmax(320px,420px)_minmax(0,1fr)]">
        <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-xl shadow-slate-950/60">
          <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-300">Run Action</h3>
          <form onSubmit={onRestartSubmit} className="mt-4 space-y-3">
            <label className="block text-xs uppercase tracking-wide text-slate-500">
              Worker ID
              <input
                value={workerId}
                onChange={(event) => setWorkerId(event.target.value)}
                placeholder="Worker ID"
                aria-label="Worker ID"
                className="mt-2 w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-cyan-400/50"
              />
            </label>
            <button
              type="submit"
              className="w-full rounded-xl border border-cyan-400/40 bg-cyan-400/10 px-3 py-2 text-sm font-semibold text-cyan-200 transition hover:border-cyan-300/60 hover:bg-cyan-400/15"
            >
              Restart Worker
            </button>
          </form>

          <div className="mt-3 grid gap-3">
            <button
              type="button"
              className="rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-sm font-medium text-slate-200 transition hover:border-slate-700"
              onClick={() => void runAction("retry_failed")}
            >
              Retry Latest Failed Worker
            </button>
            <button
              type="button"
              className="rounded-xl border border-slate-800 bg-slate-950/80 px-3 py-2 text-sm font-medium text-slate-200 transition hover:border-slate-700"
              onClick={() => void runAction("clear_control_queue")}
            >
              Clear Control Queue
            </button>
          </div>

          <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/70 p-4">
            <div className="text-xs uppercase tracking-wide text-slate-500">Result</div>
            <p className="mt-2 text-sm text-slate-300">{resultMessage}</p>
            {error ? <p className="mt-2 text-sm text-rose-300">Load error: {error}</p> : null}
          </div>
        </article>

        <article className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-xl shadow-slate-950/60">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-300">Action History</h3>
            <p className="text-xs text-slate-500">Latest backend audit entries</p>
          </div>
          {loading ? (
            <p className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-slate-400">Loading history...</p>
          ) : history.length === 0 ? (
            <p className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-slate-400">No action history.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="border-b border-slate-800 px-3 py-2">Time</th>
                    <th className="border-b border-slate-800 px-3 py-2">Action</th>
                    <th className="border-b border-slate-800 px-3 py-2">Requester</th>
                    <th className="border-b border-slate-800 px-3 py-2">Status</th>
                    <th className="border-b border-slate-800 px-3 py-2">Message</th>
                  </tr>
                </thead>
                <tbody>
                  {history.slice(0, 12).map((item, index) => (
                    <tr key={`${item.timestamp ?? "n/a"}-${index}`} className="border-b border-slate-900">
                      <td className="px-3 py-3 text-slate-400">{formatLocalDateTime(item.timestamp)}</td>
                      <td className="px-3 py-3 text-slate-200">
                        {item.action ?? "action"}
                        {item.worker_id ? ` (${item.worker_id})` : ""}
                      </td>
                      <td className="px-3 py-3 text-slate-300">{item.requested_by ?? "dashboard"}</td>
                      <td className="px-3 py-3">
                        <span className={`rounded-full border px-2 py-1 text-xs uppercase tracking-wide ${statusTone(item.result?.status)}`}>
                          {String(item.result?.status ?? "unknown")}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-slate-300">{item.result?.message ?? "n/a"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
