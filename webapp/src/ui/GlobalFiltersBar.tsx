import { useEffect, useState } from "react";
import type { ChangeEvent } from "react";

export type DashboardFilters = {
  windowMinutes: 15 | 60 | 240 | 1440;
  service: "all" | "gateway" | "octo" | "telegram" | "exec_run" | "mcp" | "workers";
  environment: "all" | "local" | "dev" | "staging" | "prod";
  token: string;
};

type GlobalFiltersBarProps = {
  filters: DashboardFilters;
  onChange: (next: DashboardFilters) => void;
};

const fieldClassName =
  "w-full rounded-2xl border border-white/8 bg-[var(--field-bg)] px-3 py-2.5 text-sm text-[var(--text-strong)] outline-none transition placeholder:text-[var(--text-dim)] focus:border-white/18 focus:bg-white/[0.08]";

export function GlobalFiltersBar({ filters, onChange }: GlobalFiltersBarProps) {
  const [draftToken, setDraftToken] = useState<string>(filters.token);

  useEffect(() => {
    setDraftToken(filters.token);
  }, [filters.token]);

  const onSelectWindow = (event: ChangeEvent<HTMLSelectElement>) => {
    onChange({ ...filters, windowMinutes: Number(event.target.value) as DashboardFilters["windowMinutes"] });
  };

  return (
    <section
      className="rounded-[28px] border border-white/6 bg-[var(--surface-panel)] px-4 py-4 shadow-[0_24px_80px_rgba(0,0,0,0.28)]"
      aria-label="Global filters"
    >
      <div className="grid gap-3 xl:grid-cols-[140px_180px_180px_minmax(260px,1fr)_auto]">
        <label className="grid gap-1.5 text-[11px] uppercase tracking-[0.18em] text-[var(--text-dim)]">
          Window
          <select value={filters.windowMinutes} onChange={onSelectWindow} className={fieldClassName}>
            <option value={15}>15m</option>
            <option value={60}>1h</option>
            <option value={240}>4h</option>
            <option value={1440}>24h</option>
          </select>
        </label>

        <label className="grid gap-1.5 text-[11px] uppercase tracking-[0.18em] text-[var(--text-dim)]">
          Service
          <select
            value={filters.service}
            onChange={(event) =>
              onChange({ ...filters, service: event.target.value as DashboardFilters["service"] })
            }
            className={fieldClassName}
          >
            <option value="all">All services</option>
            <option value="gateway">Gateway</option>
            <option value="octo">Octo</option>
            <option value="telegram">Telegram</option>
            <option value="exec_run">Exec run</option>
            <option value="mcp">MCP</option>
            <option value="workers">Workers</option>
          </select>
        </label>

        <label className="grid gap-1.5 text-[11px] uppercase tracking-[0.18em] text-[var(--text-dim)]">
          Environment
          <select
            value={filters.environment}
            onChange={(event) =>
              onChange({ ...filters, environment: event.target.value as DashboardFilters["environment"] })
            }
            className={fieldClassName}
          >
            <option value="all">All environments</option>
            <option value="local">Local</option>
            <option value="dev">Dev</option>
            <option value="staging">Staging</option>
            <option value="prod">Prod</option>
          </select>
        </label>

        <label className="grid gap-1.5 text-[11px] uppercase tracking-[0.18em] text-[var(--text-dim)]">
          Dashboard token
          <input
            value={draftToken}
            onChange={(event) => setDraftToken(event.target.value)}
            type="password"
            placeholder="Optional access token"
            className={fieldClassName}
          />
        </label>

        <div className="flex items-end gap-2">
          <button
            type="button"
            className="rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--text-strong)] transition hover:bg-white/[0.1]"
            onClick={() => onChange({ ...filters, token: draftToken.trim() })}
          >
            Apply
          </button>
          <button
            type="button"
            className="rounded-2xl border border-white/8 bg-transparent px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--text-muted)] transition hover:border-white/14 hover:text-[var(--text-strong)]"
            onClick={() => {
              setDraftToken("");
              onChange({ ...filters, token: "" });
            }}
          >
            Clear
          </button>
        </div>
      </div>
    </section>
  );
}
