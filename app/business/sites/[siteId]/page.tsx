import { BusinessPortal } from '@/components/workspaces/business-portal';

export default async function BusinessSitePage({
  params
}: {
  params: Promise<{ siteId: string }>;
}) {
  const { siteId } = await params;
  return <BusinessPortal view="site" siteId={siteId} />;
}
