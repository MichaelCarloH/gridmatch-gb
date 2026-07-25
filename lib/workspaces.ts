export type WorkspaceId =
  | 'business'
  | 'generator'
  | 'operations'
  | 'models'
  | 'research'
  | 'admin';

export type WorkspaceLink = {
  label: string;
  href: string;
  icon: string;
  description?: string;
};

export type Workspace = {
  id: WorkspaceId;
  label: string;
  shortLabel: string;
  href: string;
  icon: string;
  description: string;
  primary: WorkspaceLink[];
  secondary: WorkspaceLink[];
};

export const DEMO_PERIOD_LABEL = 'Forecast window · 17–30 Jun 2025';

export const workspaces: Workspace[] = [
  {
    id: 'business',
    label: 'Business customer',
    shortLabel: 'Business',
    href: '/business',
    icon: 'sites',
    description: 'Demand, renewable coverage and account evidence.',
    primary: [
      { label: 'Workspace home', href: '/business', icon: 'grid' },
      { label: 'Business sites', href: '/business/sites', icon: 'sites' },
      { label: 'Renewable supply', href: '/business/renewables', icon: 'match' },
      { label: 'Energy plan', href: '/business/energy-plan', icon: 'market' }
    ],
    secondary: [
      { label: 'Overview', href: '/business', icon: 'grid' },
      { label: 'Sites', href: '/business/sites', icon: 'sites' },
      { label: 'Renewables', href: '/business/renewables', icon: 'match' },
      { label: 'Energy plan', href: '/business/energy-plan', icon: 'market' },
      { label: 'Reports', href: '/business/reports', icon: 'report' }
    ]
  },
  {
    id: 'generator',
    label: 'Renewable generator',
    shortLabel: 'Generator',
    href: '/generator',
    icon: 'bolt',
    description: 'Asset output, forecast evidence and allocation outcomes.',
    primary: [
      { label: 'Workspace home', href: '/generator', icon: 'grid' },
      { label: 'Output', href: '/generator/output', icon: 'chart' },
      { label: 'Commercial offtake', href: '/generator/offtake', icon: 'match' },
      { label: 'Revenue context', href: '/generator/revenue', icon: 'market' }
    ],
    secondary: [
      { label: 'Overview', href: '/generator', icon: 'grid' },
      { label: 'Output', href: '/generator/output', icon: 'chart' },
      { label: 'Offtake', href: '/generator/offtake', icon: 'match' },
      { label: 'Revenue', href: '/generator/revenue', icon: 'market' },
      { label: 'Assets', href: '/generator/assets', icon: 'sites' },
      { label: 'Report', href: '/generator/reports', icon: 'report' }
    ]
  },
  {
    id: 'operations',
    label: 'Portfolio operations',
    shortLabel: 'Operations',
    href: '/operations',
    icon: 'grid',
    description: 'Portfolio position, matching and market decision support.',
    primary: [
      { label: 'Workspace home', href: '/operations', icon: 'grid' },
      { label: 'Portfolio position', href: '/operations/portfolio', icon: 'chart' },
      { label: 'Matching', href: '/operations/matching', icon: 'match' },
      { label: 'Risk', href: '/operations/risk', icon: 'market' }
    ],
    secondary: [
      { label: 'Control room', href: '/operations', icon: 'grid' },
      { label: 'Portfolio', href: '/operations/portfolio', icon: 'chart' },
      { label: 'Forecasts', href: '/operations/forecasts', icon: 'flask' },
      { label: 'Matching', href: '/operations/matching', icon: 'match' },
      { label: 'Risk', href: '/operations/risk', icon: 'market' },
      { label: 'Scenarios', href: '/operations/scenarios', icon: 'settings' },
      { label: 'Diversification', href: '/operations/diversification', icon: 'chart' },
      { label: 'Stress tests', href: '/operations/stress-tests', icon: 'alert' },
      { label: 'Report', href: '/operations/reports', icon: 'report' }
    ]
  },
  {
    id: 'models',
    label: 'Model operations',
    shortLabel: 'Models',
    href: '/models',
    icon: 'flask',
    description: 'Forecast performance, registry lineage and limitations.',
    primary: [
      { label: 'Workspace home', href: '/models', icon: 'grid' },
      { label: 'Performance', href: '/models/performance', icon: 'chart' },
      { label: 'Calibration', href: '/models/calibration', icon: 'flask' },
      { label: 'Registry', href: '/models/registry', icon: 'book' }
    ],
    secondary: [
      { label: 'Overview', href: '/models', icon: 'grid' },
      { label: 'Performance', href: '/models/performance', icon: 'chart' },
      { label: 'Calibration', href: '/models/calibration', icon: 'flask' },
      { label: 'Registry', href: '/models/registry', icon: 'book' },
      { label: 'Incidents', href: '/models/incidents', icon: 'alert' },
      { label: 'Data drift', href: '/models/data-drift', icon: 'market' }
    ]
  },
  {
    id: 'research',
    label: 'Research',
    shortLabel: 'Research',
    href: '/research',
    icon: 'book',
    description: 'Executed notebooks, model cards and source lineage.',
    primary: [
      { label: 'Research evidence', href: '/research', icon: 'book' },
      { label: 'Forecast evidence', href: '/forecasts', icon: 'flask' },
      { label: 'Reporting', href: '/reports', icon: 'report' }
    ],
    secondary: [
      { label: 'Notebooks & models', href: '/research', icon: 'book' },
      { label: 'Forecast lab', href: '/forecasts', icon: 'flask' },
      { label: 'Reports', href: '/reports', icon: 'report' }
    ]
  },
  {
    id: 'admin',
    label: 'Data administration',
    shortLabel: 'Admin',
    href: '/admin',
    icon: 'report',
    description: 'Artifact readiness, data origins and validation boundaries.',
    primary: [
      { label: 'Workspace home', href: '/admin', icon: 'grid' },
      { label: 'Customers', href: '/admin/customers', icon: 'sites' },
      { label: 'Generators', href: '/admin/generators', icon: 'bolt' },
      { label: 'Data operations', href: '/admin/data', icon: 'report' }
    ],
    secondary: [
      { label: 'Overview', href: '/admin', icon: 'grid' },
      { label: 'Customers', href: '/admin/customers', icon: 'sites' },
      { label: 'Generators', href: '/admin/generators', icon: 'bolt' },
      { label: 'Contracts', href: '/admin/contracts', icon: 'report' },
      { label: 'Data', href: '/admin/data', icon: 'chart' },
      { label: 'Uploads', href: '/admin/data/uploads', icon: 'check' },
      { label: 'Incidents', href: '/admin/data/incidents', icon: 'alert' }
    ]
  }
];

const routeDefaults: Array<[string, WorkspaceId]> = [
  ['/forecasts', 'models'],
  ['/research', 'research'],
  ['/market', 'operations'],
  ['/matching', 'operations'],
  ['/dashboard', 'operations'],
  ['/map', 'generator'],
  ['/sites', 'business'],
  ['/reports', 'business']
];

export function getWorkspace(id: WorkspaceId): Workspace {
  return workspaces.find((workspace) => workspace.id === id) ?? workspaces[2];
}

export function explicitWorkspace(pathname: string): WorkspaceId | null {
  const match = workspaces.find(
    (workspace) =>
      pathname === workspace.href || pathname.startsWith(`${workspace.href}/`)
  );
  return match?.id ?? null;
}

export function defaultWorkspace(pathname: string): WorkspaceId {
  return (
    routeDefaults.find(([prefix]) => pathname.startsWith(prefix))?.[1] ??
    'operations'
  );
}

export function isWorkspaceId(value: string | null): value is WorkspaceId {
  return workspaces.some((workspace) => workspace.id === value);
}
