# ALXNDRA — форк Claude Commerce Agents под каталог Complecta

**Состояние на 3 сентября 2026.** Это форк эталона `anthropics/commerce-agents`
(его README ниже по репозиторию — про эталон). Наше — вертикаль `examples/complecta`:
шопинг-агент ALXNDRA, который ходит в **MCP-сервер каталога Complecta** и ничего не знает
о ценах. Основное приложение и MCP живут в репозитории
github.com/pendrakovska/Complecta-commerce-alxndra (там `README.md`).

## 1. Что где

| Часть | Путь | Проект Vercel | Прод |
|---|---|---|---|
| Демо-API (Python, FastAPI-функция) | `api/index.py` → `examples/complecta/api/main.py` | `alxndra-api` | https://alxndra-api.vercel.app |
| Витрина (Next.js) | `examples/complecta/storefront-web` | `alxndra` (rootDirectory `complecta/storefront-web`, корень проекта — `examples/`) | https://alxndra.vercel.app |

Файлы вертикали:

- `examples/complecta/api/complecta_backend.py` — `StorefrontBackend` поверх MCP: семейства/варианты, отделки, паспорт DPP; при `price: null` от MCP — 0 и текст «on request», цифру не выдумывает.
- `examples/complecta/api/finishes_view.py` — презентационный инструмент `present_finishes` (свотчи, `kind`).
- `examples/complecta/api/sessions_neon.py` — хранилище сессий в Neon (`alxndra_sessions`, `alxndra_messages`), включается при `DATABASE_URL`.
- `examples/complecta/api/main.py`, `agent_config.py` — сборка агента: скиллы, презентационные инструменты, прогрев в фоне.
- `examples/complecta/skills/*/SKILL.md` — навыки; `interior-design` — наш, там же правило «не называть цены».
- `examples/complecta/storefront-web` — витрина в дизайн-системе Complecta: карточки с попапом и ссылкой в студию, свотчи, чекаут как запрос дилеру, голосовой ввод (`examples/web-shared/Composer.tsx`), embed-режим `?embed=1` с конвертами родителю.
- `demo_common/host.py` — общий хост демо; разрешённые хосты/origin: `ALLOWED_CODES`.

## 2. Локально

Python 3.12 (`.venv`), Node 20+.

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements-local.txt
cp .env.example .env            # заполнить: см. §3
.venv/bin/python scripts/run_demo.py complecta   # API :8004, витрина :3004
.venv/bin/python -m pytest                        # тесты
```

`requirements.txt` — только сторонние пины для Vercel, семь пакетов репозитория подключаются
через `sys.path` в `api/index.py`. Для разработки — `requirements-local.txt`.

## 3. Переменные окружения (имена, без значений)

| Имя | Где | Зачем |
|---|---|---|
| `ANTHROPIC_API_KEY` | alxndra-api | модель агента |
| `COMPLECTA_MCP_URL` | alxndra-api | `https://complecta-commerce.vercel.app/api/mcp` |
| `COMPLECTA_ACCESS_KEY` | alxndra-api | **гостевой** ключ `alxndra-demo` из `DOCS_KEYS` основного проекта — MCP отдаёт всё, кроме цен |
| `COMPLECTA_APP_URL` | alxndra-api | адрес приложения для ссылок в студию |
| `DATABASE_URL` | alxndra-api | Neon, сессии агента |
| `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_COMPLECTA_APP_URL`, `NEXT_PUBLIC_HOST_ORIGINS` | сборка витрины | адрес API, приложения, origin-ы родителя для embed |

Хозяйский ключ основного приложения сюда не попадает никогда: демо публичное, а цены — не публичные данные.
Значения берутся через `npx vercel env pull` после добавления в проект, не через почту и мессенджеры.

## 4. Деплой — только из терминала

Автосборка из GitHub отключена (`vercel.json → git.deploymentEnabled.main=false`).

API, из корня форка:

```bash
npx vercel deploy --prod --yes --archive=tgz
```

Витрина, из `examples/` (значения `NEXT_PUBLIC_*` передаются в окружении сборки, потому что
`vercel pull` маскирует их как `[SENSITIVE]`):

```bash
cd examples && NEXT_PUBLIC_API_URL=https://alxndra-api.vercel.app NEXT_PUBLIC_COMPLECTA_APP_URL=https://complecta-commerce.vercel.app npx vercel build --prod && npx vercel deploy --prebuilt --prod --yes
```

Крон `*/5` на `/api/health` держит функцию тёплой; холодный старт был причиной «агент молчит на первый вопрос».

## 5. Правила

- Агент **не называет цены, НДС и доставку** — только «у авторизованного дилера». Это серверная политика MCP, витрина её не обходит.
- Нет данных — нет цифры. `null` с причиной, не «примерно».
- Строки интерфейса — английские, комментарии в коде — русские.
- Код и данные Complecta — только в этих репозиториях и на этом Vercel.
