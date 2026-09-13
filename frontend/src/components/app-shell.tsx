"use client";

import { useEffect, useState } from "react";
import { getProfiles, type Profile, type Role } from "@/lib/profile";
import { Icon, type IconName } from "./icons";

const primary: { label: string; icon: IconName; href: string; roles: Role[] }[] = [
  { label: "Home", icon: "home", href: "/", roles: ["empresa"] },
  { label: "Facturas", icon: "invoice", href: "/invoices", roles: ["empresa"] },
  { label: "Ofertas", icon: "grid", href: "/publications", roles: ["empresa"] },
  { label: "Transacciones", icon: "transfer", href: "#", roles: ["empresa"] },
  { label: "Financiamientos", icon: "cube", href: "/financing", roles: ["financiadora"] },
];
const secondary: { label: string; icon: IconName; href: string }[] = [
  { label: "Configuración", icon: "settings", href: "#" }, { label: "Ayuda", icon: "help", href: "#" },
];

const ROLE_STORAGE_KEY = "factora-role";

function useActiveRole() {
  const [role, setRoleState] = useState<Role>("empresa");

  useEffect(() => {
    // localStorage doesn't exist during SSR, so the stored role can only
    // be read post-mount — this is syncing with that external system, not
    // deriving state, hence the lint exception below.
    try {
      const stored = localStorage.getItem(ROLE_STORAGE_KEY);
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (stored === "empresa" || stored === "financiadora") setRoleState(stored);
    } catch {
      // Private browsing / storage disabled — default role is fine.
    }
  }, []);

  function setRole(next: Role) {
    setRoleState(next);
    try {
      localStorage.setItem(ROLE_STORAGE_KEY, next);
    } catch {
      // Nothing to persist to, but the in-memory switch still works.
    }
  }

  return [role, setRole] as const;
}

function useProfiles() {
  const [profiles, setProfiles] = useState<Profile[]>([]);

  useEffect(() => {
    getProfiles()
      .then(setProfiles)
      .catch(() => setProfiles([]));
  }, []);

  return profiles;
}

function BrandMark() {
  return <span className="relative block h-9 w-9 shrink-0"><i className="absolute left-0 top-2 h-5 w-5 rounded-full bg-[#d6f36b]"/><i className="absolute left-3 top-0 h-5 w-5 rounded-full bg-navy"/><i className="absolute bottom-0 left-3 h-5 w-5 rounded-full bg-[#b9e93e]/80"/></span>;
}

type NavItem = { label: string; icon: IconName; href: string };

function NavList({ items, activeSection, collapsed }: { items: NavItem[]; activeSection?: string; collapsed: boolean }) {
  return <nav className="space-y-2.5">{items.map((item) => <a key={item.label} href={item.href} title={collapsed ? item.label : undefined} aria-label={collapsed ? item.label : undefined} className={`flex h-12 items-center overflow-hidden rounded-xl text-[15px] font-medium transition-[background-color,color,padding,gap] duration-[250ms] ease-in-out ${collapsed ? "justify-center gap-0 px-0" : "gap-5 px-4"} ${item.label === activeSection ? "bg-gradient-to-r from-[#efffc3] to-[#f6ffd9] text-navy" : "text-navy hover:bg-slate-50"}`}><Icon name={item.icon} size={22} className="shrink-0"/><span aria-hidden={collapsed} className={`overflow-hidden whitespace-nowrap transition-[max-width,opacity] delay-75 duration-200 ease-in-out ${collapsed ? "max-w-0 opacity-0" : "max-w-[150px] opacity-100"}`}>{item.label}</span></a>)}</nav>;
}

export function AppSidebar({ activeSection = "Ofertas", collapsed, onToggle, role }: { activeSection?: string; collapsed: boolean; onToggle: () => void; role: Role }) {
  const visiblePrimary = primary.filter((item) => item.roles.includes(role));
  return <aside className={`fixed inset-y-0 left-0 z-20 hidden border-r border-slate-200 bg-white py-6 transition-[width,padding] duration-[250ms] ease-in-out lg:flex lg:flex-col ${collapsed ? "w-20 px-3" : "w-[226px] px-4"}`}>
    <div className={`flex min-h-12 items-center transition-[padding,gap] duration-[250ms] ease-in-out ${collapsed ? "justify-center gap-0 px-0" : "gap-2 px-2"}`}><BrandMark/><div className={`overflow-hidden whitespace-nowrap py-0.5 transition-[max-width,opacity] delay-75 duration-200 ease-in-out ${collapsed ? "max-w-0 opacity-0" : "max-w-[155px] opacity-100"}`}><div className="text-[24px] font-bold leading-6 tracking-[-.04em] text-navy">Factora</div><div className="mt-1 text-[9px] leading-3 text-navy">Financiamiento que impulsa.</div></div></div>
    <button type="button" onClick={onToggle} aria-label={collapsed ? "Expandir barra lateral" : "Contraer barra lateral"} title={collapsed ? "Expandir" : "Contraer"} className="absolute -right-3 top-[82px] flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 bg-white text-[#52688f] shadow-sm transition hover:bg-slate-50 hover:text-navy focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy"><Icon name={collapsed ? "chevronRight" : "chevronLeft"} size={16}/></button>
    <div className="mt-14"><NavList items={visiblePrimary} activeSection={activeSection} collapsed={collapsed}/></div>
    <div className="mt-10 border-t border-slate-200 pt-7"><NavList items={secondary} activeSection={activeSection} collapsed={collapsed}/></div>
    <div aria-hidden="true" className={`relative mt-auto overflow-hidden bg-gradient-to-br from-[#f6ffdc] via-[#effbcf] to-[#d8f3c8] transition-[height,border-radius,opacity,transform] duration-[250ms] ease-in-out ${collapsed ? "h-16 scale-90 rounded-2xl opacity-70" : "h-[150px] scale-100 rounded-[28px] opacity-100"}`}><span className="absolute -left-10 -top-12 h-32 w-24 rotate-45 rounded-full bg-sky-200/55"/><span className="absolute left-14 -top-7 h-28 w-20 rotate-[28deg] rounded-full bg-orange-200/55"/><span className="absolute -bottom-12 -left-2 h-28 w-32 rounded-full bg-[#d6f36b]/45"/><span className="absolute -bottom-10 right-[-18px] h-32 w-28 rounded-full bg-emerald-300/35"/></div>
  </aside>;
}

export function TopBar({ collapsed, role, onChangeRole, profile }: { collapsed: boolean; role: Role; onChangeRole: (role: Role) => void; profile?: Profile }) {
  const initials = (profile?.display_name ?? "").split(/\s+/).map((word) => word[0]).join("").slice(0, 2).toUpperCase() || "?";
  return <header className={`sticky top-0 z-10 flex h-[76px] items-center border-b border-slate-200 bg-white/95 px-5 backdrop-blur transition-[margin-left] duration-[250ms] ease-in-out md:px-7 ${collapsed ? "lg:ml-20" : "lg:ml-[226px]"}`}>
    <div className="flex h-12 w-full max-w-[610px] items-center gap-3 rounded-xl bg-[#f1f5f9] px-4 text-[#6b7fa5]"><Icon name="search"/><span className="text-sm">Buscar facturas, clientes...</span></div>
    <div className="ml-auto flex items-center gap-4 pl-5">
      <div role="group" aria-label="Cambiar rol" className="flex h-9 items-center rounded-full border border-slate-200 bg-slate-50 p-1 text-xs font-medium">
        <button type="button" onClick={() => onChangeRole("empresa")} aria-pressed={role === "empresa"} className={`h-7 rounded-full px-3 transition ${role === "empresa" ? "bg-navy text-white shadow-sm" : "text-navy hover:bg-white"}`}>Empresa</button>
        <button type="button" onClick={() => onChangeRole("financiadora")} aria-pressed={role === "financiadora"} className={`h-7 rounded-full px-3 transition ${role === "financiadora" ? "bg-navy text-white shadow-sm" : "text-navy hover:bg-white"}`}>Financiadora</button>
      </div>
      <button className="relative rounded-full p-2 text-navy transition hover:bg-slate-100" aria-label="Notificaciones"><Icon name="bell"/><span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white"/></button>
      <span className="hidden h-7 w-px bg-slate-200 md:block"/>
      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-navy text-sm font-medium text-white">{initials}</div>
      <div className="hidden min-w-[155px] md:block"><div className="text-sm font-semibold text-navy">{profile?.display_name ?? "Cargando..."}</div><div className="mt-1 text-xs text-[#52688f]">{profile?.org_name ?? ""}</div></div>
      <Icon name="chevron" size={18} className="hidden md:block"/>
    </div>
  </header>;
}

export function AppShell({ children, activeSection = "Ofertas" }: { children: React.ReactNode; activeSection?: string }) {
  const [collapsed, setCollapsed] = useState(false);
  const [role, setRole] = useActiveRole();
  const profiles = useProfiles();
  const activeProfile = profiles.find((profile) => profile.role === role);

  return <div className="min-h-screen bg-[#fbfcfe]">
    <AppSidebar activeSection={activeSection} collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} role={role}/>
    <TopBar collapsed={collapsed} role={role} onChangeRole={setRole} profile={activeProfile}/>
    <main className={`px-5 py-6 transition-[margin-left] duration-[250ms] ease-in-out md:px-7 ${collapsed ? "lg:ml-20" : "lg:ml-[226px]"}`}>{children}</main>
  </div>;
}
