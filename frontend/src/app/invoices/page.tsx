import { AppShell } from "@/components/app-shell";
import { InvoicesPageContent } from "@/components/invoices/invoices-page";
import { getInvoices } from "@/lib/invoices";

export default async function InvoicesPage() {
  const invoices = await getInvoices();
  return <AppShell activeSection="Facturas"><InvoicesPageContent invoices={invoices}/></AppShell>;
}
