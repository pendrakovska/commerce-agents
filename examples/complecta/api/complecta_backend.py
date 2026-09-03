# Complecta — StorefrontBackend over the Complecta catalog MCP (complecta-commerce.vercel.app/api/mcp).
# Реш. Olexandra 2026-09-03: «форкни репо и подставь наш MCP». Агент думает, каталог даёт факты:
# цены только из прайсов брендов, ничего не выдумываем. Что каталог не знает (остатки, сроки,
# заказы) — здесь сказано словами, а не нулями (docs/backends.md: «figures your platform
# cannot supply»).
from __future__ import annotations

import os
from typing import Any

import httpx
from demo_common.storefront_fixtures import SessionCarts, cart_line

from shopping_agent import (
    Cart,
    CheckoutHandoff,
    Disclosure,
    DisclosureRow,
    FulfillmentOption,
    Order,
    Policy,
    Product,
    ProductDetails,
    SearchFilters,
    ShoppingSessionContext,
    StorefrontBackend,
    Unavailable,
    UserPreferences,
)

# Адреса читаются В МОМЕНТ СОЗДАНИЯ бэкенда, а не при импорте: main.py грузит .env
# вертикали после импорта модуля, и константа на уровне модуля видела бы только дефолт.
DEFAULT_MCP_URL = "https://complecta-commerce.vercel.app/api/mcp"
DEFAULT_APP_URL = "https://complecta-commerce.vercel.app"
AVAILABILITY = "made to order — the brand does not publish stock; lead time is confirmed by the dealer"


class ComplectaBackend(StorefrontBackend):
    """Catalog, prices and variants come from the Complecta MCP; the cart is per-session state;
    checkout hands off to a dealer quote in the Complecta app."""

    store_name = "Complecta"

    def __init__(self, mcp_url: str | None = None, access_key: str | None = None) -> None:
        self._url = mcp_url or os.environ.get("COMPLECTA_MCP_URL", DEFAULT_MCP_URL)
        self._app_url = os.environ.get("COMPLECTA_APP_URL", DEFAULT_APP_URL)
        self._key = access_key or os.environ.get("COMPLECTA_ACCESS_KEY", "")
        self._carts = SessionCarts()
        self._seen: dict[str, ProductDetails] = {}  # product_id → details (families and variants)
        self._rpc_id = 0
        # Хост показывает витрину из ``products`` (главная страница, /api/health): у мока это
        # весь каталог из фикстур, у нас — прогретая выборка семей по основным категориям.
        # Заполняется при старте синхронно (MCP отвечает за ~200 мс на категорию).
        self.products: dict[str, ProductDetails] = {}
        # прогрев в фоне: холодный старт serverless-функции не должен ждать девять
        # обращений к MCP — сессия и чат отвечают сразу, витрина главной догружается
        import threading
        threading.Thread(target=self._warm, daemon=True).start()

    WARM_CATEGORIES = ("sofa", "armchair", "coffee-table", "dining-table", "chair", "bed", "sideboard", "pendant", "floor-lamp")

    def _warm(self) -> None:
        if not self._key:
            return
        for cat in self.WARM_CATEGORIES:
            try:
                out = self._call_sync("search_products", {"category": cat, "limit": 6})
            except Exception:  # витрина без прогрева — не повод не подняться
                continue
            for f in out.get("products", []):
                rec = self._family(f)
                if rec is not None:
                    self.products[rec.product_id] = rec

    # ------------------------------------------------------------------ MCP
    async def _call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self._key:
            raise RuntimeError("COMPLECTA_ACCESS_KEY is not set — the Complecta MCP needs the access key")
        self._rpc_id += 1
        payload = {"jsonrpc": "2.0", "id": self._rpc_id, "method": "tools/call",
                   "params": {"name": tool, "arguments": arguments}}
        headers = {"content-type": "application/json", "accept": "application/json, text/event-stream",
                   "x-access-key": self._key}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(self._url, json=payload, headers=headers)
        r.raise_for_status()
        body = r.json()
        if "error" in body:
            raise RuntimeError(f"MCP error: {body['error']}")
        result = body.get("result") or {}
        if result.get("isError"):
            raise RuntimeError(result.get("content", [{}])[0].get("text", "tool error"))
        return result.get("structuredContent") or {}

    # ------------------------------------------------------------------ mapping
    @staticmethod
    def _attributes(f: dict[str, Any]) -> dict[str, str]:
        out: dict[str, str] = {"availability": AVAILABILITY}
        d = f.get("dims_cm") or {}
        if d.get("width"):
            out["dimensions"] = f"{d.get('width')}×{d.get('depth')}×{d.get('height')} cm (W×D×H)"
        if f.get("has_3d"):
            out["3d_model"] = "yes — can be placed in a room render"
        if f.get("finish_default"):
            out["default_finish"] = str(f["finish_default"])
        return out

    def _image(self, url: str | None) -> str | None:
        """Снимки каталога лежат на домене Complecta; относительный путь витрина
        localhost не найдёт — делаем абсолютным."""
        if not url:
            return None
        if url.startswith("/"):
            return self._app_url.rstrip("/") + url
        return url

    ON_REQUEST = "on request from an authorised dealer"

    def _family(self, f: dict[str, Any]) -> ProductDetails | None:
        """Family record. Цена может отсутствовать по двум причинам: бренд не прислал прайс,
        или ключ демо не имеет права видеть цены (реш. Olexandra 2026-09-03: прайсы в сеть не
        утекают). В обоих случаях предмет ОСТАЁТСЯ в витрине: price = 0 с пометкой «по
        запросу у дилера» — контракт требует число, а ноль с пометкой честнее пропажи."""
        priced = f.get("price") is not None
        attrs = self._attributes(f)
        if not priced:
            attrs["price"] = f.get("price_note") or self.ON_REQUEST
        rec = ProductDetails(
            product_id=f["product_id"], title=f["title"], brand=f.get("brand"),
            price=float(f["price"]) if priced else 0.0, currency="EUR", image_url=self._image(f.get("image")),
            category=f.get("category"), labels=(["3D model"] if f.get("has_3d") else []) + ([] if priced else ["price on request"]),
            attributes=attrs, in_stock=True,
            short_description=f"{f.get('brand')} · {f.get('category')}",
            options={k: [str(x) for x in v] for k, v in (f.get("options") or {}).items()},
            specs={k: v for k, v in self._attributes(f).items() if k != "availability"},
        )
        self._seen[rec.product_id] = rec
        return rec

    def _variant(self, family: ProductDetails, v: dict[str, Any]) -> ProductDetails | None:
        priced = v.get("price") is not None
        if not priced and family.price > 0:
            return None  # у ценового каталога этот размер × отделка не выпускается («--»)
        rec = ProductDetails(
            product_id=v["product_id"], title=family.title, brand=family.brand,
            price=float(v["price"]) if priced else 0.0, currency="EUR", image_url=family.image_url,
            category=family.category, labels=list(family.labels),
            attributes=self._attributes({**v, "has_3d": v.get("has_3d")}),
            in_stock=True, option_values={k: str(x) for k, x in (v.get("option_values") or {}).items()},
            variant_of=family.product_id,
        )
        self._seen[rec.product_id] = rec
        return rec

    # ------------------------------------------------------------------ StorefrontBackend
    async def search_products(self, session: ShoppingSessionContext, query: str,
                              filters: SearchFilters | None = None, limit: int = 8) -> list[Product]:
        del session
        args: dict[str, Any] = {"query": query, "limit": max(limit * 2, 8)}
        if filters:
            if filters.category:
                args["category"] = filters.category
            if filters.max_price is not None:
                args["maxPriceEur"] = filters.max_price
            for k, v in (filters.attributes or {}).items():
                if k in ("brand",):
                    args["brand"] = v
                if k in ("max_width_cm", "maxWidthCm"):
                    args["maxWidthCm"] = float(v)
        out = await self._call("search_products", args)
        families = [self._family(f) for f in out.get("products", [])]
        listed = [f for f in families if f is not None]
        for f in listed:
            self.products.setdefault(f.product_id, f)
        if filters and filters.min_price is not None:
            listed = [f for f in listed if f.price == 0 or f.price >= filters.min_price]
        if filters and filters.sort == "price_asc":
            listed.sort(key=lambda p: p.price)
        elif filters and filters.sort == "price_desc":
            listed.sort(key=lambda p: -p.price)
        return [Product.model_validate(p.model_dump(exclude={"variants", "specs", "long_description", "review_highlights"}))
                for p in listed[:limit]]

    async def get_product_details(self, session: ShoppingSessionContext, product_id: str) -> ProductDetails | None:
        del session
        family_id = product_id.split("#")[0]
        out = await self._call("get_product", {"product_id": family_id})
        if out.get("error"):
            return None
        family = self._family(out)
        if family is None:
            return None
        variants = [v for v in (self._variant(family, v) for v in out.get("variants", [])) if v is not None]
        family.variants = [Product.model_validate(v.model_dump(exclude={"variants", "specs", "long_description", "review_highlights"}))
                           for v in variants]
        note = out.get("finish_note")
        try:
            fin = await self._call("get_finishes", {"product_id": family_id})
            for sl in fin.get("slots", []):
                parts = []
                for o in sl.get("options", []):
                    fams = o.get("families")
                    if fams:
                        parts.append(f"{o.get('label')} ({', '.join(f.get('label') or f.get('code') for f in fams)}: "
                                     f"{sum(len(f.get('colors', [])) for f in fams)} colours)")
                        # ИМЕНА ЦВЕТОВ — В КАРТОЧКЕ, а не только в паспорте: агент отвечал
                        # «каталог не называет цвета», пока имена жили в отдельном шаге.
                        for f in fams:
                            names = [c.get("name") or c.get("code") for c in f.get("colors", []) if c.get("name") or c.get("code")]
                            if names:
                                shown = ", ".join(dict.fromkeys(names))
                                family.specs[f"colours · {o.get('label')} · {f.get('label') or f.get('code')}"] = (
                                    shown[:400] + (" …" if len(shown) > 400 else ""))
                    else:
                        parts.append(str(o.get("label")))
                family.specs[f"finishes · {sl['slot']}"] = "; ".join(parts) or "—"
        except Exception:
            family.specs["finishes"] = "see present_disclosure"
        family.long_description = (
            f"{family.brand} {family.title}: list price from the brand price list, EUR. "
            + (f"{len(variants)} priced size × finish variants. " if variants else "")
            + (f"Note: {note}. " if note else "")
            + f"Availability: {AVAILABILITY}."
        )
        if product_id != family_id:
            return self._seen.get(product_id)
        return family

    async def get_cart(self, session: ShoppingSessionContext) -> Cart:
        cart = self._carts.cart(session.session_id)
        cart.currency = "EUR"
        return cart

    async def add_to_cart(self, session: ShoppingSessionContext, product_id: str, quantity: int) -> Cart:
        product = self._seen.get(product_id)
        if product is None:
            await self.get_product_details(session, product_id)
            product = self._seen.get(product_id)
        if product is None or product.has_options:
            raise KeyError(product_id)  # a family or an unknown id — the executor gates this
        existing = self._carts.lines(session.session_id).get(product_id)
        quantity += existing.quantity if existing else 0
        cart = self._carts.put(session.session_id, product, quantity)
        cart.currency = "EUR"
        return cart

    async def update_cart_item(self, session: ShoppingSessionContext, product_id: str, quantity: int) -> Cart:
        cart = self._carts.set_quantity(session.session_id, product_id, quantity)
        cart.currency = "EUR"
        return cart

    async def remove_from_cart(self, session: ShoppingSessionContext, product_id: str) -> Cart:
        cart = self._carts.remove(session.session_id, product_id)
        cart.currency = "EUR"
        return cart

    async def get_preferences(self, session: ShoppingSessionContext) -> UserPreferences:
        return UserPreferences(user_id=session.user_id, preferences={"currency": "EUR"})

    async def checkout_handoff(self, session: ShoppingSessionContext, cart: Cart) -> list[CheckoutHandoff]:
        # No card checkout: furniture is sold through dealers on a quote. The cart hands off
        # to the Complecta app, where the set becomes a specification and a dealer quote.
        del session, cart
        return [CheckoutHandoff(url=self._app_url, label="Request a dealer quote in Complecta")]

    async def get_account_context(self, session: ShoppingSessionContext) -> dict[str, Any] | None:
        del session
        return None

    async def get_orders(self, session: ShoppingSessionContext, limit: int = 5) -> list[Order]:
        del session, limit
        return []  # orders live with the dealer; the catalog holds none

    async def get_order(self, session: ShoppingSessionContext, order_id: str) -> Order | None:
        del session, order_id
        return None

    async def search_policies(self, session: ShoppingSessionContext, query: str) -> list[Policy]:
        del session
        out = await self._call("catalog_limitations", {})
        rows = out.get("limitations", [])
        gaps = "; ".join(f"{r.get('source')}: {r.get('note')}" for r in rows)
        policies = [
            Policy(policy_id="pricing", title="Prices", category="pricing",
                   content="Every price is the brand's list price in EUR taken from its current price list. "
                           "Dealer discounts and delivery are quoted by the dealer."),
            Policy(policy_id="availability", title="Availability and lead times", category="delivery",
                   content=f"Pieces are made to order. {AVAILABILITY}."),
            Policy(policy_id="catalog-gaps", title="What the catalog cannot tell", category="catalog",
                   content=gaps or "No known gaps."),
        ]
        q = query.lower()
        hits = [p for p in policies if any(w in (p.title + p.content).lower() for w in q.split())]
        return hits or policies

    async def get_disclosure(self, session: ShoppingSessionContext, product_id: str) -> Disclosure | None:
        """Паспорт отделок: сорта, семейства и КОНКРЕТНЫЕ ЦВЕТА из книги материалов
        бренда (реш. Olexandra 2026-09-03: «всё об отделках»). Ничего не выдумано —
        чего нет в книге, того нет в строках, и это сказано."""
        del session
        family_id = product_id.split("#")[0]
        out = await self._call("get_finishes", {"product_id": family_id})
        if out.get("error"):
            return None
        rows = []
        for sl in out.get("slots", []):
            for o in sl.get("options", []):
                fams = o.get("families")
                if fams is None:
                    rows.append(DisclosureRow(label=f"{sl['slot']} · {o.get('label')}",
                                              value=o.get("hex") or "sample on request",
                                              note="swatch: " + o["swatch"] if o.get("swatch") else None))
                    continue
                if not fams:
                    rows.append(DisclosureRow(label=f"{sl['slot']} · {o.get('label')}", value="grade priced, no colour samples in the brand book",
                                              note=o.get("note")))
                    continue
                for f in fams:
                    names = [c.get("name") or c.get("code") for c in f.get("colors", []) if c.get("name") or c.get("code")]
                    rows.append(DisclosureRow(
                        label=f"{sl['slot']} · {o.get('label')} · {f.get('label')}",
                        value=", ".join(names[:24]) + (f" … (+{len(names) - 24})" if len(names) > 24 else "") or "colours on request",
                        note=f"{len(names)} colours" + (f" · {f['material']}" if f.get("material") else ""),
                    ))
        if not rows:
            rows.append(DisclosureRow(label="finishes", value=out.get("note") or "no finish choice in the price list"))
        return Disclosure(title=f"{out.get('brand')} {out.get('title')} — finishes and colours", product_id=family_id,
                          rows=rows, sources=["brand materials book (Complecta catalog)"],
                          footnotes=["Default finish: " + str(out.get("default"))] if out.get("default") else [])

    async def get_fulfillment_options(self, session: ShoppingSessionContext, product_ids: list[str]) -> list[FulfillmentOption]:
        del session, product_ids
        return []  # delivery is arranged by the dealer; no figure to show

    # ------------------------------------------------------------------ host protocol (sync)
    def _call_sync(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Синхронный вызов MCP для хостовых маршрутов (страница товара, кнопка «в
        корзину»), которым протокол DemoStorefront даёт только sync product()."""
        if not self._key:
            raise RuntimeError("COMPLECTA_ACCESS_KEY is not set")
        self._rpc_id += 1
        payload = {"jsonrpc": "2.0", "id": self._rpc_id, "method": "tools/call",
                   "params": {"name": tool, "arguments": arguments}}
        headers = {"content-type": "application/json", "accept": "application/json, text/event-stream",
                   "x-access-key": self._key}
        r = httpx.post(self._url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        result = r.json().get("result") or {}
        return result.get("structuredContent") or {}

    def product(self, product_id: str) -> ProductDetails | None:
        """Sync lookup: cache first, then the MCP. Variants resolve through their family."""
        if product_id in self._seen:
            return self._seen[product_id]
        family_id = product_id.split("#")[0]
        out = self._call_sync("get_product", {"product_id": family_id})
        if out.get("error"):
            return None
        family = self._family(out)
        if family is None:
            return None
        variants = [v for v in (self._variant(family, v) for v in out.get("variants", [])) if v is not None]
        family.variants = [Product.model_validate(v.model_dump(exclude={"variants", "specs", "long_description", "review_highlights"}))
                           for v in variants]
        return self._seen.get(product_id)

    def reset_session(self, session_id: str) -> None:
        self._carts.reset(session_id)
