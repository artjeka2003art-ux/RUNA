# CLAUDE CODE TASK — DOCUMENT CANDIDATE SELECTION / ROUTING V1

## Задача

Сделай узкий pragmatic шаг: добавь **document candidate selection / routing layer** перед chunk retrieval и evidence extraction.

Цель шага:
Runa должна уметь **сама понимать, какие документы релевантны текущему question / mode / sphere context**, даже если пользователь не пишет в вопросе слово вроде "оффер", "контракт" или "анализы".

Нужно уйти от слабой логики:
- взять все документы подряд;
- или надеяться, что пользователь сам явно назовёт нужный документ.

И прийти к более сильной логике:
- question / mode / sphere context
- → select top candidate documents
- → chunk retrieval only inside selected docs
- → evidence extraction

---

## Сначала обязательно изучи source of truth

Сначала обязательно изучи `CLAUDE.md` и `RUNA_PRODUCT_BLUEPRINT.md` как source of truth.
Также обязательно изучи `CLAUDE_PRODUCT_PHASE_FREEZE.md`.

Не трогай reasoning core без сильного основания.
Не строй giant RAG-system.
Не делай decorative complexity.

---

## Что нужно получить в результате

Нужен **v1 слой document routing**, который отвечает на вопрос:

> какие 1–3 документа вообще стоит смотреть для данного prediction question?

А не сразу:
- брать все документы,
- или передавать все snippets в extraction.

---

## Продуктовый смысл

Правильное поведение Runa должно быть таким:

Пользователь спрашивает:
- "Стоит ли мне принимать эту работу?"
- "Насколько рискован этот переход?"
- "Стоит ли мне сейчас увеличивать нагрузку?"

И система сама понимает:
- вопрос career / health / investment / etc;
- какие сферы наиболее релевантны;
- среди доступных user documents какие документы наиболее вероятно содержат decision-critical evidence;
- какие документы можно не тащить в pipeline вообще.

Пользователь **не должен** помнить название файла или вручную писать:
- "посмотри мой оффер"
- "посмотри анализ крови"
- "посмотри договор"

---

## Что именно сделать

### 1. Добавить document candidate selection layer

Нужен узкий routing/scoring layer, который для каждого доступного user document оценивает релевантность текущему вопросу.

V1 может быть heuristic / lightweight, без overengineering.

Допустимые сигналы для document relevance:
- sphere match / sphere proximity
- filename hints
- document title / metadata if available
- overlap с question terms
- overlap с question mode hints
- lightweight type hints внутри документа
- maybe relation to active sphere / active decision context

Нельзя делать giant system.

---

### 2. Ввести typed document candidate entity

Добавь typed сущность/схему уровня кандидата документа.

Примерно такого уровня:
- document_id / file_id
- document_name
- sphere_id or sphere_name if available
- candidate_score
- candidate_reasons
- maybe document_type_hint
- selected_for_evidence: bool

Не обязательно именно эти поля, но логика должна быть typed и прозрачной.

---

### 3. Выбирать top candidate docs до chunk retrieval

Сделай так, чтобы chunk retrieval и evidence extraction применялись **не ко всем документам подряд**, а только к top candidate docs.

Для v1 достаточно:
- top 1–3 docs
- или top docs above threshold

Главное:
- уменьшить шум;
- не терять релевантный документ;
- не тянуть всё подряд.

---

### 4. Добавить honest reporting

Нужно уметь честно объяснить:
- какие документы были выбраны;
- почему;
- какие документы были проигнорированы / не подошли.

Это не обязательно выводить в идеальном UI, но хотя бы в result / typed report / debug-friendly structure.

---

### 5. Сохранить текущий document evidence flow

Текущий flow:
- select chunks
- extract evidence
- inject into prediction
- show evidence to user

Нужно не ломать.

Новый слой должен быть именно:
- document candidate selection
n- затем chunk retrieval
- затем evidence extraction

---

## Что НЕ нужно делать

Не нужно:
- giant RAG architecture
- vector DB migration
- embeddings-first redesign
- universal document ontology
- сложную ML-классификацию
- mode-specific extraction packs как основной фокус
- большой UI-рефакторинг

Это должен быть **узкий pragmatic v1**.

---

## Принцип реализации

Предпочтительно:
- простая, объяснимая scoring logic
- typed output
- устойчивость и прозрачность
- минимум новых сущностей, но достаточно для product usefulness

Важнее:
- выбрать правильный документ

Чем:
- сделать очень умный extraction внутри неправильного документа

---

## Что желательно проверить

Минимум на 2–3 сценариях:

### Сценарий 1
Есть несколько документов в разных сферах.
Вопрос карьерный.
Система должна выбрать offer / contract / relevant career doc, а не случайный документ.

### Сценарий 2
Есть длинный нерелевантный документ и короткий релевантный.
Система должна не тащить нерелевантный просто потому, что он длинный.

### Сценарий 3
Нет явно подходящих документов.
Система должна честно сказать, что strong document evidence не найден.

---

## Что считается успехом

Шаг считается успешным, если:
- document pipeline больше не работает по модели "смотрим все документы подряд";
- до evidence extraction есть понятный candidate selection layer;
- выбор документа зависит от question / mode / sphere context;
- в result можно понять, какие документы были выбраны и почему;
- prediction становится менее шумным и более grounded.

---

## Технические ограничения

- Используй public/free подход, если возможно.
- Если нужен API key — не стопорись, сделай через env config и graceful fallback.
- Не ломай текущие investment/document flows.
- Не трогай reasoning core без серьёзного основания.

---

## В финальном отчёте обязательно

Отчитайся по этому MD-файлу.

Отдельно укажи:
1. что изменил;
2. как теперь работает pipeline;
3. что стало лучше product-wise;
4. какие слабые стороны остались;
5. как проверить;
6. нужен ли ключ;
7. что пользователь должен сделать руками;
8. что удалось протестировать;
9. что не удалось завершить полностью автоматически;
10. усилился ли personal evidence usefulness;
11. какой следующий логичный шаг.

И отдельно обязательно напиши:
- какие документы routing layer выбирает;
- по каким reason signals;
- как он избегает document noise.
