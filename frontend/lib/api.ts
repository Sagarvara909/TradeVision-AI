const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

export async function registerUser(email: string, password: string) {
  const res = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Registration failed");
  }
  return res.json();
}

export async function loginUser(email: string, password: string) {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Login failed");
  }
  return res.json();
}

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

// add alongside your existing `ocr` object in `api`:
market: {
  analyze: (symbol: string) =>
    request<TechnicalAnalysis>(`/market/analysis/${symbol}`, { auth: true }),
},