'use client';

import { Icon } from '@/components/ui/icon';
import { workspaces, type WorkspaceId } from '@/lib/workspaces';
import { useWorkspace } from './workspace-context';

export function WorkspaceSwitcher() {
  const { workspaceId, selectWorkspace } = useWorkspace();
  return (
    <label className="workspace-switcher">
      <span>Workspace</span>
      <span className="workspace-select">
        <Icon name={workspaces.find((item) => item.id === workspaceId)?.icon ?? 'grid'} />
        <select
          aria-label="Select workspace"
          value={workspaceId}
          onChange={(event) =>
            selectWorkspace(event.target.value as WorkspaceId)
          }
        >
          {workspaces.map((workspace) => (
            <option value={workspace.id} key={workspace.id}>
              {workspace.label}
            </option>
          ))}
        </select>
      </span>
    </label>
  );
}
