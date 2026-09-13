"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { sendAssistantMessage, type AssistantMessage } from "@/lib/invoice-assistant";
import { Icon } from "../icons";

const GREETING =
  "Hola, soy tu asistente de factoraje. Puedo revisar tus facturas pendientes, ayudarte a decidir cuáles conviene juntar en una publicación, y publicarla por ti en cuanto la confirmes. Por ejemplo: “¿qué facturas me conviene publicar juntas?”";

const SUGGESTIONS = [
  "¿Qué facturas me conviene juntar en una publicación?",
  "¿Cuál es la factura con menor riesgo ahora mismo?",
  "Compárame juntar todo contra publicar por separado.",
];

interface ChatEntry extends AssistantMessage {
  publishedBatchId?: number | null;
}

export function InvoiceAssistantPanel() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatEntry[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    const history = messages.map(({ role, text }) => ({ role, text }));
    setMessages([...messages, { role: "user", text: trimmed }]);
    setInput("");
    setSending(true);
    setError("");
    try {
      const { reply, publishedBatchId } = await sendAssistantMessage(trimmed, history);
      setMessages((current) => [...current, { role: "model", text: reply, publishedBatchId }]);
      if (publishedBatchId) router.refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "El asistente no está disponible en este momento.");
    } finally {
      setSending(false);
    }
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    send(input);
  }

  return <>
    <button
      type="button"
      onClick={() => setOpen((current) => !current)}
      className="fixed bottom-6 right-6 z-40 flex h-14 items-center gap-2.5 rounded-full bg-navy px-5 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(15,31,68,.25)] transition hover:bg-[#173267]"
    >
      <Icon name="sparkles" size={20}/>
      {open ? "Cerrar asistente" : "Asistente IA"}
    </button>

    {open && <section className="fixed bottom-24 right-6 z-40 flex h-[min(600px,70vh)] w-[min(420px,calc(100vw-3rem))] flex-col overflow-hidden rounded-[20px] border border-slate-200 bg-white shadow-[0_20px_60px_rgba(15,31,68,.18)]">
      <header className="flex items-center gap-2.5 border-b border-slate-100 bg-[#f7f9fc] px-4 py-3.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#dcf36e] text-navy"><Icon name="sparkles" size={18}/></span>
        <div><strong className="block text-sm font-bold text-navy">Asistente de facturación</strong><span className="block text-xs text-[#52688f]">Recomendaciones con datos reales</span></div>
      </header>

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        <Bubble role="model" text={GREETING}/>
        {messages.length === 0 && <div className="flex flex-col gap-2">{SUGGESTIONS.map((suggestion) => <button key={suggestion} onClick={() => send(suggestion)} className="rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-left text-xs font-medium text-navy transition hover:border-slate-300 hover:bg-slate-50">{suggestion}</button>)}</div>}
        {messages.map((entry, index) => <Bubble key={index} role={entry.role} text={entry.text} publishedBatchId={entry.publishedBatchId}/>)}
        {sending && <Bubble role="model" text="Analizando tus facturas..." pending/>}
      </div>

      {error && <p role="alert" className="mx-4 mb-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">{error}</p>}

      <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-slate-100 p-3">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Escribe tu pregunta..."
          disabled={sending}
          className="h-11 flex-1 rounded-xl border border-slate-200 bg-[#f6f8fb] px-3.5 text-sm text-navy outline-none placeholder:text-[#9fb0c9] focus:border-navy disabled:opacity-60"
        />
        <button type="submit" disabled={sending || !input.trim()} aria-label="Enviar" className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-navy text-white transition hover:bg-[#173267] disabled:cursor-not-allowed disabled:opacity-40">
          <Icon name="send" size={18}/>
        </button>
      </form>
    </section>}
  </>;
}

function Bubble({ role, text, pending, publishedBatchId }: { role: "user" | "model"; text: string; pending?: boolean; publishedBatchId?: number | null }) {
  const isUser = role === "user";
  return <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
    <div className={`max-w-[88%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${isUser ? "bg-navy text-white" : "bg-[#f1f5fa] text-navy"} ${pending ? "italic text-[#6b7fa5]" : ""}`}>
      {isUser ? <p className="whitespace-pre-wrap">{text}</p> : <div className="assistant-markdown"><Markdown remarkPlugins={[remarkGfm]} components={{ table: ({ children }) => <div className="overflow-x-auto"><table>{children}</table></div> }}>{text}</Markdown></div>}
      {publishedBatchId != null && <Link href={`/publications/${publishedBatchId}`} className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-navy px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-[#173267]">Ver publicación PUB-{String(publishedBatchId).padStart(4, "0")} →</Link>}
    </div>
  </div>;
}
