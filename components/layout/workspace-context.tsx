'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from 'react';
import { usePathname, useRouter } from 'next/navigation';
import {
  defaultWorkspace,
  explicitWorkspace,
  getWorkspace,
  isWorkspaceId,
  type WorkspaceId
} from '@/lib/workspaces';

const STORAGE_KEY = 'gridmatch.workspace';

type WorkspaceContextValue = {
  workspaceId: WorkspaceId;
  selectWorkspace: (workspaceId: WorkspaceId) => void;
};

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const explicit = explicitWorkspace(pathname);
  const [workspaceId, setWorkspaceId] = useState<WorkspaceId>(
    explicit ?? defaultWorkspace(pathname)
  );

  useEffect(() => {
    if (explicit) {
      setWorkspaceId(explicit);
      window.localStorage.setItem(STORAGE_KEY, explicit);
      return;
    }
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (isWorkspaceId(stored)) setWorkspaceId(stored);
  }, [explicit, pathname]);

  const selectWorkspace = useCallback(
    (nextWorkspace: WorkspaceId) => {
      setWorkspaceId(nextWorkspace);
      window.localStorage.setItem(STORAGE_KEY, nextWorkspace);
      router.push(getWorkspace(nextWorkspace).href);
    },
    [router]
  );

  const value = useMemo(
    () => ({ workspaceId, selectWorkspace }),
    [workspaceId, selectWorkspace]
  );
  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace(): WorkspaceContextValue {
  const value = useContext(WorkspaceContext);
  if (!value) throw new Error('useWorkspace must be used inside WorkspaceProvider.');
  return value;
}
