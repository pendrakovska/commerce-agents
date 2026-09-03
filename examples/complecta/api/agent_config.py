# Complecta shopping agent config — brand voice for the furniture assistant.
from __future__ import annotations

from shopping_agent import ShoppingAgentConfig


def build_shopping_config() -> ShoppingAgentConfig:
    return ShoppingAgentConfig(
        brand_name="Complecta",
        assistant_name="ALXNDRA",
        brand_voice="an interior-design consultant: precise about dimensions, materials and list prices; "
                    "never invents a product, a price or a lead time; says plainly when the catalog does not know",
    )
