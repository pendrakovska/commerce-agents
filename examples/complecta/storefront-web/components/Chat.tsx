// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

"use client";

import { type ReactNode, useEffect, useState } from "react";
import { type AgentTurn, type AssistantChatItem, Chat as ChatShell } from "web-shared";
import { addToCart } from "@/lib/api";
import type { CartPayload } from "@/lib/types";
import GenerativeBlock from "./generative";

const WIDE = new Set(["comparison", "plan"]);

/** Seconds since the turn started — shown once the wait is long enough to feel like a stall. */
function useElapsed(active: boolean) {
  const [s, setS] = useState(0);
  useEffect(() => {
    if (!active) return;
    setS(0);
    const t0 = Date.now();
    const id = setInterval(() => setS(Math.round((Date.now() - t0) / 1000)), 1000);
    return () => clearInterval(id);
  }, [active]);
  return s;
}

/**
 * Что ALXNDRA делает прямо сейчас — словами, а не пустым мерцанием.
 *
 * Первый ответ занимает 5–10 с (поиск по каталогам + ответ модели), и в это время экран показывал только
 * серый «скелетон» без текста: со стороны это читалось как «не подключилась» (Olexandra, 2026-09-07).
 * Поток событий уже несёт подписи шагов (tool_call.label — «Looking for accent armchairs»); здесь они и
 * показываются, а паузы между событиями (до первого шага, после поиска до текста) закрываются своими словами.
 * Через 4 секунды рядом появляется счётчик секунд — видно, что процесс идёт. UI-строки — английские.
 */
function statusOf(item: AssistantChatItem): string {
  if (item.activity) return item.activity;
  if (!item.tools.length) return "ALXNDRA is reading your request…";
  if (item.tools.includes("search_products")) return "Found the pieces — composing the answer…";
  return "Composing the answer…";
}

function Pending({ item }: { item: AssistantChatItem }) {
  const elapsed = useElapsed(item.pending);
  const searching = item.tools.includes("search_products") && !item.segments.some((s) => s.type === "ui");
  const text = statusOf(item);
  const line = (
    <div role="status" aria-live="polite" className="flex items-center gap-2 text-[15px] text-(--ink-soft)">
      <span className="inline-block h-2 w-2 shrink-0 animate-pulse rounded-full bg-(--accent)" />
      <span className="min-w-0 truncate">{text}</span>
      {elapsed >= 4 ? <span className="shrink-0 tabular-nums text-[13px] opacity-70">· {elapsed} s</span> : null}
    </div>
  );
  if (!searching) return item.segments.length ? null : line;
  return (
    <section role="status" className="rounded-2xl border border-(--line) bg-(--card) p-3 shadow-(--shadow-sm)">
      <div className="mb-3">{line}</div>
      <div className="flex gap-3 overflow-hidden pb-1">
        {[0, 1, 2, 3].map((slot) => (
          <div key={slot} className="ac-skeleton h-[150px] w-48 shrink-0 rounded-xl" />
        ))}
      </div>
    </section>
  );
}

export default function Chat({ chat, home, onCartUpdate }: { chat: AgentTurn; home: ReactNode; onCartUpdate: (cart: CartPayload) => void }) {
  return (
    <ChatShell
      chat={chat}
      home={home}
      wide={WIDE}
      renderPending={(item) => <Pending item={item} />}
      renderBlock={(segment) => (
        <GenerativeBlock
          block={segment.block}
          status={segment.status}
          onAdd={async (product) => {
            const cart = await addToCart(product.product_id);
            if (cart) onCartUpdate(cart);
            return cart !== null;
          }}
        />
      )}
    />
  );
}
