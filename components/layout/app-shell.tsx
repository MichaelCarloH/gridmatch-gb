'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { Icon } from '@/components/ui/icon';

const nav = [
  ['Dashboard', '/dashboard', 'grid'],
  ['GB map', '/map', 'map'],
  ['Sites', '/sites', 'sites'],
  ['Forecast lab', '/forecasts', 'flask'],
  ['Matching', '/matching', 'match'],
  ['Market', '/market', 'market'],
  ['Research', '/research', 'book'],
  ['Reports', '/reports', 'report']
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <div className="app-frame">
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <Link href="/" className="brand" onClick={() => setOpen(false)}>
          <span className="brand-mark"><Icon name="bolt" /></span>
          <span>GridMatch <b>GB</b></span>
        </Link>
        <nav aria-label="Product">
          {nav.map(([label, href, icon]) => (
            <Link
              key={href}
              href={href}
              className={pathname === href || pathname.startsWith(`${href}/`) ? 'active' : ''}
              onClick={() => setOpen(false)}
            >
              <Icon name={icon} /><span>{label}</span>
            </Link>
          ))}
        </nav>
        <div className="sidebar-foot">
          <span className="live-dot" /> Demo artifacts
          <small>UTC storage · London display</small>
        </div>
      </aside>
      <div className="app-body">
        <header className="mobile-bar">
          <Link href="/" className="brand"><span className="brand-mark"><Icon name="bolt" /></span>GridMatch GB</Link>
          <button aria-label="Toggle menu" onClick={() => setOpen(!open)}><Icon name={open ? 'close' : 'menu'} /></button>
        </header>
        {open && <button className="nav-scrim" aria-label="Close menu" onClick={() => setOpen(false)} />}
        <main className="product-main">{children}</main>
      </div>
    </div>
  );
}
