import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import octopalLogo from "../assets/octopal-logo.png";
import { GlobalFiltersBar } from "./GlobalFiltersBar";
import type { DashboardFilters } from "./GlobalFiltersBar";

const filtersStorageKey = "octopal.webapp.filters";
const tokenStorageKey = "octopal.webapp.token";

const defaultFilters: DashboardFilters = {
  windowMinutes: 60,
  service: "all",
  environment: "all",
  token: "",
};

export type AppShellOutletContext = {
  filters: DashboardFilters;
  setFilters: (next: DashboardFilters) => void;
};

type NavItem = {
  to: string;
  label: string;
  description: string;
};

const navGroups: { title: string; items: NavItem[] }[] = [
  {
    title: "Operations",
    items: [
      { to: "/", label: "Control", description: "Live operating surface" },
      { to: "/overview", label: "Overview", description: "Health, KPIs, incidents" },
      { to: "/octo", label: "Octo", description: "Runtime state and coordination" },
      { to: "/incidents", label: "Incidents", description: "Open signals and pressure" },
    ],
  },
  {
    title: "Workspace",
    items: [
      { to: "/workers", label: "Workers", description: "Templates and worker setup" },
      { to: "/system", label: "System", description: "Host, queues, and stability" },
      { to: "/actions", label: "Actions", description: "Operator actions and controls" },
    ],
  },
];

const pageMeta = new Map<string, { title: string; description: string }>(
  navGroups.flatMap((group) => group.items.map((item) => [item.to, { title: item.label, description: item.description }])),
);

function getPageMeta(pathname: string): { title: string; description: string } {
  if (pathname === "/") {
    return pageMeta.get("/") ?? { title: "Control", description: "Live operating surface" };
  }

  const match = Array.from(pageMeta.entries()).find(([to]) => to !== "/" && pathname.startsWith(to));
  return match?.[1] ?? { title: "Dashboard", description: "Operator workspace" };
}

export function AppShell() {
  const location = useLocation();
  const [filters, setFilters] = useState<DashboardFilters>(() => {
    const raw = localStorage.getItem(filtersStorageKey);
    const token = sessionStorage.getItem(tokenStorageKey) ?? "";
    if (!raw) {
      return { ...defaultFilters, token };
    }
    try {
      const parsed = JSON.parse(raw) as Partial<DashboardFilters>;
      return {
        windowMinutes:
          parsed.windowMinutes === 15 ||
          parsed.windowMinutes === 60 ||
          parsed.windowMinutes === 240 ||
          parsed.windowMinutes === 1440
            ? parsed.windowMinutes
            : 60,
        service: parsed.service ?? "all",
        environment: parsed.environment ?? "all",
        token,
      };
    } catch (_error) {
      return { ...defaultFilters, token };
    }
  });

  useEffect(() => {
    localStorage.setItem(
      filtersStorageKey,
      JSON.stringify({
        windowMinutes: filters.windowMinutes,
        service: filters.service,
        environment: filters.environment,
      }),
    );
    if (filters.token) {
      sessionStorage.setItem(tokenStorageKey, filters.token);
    } else {
      sessionStorage.removeItem(tokenStorageKey);
    }
  }, [filters]);

  const currentPage = getPageMeta(location.pathname);

  return (
    <div className="min-h-screen bg-[var(--app-bg)] text-[var(--text-strong)]">
      <div className="grid min-h-screen lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="border-b border-[var(--border-soft)] bg-[var(--sidebar-bg)] lg:border-b-0 lg:border-r">
          <div className="flex h-full flex-col px-4 py-4 lg:px-5 lg:py-6">
            <div className="flex items-center gap-3 border-b border-[var(--border-soft)] pb-4">
              <div className="flex h-11 w-11 items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-white/5">
                <img src={octopalLogo} alt="Octopal" className="h-8 w-8 object-contain" />
              </div>
              <div className="min-w-0">
                <p className="text-[11px] uppercase tracking-[0.24em] text-[var(--text-muted)]">Octopal</p>
                <h1 className="truncate text-lg font-semibold text-white">Agent Control</h1>
              </div>
            </div>

            <div className="mt-6 space-y-6">
              {navGroups.map((group) => (
                <section key={group.title}>
                  <p className="mb-2 px-2 text-[11px] uppercase tracking-[0.22em] text-[var(--text-dim)]">
                    {group.title}
                  </p>
                  <nav className="space-y-1.5">
                    {group.items.map((item) => (
                      <NavLink
                        key={item.to}
                        to={item.to}
                        end={item.to === "/"}
                        className={({ isActive }) =>
                          [
                            "group block rounded-2xl px-3 py-3 transition",
                            isActive
                              ? "bg-[var(--nav-active)] text-white shadow-[inset_0_0_0_1px_rgba(255,255,255,0.06)]"
                              : "text-[var(--text-muted)] hover:bg-white/[0.03] hover:text-[var(--text-strong)]",
                          ].join(" ")
                        }
                      >
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-sm font-medium">{item.label}</span>
                          <span className="h-2 w-2 rounded-full bg-current opacity-25 transition group-hover:opacity-40" />
                        </div>
                        <p className="mt-1 text-xs text-[var(--text-dim)]">{item.description}</p>
                      </NavLink>
                    ))}
                  </nav>
                </section>
              ))}
            </div>

            <div className="mt-6 rounded-3xl border border-white/6 bg-white/[0.03] p-4">
              <p className="text-[11px] uppercase tracking-[0.22em] text-[var(--text-dim)]">Live mode</p>
              <p className="mt-2 text-sm text-[var(--text-strong)]">Data refreshes continuously across the dashboard.</p>
              <div className="mt-3 flex items-center gap-2 text-xs text-[var(--text-muted)]">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                Poll every 15s plus stream updates when available
              </div>
            </div>

            <div className="mt-auto hidden border-t border-[var(--border-soft)] pt-4 text-xs text-[var(--text-dim)] lg:block">
              Built for operator-first monitoring.
            </div>
          </div>
        </aside>

        <div className="min-w-0">
          <header className="border-b border-[var(--border-soft)] bg-[var(--surface-top)]/92 backdrop-blur">
            <div className="px-4 py-5 md:px-6 lg:px-8">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.24em] text-[var(--text-dim)]">Operations Dashboard</p>
                  <h2 className="mt-2 text-3xl font-semibold tracking-[-0.03em] text-white">{currentPage.title}</h2>
                  <p className="mt-2 max-w-3xl text-sm text-[var(--text-muted)]">{currentPage.description}</p>
                </div>
                <div className="rounded-full border border-white/8 bg-white/[0.04] px-4 py-2 text-sm text-[var(--text-muted)]">
                  {filters.environment === "all" ? "All environments" : filters.environment}
                </div>
              </div>
              <div className="mt-5">
                <GlobalFiltersBar filters={filters} onChange={setFilters} />
              </div>
            </div>
          </header>

          <main className="px-4 py-5 md:px-6 lg:px-8 lg:py-8">
            <Outlet context={{ filters, setFilters }} />
          </main>
        </div>
      </div>
    </div>
  );
}
