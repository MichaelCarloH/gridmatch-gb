import { GeneratorPortal } from '@/components/workspaces/generator-portal';

export default async function GeneratorSitePage({
  params
}: {
  params: Promise<{ siteId: string }>;
}) {
  const { siteId } = await params;
  return <GeneratorPortal view="site" siteId={siteId} />;
}
