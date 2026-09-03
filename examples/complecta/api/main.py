"""Complecta example API: the Complecta furniture catalog (17 Italian brands, list prices,
size × finish variants) served to the shopping agent through the Complecta MCP.

    uvicorn complecta.api.main:app --app-dir examples --reload --port 8004

Environment: ANTHROPIC_API_KEY (agent), COMPLECTA_ACCESS_KEY (MCP access key),
optional COMPLECTA_MCP_URL / COMPLECTA_APP_URL.
"""
from __future__ import annotations

from pathlib import Path

from commerce_common.memory import InMemoryMemoryStore
from demo_common import REPO_ROOT, CartAddRequest, MemorySeeder, build_storefront_host, load_demo_env
from shopping_agent import ProductDetails
from shopping_agent_runtime import ShoppingAgent

from .agent_config import build_shopping_config
from .complecta_backend import ComplectaBackend
from .finishes_view import build_finishes_extension

EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
load_demo_env(EXAMPLE_ROOT)

backend = ComplectaBackend()
agent = ShoppingAgent(
    backend=backend,
    # свои скиллы: эталонные пять + interior-design (правила комплекта, доли бюджета, нормы)
    skills_dir=EXAMPLE_ROOT / "skills",
    config=build_shopping_config(),
    memory_store=InMemoryMemoryStore(),
    # свотчи отделок в чате: present_finishes (сорт → семейство → цвет с образцом)
    extra_presentation_tools=[build_finishes_extension(backend)],
)


def product_detail(product: ProductDetails) -> dict:
    """Карточка в витрине несёт и образцы отделок — свотчи под описанием."""
    data = product.model_dump()
    try:
        fin = backend._call_sync("get_finishes", {"product_id": product.product_id.split("#")[0]})
        data["finishes"] = fin if fin.get("slots") else None
    except Exception:
        data["finishes"] = None
    return data


host = build_storefront_host(
    title="Complecta demo API",
    example_root=EXAMPLE_ROOT,
    backend=backend,
    agent=agent,
    # seed-файла нет: у витрины каталога нет вымышленных фактов о покупателе
    memory_seeder=MemorySeeder(EXAMPLE_ROOT / "data" / "memory-seed.json"),
    product_detail=product_detail,
)
app = host.app


@app.post("/api/cart/add")
async def cart_add(request: CartAddRequest, record: host.CurrentSession) -> dict:
    return await host.direct_add(
        record, request,
        note="Customer tapped the add-to-cart button on {title} ({product_id}), quantity {quantity}.",
    )
