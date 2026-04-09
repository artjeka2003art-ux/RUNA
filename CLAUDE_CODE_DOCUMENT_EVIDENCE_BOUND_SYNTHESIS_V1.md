# CLAUDE_CODE_DOCUMENT_EVIDENCE_BOUND_SYNTHESIS_V1

## Контекст

Runa уже прошла несколько важных шагов в document branch:

- document evidence extraction v1
- chunk retrieval + evidence selection v1
- document candidate selection / routing v1
- document routing transparency in UI

Сейчас document layer уже умеет:
- выбирать кандидатов среди документов
- выбирать релевантные chunks
- извлекать evidence
- показывать пользователю, какие документы были выбраны и почему

Но всплыл критичный product-quality gap:

## Главная проблема сейчас

Даже если Runa:
- выбрала правильный документ,
- нашла правильные chunks,
- извлекла правильные evidence facts,

финальный synthesis всё ещё может **галлюцинировать numeric / contract facts** поверх evidence.

### Пример реального сбоя
В test offer document явно указано:
- `EUR 92,000 gross per year`
- `12% discretionary annual bonus`
- `EUR 8,000 gross sign-on bonus`
- `12-month non-compete in Benelux`
- `2-month probation`
- `2-month employee notice period`

Но итоговый prediction мог выдать:
- `350,000 руб/мес`

Это недопустимо.

---

## Цель этого шага

Сделать **evidence-bound synthesis** для document-backed numeric / contract facts.

То есть:
- если факт подтверждён документом, модель должна брать именно его;
- если факт НЕ подтверждён документом, модель не должна его придумывать;
- если document evidence недостаточно для точного вывода, система должна говорить это честно.

---

## Что нужно сделать

Сделай узкий pragmatic шаг без giant redesign.

### 1. Ввести explicit contract для document-backed hard facts
Нужен отдельный слой / структура / блок, который фиксирует из `document_evidence` именно те факты, которые нельзя свободно перефразировать и тем более домысливать.

Это касается прежде всего:
- salary / compensation numbers
- bonus numbers / conditions
- sign-on / repayment / clawback terms
- notice period
- probation period
- non-compete duration / geography
- relocation deadlines
- payment obligations
- other clearly document-backed numeric or contractual conditions

### 2. Синтез должен быть evidence-bound для этих фактов
Если в финальном ответе используются такие facts, они должны:
- либо браться **только** из extracted document evidence / bound facts block;
- либо не использоваться вообще.

Недопустимо:
- конвертировать salary в другую валюту без явного document evidence;
- превращать annual gross в monthly net, если документ этого не даёт;
- менять duration / period values;
- усиливать условия контракта без evidence.

### 3. Honest fallback
Если документ даёт только:
- annual gross salary

а пользовательский вопрос или synthesis подразумевает:
- monthly net income

система должна отвечать честно в духе:
- "В документе указано EUR 92,000 gross per year; monthly net не указан."

А не додумывать.

### 4. Подтянуть prompt / synthesis contract
Нужно явно зажать synthesis:
- numeric and contractual facts from documents are evidence-bound;
- do not invent or transform unless the transformed value is explicitly supported;
- if unsupported, say unsupported / not specified in the document.

### 5. Сделать user-visible transparency лучше
Если возможно без лишней сложности, в document evidence / prediction surface должно быть понятнее видно:
- какие hard facts были использованы как confirmed document facts
- а где информации недостаточно

Не нужен giant UI-redesign.
Достаточно pragmatic improvement.

---

## Важно: учесть 2 текущие слабости document routing, но не расползтись

В предыдущем шаге уже были замечены 2 слабости:

### A. Routing всё ещё очень heuristic
Да, это правда.
Но **этот шаг НЕ должен превращаться в большой reranking/semantic routing project**.

Что можно сделать в рамках текущего шага:
- если это помогает evidence-bound synthesis, аккуратно уменьшить риск routing miss для numeric/contract docs;
- например чуть сильнее учитывать document type hints / contract-like docs / offer-like docs;
- но не превращать задачу в новый retrieval engine.

### B. Sphere selection по-прежнему выше document routing
Да, это тоже правда.
Но **этот шаг НЕ должен превращаться в большой sphere-selection redesign**.

Что можно сделать pragmatically:
- если у тебя есть безопасный способ не терять явно сильный contract-like / offer-like document только из-за слабого sphere filtering — предложи и сделай очень узко;
- например lightweight fallback pass или candidate rescue path;
- но только если это действительно небольшой и grounded change.

Если это уже расползается в отдельную архитектурную задачу — **не лезь**.
Тогда просто честно зафиксируй это как следующий отдельный слой.

---

## Что НЕ нужно делать

Не нужно:
- строить giant RAG-system
- строить full semantic retrieval stack
- строить full contract parser platform
- строить giant financial calculator
- трогать reasoning core глубоко
- уходить в endless polishing

---

## Что должно стать лучше после шага

После этого шага Runa должна:
- использовать document-backed salary/terms/facts более жёстко и честно;
- не выдумывать месячные доходы, валютные конверсии, сроки, penalties;
- лучше сохранять trust в document-backed predictions;
- честно говорить, когда документ подтверждает факт, а когда нет.

---

## Как проверить

Сделай понятную проверку на offer-like document, где явно есть:
- annual gross salary
- discretionary bonus
- sign-on clawback
- probation
- notice
- non-compete
- relocation deadline

И проверь, что финальный synthesis:
- не выдумывает monthly net или salary in RUB;
- корректно использует exact documented values;
- честно пишет, если чего-то нет.

---

## Ограничения

Это v1.
Не надо делать идеальную system-of-record for contracts.
Нужен pragmatic anti-hallucination layer для document-backed hard facts.

---

## Финальный критерий успеха

Успех = если Runa при работе с оффером / контрактом:
- не галлюцинирует numeric / contract facts,
- использует только подтверждённые значения,
- и честно сообщает о пробелах.

---

## Что нужно в финальном отчёте

В финальном отчёте обязательно отдельно укажи:

1. что изменил по этому MD-файлу
2. как теперь работает evidence-bound synthesis pipeline
3. что стало лучше product-wise
4. какие слабые стороны остались
5. как проверить
6. нужен ли API key
7. что пользователь должен сделать руками
8. что удалось протестировать без этого
9. что не удалось завершить полностью автоматически
10. какой следующий логичный шаг

И отдельно:
- честно скажи, удалось ли в рамках этого шага хоть немного снизить риск от heuristic routing / sphere-first filtering,
- или это остаётся отдельной следующей задачей.
