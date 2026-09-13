"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { ROLE_CONFIG } from "@/lib/session";
import { Icon, type IconName } from "./icons";

type Experience = "sme" | "financier";
type NavItem = { label: string; icon: IconName; href: string };

const smePrimary: NavItem[] = [
  { label: "Home", icon: "home", href: "/" }, { label: "Facturas", icon: "invoice", href: "/invoices" },
  { label: "Ofertas", icon: "grid", href: "/publications" }, { label: "Financiamientos", icon: "cube", href: "/financing" },
];
const financierPrimary: NavItem[] = [
  { label: "Inicio", icon: "home", href: "/financier" }, { label: "Marketplace", icon: "search", href: "/marketplace" },
  { label: "Ofertas", icon: "grid", href: "/financier/offers" }, { label: "Portafolio", icon: "briefcase", href: "/portfolio" },
];
const secondary: NavItem[] = [
  { label: "Configuración", icon: "settings", href: "#" }, { label: "Ayuda", icon: "help", href: "#" },
];

function BrandMark() {
  return <span className="relative block h-10 w-10 shrink-0"><Image src="/factora-mark.svg" alt="" fill sizes="40px" className="object-contain" priority/></span>;
}

function NavList({ items, activeSection, collapsed }: { items: NavItem[]; activeSection?: string; collapsed: boolean }) {
  return <nav className="space-y-2.5">{items.map((item) => <a key={item.label} href={item.href} title={collapsed ? item.label : undefined} aria-label={collapsed ? item.label : undefined} className={`flex h-12 items-center overflow-hidden rounded-xl text-[15px] font-medium transition-[background-color,color,padding,gap] duration-[250ms] ease-in-out ${collapsed ? "justify-center gap-0 px-0" : "gap-5 px-4"} ${item.label === activeSection ? "bg-gradient-to-r from-[#efffc3] to-[#f6ffd9] text-navy" : "text-navy hover:bg-slate-50"}`}><Icon name={item.icon} size={22} className="shrink-0"/><span aria-hidden={collapsed} className={`overflow-hidden whitespace-nowrap transition-[max-width,opacity] delay-75 duration-200 ease-in-out ${collapsed ? "max-w-0 opacity-0" : "max-w-[150px] opacity-100"}`}>{item.label}</span></a>)}</nav>;
}

export function AppSidebar({ activeSection = "Ofertas", collapsed, onToggle, experience = "sme" }: { activeSection?: string; collapsed: boolean; onToggle: () => void; experience?: Experience }) {
  const primary = experience === "financier" ? financierPrimary : smePrimary;
  const tagline = experience === "financier" ? "Conecta capital con oportunidades" : "Financiamiento que impulsa.";
  return <aside className={`fixed inset-y-0 left-0 z-20 hidden border-r border-slate-200 bg-white py-6 transition-[width,padding] duration-[250ms] ease-in-out lg:flex lg:flex-col ${collapsed ? "w-20 px-3" : "w-[226px] px-4"}`}>
    <div className={`flex min-h-12 items-center transition-[padding,gap] duration-[250ms] ease-in-out ${collapsed ? "justify-center gap-0 px-0" : "gap-2 px-2"}`}><BrandMark/><div className={`overflow-hidden whitespace-nowrap py-0.5 transition-[max-width,opacity] delay-75 duration-200 ease-in-out ${collapsed ? "max-w-0 opacity-0" : "max-w-[155px] opacity-100"}`}><div className="text-[24px] font-bold leading-6 tracking-[-.04em] text-navy">Factora</div><div className={`mt-1 leading-3 text-navy ${experience === "financier" ? "text-[8px]" : "text-[9px]"}`}>{tagline}</div></div></div>
    <button type="button" onClick={onToggle} aria-label={collapsed ? "Expandir barra lateral" : "Contraer barra lateral"} title={collapsed ? "Expandir" : "Contraer"} className="absolute -right-3 top-[82px] flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 bg-white text-[#52688f] shadow-sm transition hover:bg-slate-50 hover:text-navy focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy"><Icon name={collapsed ? "chevronRight" : "chevronLeft"} size={16}/></button>
    <div className="mt-14"><NavList items={primary} activeSection={activeSection} collapsed={collapsed}/></div>
    <div className="mt-10 border-t border-slate-200 pt-7"><NavList items={secondary} activeSection={activeSection} collapsed={collapsed}/></div>
  </aside>;
}

export function TopBar({ collapsed, experience = "sme" }: { collapsed: boolean; experience?: Experience }) {
  const financier = experience === "financier";
  const role = financier ? "financier" : "sme";
  const profile = ROLE_CONFIG[role];
  const router = useRouter();
  const [profileOpen, setProfileOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  async function logout() {
    setLoggingOut(true);
    await fetch("/api/session", { method: "DELETE" });
    router.replace("/login");
    router.refresh();
  }
  return <header className={`sticky top-0 z-10 flex h-[76px] items-center border-b border-slate-200 bg-white/95 px-5 backdrop-blur transition-[margin-left] duration-[250ms] ease-in-out md:px-7 ${collapsed ? "lg:ml-20" : "lg:ml-[226px]"}`}>
    <div className={`flex h-12 w-full items-center gap-3 rounded-xl bg-[#f1f5f9] px-4 text-[#6b7fa5] ${financier ? "max-w-[720px]" : "max-w-[610px]"}`}><Icon name="search"/><span className="text-sm">{financier ? "Buscar empresa, deudor o número de factura..." : "Buscar facturas, clientes..."}</span></div>
    <div className="ml-auto flex items-center gap-4 pl-5"><button className="relative rounded-full p-2 text-navy transition hover:bg-slate-100" aria-label="Notificaciones"><Icon name="bell"/><span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white"/></button><span className="hidden h-7 w-px bg-slate-200 md:block"/><div className="relative"><button type="button" onClick={() => setProfileOpen((open) => !open)} aria-expanded={profileOpen} aria-haspopup="menu" className="flex items-center gap-3 rounded-xl p-1 text-left hover:bg-slate-50"><div className="flex h-11 w-11 items-center justify-center rounded-full bg-navy text-sm font-medium text-white">{financier ? "FI" : "LM"}</div><div className="hidden min-w-[155px] md:block"><div className="text-sm font-semibold text-navy">{profile.name}</div><div className="mt-1 text-xs text-[#52688f]">{profile.company}</div></div><Icon name="chevron" size={18} className="hidden md:block"/></button>{profileOpen && <div role="menu" className="absolute right-0 top-[58px] w-60 overflow-hidden rounded-xl border border-slate-200 bg-white p-2 shadow-[0_14px_36px_rgba(15,31,68,.14)]"><div className="border-b border-slate-100 px-3 py-2 md:hidden"><strong className="block text-sm text-navy">{profile.name}</strong><span className="text-xs text-[#52688f]">{profile.company}</span></div><Link role="menuitem" href="#" className="block rounded-lg px-3 py-2.5 text-sm text-navy hover:bg-slate-50">Mi cuenta</Link><button role="menuitem" type="button" disabled={loggingOut} onClick={logout} className="w-full rounded-lg px-3 py-2.5 text-left text-sm text-red-600 hover:bg-red-50 disabled:opacity-50">{loggingOut ? "Cerrando sesión..." : "Cerrar sesión"}</button></div>}</div></div>
  </header>;
}

export function AppShell({ children, activeSection = "Ofertas", experience = "sme" }: { children: React.ReactNode; activeSection?: string; experience?: Experience }) {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  const backHref = secondaryPageBackHref(pathname);
  return <div className="min-h-screen bg-[#fbfcfe]"><AppSidebar activeSection={activeSection} collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} experience={experience}/><TopBar collapsed={collapsed} experience={experience}/><main className={`px-5 py-6 transition-[margin-left] duration-[250ms] ease-in-out md:px-7 ${collapsed ? "lg:ml-20" : "lg:ml-[226px]"}`}>{backHref && <Link href={backHref} aria-label="Volver" className="mb-3 inline-flex h-9 w-9 items-center justify-center rounded-lg text-navy transition hover:bg-slate-100"><Icon name="chevronLeft" size={22}/></Link>}{children}</main></div>;
}

function secondaryPageBackHref(pathname: string): string | null {
  if (pathname === "/" || pathname === "/financier" || pathname === "/invoices" || pathname === "/invoices/package" || pathname === "/marketplace" || pathname.startsWith("/marketplace/")) return null;
  if (pathname.startsWith("/publications/")) return "/publications";
  if (pathname === "/publications" || pathname === "/financing" || pathname.startsWith("/offers/")) return "/";
  if (pathname === "/portfolio" || pathname === "/financier/offers") return "/financier";
  return null;
}
