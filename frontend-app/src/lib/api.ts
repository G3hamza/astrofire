import { useCallback, useEffect, useState } from "react";

/** The UI talks only to /api/* (NFR8). Typed client per endpoint arrives in G2-P2. */
export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      ...init,
      headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError("The StarryNight API is not reachable. Is the server running?");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body?.detail === "string" ? body.detail : JSON.stringify(body?.detail ?? body);
    } catch { /* keep statusText */ }
    throw new ApiError(`API ${res.status}: ${detail}`, res.status);
  }
  return res.json() as Promise<T>;
}

export function useApi<T>(path: string | null, init?: RequestInit) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(!!path);
  const [tick, setTick] = useState(0);
  const body = init?.body;
  const method = init?.method;

  useEffect(() => {
    if (!path) return;
    let alive = true;
    setLoading(true);
    setError(null);
    api<T>(path, { method, body })
      .then((d) => alive && setData(d))
      .catch((e: Error) => alive && setError(e.message))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [path, method, body, tick]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { data, error, loading, reload };
}

/* ---------- useQuery: keyed, cached, typed (screens re-open instantly) ---------- */
const cache = new Map<string, unknown>();

export function useQuery<T>(key: string | null, fn: () => Promise<T>) {
  const [data, setData] = useState<T | null>(() => (key && cache.has(key) ? (cache.get(key) as T) : null));
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(!!key && !cache.has(key));
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!key) { setData(null); setLoading(false); return; }
    if (cache.has(key) && tick === 0) { setData(cache.get(key) as T); setLoading(false); setError(null); return; }
    let alive = true;
    setLoading(true);
    setError(null);
    fn()
      .then((d) => { cache.set(key, d); if (alive) setData(d); })
      .catch((e: Error) => alive && setError(e.message))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, tick]);

  const reload = useCallback(() => { if (key) cache.delete(key); setTick((t) => t + 1); }, [key]);
  return { data, error, loading, reload };
}
