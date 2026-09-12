import { Icon, type IconName } from "./icons";

const primary: { label: string; icon: IconName }[] = [
  { label: "Home", icon: "home" }, { label: "Facturas", icon: "invoice" },
  { label: "Ofertas", icon: "grid" }, { label: "Financiamientos", icon: "cube" },
  { label: "Transacciones", icon: "transfer" },
];
const secondary: { label: string; icon: IconName }[] = [
  { label: "Configuración", icon: "settings" }, { label: "Ayuda", icon: "help" },
];

function BrandMark() {
  return <span className="relative block h-9 w-9 shrink-0"><i className="absolute left-0 top-2 h-5 w-5 rounded-full bg-[#d6f36b]"/><i className="absolute left-3 top-0 h-5 w-5 rounded-full bg-navy"/><i className="absolute bottom-0 left-3 h-5 w-5 rounded-full bg-[#b9e93e]/80"/></span>;
}

function NavList({ items }: { items: typeof primary }) {
  return <nav className="space-y-2.5">{items.map((item) => <a key={item.label} href={item.label === "Ofertas" ? "/offers/INV-1842" : "#"} className={`flex h-12 items-center gap-5 rounded-xl px-4 text-[15px] font-medium transition ${item.label === "Ofertas" ? "bg-gradient-to-r from-[#efffc3] to-[#f6ffd9] text-navy" : "text-navy hover:bg-slate-50"}`}><Icon name={item.icon} size={22}/><span>{item.label}</span></a>)}</nav>;
}

export function AppSidebar() {
  return <aside className="fixed inset-y-0 left-0 z-20 hidden w-[226px] border-r border-slate-200 bg-white px-4 py-6 lg:flex lg:flex-col">
    <div className="flex items-center gap-2 px-2"><BrandMark/><div><div className="text-[24px] font-bold leading-6 tracking-[-.04em] text-navy">Factora</div><div className="mt-1 text-[9px] text-navy">Financiamiento que impulsa.</div></div></div>
    <div className="mt-14"><NavList items={primary}/></div>
    <div className="mt-10 border-t border-slate-200 pt-7"><NavList items={secondary}/></div>
    <div aria-hidden="true" className="relative mt-auto h-[150px] overflow-hidden rounded-[28px] bg-gradient-to-br from-[#f6ffdc] via-[#effbcf] to-[#d8f3c8]"><span className="absolute -left-10 -top-12 h-32 w-24 rotate-45 rounded-full bg-sky-200/55"/><span className="absolute left-14 -top-7 h-28 w-20 rotate-[28deg] rounded-full bg-orange-200/55"/><span className="absolute -bottom-12 -left-2 h-28 w-32 rounded-full bg-[#d6f36b]/45"/><span className="absolute -bottom-10 right-[-18px] h-32 w-28 rounded-full bg-emerald-300/35"/></div>
  </aside>;
}

export function TopBar() {
  return <header className="sticky top-0 z-10 flex h-[76px] items-center border-b border-slate-200 bg-white/95 px-5 backdrop-blur md:px-7 lg:ml-[226px]">
    <div className="flex h-12 w-full max-w-[610px] items-center gap-3 rounded-xl bg-[#f1f5f9] px-4 text-[#6b7fa5]"><Icon name="search"/><span className="text-sm">Buscar facturas, clientes...</span></div>
    <div className="ml-auto flex items-center gap-4 pl-5"><button className="relative rounded-full p-2 text-navy transition hover:bg-slate-100" aria-label="Notificaciones"><Icon name="bell"/><span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white"/></button><span className="hidden h-7 w-px bg-slate-200 md:block"/><div className="flex h-11 w-11 items-center justify-center rounded-full bg-navy text-sm font-medium text-white">LM</div><div className="hidden min-w-[155px] md:block"><div className="text-sm font-semibold text-navy">Lucía Martínez</div><div className="mt-1 text-xs text-[#52688f]">Industrias Monterrey</div></div><Icon name="chevron" size={18} className="hidden md:block"/></div>
  </header>;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return <div className="min-h-screen bg-[#fbfcfe]"><AppSidebar/><TopBar/><main className="px-5 py-6 md:px-7 lg:ml-[226px]">{children}</main></div>;
}
