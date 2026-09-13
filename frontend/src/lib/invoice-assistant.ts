const API_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");

export interface AssistantMessage {
  role: "user" | "model";
  text: string;
}

export async function sendAssistantMessage(message: string, history: AssistantMessage[]): Promise<string> {
  if (!API_URL) throw new Error("NEXT_PUBLIC_API_URL is not set");

  const response = await fetch(`${API_URL}/api/invoices/assistant/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ message, history }),
  });

  const body = await response.text();
  if (!response.ok) {
    let detail = "El asistente no está disponible en este momento.";
    try {
      detail = (JSON.parse(body) as { detail?: string }).detail ?? detail;
    } catch {
      // Preserve the generic message for a non-JSON upstream error.
    }
    throw new Error(detail);
  }

  return (JSON.parse(body) as { reply: string }).reply;
}
