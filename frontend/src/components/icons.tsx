import type { SVGProps } from "react";

export type IconName =
  | "home" | "invoice" | "grid" | "cube" | "transfer" | "settings"
  | "help" | "search" | "bell" | "chevron" | "calendar" | "check"
  | "compare" | "star" | "coins" | "bolt" | "clock" | "bars" | "arrow";

const paths: Record<IconName, React.ReactNode> = {
  home: <><path d="m3 11 9-8 9 8"/><path d="M5 10v10h5v-6h4v6h5V10"/></>,
  invoice: <><path d="M6 2h9l4 4v16H6z"/><path d="M14 2v5h5M9 11h6M9 15h6"/></>,
  grid: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
  cube: <><path d="m12 2 9 5-9 5-9-5z"/><path d="m3 7 9 5v10l-9-5zm18 0-9 5v10l9-5z"/></>,
  transfer: <><path d="M5 7h14l-3-3M19 17H5l3 3"/><path d="M19 7a3 3 0 0 1 0 6M5 17a3 3 0 0 1 0-6"/></>,
  settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3V2.8h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"/></>,
  help: <><circle cx="12" cy="12" r="9"/><path d="M9.8 9a2.3 2.3 0 1 1 3.6 1.9c-.9.6-1.4 1-1.4 2.1M12 17h.01"/></>,
  search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
  bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></>,
  chevron: <path d="m8 10 4 4 4-4"/>, calendar: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></>,
  check: <path d="m7 12 3 3 7-7"/>, compare: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
  star: <path d="m12 2 3 6 6 .9-4.5 4.4 1.1 6.2L12 16.6l-5.6 2.9 1.1-6.2L3 8.9 9 8z"/>,
  coins: <><ellipse cx="9" cy="6" rx="5" ry="2.5"/><path d="M4 6v4c0 1.4 2.2 2.5 5 2.5s5-1.1 5-2.5V6M4 10v4c0 1.4 2.2 2.5 5 2.5M16 13c2.8 0 5 1.1 5 2.5S18.8 18 16 18s-5-1.1-5-2.5 2.2-2.5 5-2.5Z"/><path d="M11 15.5v4c0 1.4 2.2 2.5 5 2.5s5-1.1 5-2.5v-4"/></>,
  bolt: <path d="M13 2 5 14h7l-1 8 8-12h-7z"/>, clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
  bars: <><path d="M5 20v-6h3v6zM11 20V9h3v11zM17 20V4h3v16z"/></>, arrow: <path d="M5 12h14m-4-4 4 4-4 4"/>,
};

export function Icon({ name, size = 22, className = "", ...props }: SVGProps<SVGSVGElement> & { name: IconName; size?: number }) {
  return <svg viewBox="0 0 24 24" width={size} height={size} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true" {...props}>{paths[name]}</svg>;
}
