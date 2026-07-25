import Link from 'next/link';
import { Icon } from './icon';

export function ActionCard({
  title,
  description,
  href,
  icon,
  origin
}: {
  title: string;
  description: string;
  href: string;
  icon: string;
  origin?: 'public' | 'simulated' | 'uploaded';
}) {
  return (
    <article className="card action-card">
      <span className="metric-icon"><Icon name={icon} /></span>
      <div>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      <footer>
        {origin && <span className={`badge origin-${origin}`}>{origin}</span>}
        <Link href={href}>Open evidence <Icon name="arrow" /></Link>
      </footer>
    </article>
  );
}
