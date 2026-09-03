// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

"use client";

import { useEffect, useRef, useState } from "react";

// ГОЛОСОВОЙ ВВОД (реш. Olexandra 2026-09-03: «прикрутить голосовой ввод в строку промпта»).
// Web Speech API браузера — без сервера и без ключей, как у комнатного копайлота Complecta.
// Язык — язык браузера (uk/ru/en/it…); распознанное ложится В ПОЛЕ, а не отправляется само:
// человек видит текст и правит перед отправкой. В браузерах без API кнопки нет (Firefox).
type Recognition = { lang: string; interimResults: boolean; maxAlternatives: number; start(): void; stop(): void;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null; onend: (() => void) | null; onerror: (() => void) | null };
function speechRecognition(): (new () => Recognition) | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}
function MicButton({ onText, disabled, size }: { onText: (t: string) => void; disabled: boolean; size: string }) {
  const [listening, setListening] = useState(false);
  const [SR, setSR] = useState<(new () => Recognition) | null>(null);
  const recRef = useRef<Recognition | null>(null);
  // на сервере API нет, на клиенте есть — решать только после монтирования, иначе
  // разметка не сходится (React #418) и обработчики страницы не подключаются
  // конструктор — через функцию-обновитель: иначе React вызовет класс как updater
  useEffect(() => { setSR(() => speechRecognition()); }, []);
  if (!SR) return null;
  const toggle = () => {
    if (listening) { recRef.current?.stop(); setListening(false); return; }
    const r = new SR();
    r.lang = typeof navigator !== "undefined" && navigator.language ? navigator.language : "en-US";
    r.interimResults = false; r.maxAlternatives = 1;
    r.onresult = (e) => { const t = e.results?.[e.results.length - 1]?.[0]?.transcript?.trim(); if (t) onText(t); };
    r.onend = () => setListening(false);
    r.onerror = () => setListening(false);
    recRef.current = r; setListening(true);
    try { r.start(); } catch { setListening(false); }
  };
  return (
    <button type="button" onClick={toggle} disabled={disabled} aria-pressed={listening}
      aria-label={listening ? "Stop listening" : "Speak your request"}
      title={listening ? "Listening… click to stop" : "Speak your request (browser speech recognition)"}
      className={`grid shrink-0 place-items-center rounded-[11px] border transition disabled:opacity-35 ${size} ${
        listening ? "border-(--accent) bg-(--accent-soft) text-(--accent-ink)" : "border-(--line-strong) bg-(--card) text-(--ink-soft) hover:text-(--ink)"}`}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <rect x="9" y="3" width="6" height="11" rx="3" /><path d="M5 11a7 7 0 0 0 14 0" /><path d="M12 18v3" /><path d="M8 21h8" />
      </svg>
    </button>
  );
}
import { Icon } from "./icons";

export interface Prefill {
  text: string;
  /** Changes on every request so the same text can be offered twice. */
  nonce: number;
}

const VARIANTS = {
  /** The storefront's composer under the page: one roomy field with the send arrow inside it. */
  dock: {
    form: "items-center gap-2 rounded-[16px] border border-(--line-strong) bg-(--card) py-1.5 pl-4 pr-1.5 shadow-(--shadow) transition-colors focus-within:border-(--accent)",
    input: "bg-transparent py-1.5 text-[16px]",
    button: "h-9 w-9 rounded-[11px]",
  },
  /** The portal rail: the same field, compact. */
  field: {
    form: "items-center gap-1.5 rounded-[14px] border border-(--line-strong) bg-(--card) py-[5px] pl-3.5 pr-[5px] shadow-(--shadow-sm) transition-colors focus-within:border-(--accent)",
    // 16px below lg so touch browsers do not zoom on focus.
    input: "bg-transparent py-1.5 text-[16px] lg:text-[14.5px]",
    button: "h-8 w-8 rounded-[10px]",
  },
};

/** A prefill only fills the draft. screenshot_tour.py waits on the "Working…" placeholder. */
export function Composer({
  send,
  ready,
  busy,
  label,
  placeholder,
  prefill,
  variant = "dock",
  className = "",
}: {
  send: (text: string) => void;
  ready: boolean;
  busy: boolean;
  label: string;
  placeholder: string;
  prefill?: Prefill | null;
  variant?: keyof typeof VARIANTS;
  className?: string;
}) {
  const [draft, setDraft] = useState("");
  const boxRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!prefill) return;
    setDraft(prefill.text);
    boxRef.current?.focus();
  }, [prefill]);

  const submit = () => {
    if (!draft.trim() || busy || !ready) return;
    send(draft);
    setDraft("");
  };

  return (
    <form
      className={`flex ${VARIANTS[variant].form} ${className}`}
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <textarea
        ref={boxRef}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
            event.preventDefault();
            submit();
          }
        }}
        rows={1}
        aria-label={label}
        placeholder={busy ? "Working…" : placeholder}
        className={`max-h-40 min-w-0 flex-1 resize-none text-(--ink) outline-none transition placeholder:text-(--ink-soft)/70 ${VARIANTS[variant].input}`}
      />
      <MicButton disabled={busy || !ready} size={VARIANTS[variant].button}
        onText={(t) => { setDraft((d) => (d.trim() ? `${d.trim()} ${t}` : t)); boxRef.current?.focus(); }} />
      <button
        type="submit"
        disabled={busy || !ready || !draft.trim()}
        aria-label="Send"
        className={`grid shrink-0 place-items-center bg-(--ink) text-(--surface) transition hover:brightness-110 disabled:opacity-35 ${VARIANTS[variant].button}`}
      >
        <Icon name="arrow-up" size={16} />
      </button>
    </form>
  );
}
