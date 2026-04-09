# CLAUDE_CODE_DOCUMENT_CHUNK_CACHE_STABLE_EVIDENCE_PIPELINE_V1

## Задача

Сделай **узкий pragmatic шаг**: укрепи текущий document evidence pipeline так, чтобы он был **стабильнее, дешевле и быстрее при rerun**, **без giant RAG-system** и **без прыжка в domain-specific extraction**.

Сейчас documents уже стали first-class evidence:
- есть document evidence extraction,
- есть chunk retrieval,
- есть UI surface.

Но главный практический минус текущего слоя:
- документы chunked/scored заново при каждом rerun,
- есть лишняя работа в pipeline,
- baseline document evidence pipeline ещё не до конца stabilised.

На этом шаге нужно сделать именно **cache/stability pass**, а не новую большую ветку.

---

## Сначала обязательно изучи

- `CLAUDE.md`
- `RUNA_PRODUCT_BLUEPRINT.md`
- `CLAUDE_PRODUCT_PHASE_FREEZE.md`

Это source of truth.

---

## Главная цель

Сделать так, чтобы текущий `Document Chunk Retrieval + Evidence Selection` слой:
1. не делал лишнюю повторную работу на каждом rerun;
2. был более предсказуемым как pipeline;
3. оставался простым;
4. не превращался в сложный RAG framework;
5. усиливал **personal evidence usefulness**, а не complexity ради complexity.

---

## Что нужно сделать

### 1. Добавить pragmatic caching для document chunk pipeline
Нужно добавить простой cache/reuse слой для document chunk retrieval.

Минимально достаточно:
- не пересчитывать chunking одного и того же документа на каждом rerun, если документ не изменился;
- по возможности не пересчитывать selected top chunks, если вопрос/variants/doc version не изменились;
- можно сделать это просто и локально — без overengineering.

Подход может быть pragmatic:
- cache key на базе `document_id + updated_at/hash`
- для selection cache: `document_id + question + variants signature + updated_at/hash`

Не надо строить distributed search infra.
Нужен **разумный v1**.

### 2. Убрать лишнюю повторную работу в pipeline
Если сейчас один и тот же документ chunked/scored несколько раз в одном request flow — сократи это.
Нужно убрать очевидный мелкий waste.

### 3. Сохранить question-aware retrieval
Важно: caching не должен ломать то, что уже стало сильнее:
- chunk selection должен оставаться привязан к вопросу пользователя;
- evidence должен извлекаться из релевантных частей документа, а не из первых символов.

### 4. Сделать pipeline чуть более устойчивым
Добавь простые guardrails:
- если текст документа пустой / слишком короткий / chunking дал пустой результат — graceful fallback;
- если chunk scoring не нашёл сильных кандидатов — использовать разумный fallback;
- если evidence extraction ничего не вернуло — честный empty result.

### 5. Не уходить в giant refactor
Не надо:
- вводить Qdrant/embeddings ради этого шага;
- делать полный document indexer;
- строить новый global retrieval subsystem;
- тащить тяжёлый orchestration;
- ломать текущий workspace flow.

Это должен быть **узкий strengthening step**.

---

## Что НЕ делать

Не надо:
- делать domain-specific extraction на этом шаге;
- лезть в новый mode pack;
- строить giant RAG;
- переписывать весь prediction pipeline;
- делать полировку ради полировки.

---

## Что считается хорошим результатом

Хороший результат — если после шага:
- document evidence pipeline работает так же или лучше по качеству;
- rerun по тем же документам делает меньше лишней работы;
- код становится чуть чище и стабильнее;
- user-facing поведение не деградирует;
- personal evidence layer становится practical, а не только conceptually good.

---

## Где менять

С высокой вероятностью основные изменения будут в:
- `backend/agents/prediction_query_agent.py`

Но если нужно аккуратно вынести маленькие helper structures / cache helpers — можно.
Без разрастания архитектуры.

---

## Как проверить

Нужно показать, что:
1. длинный документ всё ещё даёт релевантные evidence chunks;
2. повторный rerun по тому же вопросу и тем же документам использует reuse/cache path;
3. graceful fallback не ломает flow на пустом/коротком документе.

---

## Ограничения

- Используй public/free/local-first подходы, если возможно.
- Если нужен API key — не стопорься, сделай через env config и graceful fallback.
- Не трогай reasoning core без сильного основания.
- Не превращай этот шаг в новый большой project branch.

---

## В финальном отчёте обязательно

Отчитайся по этому MD-файлу и отдельно укажи:

1. что изменил;
2. как теперь работает pipeline;
3. что стало лучше product-wise;
4. какие слабые стороны остались;
5. как проверить;
6. нужен ли ключ;
7. что пользователь должен сделать руками;
8. что удалось протестировать без этого;
9. что не удалось завершить полностью автоматически;
10. усилился ли personal evidence usefulness;
11. какой следующий логичный шаг.

---

## Главный фильтр

Перед любым решением проверяй:

**Это делает Runa сильнее как personal prediction engine + personal evidence engine?**

И ещё конкретнее:

**Это помогает использовать user documents как более надёжные и полезные evidence, а не как decorative text layer?**
