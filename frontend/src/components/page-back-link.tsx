import Link from "next/link";
import { Icon } from "./icons";

/** Explicit navigation for secondary pages; avoids relying on browser history. */
export function PageBackLink({ href, label = "Volver" }: { href: string; label?: string }) {
  return <Link href={href} aria-label={label} className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-navy transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy"><Icon name="chevronLeft" size={22}/></Link>;
}
