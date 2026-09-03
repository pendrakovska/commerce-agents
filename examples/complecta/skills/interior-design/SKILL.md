---
name: interior-design
description: Assembling a furniture set for a room (living room, bedroom, dining, office) — splitting the budget by piece, checking fit and composition, and saying plainly what the catalog cannot confirm. Use whenever the request names a room, several pieces, or a budget for a space.
---

# Furnishing a room as one set

The customer buys a room, not a chair. Judge pieces together and split money before choosing.

## Split the budget first

Weights are how money is spent across real projects (engine calibrated on the MOHD portfolio); they are relative, so drop the pieces the room does not need and share the rest proportionally.

| piece | weight | piece | weight |
|---|---|---|---|
| sofa | 36 | bed | 39 |
| corner sofa | 42 | nightstand (each) | 6 |
| armchair | 12 | wardrobe | 15 |
| coffee table | 8 | bench | 7 |
| rug | 9 | dining table | 34 |
| sideboard | 13 | dining chair (each) | 5 |
| pouf | 4.5 | stool (each) | 3 |
| console | 7 | desk | 14 |
| shelf / bookcase | 8 / 10 | floor lamp | 3 |
| TV unit | 11 | pendant | 3 |
| mirror | 4 | table lamp / sconce | 1.25 / 1.5 |

Cap per piece = budget × weight / sum of weights of the pieces in the set. Search each piece with `max_price` at its cap (round up by ~15% when the cap is tight); a piece over its cap is a decision to name, not a mistake to hide — say what it displaces.

## Composition rules the photographs must pass

- One statement piece per room; the rest supports it.
- Silhouettes talk to each other: a blocky sofa wants a table with visual weight, not delicate turned legs.
- Two or three textures, not one and not five (leather + wood + stone or fabric).
- Scale agrees: nothing monumental beside something weightless.
- A set that reads as a showroom floor is not a room — vary heights and materials.

## Fit and circulation (verified norms)

- A passage for one person needs 815 mm minimum, 915 mm ideal (ADA 403.5.1); two people passing — 1525 mm (ADA 403.5.3).
- Behind a seated diner with no traffic: 813 mm; where people walk past: 1118 mm (NKBA Guideline 8).
- Beside a bed: 600 mm minimum, 750 mm ideal (Neufert).
- A piece longer than the room's shorter wall does not fit; say so before proposing it.
- Sofa-to-coffee-table distance and TV viewing distance are NOT verified norms in this catalog — do not quote numbers for them; recommend a layout check in the Complecta room planner instead.

## Finishes and colours

The brand book has grades, families and actual colours, and the catalog record carries them: `get_product_details` returns `specs` rows named `colours · <grade> · <family>` with the colour names, and `present_disclosure` renders the full box (grade → family → every colour with its swatch). When the customer asks about colours, leather, fabric or materials: call `present_finishes` for that product — it shows every grade, family and colour as swatch images — and name the colours from it (`present_disclosure` gives the same as a text box) — never say the catalog does not list colours when those rows exist. If a grade truly has no samples in the book, say exactly that.

## Prices in this storefront

A price of 0 with the attribute "on request from an authorised dealer" means the price is not disclosed here — never state, estimate or compare a number for it, and do not call anything cheaper or more expensive. Say that the dealer's quote gives the price and VAT, and offer to collect the set for that quote. Budget splitting then works in shares, not euros.

## What the catalog cannot confirm

Prices are brand list prices; stock and lead times are not published — say "made to order, lead time from the dealer". Never invent a finish, a size or a price that `get_product_details` did not return; when a requested material is not listed, say so and offer what is listed.

## Show it

Use `present_plan` with one step per piece (the budget cap in the detail line and the pick attached). Order steps by weight. Offer the Complecta planner for placement and a render of the set in the actual room.
