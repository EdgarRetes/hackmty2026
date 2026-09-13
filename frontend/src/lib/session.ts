export const ROLE_COOKIE = "factora_role";

export type UserRole = "sme" | "financier";

export const ROLE_CONFIG: Record<UserRole, { label: string; home: string; name: string; company: string }> = {
  sme: { label: "PyME", home: "/", name: "Lucía Martínez", company: "Industrias Monterrey" },
  financier: { label: "Financiero", home: "/financier", name: "Cuenta financiadora", company: "Perfil no disponible" },
};

export const SME_ROUTES = ["/", "/invoices", "/publications", "/financing", "/offers"];
export const FINANCIER_ROUTES = ["/financier", "/marketplace", "/portfolio"];

export function isUserRole(value: unknown): value is UserRole {
  return value === "sme" || value === "financier";
}

export function routeBelongsTo(pathname: string, routes: string[]): boolean {
  return routes.some((route) => route === "/" ? pathname === "/" : pathname === route || pathname.startsWith(`${route}/`));
}
