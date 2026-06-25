export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { credentials: "include", headers: { "Content-Type": "application/json" }, ...init });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail ?? detail; } catch { /* noop */ }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
};

export type Plan = { id: string; title: string; months: number; price_rub: number; discount_percent: number };
export type Me = { telegram_id: number; username: string | null; subscription_until: string | null; balance_rub: number };
export type PaymentCreated = { invoice_id: number; pay_url: string; amount_rub: number; payable_rub: number; status: string };
export type PaymentStatus = { invoice_id: number; status: string; paid: boolean };
export type KeyConfig = { server: string; protocol: string; url: string; active: boolean };
export type CabinetKeys = { active: boolean; subscription_url: string | null; subscription_until: string | null; configs: KeyConfig[] };
export type PaymentHistoryItem = { invoice_id: number; amount_rub: number; payable_rub: number; months: number; plan_id: string; status: string; created_at: string | null; paid_at: string | null };
