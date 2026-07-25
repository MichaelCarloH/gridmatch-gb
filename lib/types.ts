export type Envelope<T> = {
  data: T;
  meta?: {
    count?: number;
    limit?: number;
    offset?: number;
    units?: unknown;
    method?: string | null;
    delivery_mode?: 'api' | 'static';
  };
  warnings?: string[];
};

export type Site = {
  site_id: string;
  name: string;
  site_role: 'demand' | 'generation';
  technology: string;
  business_archetype: string;
  latitude: number;
  longitude: number;
  installed_capacity_mw: number;
  region: string;
  data_origin: 'public' | 'simulated' | 'uploaded';
  quality_score: number;
  site_readiness: string;
  modelled: boolean;
};

export type PortfolioPoint = {
  issue_time_utc: string;
  valid_time_utc: string;
  settlement_period: number;
  method: string;
  actual_demand_mwh: number;
  demand_point_mwh: number;
  demand_q10_mwh: number;
  demand_q50_mwh: number;
  demand_q90_mwh: number;
  actual_generation_mwh: number;
  generation_point_mwh: number;
  generation_q10_mwh: number;
  generation_q50_mwh: number;
  generation_q90_mwh: number;
  actual_net_mwh: number;
  net_point_mwh: number;
  net_q10_mwh: number;
  net_q50_mwh: number;
  net_q90_mwh: number;
};

export type PortfolioMetric = {
  target: string;
  method: string;
  mae: number;
  rmse: number;
  bias: number;
  interval_coverage: number | null;
  interval_width?: number | null;
  nmae?: number;
  peak_error?: number;
  pinball_loss?: number | null;
  evaluation_rows?: number;
  simulated_hedge_cost_gbp: number;
};

export type MatchingPeriod = {
  timestamp_utc: string;
  settlement_period: number;
  allocation_type: string;
  matching_mode: string;
  total_demand_mwh: number;
  total_generation_mwh: number;
  matched_mwh: number;
  residual_grid_demand_mwh: number;
  unused_generation_mwh: number;
  renewable_match_rate: number;
};

export type GeoFeature = {
  type: 'Feature';
  geometry: { type: 'Point'; coordinates: [number, number] };
  properties: Site;
};

export type GeoCollection = {
  type: 'FeatureCollection';
  features: GeoFeature[];
  bbox?: [number, number, number, number];
};

export type Notebook = {
  name: string;
  status: string;
  summary: string;
  key_result: string;
  execution_timestamp: string;
  duration_seconds: number;
  artifact_links: string[];
};

export type ModelRecord = {
  model_id: string;
  site_id: string | null;
  scope: string;
  target: string;
  algorithm: string;
  quantile: number | null;
  status: string;
  mae: number | null;
  coverage: number | null;
  intended_use: string;
  limitations: string;
};

export type Dictionary = Record<string, any>;

export type HealthStatus = {
  status: 'healthy' | 'degraded';
  application_version: string;
  artifact_availability: Record<string, boolean>;
  model_registry_available: boolean;
  demo_mode: boolean;
  last_artifact_update: string | null;
};
