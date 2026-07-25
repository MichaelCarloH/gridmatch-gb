'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Icon } from '@/components/ui/icon';
import { getWorkspace } from '@/lib/workspaces';
import { useWorkspace } from './workspace-context';

export function SecondaryNav() {
  const pathname = usePathname();
  const { workspaceId } = useWorkspace();
  const workspace = getWorkspace(workspaceId);
  return (
    <nav className="secondary-nav" aria-label={`${workspace.shortLabel} secondary navigation`}>
      <span className="secondary-workspace">{workspace.shortLabel}</span>
      {workspace.secondary.map((item) => (
        <Link
          href={item.href}
          key={`${workspace.id}-${item.href}`}
          className={
            pathname === item.href || pathname.startsWith(`${item.href}/`)
              ? 'active'
              : ''
          }
        >
          <Icon name={item.icon} />
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
