# CLAUDE_CODE_DOCUMENT_PERSONAL_EVIDENCE_INTEGRATION_V1

## Задача

Сделай **узкий pragmatic шаг**:

Интегрируй **user documents / personal files** в prediction pipeline как **first-class personal evidence**, а не как декоративный кусок контекста.

Важно: это НЕ шаг про giant RAG system, НЕ шаг про полный document platform, и НЕ шаг про endless retrieval polishing.

Нужен именно **Document / Personal Evidence Integration v1**.

---

## Сначала обязательно изучи

- `CLAUDE.md`
- `RUNA_PRODUCT_BLUEPRINT.md`
- `CLAUDE_PRODUCT_PHASE_FREEZE.md`

Считай их source of truth.

---

## Зачем нужен этот шаг

Сейчас investment baseline уже доведён до good enough:
- market fusion
- personal suitability
- structured profile
- typed missing context capture
- structured missing-context contract
- allocation / exposure policy
- policy UI surface

Следующий продуктовый шаг должен усилить другую ключевую часть формулы Runa:

**personal world model + personal evidence + outside world = stronger prediction**

Сейчас документы пользователя ещё недостаточно похожи на **first-class evidence**.
Они могут участвовать в personal context, но не живут как явный слой доказательств, влияющих на prediction.

Нужно сделать так, чтобы prediction умел:
- явно видеть, какие user documents были использованы;
- извлекать из них **decision-relevant evidence**;
- показывать, что именно из документов повлияло на вывод;
- честно говорить, когда документы не помогли или слишком слабы.

---

## Что НЕ нужно делать

Не надо:
- строить giant document platform;
- делать новый сложный универсальный RAG framework;
- переписывать весь retrieval слой;
- уходить в сложный UI-документооборот;
- делать full OCR pipeline, если без этого можно обойтись;
- делать huge multi-mode system.

Также не трогай reasoning core без сильного основания.

---

## Что нужно сделать

Нужен **v1 personal evidence layer** для prediction pipeline.

### 1. Ввести явную сущность personal document evidence

Нужен typed слой, который позволяет представить документальные evidence items примерно в таком духе:
- document id / reference
- document name
- evidence snippet / extracted fact
- evidence_type
- relevance / confidence
- why_it_matters
- linked question mode if useful

Не обязательно копировать именно эти поля 1 в 1, но смысл должен быть именно таким:
**document-derived evidence становится отдельной продуктовой сущностью, а не просто текстом в общем personal_context dump**.

### 2. Добавить document evidence extraction / selection в prediction pipeline

На узком pragmatic уровне:
- если у пользователя уже есть документы / файлы / document-derived context в системе, prediction должен уметь выбрать релевантные evidence items;
- для investment mode хотя бы базово использовать это как personal evidence;
- если документов нет — graceful fallback.

Здесь не нужно строить идеальный retrieval engine.
Нужно сделать **работающий first-class evidence path**.

### 3. Добавить evidence в synthesis context как отдельный блок

Не смешивать это бесформенно с остальным personal context.
Нужен отдельный блок, который явно говорит:
- какие personal evidence items использованы;
- что именно они подтверждают / уточняют;
- насколько они важны для ответа.

### 4. Добавить honest reporting

Prediction должен уметь честно отражать:
- documents used
- documents not useful / weak
- no relevant personal evidence found

Не надо притворяться, что документы помогают, если они реально не помогли.

### 5. Добавить минимальную source transparency для personal evidence

Хотя бы на backend / structured response уровне должно быть видно:
- какие документы реально участвовали;
- какие evidence items были извлечены.

Если успеешь безопасно и без лишней сложности — можно вывести это в UI как простой evidence block.
Но это не обязательно, если начнётся расползание.

---

## Очень важный продуктовый принцип

Документы должны усиливать prediction как **evidence**, а не как “ещё один длинный текстовый блок”.

То есть плохой результат:
- документ просто добавили в context dump
- LLM как-то его пересказал

Правильный результат:
- document-derived evidence стал отдельной частью reasoning
- можно показать, что конкретно из документа повлияло на вывод

---

## Где сфокусироваться

Сделай это **сначала для current prediction flow**, не пытайся решить всё на будущее.

Если нужно сузить шаг — сузь.
Например:
- investment questions
- document evidence for financial/personal constraint confirmation
- only files already present in system

Это нормально.

---

## Какой результат считается хорошим

Хороший результат — если после шага можно честно сказать:

- prediction теперь умеет использовать user documents как явные evidence items;
- видно, что именно из документов повлияло на вывод;
- documents больше не выглядят как декоративный appendage;
- personal evidence layer реально усилил personal prediction usefulness.

---

## Как проверить

Предложи понятную проверку через:
- UI
- API
- или test scenario

Проверка должна демонстрировать именно это:
- документ загружен / доступен;
- prediction использует его как evidence;
- evidence видно в structured result или synthesis context;
- если документ нерелевантен, это честно отражается.

---

## Ограничения

- Используй public/free source, если возможно.
- Если нужен API key — не стопорься, сделай через env config и graceful fallback.
- Если что-то нельзя завершить полностью автоматически — явно скажи, что нужно сделать руками.
- Не усложняй систему без реального product uplift.

---

## В финальном отчёте обязательно

Отчитайся **по MD-файлу**.

Отдельно укажи:
1. что изменил
2. как теперь работает pipeline
3. что стало лучше product-wise
4. какие слабые стороны остались
5. как проверить
6. нужен ли ключ
7. что пользователь должен сделать руками
8. что удалось протестировать без этого
9. что не удалось завершить полностью автоматически
10. усилился ли personal OSINT / personal evidence usefulness
11. какой следующий логичный шаг

