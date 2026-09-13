import { NextResponse } from "next/server";
import { isUserRole, ROLE_CONFIG, ROLE_COOKIE } from "@/lib/session";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null) as { role?: unknown } | null;
  if (!isUserRole(body?.role)) return NextResponse.json({ detail: "Selecciona un rol válido." }, { status: 400 });

  const response = NextResponse.json({ role: body.role, redirectTo: ROLE_CONFIG[body.role].home });
  response.cookies.set(ROLE_COOKIE, body.role, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 12,
  });
  return response;
}

export function DELETE() {
  const response = NextResponse.json({ ok: true });
  response.cookies.set(ROLE_COOKIE, "", { httpOnly: true, sameSite: "lax", path: "/", maxAge: 0 });
  return response;
}
