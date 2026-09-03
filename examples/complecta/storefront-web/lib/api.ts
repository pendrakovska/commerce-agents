// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

import { AgentApi } from "web-shared";
import type { CartPayload, Product, ProductDetails } from "./types";

// АДРЕС API — УСТОЙЧИВЫЙ К СБОРКЕ. `vercel pull` отдаёт NEXT_PUBLIC_* как "[SENSITIVE]", и
// такой «адрес» уже уезжал в бандл (запросы шли на /[SENSITIVE]/api/…, витрина молчала).
// Плейсхолдер и пустоту не считаем адресом; на *.vercel.app — прод-API, иначе локальный демо-API.
const RAW_API = process.env.NEXT_PUBLIC_API_URL ?? "";
const API_URL = RAW_API && !RAW_API.includes("[") ? RAW_API
  : (typeof window !== "undefined" && window.location.hostname.endsWith("vercel.app")) ? "https://alxndra-api.vercel.app"
  : "http://localhost:8004";

export const api = new AgentApi(API_URL, "/api");

export const UNREACHABLE =
  "Couldn't reach the retail API on port 8000. Start it with " +
  "`uvicorn retail.api.main:app --app-dir examples --port 8000` and try again.";

export async function fetchProducts(): Promise<Product[] | null> {
  const data = await api.get<{ products: Product[] }>("/products", { limit: "100" });
  return data?.products ?? null;
}

export function fetchProduct(productId: string): Promise<ProductDetails | null> {
  return api.get<ProductDetails>(`/products/${encodeURIComponent(productId)}`);
}

export async function addToCart(productId: string, quantity = 1): Promise<CartPayload | null> {
  const data = await api.post<{ cart: CartPayload }>("/cart/add", { product_id: productId, quantity });
  return data?.cart ?? null;
}
