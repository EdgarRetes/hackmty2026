"use client";

import { useEffect, useState } from "react";
import { getHealth, type HealthResponse } from "@/lib/api";

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-zinc-50 p-8 font-sans">
      <h1 className="text-2xl font-semibold text-zinc-900">
        factorai — backend connectivity check
      </h1>

      {error && (
        <p className="rounded bg-red-100 px-4 py-2 text-red-700">
          Error: {error}
        </p>
      )}

      {!error && !health && (
        <p className="text-zinc-500">Calling backend…</p>
      )}

      {health && (
        <pre className="rounded bg-white px-4 py-3 text-sm text-zinc-800 shadow">
          {JSON.stringify(health, null, 2)}
        </pre>
      )}
    </div>
  );
}
