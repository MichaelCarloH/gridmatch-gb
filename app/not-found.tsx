import Link from 'next/link';
import { EmptyState } from '@/components/ui/states';

export default function NotFound() {
  return (
    <div className="not-found-page">
      <EmptyState message="This route is not part of the current extension phase." />
      <Link className="button green" href="/operations">
        Return to operations
      </Link>
    </div>
  );
}
