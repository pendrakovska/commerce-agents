// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

/** Complecta: furniture is made to order; no card checkout — a dealer quote closes the sale. */
export const STORE_POLICY = {
  returnsShort: "Made to order · dealer terms",
  returnsLine: "Pieces are made to order by the brand; lead times, delivery and returns follow the dealer's terms confirmed in the quote.",
  freeShippingThreshold: 49,
  standardShippingEta: "lead time confirmed by the dealer",
} as const;
