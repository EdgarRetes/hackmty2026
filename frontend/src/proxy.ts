import { NextRequest, NextResponse } from "next/server";
import { FINANCIER_ROUTES, isUserRole, ROLE_CONFIG, ROLE_COOKIE, routeBelongsTo, SME_ROUTES } from "@/lib/session";

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const rawRole = request.cookies.get(ROLE_COOKIE)?.value;
  const role = isUserRole(rawRole) ? rawRole : null;

  if (pathname === "/login") {
    return role ? NextResponse.redirect(new URL(ROLE_CONFIG[role].home, request.url)) : NextResponse.next();
  }

  const expectedRole = routeBelongsTo(pathname, FINANCIER_ROUTES) ? "financier" : routeBelongsTo(pathname, SME_ROUTES) ? "sme" : null;
  if (!expectedRole) return NextResponse.next();
  if (!role) return NextResponse.redirect(new URL("/login", request.url));
  if (role !== expectedRole) return NextResponse.redirect(new URL(ROLE_CONFIG[role].home, request.url));
  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/login", "/invoices/:path*", "/publications/:path*", "/financing/:path*", "/offers/:path*", "/financier/:path*", "/marketplace/:path*"],
};
