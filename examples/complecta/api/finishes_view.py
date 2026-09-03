# ``present_finishes``: образцы отделок предмета — сорта, семейства и КАЖДЫЙ ЦВЕТ с картинкой
# свотча (реш. Olexandra 2026-09-03: «а можем прям свотчи показывать?»). Модель называет
# товар и, при желании, слот; все данные — из книги материалов бренда через Complecta MCP.
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from commerce_common.presentation import EnrichmentContext, PresentationExtension

from .complecta_backend import ComplectaBackend


class FinishesPayload(BaseModel):
    product_id: str
    slot: str | None = Field(default=None, description="upholstery, wood, metal, stone … (omit for all)")
    note: str | None = Field(default=None, max_length=200, description="one line on what the customer asked for")


_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "product_id": {"type": "string"},
        "slot": {"type": "string", "description": "upholstery, wood, metal, stone … (omit for all)"},
        "note": {"type": "string", "maxLength": 200, "description": "one line on what the customer asked for"},
    },
    "required": ["product_id"],
    "additionalProperties": False,
}


def build_finishes_extension(backend: ComplectaBackend) -> PresentationExtension:
    async def _enrich(payload: FinishesPayload, context: EnrichmentContext) -> dict[str, Any]:
        del context
        args: dict[str, Any] = {"product_id": payload.product_id.split("#")[0]}
        if payload.slot:
            args["slot"] = payload.slot
        out = await backend._call("get_finishes", args)
        if out.get("error"):
            raise ValueError(f"{out['error']} — use a product_id from this session's search results.")
        if not out.get("slots"):
            raise ValueError(out.get("note") or "The price list gives no finish choice for this product.")
        # ужать до того, что рисуется: сорт → семейства → цвета (имя, код, тон, образец)
        slots = []
        for sl in out["slots"]:
            options = []
            for o in sl.get("options", []):
                fams = o.get("families")
                entry = {"key": o.get("key"), "label": o.get("label"), "kind": o.get("kind"),
                         "hex": o.get("hex"), "swatch": o.get("swatch"), "note": o.get("note")}
                if fams is not None:
                    entry["families"] = [{
                        "code": f.get("code"), "label": f.get("label") or f.get("code"), "material": f.get("material"),
                        "colors": [{"code": c.get("code"), "name": c.get("name"), "hex": c.get("hex"), "swatch": c.get("swatch")}
                                   for c in f.get("colors", [])],
                    } for f in fams]
                options.append(entry)
            slots.append({"slot": sl["slot"], "options": options})
        return {"product_id": out["product_id"], "title": out.get("title"), "brand": out.get("brand"),
                "default": out.get("default"), "slots": slots, "note": payload.note}

    return PresentationExtension(
        name="present_finishes",
        component="finishes",
        description=(
            "Show the finish samples of one product as swatches: every upholstery grade with its "
            "families and each colour's swatch image, and the wood, metal or stone options with "
            "their samples. Use it whenever the customer asks about colours, leather, fabric, "
            "materials or finishes, or before recommending a finish; pass a product_id from this "
            "session's results. Everything shown comes from the brand's materials book."
        ),
        input_schema=_INPUT_SCHEMA,
        payload_model=FinishesPayload,
        enrich=_enrich,
    )
