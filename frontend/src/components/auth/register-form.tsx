"use client";

import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { useId, useState } from "react";
import { isUserRole, ROLE_CONFIG, type UserRole } from "@/lib/session";
import { Icon, type IconName } from "../icons";

const SECTORS = [
  { value: "retail_chain", label: "Comercio minorista" },
  { value: "construction", label: "Construcción" },
  { value: "construction_supplies", label: "Materiales de construcción" },
  { value: "manufacturing", label: "Manufactura" },
  { value: "pharma_retail", label: "Farmacéutico" },
  { value: "logistics", label: "Logística y transporte" },
  { value: "technology", label: "Tecnología" },
  { value: "textile", label: "Textil" },
  { value: "agriculture", label: "Agroindustria" },
  { value: "hospitality", label: "Hotelería" },
];

const roleOptions: { role: UserRole; title: string; description: string; icon: IconName }[] = [
  { role: "sme", title: "PyME", description: "Registra tu empresa para publicar facturas.", icon: "building" },
  { role: "financier", title: "Financiero", description: "Regístrate para invertir en el marketplace.", icon: "briefcase" },
];

/**
 * A real, multi-step onboarding UI — but same "demo access" contract as
 * LoginForm: nothing typed here is validated, stored, or sent anywhere
 * except the chosen role. Finishing just calls the same POST /api/session
 * the login screen uses.
 */
export function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialRole = searchParams.get("role");
  const [role, setRole] = useState<UserRole>(isUserRole(initialRole) ? initialRole : "sme");
  const [step, setStep] = useState<1 | 2>(1);
  const [rostroVerificado, setRostroVerificado] = useState(false);
  const [verificando, setVerificando] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const totalSteps = role === "sme" ? 2 : 1;
  const canFinish = role === "financier" ? rostroVerificado : true;

  function changeRole(next: UserRole) {
    setRole(next);
    setStep(1);
  }

  function verifyFace() {
    setVerificando(true);
    setTimeout(() => {
      setVerificando(false);
      setRostroVerificado(true);
    }, 1400);
  }

  async function finish() {
    setSubmitting(true);
    setError("");
    try {
      const response = await fetch("/api/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ role }) });
      if (!response.ok) throw new Error("No fue posible completar el registro.");
      router.replace(ROLE_CONFIG[role].home);
      router.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No fue posible completar el registro.");
      setSubmitting(false);
    }
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (role === "sme" && step === 1) {
      setStep(2);
      return;
    }
    if (!canFinish) return;
    finish();
  }

  return <main className="flex min-h-screen items-center justify-center bg-[#f7f9fc] px-5 py-10">
    <section className="w-full max-w-[760px] rounded-[24px] border border-slate-200 bg-white p-7 shadow-[0_20px_60px_rgba(15,31,68,.08)] sm:p-10">
      <div className="flex items-center justify-center gap-3"><span className="relative h-12 w-12"><Image src="/factora-mark.svg" alt="" fill sizes="48px" priority/></span><div><h1 className="text-[30px] font-bold leading-none tracking-[-.04em] text-navy">Factora</h1><p className="mt-1 text-[10px] text-[#38517d]">Financiamiento que impulsa.</p></div></div>
      <div className="mt-9 text-center"><h2 className="text-2xl font-bold text-navy">Crea tu cuenta</h2><p className="mt-2 text-sm text-[#52688f]">Selecciona tu perfil y completa tu expediente de originación.</p></div>

      <div className="mt-7 grid gap-3 sm:grid-cols-2">{roleOptions.map((option) => <button key={option.role} type="button" onClick={() => changeRole(option.role)} aria-pressed={role === option.role} className={`rounded-2xl border p-5 text-left transition ${role === option.role ? "border-[#badc45] bg-[#f5ffd9] shadow-[0_6px_20px_rgba(130,170,30,.1)]" : "border-slate-200 hover:border-slate-300"}`}><span className={`flex h-11 w-11 items-center justify-center rounded-xl ${role === option.role ? "bg-[#dcf36e] text-navy" : "bg-[#edf2f8] text-[#52688f]"}`}><Icon name={option.icon}/></span><strong className="mt-4 block text-lg text-navy">{option.title}</strong><span className="mt-1 block text-sm leading-5 text-[#52688f]">{option.description}</span></button>)}</div>

      {totalSteps > 1 && <div className="mt-6 flex items-center gap-3"><StepDot active={step === 1} done={step > 1} number={1} label="Identidad y operación"/><span className="h-px flex-1 bg-slate-200"/><StepDot active={step === 2} done={false} number={2} label="Fiscal y bancario"/></div>}

      <form onSubmit={handleSubmit} className="mt-6">
        {role === "sme" ? (step === 1 ? <SmeStepOne/> : <SmeStepTwo/>) : <FinancierFields verificado={rostroVerificado} verificando={verificando} onVerify={verifyFace}/>}

        {error && <p role="alert" className="mt-4 text-center text-sm text-red-600">{error}</p>}

        <div className="mt-7 flex gap-3">
          {role === "sme" && step === 2 && <button type="button" onClick={() => setStep(1)} className="h-12 flex-1 rounded-xl border border-slate-200 text-sm font-semibold text-navy transition hover:bg-slate-50">Atrás</button>}
          <button type="submit" disabled={submitting || (role === "sme" ? false : !canFinish && false)} className="h-12 flex-1 rounded-xl bg-navy text-sm font-semibold text-white transition hover:bg-[#173267] disabled:cursor-not-allowed disabled:opacity-60">
            {submitting ? "Enviando..." : role === "sme" && step === 1 ? "Continuar" : `Finalizar registro como ${ROLE_CONFIG[role].label}`}
          </button>
        </div>
        {role === "financier" && !rostroVerificado && step === 1 && <p className="mt-3 text-center text-xs text-[#9fb0c9]">Completa la verificación de rostro para poder finalizar.</p>}
      </form>

      <p className="mt-5 text-center text-xs text-[#6b7fa5]">Acceso temporal para demostración. No solicita ni almacena documentos ni credenciales reales.</p>
      <p className="mt-3 text-center text-sm text-[#52688f]">¿Ya tienes cuenta? <a href="/login" className="font-semibold text-navy underline">Inicia sesión</a></p>
    </section>
  </main>;
}

function StepDot({ active, done, number, label }: { active: boolean; done: boolean; number: number; label: string }) {
  return <span className={`flex items-center gap-2 text-xs font-medium ${active || done ? "text-navy" : "text-[#9fb0c9]"}`}><i className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] ${active ? "bg-navy text-white" : done ? "bg-[#dcf36e] text-navy" : "bg-slate-100 text-[#9fb0c9]"}`}>{done ? <Icon name="check" size={12}/> : number}</i><span className="hidden sm:inline">{label}</span></span>;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <fieldset className="rounded-xl border border-slate-200 p-4"><legend className="px-1 text-sm font-bold text-navy">{title}</legend><div className="mt-2 grid gap-3 sm:grid-cols-2">{children}</div></fieldset>;
}

function TextField({ label, type = "text", placeholder, span }: { label: string; type?: string; placeholder?: string; span?: boolean }) {
  return <label className={span ? "sm:col-span-2" : undefined}><span className="mb-1.5 block text-xs font-medium text-[#38517d]">{label}</span><input type={type} placeholder={placeholder} className="h-11 w-full rounded-lg border border-slate-200 bg-white px-3.5 text-sm text-navy outline-none placeholder:text-[#9fb0c9] focus:border-navy"/></label>;
}

function SelectField({ label, options }: { label: string; options: { value: string; label: string }[] }) {
  return <label><span className="mb-1.5 block text-xs font-medium text-[#38517d]">{label}</span><select className="h-11 w-full rounded-lg border border-slate-200 bg-white px-3.5 text-sm text-navy outline-none focus:border-navy">{options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>;
}

function FileField({ label, hint, span }: { label: string; hint?: string; span?: boolean }) {
  const id = useId();
  const [fileName, setFileName] = useState<string | null>(null);
  return <label htmlFor={id} className={`flex cursor-pointer items-center gap-3 rounded-lg border border-dashed border-slate-300 bg-[#f8fafc] px-3.5 py-3 transition hover:border-slate-400 ${span ? "sm:col-span-2" : ""}`}>
    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white text-[#52688f]"><Icon name="upload" size={18}/></span>
    <span className="min-w-0 flex-1"><span className="block text-xs font-medium text-[#38517d]">{label}</span><span className="mt-0.5 block truncate text-xs text-[#9fb0c9]">{fileName ?? hint ?? "Ningún archivo seleccionado"}</span></span>
    <input id={id} type="file" className="hidden" onChange={(event) => setFileName(event.target.files?.[0]?.name ?? null)}/>
  </label>;
}

function SmeStepOne() {
  return <div className="grid gap-4">
    <Section title="Identidad societaria">
      <TextField label="RFC" placeholder="XAXX010101000"/>
      <TextField label="Calle y número"/>
      <TextField label="Ciudad"/>
      <TextField label="Estado"/>
      <TextField label="Código postal"/>
      <FileField label="Acta constitutiva (PDF)"/>
    </Section>
    <Section title="Operación">
      <TextField label="Años operando" type="number" placeholder="5"/>
      <SelectField label="Giro / industria" options={SECTORS}/>
      <TextField label="Número de empleados" type="number" placeholder="20"/>
      <TextField label="Principales clientes" placeholder="Separados por coma"/>
    </Section>
  </div>;
}

function SmeStepTwo() {
  return <div className="grid gap-4">
    <Section title="Fiscal">
      <FileField label="CFDI de los últimos 24 meses" hint="Acepta .zip" span/>
      <div className="flex items-center justify-between gap-3 rounded-lg bg-[#f1f5fa] px-3.5 py-3 sm:col-span-2"><span className="text-sm text-navy">O conecta directo con el SAT</span><button type="button" className="h-9 shrink-0 rounded-lg border border-navy px-4 text-xs font-semibold text-navy transition hover:bg-white">Conectar SAT</button></div>
    </Section>
    <Section title="Bancario">
      <TextField label="Banco"/>
      <TextField label="CLABE interbancaria" placeholder="18 dígitos"/>
      <FileField label="Estados de cuenta (12 meses)" hint="PDF o .zip" span/>
    </Section>
  </div>;
}

function FinancierFields({ verificado, verificando, onVerify }: { verificado: boolean; verificando: boolean; onVerify: () => void }) {
  return <div className="grid gap-4">
    <Section title="Identidad">
      <FileField label="INE (frente)"/>
      <FileField label="INE (reverso)"/>
      <div className="flex items-center justify-between gap-3 rounded-lg bg-[#f1f5fa] px-3.5 py-3 sm:col-span-2">
        <span className="flex items-center gap-2 text-sm text-navy"><Icon name="camera" size={18}/>Verificación de rostro</span>
        {verificado
          ? <span className="flex shrink-0 items-center gap-1.5 rounded-lg bg-[#dcfce7] px-3 py-1.5 text-xs font-semibold text-[#16833f]"><Icon name="check" size={14}/>Verificado</span>
          : <button type="button" onClick={onVerify} disabled={verificando} className="h-9 shrink-0 rounded-lg border border-navy px-4 text-xs font-semibold text-navy transition hover:bg-white disabled:opacity-60">{verificando ? "Verificando..." : "Iniciar verificación"}</button>}
      </div>
      <FileField label="Comprobante de domicilio" span/>
      <TextField label="RFC"/>
    </Section>
    <Section title="Datos bancarios">
      <TextField label="Banco"/>
      <TextField label="CLABE interbancaria" placeholder="18 dígitos"/>
    </Section>
  </div>;
}
