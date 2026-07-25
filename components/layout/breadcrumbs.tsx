'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { getWorkspace } from '@/lib/workspaces';
import { titleCase } from '@/lib/format';
import { useWorkspace } from './workspace-context';

export function Breadcrumbs() {
  const pathname = usePathname();
  const { workspaceId } = useWorkspace();
  const workspace = getWorkspace(workspaceId);
  const segments = pathname.split('/').filter(Boolean);
  const finalLabel =
    segments.length && segments[0] !== workspace.id
      ? titleCase(segments.at(-1) ?? '')
      : null;
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      <Link href="/">GridMatch GB</Link>
      <span aria-hidden="true">/</span>
      <Link href={workspace.href}>{workspace.shortLabel}</Link>
      {finalLabel && (
        <>
          <span aria-hidden="true">/</span>
          <span aria-current="page">{finalLabel}</span>
        </>
      )}
    </nav>
  );
}
