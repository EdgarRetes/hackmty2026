"use client";

import Image from "next/image";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ROLE_CONFIG, type UserRole } from "@/lib/session";
import { Icon } from "../icons";

const options: { role: UserRole; title: string; description: string; icon: "invoice" | "briefcase" }[] = [
  { role: "sme", title: "PyME", description: "Administra tus facturas y encuentra financiamiento.", icon: "invoice" },
  { role: "financier", title: "Financiero", description: "Descubre oportunidades y gestiona tu portafolio.", icon: "briefcase" },
];

export function LoginForm() {
  const router = useRouter();
  const [selected, setSelected] = useState<UserRole>("sme");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function login() {
    setPending(true); setError("");
    try {
      const response = await fetch("/api/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ role: selected }) });
      if (!response.ok) throw new Error("No fue posible iniciar sesión.");
      router.replace(ROLE_CONFIG[selected].home);
      router.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No fue posible iniciar sesión.");
      setPending(false);
    }
  }

  return <main className="flex min-h-screen items-center justify-center bg-[#f7f9fc] px-5 py-10"><section className="w-full max-w-[660px] rounded-[24px] border border-slate-200 bg-white p-7 shadow-[0_20px_60px_rgba(15,31,68,.08)] sm:p-10"><div className="flex items-center justify-center gap-3"><span className="relative h-12 w-12"><Image src="/factora-mark.svg" alt="" fill sizes="48px" priority/></span><div><h1 className="text-[30px] font-bold leading-none tracking-[-.04em] text-navy">Factora</h1><p className="mt-1 text-[10px] text-[#38517d]">Financiamiento que impulsa.</p></div></div><div className="mt-9 text-center"><h2 className="text-2xl font-bold text-navy">Bienvenido a Factora</h2><p className="mt-2 text-sm text-[#52688f]">Selecciona cómo quieres ingresar.</p></div><div className="mt-7 grid gap-3 sm:grid-cols-2">{options.map((option) => <button key={option.role} type="button" onClick={() => setSelected(option.role)} aria-pressed={selected === option.role} className={`rounded-2xl border p-5 text-left transition ${selected === option.role ? "border-[#badc45] bg-[#f5ffd9] shadow-[0_6px_20px_rgba(130,170,30,.1)]" : "border-slate-200 hover:border-slate-300"}`}><span className={`flex h-11 w-11 items-center justify-center rounded-xl ${selected === option.role ? "bg-[#dcf36e] text-navy" : "bg-[#edf2f8] text-[#52688f]"}`}><Icon name={option.icon}/></span><strong className="mt-4 block text-lg text-navy">{option.title}</strong><span className="mt-1 block text-sm leading-5 text-[#52688f]">{option.description}</span></button>)}</div>{error && <p role="alert" className="mt-4 text-center text-sm text-red-600">{error}</p>}<button type="button" disabled={pending} onClick={login} className="mt-7 h-12 w-full rounded-xl bg-navy text-sm font-semibold text-white transition hover:bg-[#173267] disabled:cursor-wait disabled:opacity-60">{pending ? "Ingresando..." : `Continuar como ${ROLE_CONFIG[selected].label}`}</button><p className="mt-5 text-center text-xs text-[#6b7fa5]">Acceso temporal para demostración. No solicita ni almacena credenciales.</p></section></main>;
}
