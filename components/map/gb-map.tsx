'use client';

import type { Dictionary, GeoFeature } from '@/lib/types';

// Natural Earth 1:110m public-domain geometry, United Kingdom feature.
// The largest island polygon is Great Britain; Northern Ireland is excluded.
// https://www.naturalearthdata.com/downloads/110m-cultural-vectors/
const gbPolygons: Array<Array<[number, number]>> = [
  [
    [-3.093831, 53.404547], [-3.09208, 53.404441],
    [-2.945009, 53.985], [-3.614701, 54.600937],
    [-3.630005, 54.615013], [-4.844169, 54.790971],
    [-5.082527, 55.061601], [-4.719112, 55.508473],
    [-5.047981, 55.783986], [-5.586398, 55.311146],
    [-5.644999, 56.275015], [-6.149981, 56.78501],
    [-5.786825, 57.818848], [-5.009999, 58.630013],
    [-4.211495, 58.550845], [-3.005005, 58.635],
    [-4.073828, 57.553025], [-3.055002, 57.690019],
    [-1.959281, 57.6848], [-2.219988, 56.870017],
    [-3.119003, 55.973793], [-2.085009, 55.909998],
    [-2.005676, 55.804903], [-1.114991, 54.624986],
    [-0.430485, 54.464376], [0.184981, 53.325014],
    [0.469977, 52.929999], [1.681531, 52.73952],
    [1.559988, 52.099998], [1.050562, 51.806761],
    [1.449865, 51.289428], [0.550334, 50.765739],
    [-0.787517, 50.774989], [-2.489998, 50.500019],
    [-2.956274, 50.69688], [-3.617448, 50.228356],
    [-4.542508, 50.341837], [-5.245023, 49.96],
    [-5.776567, 50.159678], [-4.30999, 51.210001],
    [-3.414851, 51.426009], [-3.422719, 51.426848],
    [-4.984367, 51.593466], [-5.267296, 51.9914],
    [-4.222347, 52.301356], [-4.770013, 52.840005],
    [-4.579999, 53.495004], [-3.093831, 53.404547]
  ],
  // Anglesey
  [
    [-4.196777, 53.321436], [-4.049365, 53.305762],
    [-4.084277, 53.264307], [-4.373047, 53.13418],
    [-4.553223, 53.260449], [-4.567871, 53.386475],
    [-4.315088, 53.417236], [-4.196777, 53.321436]
  ],
  // Isle of Wight
  [
    [-1.065576, 50.690234], [-1.17583, 50.615234],
    [-1.306299, 50.588525], [-1.563428, 50.666113],
    [-1.38584, 50.733545], [-1.144238, 50.734717],
    [-1.065576, 50.690234]
  ],
  // Orkney
  [
    [-3.30, 58.84], [-3.16, 58.79], [-2.94, 58.74],
    [-2.76, 58.96], [-2.86, 59.25], [-3.24, 59.14],
    [-3.35, 59.02], [-3.30, 58.84]
  ],
  // Shetland
  [
    [-1.35, 59.91], [-1.15, 60.18], [-1.05, 60.44],
    [-0.91, 60.69], [-0.77, 60.81], [-0.89, 60.82],
    [-1.09, 60.72], [-1.42, 60.60], [-1.55, 60.48],
    [-1.35, 59.91]
  ],
  // Outer Hebrides
  [
    [-7.42, 56.97], [-7.25, 57.12], [-7.41, 57.38],
    [-7.20, 57.68], [-7.08, 57.81], [-6.96, 58.18],
    [-6.54, 58.38], [-6.20, 58.36], [-6.40, 58.04],
    [-6.14, 57.50], [-6.32, 57.20], [-6.43, 57.02],
    [-7.42, 56.97]
  ]
];

export function GBMap({
  features,
  arcs = [],
  selected,
  onSelect
}: {
  features: GeoFeature[];
  arcs?: Dictionary[];
  selected?: string | null;
  onSelect?: (siteId: string) => void;
}) {
  const project = ([lon, lat]: [number, number]) => ({
    x: 50 + ((lon + 8.8) / 11.2) * 380,
    y: 35 + ((61 - lat) / 11.5) * 540
  });
  const coastlinePaths = gbPolygons.map((polygon) =>
    `${polygon.map((coordinate, index) => {
      const point = project(coordinate);
      return `${index === 0 ? 'M' : 'L'}${point.x.toFixed(2)} ${point.y.toFixed(2)}`;
    }).join(' ')} Z`
  );
  return (
    <div className="gb-map">
      <svg viewBox="0 0 480 620" role="img" aria-label="Map of modelled Great Britain energy sites">
        <defs>
          <clipPath id="gb-land">
            {coastlinePaths.map((path, index) => <path d={path} key={index} />)}
          </clipPath>
        </defs>
        {coastlinePaths.map((path, index) => <path className="gb-shape" d={path} key={index} />)}
        <g clipPath="url(#gb-land)">
          <path className="map-grid" d="M40 130H440M40 250H440M40 370H440M40 490H440M140 20V600M240 20V600M340 20V600" />
        </g>
        {arcs.map((arc, index) => {
          const start = project([Number(arc.start_longitude), Number(arc.start_latitude)]);
          const end = project([Number(arc.end_longitude), Number(arc.end_latitude)]);
          return <line key={`${arc.generator_site_id}-${arc.consumer_site_id}-${index}`} x1={start.x} y1={start.y} x2={end.x} y2={end.y} className="matching-arc"><title>{Number(arc.matched_mwh).toFixed(3)} MWh commercial allocation</title></line>;
        })}
        {features.map((feature) => {
          const point = project(feature.geometry.coordinates);
          const generation = feature.properties.site_role === 'generation';
          return (
            <g key={feature.properties.site_id} className="map-point" onClick={() => onSelect?.(feature.properties.site_id)}>
              <circle cx={point.x} cy={point.y} r={selected === feature.properties.site_id ? 9 : feature.properties.modelled ? 6 : 2.1} className={`${generation ? 'generation' : 'demand'} ${feature.properties.modelled ? '' : 'public-site'}`} />
              <title>{feature.properties.name} · {feature.properties.installed_capacity_mw} MW</title>
            </g>
          );
        })}
      </svg>
      <div className="map-key"><span><i className="demand-dot" />Demand</span><span><i className="generation-dot" />Generation</span><span><i className="public-dot" />Public REPD</span><span><i className="arc-line" />Matched</span></div>
    </div>
  );
}
