// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

"use client";

import { useCallback, useEffect, useState } from "react";
import { type AgentEvent, formatMoney, OrdersView, plural, StoreShell, type StoreView, upcoming, useAgentTurn, useResource, useSession } from "web-shared";
import CartPanel from "@/components/CartPanel";
import Chat from "@/components/Chat";
import HomeView from "@/components/views/HomeView";
import { api, UNREACHABLE } from "@/lib/api";
import { NOUNS, OrderThumb } from "@/lib/orders";
import type { CartPayload } from "@/lib/types";

type View = "assistant" | "orders";

const ASSISTANT = "ALXNDRA";

function Wordmark() {
  // Знак Complecta AI (монограмма «C» со срезом-стрелкой) + wordmark в Playfair.
  return (
    <span className="flex items-center gap-2.5 pr-1">
      <svg aria-hidden viewBox="0 0 224.88 225" className="h-[28px] w-[28px] text-(--ink)" fill="currentColor">
        <path d="M 123.429688 213.519531 C 67.636719 213.519531 22.25 168.203125 22.25 112.496094 C 22.25 56.796875 67.636719 11.480469 123.429688 11.480469 C 151.550781 11.480469 178.632812 23.308594 197.726562 43.929688 L 202.902344 49.515625 L 163.722656 85.691406 L 158.542969 80.101562 C 149.382812 70.210938 136.910156 64.761719 123.429688 64.761719 C 97.0625 64.761719 75.613281 86.179688 75.613281 112.496094 C 75.613281 126.738281 81.941406 140.140625 92.972656 149.265625 L 83.242188 160.988281 C 68.707031 148.957031 60.367188 131.285156 60.367188 112.496094 C 60.367188 77.78125 88.65625 49.539062 123.429688 49.539062 C 138.640625 49.539062 152.875 54.792969 164.234375 64.480469 L 181.105469 48.90625 C 165.386719 34.71875 144.761719 26.703125 123.429688 26.703125 C 76.046875 26.703125 37.496094 65.1875 37.496094 112.496094 C 37.496094 159.808594 76.046875 198.296875 123.429688 198.296875 C 141.519531 198.296875 158.832031 192.742188 173.492188 182.238281 C 177.417969 179.425781 181.140625 176.246094 184.5625 172.789062 L 195.410156 183.484375 C 191.386719 187.550781 187.003906 191.292969 182.378906 194.605469 C 165.117188 206.980469 144.734375 213.519531 123.429688 213.519531 Z" />
      </svg>
      <span className="brand-display text-[19px] font-semibold text-(--ink)">Complecta AI</span>
    </span>
  );
}

export default function StorefrontPage() {
  const session = useSession(api);
  const [view, setView] = useState<View>("assistant");
  const [cart, setCart] = useState<CartPayload | null>(null);
  // A staged checkout owns the panel's primary action until the cart changes again.
  const [checkoutStaged, setCheckoutStaged] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);

  const handleCartUpdate = useCallback((next: CartPayload) => {
    setCart(next);
    setCheckoutStaged(false);
  }, []);

  const onEvent = useCallback(
    (event: AgentEvent) => {
      if (event.type === "cart_update") handleCartUpdate(event.data.cart as CartPayload);
      else if (event.type === "ui" && event.data.component === "checkout") setCheckoutStaged(true);
    },
    [handleCartUpdate],
  );

  const chat = useAgentTurn(api, { ...session, unreachable: UNREACHABLE, onEvent });
  // A reply may have started a return, so orders re-read after each one.
  const { data: orders, failed: ordersFailed } = useResource(session.sessionId ? () => api.fetchOrders() : null, [session.sessionId, chat.completed]);

  useEffect(() => {
    if (session.sessionId) void api.fetchCart<CartPayload>().then((next) => next && setCart(next));
  }, [session.sessionId]);

  const late = orders?.filter((order) => order.status === "delayed").length ?? 0;
  const views: StoreView<View>[] = [
    { id: "assistant", label: "ALXNDRA", icon: "spark" },
    { id: "orders", label: "Orders", icon: "box", attention: late ? { count: late, label: `${late} delayed` } : null },
  ];
  const shopper = session.shopper ?? { name: "Guest" };
  const count = cart?.item_count ?? 0;

  return (
    <StoreShell
      brand={<Wordmark />}
      views={views}
      view={view}
      onViewChange={setView}
      chat={chat}
      api={api}
      assistantName={ASSISTANT}
      shopper={shopper}
      bag={{ label: "Cart", count, noun: "item", figure: count ? formatMoney(cart?.subtotal ?? 0, cart?.currency) : null }}
      panel={<CartPanel cart={cart} checkoutStaged={checkoutStaged} />}
      panelOpen={panelOpen}
      onPanelOpenChange={setPanelOpen}
      placeholder={view === "orders" ? "Ask about an order, a return, a delivery…" : "Ask about a product, a project, an order…"}
    >
      {/* The conversation stays mounted under the other view so its cards keep their state. */}
      <div className={view === "assistant" ? "h-full" : "hidden"}>
        <Chat chat={chat} onCartUpdate={handleCartUpdate} home={<HomeView shopperName={shopper.name} orders={orders} ordersFailed={ordersFailed} onSeeOrders={() => setView("orders")} />} />
      </div>
      {view === "orders" ? (
        <OrdersView
          orders={orders}
          failed={ordersFailed}
          nouns={NOUNS}
          subtitle={
            orders
              ? late
                ? `${plural(late, "order")} running late. Ask why, or ask about a return on anything delivered.`
                : `${plural(upcoming(orders).length, "order")} on the way. Ask about any of them, or about a return on anything delivered.`
              : undefined
          }
          thumb={(order) => <OrderThumb order={order} />}
        />
      ) : null}
    </StoreShell>
  );
}
