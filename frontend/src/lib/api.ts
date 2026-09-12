const API_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message: string, readonly status: number, readonly body: string) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  if (!API_URL) {
    throw new Error("NEXT_PUBLIC_API_URL is not set");
  }

  const response = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });

  if (!response.ok) {
    const body = await response.text();
    let detail = "El backend devolvió una respuesta no JSON.";
    try {
      const parsed = JSON.parse(body) as { detail?: string };
      detail = parsed.detail ?? detail;
    } catch {
      // Preserve a short response excerpt for non-JSON upstream errors.
    }
    throw new ApiError(`API request failed (${response.status}): ${detail}`, response.status, body);
  }

  return response.json() as Promise<T>;
}

export type HealthResponse = {
  status: string;
  service: string;
};

export async function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/api/health/");
}
