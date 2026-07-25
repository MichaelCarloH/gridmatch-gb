'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Icon } from '@/components/ui/icon';
import { ArtifactStatus } from '@/components/ui/artifact-status';
import { DataOriginBadge } from '@/components/ui/badges';
import { DEMO_PERIOD_LABEL } from '@/lib/workspaces';
import { Breadcrumbs } from './breadcrumbs';
import { PrimaryNav } from './primary-nav';
import { SecondaryNav } from './secondary-nav';
import { WorkspaceProvider } from './workspace-context';
import { WorkspaceSwitcher } from './workspace-switcher';

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <WorkspaceProvider>
      <AppShellFrame>{children}</AppShellFrame>
    </WorkspaceProvider>
  );
}

function AppShellFrame({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="app-frame">
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <Link href="/" className="brand" onClick={() => setOpen(false)}>
          <span className="brand-mark"><Icon name="bolt" /></span>
          <span>GridMatch <b>GB</b></span>
        </Link>
        <WorkspaceSwitcher />
        <PrimaryNav onNavigate={() => setOpen(false)} />
        <div className="sidebar-foot">
          <ArtifactStatus />
          <small>UTC storage · Europe/London display</small>
        </div>
      </aside>
      <div className="app-body">
        <header className="mobile-bar">
          <Link href="/" className="brand">
            <span className="brand-mark"><Icon name="bolt" /></span>
            GridMatch GB
          </Link>
          <button aria-label="Toggle menu" onClick={() => setOpen(!open)}>
            <Icon name={open ? 'close' : 'menu'} />
          </button>
        </header>
        {open && (
          <button
            className="nav-scrim"
            aria-label="Close menu"
            onClick={() => setOpen(false)}
          />
        )}
        <div className="shell-toolbar">
          <Breadcrumbs />
          <span className="badge demo-period-badge">{DEMO_PERIOD_LABEL}</span>
        </div>
        <SecondaryNav />
        <main className="product-main">{children}</main>
        <footer className="data-disclosure">
          <div>
            <strong>Demonstration data boundary</strong>
            <span>
              Public REPD and market references; deterministic simulated
              portfolio, forecasts, matching and hedge scenarios; uploaded
              files are validated in memory only.
            </span>
          </div>
          <div className="disclosure-badges">
            <DataOriginBadge origin="public" />
            <DataOriginBadge origin="simulated" />
            <DataOriginBadge origin="uploaded" />
          </div>
        </footer>
      </div>
    </div>
  );
}
