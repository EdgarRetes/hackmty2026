import { AppShell } from "@/components/app-shell";
import { PublicationPageContent } from "@/components/publications/publication-page";
import { getPublicationPageData } from "@/lib/publications";
import { notFound } from "next/navigation";

export default async function PublicationPage({ params }: { params: Promise<{ batchId: string }> }) {
  const { batchId } = await params;
  const data = await getPublicationPageData(decodeURIComponent(batchId));
  if (!data) notFound();
  return <AppShell activeSection="Facturas"><PublicationPageContent data={data}/></AppShell>;
}
