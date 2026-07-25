'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Icon } from '@/components/ui/icon';
import { getWorkspace } from '@/lib/workspaces';
import { useWorkspace } from './workspace-context';

export function PrimaryNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { workspaceId } = useWorkspace();
  const workspace = getWorkspace(workspaceId);
  return (
    <nav aria-label={`${workspace.shortLabel} primary navigation`}>
      {workspace.primary.map((item) => (
        <Link
          key={`${workspace.id}-${item.href}`}
          href={item.href}
          className={
            pathname === item.href || pathname.startsWith(`${item.href}/`)
              ? 'active'
              : ''
          }
          onClick={onNavigate}
        >
          <Icon name={item.icon} />
          <span>{item.label}</span>
        </Link>
      ))}
    </nav>
  );
}
