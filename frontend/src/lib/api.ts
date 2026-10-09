/**
 * TradeVision AI — API client.
 * Single typed module. Add new endpoints as methods on `api`.
 */

export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  "http://127.0.0.1:8000/api/v1";

const ACCESS_KEY = "tv_access_token";
const REFRESH_KEY = "tv_refresh_token";

export const tokenStore = {
  getAccess: () =>
    typeof window === "undefined" ? null : localStorage.getItem(ACCESS_KEY),
  getRefresh: () =>
    typeof window === "undefined" ? null : localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export class ApiError extends Error {
  status: number;
  data: unknown;
  constructor(message: string, status: number, data: unknown) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  auth?: boolean;
  headers?: Record<string, string>;
  signal?: AbortSignal;
};

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = false, headers = {}, signal } = opts;
  const url = `${API_BASE_URL}${path}`;

  const finalHeaders: Record<string, string> = {
    Accept: "application/json",
    ...headers,
  };
  if (body !== undefined && !(body instanceof FormData)) {
    finalHeaders["Content-Type"] = "application/json";
  }
  if (auth) {
    const token = tokenStore.getAccess();
    if (token) finalHeaders.Authorization = `Bearer ${token}`;
  }

  let res: Response;
  try {
    res = await fetch(url, {
      method,
      headers: finalHeaders,
      body:
        body === undefined
          ? undefined
          : body instanceof FormData
            ? body
            : JSON.stringify(body),
      signal,
    });
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : "Network error",
      0,
      null,
    );
  }

  const isJson = res.headers.get("content-type")?.includes("application/json");
  const data: unknown = isJson ? await res.json().catch(() => null) : await res.text().catch(() => null);

  if (!res.ok) {
    const message =
      (isJson && data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : undefined) ?? `Request failed (${res.status})`;
    throw new ApiError(message, res.status, data);
  }

  return data as T;
}

// ---- Types ----
export type User = { id: string | number; email: string };
export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};
export type OCRResult = {
  image_id: string;
  symbol: string | null;
  exchange: string | null;
  timeframe: string | null;
  raw_text_count: number;
};

// Technical indicators only — matches backend TechnicalAnalysisResponse.
export type TechnicalAnalysis = {
  symbol: string;
  ema20: number;
  ema50: number | null;
  rsi: number;
  macd: number;
  macd_signal: number;
  macd_histogram: number;
  trend: string;
  support: number | null;
  resistance: number | null;
  latest_volume: number;
  average_volume: number | null;
  volume_ratio: number | null;
  above_average_volume: boolean | null;
};

export type SentimentInfo = {
  label: string;
  score: number;
  article_count: number;
  headlines: Record<string, unknown>[];
};

// Everything TechnicalAnalysis has, PLUS the confidence/risk layer.
// Matches backend RiskAnalysisResponse (which now extends TechnicalAnalysisResponse).
export type RiskAnalysis = TechnicalAnalysis & {
  volatility_pct: number;
  sentiment: SentimentInfo;
  confidence_score: number;
  risk_level: string;
  reasoning: string[];
};

export type Report = {
  id: string;
  image_id: string;
  symbol: string;
  timeframe: string;
  confidence_score: number;
  risk_level: string;
  reasoning: string[];
  indicators: Record<string, unknown>;
  llm_report: string;
  llm_model: string | null;
  unsupported_numbers: string[];
  created_at: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  llm_model?: string | null;
  unsupported_numbers?: string[];
};

export type ChatHistory = {
  report_id: string;
  messages: ChatMessage[];
};

export type SymbolSuggestion = {
  symbol: string;
  last_close: number | null; // compare against the price on your chart
};

export type WatchlistItem = {
  id: string;
  symbol: string;
  exchange: string | null;
  added_at: string;
  price: number | null;
  change: number | null;
  percent_change: number | null;
  quote_error: string | null;
};

export type HistoryEntry = {
  report_id: string;
  symbol: string;
  timeframe: string;
  trend: string | null;
  confidence_score: number;
  risk_level: string;
  created_at: string;
  last_viewed_at: string;
};

// ---- Endpoints ----
export const api = {
  auth: {
    register: (email: string, password: string) =>
      request<User>("/auth/register", {
        method: "POST",
        body: { email, password },
      }),
    login: (email: string, password: string) =>
      request<TokenResponse>("/auth/login", {
        method: "POST",
        body: { email, password },
      }),
    me: () => request<User>("/auth/me", { auth: true }),
  },
  ocr: {
    upload: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return request<OCRResult>("/ocr/upload", {
        method: "POST",
        body: formData,
        auth: true,
      });
    },
  },
  market: {
    // exchange (e.g. "NSE", "BSE", "NASDAQ") matters for Indian tickers —
    // Yahoo Finance needs it to resolve e.g. RELIANCE -> RELIANCE.NS.
    analyze: (symbol: string, exchange?: string) =>
      request<TechnicalAnalysis>(
        `/market/analysis/${encodeURIComponent(symbol)}${exchange ? `?exchange=${encodeURIComponent(exchange)}` : ""}`,
        { auth: true },
      ),
    // Superset of analyze(): same technical fields PLUS confidence_score,
    // risk_level, reasoning and sentiment. Prefer this one in the UI.
    risk: (symbol: string, exchange?: string) =>
      request<RiskAnalysis>(
        `/market/risk/${encodeURIComponent(symbol)}${exchange ? `?exchange=${encodeURIComponent(exchange)}` : ""}`,
        { auth: true },
      ),
    // "Did you mean...?" for a symbol with no data. OCR confuses look-alike
    // characters on small fonts (T/F, O/0, S/5); the backend tries those swaps
    // and returns only variants that really have market data.
    suggest: (symbol: string, exchange?: string) =>
      request<{ suggestions: SymbolSuggestion[] }>(
        `/market/suggest/${encodeURIComponent(symbol)}${exchange ? `?exchange=${encodeURIComponent(exchange)}` : ""}`,
        { auth: true },
      ),
  },
  reports: {
    // image_id must belong to the logged-in user's own uploaded chart
    // (Report.image_id is a required foreign key on the backend).
    create: (image_id: string, symbol: string, timeframe = "1day", exchange?: string) =>
      request<Report>("/reports", {
        method: "POST",
        auth: true,
        body: { image_id, symbol, timeframe, exchange },
      }),
    get: (reportId: string) =>
      request<Report>(`/reports/${encodeURIComponent(reportId)}`, { auth: true }),
    // The PDF endpoint is JWT-protected, so a plain <a href> can't download it
    // (the browser wouldn't send the Authorization header). Fetch it as a blob
    // with the token, then trigger the download from an object URL instead.
    downloadPdf: async (reportId: string, symbol: string) => {
      const token = tokenStore.getAccess();
      let res: Response;
      try {
        res = await fetch(`${API_BASE_URL}/reports/${encodeURIComponent(reportId)}/pdf`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
      } catch (err) {
        throw new ApiError(err instanceof Error ? err.message : "Network error", 0, null);
      }
      if (!res.ok) {
        let detail = `Request failed (${res.status})`;
        try {
          const body = await res.json();
          if (body && typeof body.detail === "string") detail = body.detail;
        } catch {
          /* non-JSON error body — keep the generic message */
        }
        throw new ApiError(detail, res.status, null);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `TradeVision_${symbol}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    },
  },
  chat: {
    // Answers are grounded in the report's own data — not free-form chat.
    ask: (reportId: string, message: string) =>
      request<ChatMessage>(`/chat/${encodeURIComponent(reportId)}`, {
        method: "POST",
        auth: true,
        body: { message },
      }),
    history: (reportId: string) =>
      request<ChatHistory>(`/chat/${encodeURIComponent(reportId)}`, { auth: true }),
  },
  history: {
    // Most-recently-viewed reports first; opening an old report again
    // bumps it back to the top, same as a browser's history page.
    list: (limit = 50) =>
      request<{ entries: HistoryEntry[] }>(`/history?limit=${limit}`, { auth: true }),
  },
  watchlist: {
    // Each item comes back with a live quote; if a quote can't be fetched
    // for one symbol, that row has quote_error set instead of failing the list.
    list: () => request<{ items: WatchlistItem[] }>("/watchlist", { auth: true }),
    add: (symbol: string, exchange?: string) =>
      request<WatchlistItem>("/watchlist", {
        method: "POST",
        auth: true,
        body: { symbol, exchange },
      }),
    remove: (itemId: string) =>
      request<{ status: string }>(`/watchlist/${encodeURIComponent(itemId)}`, {
        method: "DELETE",
        auth: true,
      }),
  },
};