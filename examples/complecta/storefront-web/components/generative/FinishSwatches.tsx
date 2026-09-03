"use client";
// Образцы отделок: сорт → семейство → цвет картинкой свотча (или тоном, если картинки нет).
// Данные — книга материалов бренда через Complecta MCP; ничего не дорисовываем.
import type { FinishesPayload } from "@/lib/types";
import { studioHref } from "../ProductTile";

function Swatch({ hex, swatch, title }: { hex?: string | null; swatch?: string | null; title: string }) {
  return (
    <span
      title={title}
      className="inline-block h-9 w-9 overflow-hidden rounded-md border border-(--line) bg-(--well) align-top"
      style={hex && !swatch ? { background: hex } : undefined}
    >
      {swatch ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={swatch} alt={title} loading="lazy" className="h-full w-full object-cover" />
      ) : null}
    </span>
  );
}

export default function FinishSwatches({ payload, compact = false }: { payload: FinishesPayload; compact?: boolean }) {
  const slots = payload.slots ?? [];
  if (!slots.length) return null;
  return (
    <div className={`rounded-xl border border-(--line) bg-(--card) ${compact ? "p-3" : "p-4"} shadow-(--shadow-sm)`}>
      {!compact && (
        <div className="mb-2 flex items-baseline justify-between gap-3">
          <div className="text-[14px] font-semibold text-(--ink)">
            {payload.brand} {payload.title} — finishes
            {payload.default ? <span className="ml-2 text-[12px] font-normal text-(--ink-soft)">default: {payload.default}</span> : null}
          </div>
          <a href={studioHref({ product_id: payload.product_id })} target="_blank" rel="noreferrer"
             className="text-[12px] text-(--accent) underline-offset-2 hover:underline">open in Complecta studio</a>
        </div>
      )}
      {payload.note ? <p className="mb-2 text-[12.5px] text-(--ink-soft)">{payload.note}</p> : null}
      <div className="flex flex-col gap-3">
        {slots.map((sl) => (
          <div key={sl.slot}>
            <div className="mb-1 text-[11px] uppercase tracking-[.08em] text-(--ink-faint)">{sl.slot}</div>
            <div className="flex flex-col gap-2">
              {sl.options.map((o) => (
                <div key={o.key}>
                  <div className="flex flex-wrap items-center gap-2 text-[13px] text-(--ink)">
                    <span className="font-medium">{o.label}</span>
                    {o.kind ? <span className="text-(--ink-soft)">· {o.kind}</span> : null}
                    {!o.families && (o.swatch || o.hex) ? <Swatch hex={o.hex} swatch={o.swatch} title={o.label} /> : null}
                    {o.note ? <span className="text-[12px] text-(--warn)">— {o.note}</span> : null}
                  </div>
                  {o.families?.map((f) => (
                    <div key={f.code} className="mt-1 pl-2">
                      <div className="text-[12px] text-(--ink-soft)">
                        {f.label}{f.material ? <span className="text-(--ink-faint)"> · {f.material}</span> : null}
                        <span className="text-(--ink-faint)"> · {f.colors.length} colours</span>
                      </div>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {f.colors.slice(0, compact ? 16 : 60).map((c) => (
                          <Swatch key={c.code ?? c.name} hex={c.hex} swatch={c.swatch} title={[c.name, c.code].filter(Boolean).join(" · ")} />
                        ))}
                        {f.colors.length > (compact ? 16 : 60) ? (
                          <span className="self-center text-[11px] text-(--ink-faint)">+{f.colors.length - (compact ? 16 : 60)}</span>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
