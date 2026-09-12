import { AppShell } from "@/components/app-shell";
import { PublicationsListContent } from "@/components/publications/publications-list";
import { getPublications } from "@/lib/publications";

export default async function PublicationsPage() {
  const publications = await getPublications();
  return <AppShell activeSection="Facturas"><PublicationsListContent publications={publications}/></AppShell>;
}
