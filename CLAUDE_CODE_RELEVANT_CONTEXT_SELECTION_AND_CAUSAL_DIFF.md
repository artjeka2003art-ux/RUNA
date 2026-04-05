# Runa — Relevant Context Selection + Compact Sphere Digests + Better Causal Diff

## Source of truth
Перед началом обязательно перечитай:
- `CLAUDE.md`
- `RUNA_PRODUCT_BLUEPRINT.md`

Работай от нового core:
**Runa = personal decision intelligence system**.
Главный фокус — не graph ради graph и не complexity ради complexity, а усиление `Decision Workspace` через более сильный и более релевантный personal context.

---

# Задача этого шага

На прошлом шаге мы добились важного прогресса:
- обновления из сфер реально начали попадать в prediction;
- Redis даёт свежий контекст;
- Zep даёт long-term facts;
- re-run после возврата из сферы реально может стать умнее.

Теперь главный bottleneck:

## prediction получает слишком широкий и шумный sphere context

Если у пользователя много сфер, в prompt могут попадать:
- нерелевантные sphere chats,
- слабосвязанные факты,
- слишком сырые raw messages,
- контекст, который не помогает именно для текущего вопроса и сценариев.

Это начинает ухудшать качество reasoning.

---

# Цель шага

Сделать так, чтобы `workspace prediction`:
1. выбирал **только наиболее релевантный контекст**;
2. подтягивал его в **компактном digest-формате**, а не сырым шумом;
3. после re-run лучше показывал **вероятную причину улучшения прогноза**.

Коротко:

## Relevant Context Selection + Compact Sphere Digests + Better Causal Diff

---

# Что нужно сделать

## 1. Relevant Context Selection v1

Улучши backend retrieval/context assembly в `prediction_query_agent.py`.

Сейчас проблема в том, что sphere context тянется слишком широко.
Нужно ввести **простой, прагматичный relevance layer** без overengineering.

### Что требуется
Для текущего `question` и `variants`:
- посчитать релевантность сфер;
- выбрать только `top` наиболее релевантные сферы;
- только по ним собирать свежий chat context и Zep facts.

### Как делать v1
Не делай heavy retrieval system.
Не делай embeddings, vector DB и новые сложные сервисы.

Сделай простой scoring-based relevance selection на базе:
- текста вопроса;
- текстов scenario variants;
- имени сферы;
- описания сферы;
- при необходимости — простых synonym / alias rules.

### Ожидаемый подход
Нормальный pragmatic v1 может включать:
- exact / partial overlap;
- token overlap;
- synonym hints;
- простую итоговую relevance score;
- выбор top 3–5 сфер.

### Важно
Лучше взять меньше, но релевантнее, чем больше и шумнее.

---

## 2. Compact Sphere Digests v1

Сейчас из sphere chats тянутся raw user messages.
Для v1 это было ок, но теперь нужно сделать контекст более пригодным для reasoning.

### Что требуется
Вместо сырых фрагментов сообщений собирать **компактный digest по сфере**.

### Формат v1
Не нужен отдельный LLM-вызов на суммаризацию.
Не строй новую memory architecture.

Сделай lightweight digest из уже доступных данных.
Например, по каждой релевантной сфере можно собрать компактный блок вида:
- sphere name
- sphere description
- recent important user facts
- recent changes
- notable constraints / tensions
- relevant long-term facts from Zep

### Цель
Чтобы в final personal context попадал не сырой шум, а **короткий сильный блок по каждой релевантной сфере**.

---

## 3. Better Causal Diff v1

Сейчас diff уже показывает:
- confidence changes,
- changes in risks,
- changes in leverage factors,
- changes in known factors.

Это хорошо, но ещё не хватает ответа на человеческий вопрос:

## “Почему прогноз стал лучше или изменился?”

### Что требуется
Добавить в diff-block более явную causal/probable-cause подсказку.

Это может быть rule-based v1.
Не нужен отдельный heavy AI layer.

### Примеры того, что можно показать
- “Вероятная причина улучшения: добавлены финансовые данные”
- “Прогноз стал увереннее, потому что появились новые known factors”
- “Риск снизился после добавления контекста о support system”
- “Причина изменения: обновлён карьерный контекст”

### Как можно реализовать v1
На базе:
- added known factors,
- removed missing items,
- changed confidence,
- changed risks,
- sphere context used for re-run.

То есть нужен **простый explainability layer**, а не ещё один большой движок.

---

## 4. Не раздувать сложность

Осознанно **НЕ** делать в этом шаге:
- embeddings / vector search;
- новый retrieval microservice;
- отдельную DB для context ranking;
- большой semantic engine;
- новый UI flow кроме того, что нужно для diff/explanation;
- новый memory subsystem для workspace.

Этот шаг должен быть сильным, но компактным.

---

# Где менять код

Ожидаемые зоны:
- `backend/agents/prediction_query_agent.py`
- при необходимости: `backend/graph/graph_queries.py`
- при необходимости: memory / helper utilities, если нужно вынести selection/digest logic
- `frontend/src/PredictionView.tsx`
- при необходимости: `frontend/src/api.ts`
- `frontend/src/App.css`

Не переписывай проект широко без причины.

---

# Что должно получиться после шага

После этого шага поведение должно быть таким:

1. Пользователь задаёт вопрос в `Decision Workspace`
2. Prediction engine выбирает **релевантные сферы**, а не всё подряд
3. В prompt попадает **компактный digest**, а не сырой шум
4. После возвращения из сферы и re-run prediction становится содержательно сильнее
5. Diff показывает не только “что изменилось”, но и **почему это, вероятно, изменилось**

То есть продукт должен начать ещё лучше демонстрировать:

## added context → better reasoning → visible explanation of improvement

---

# Критерии качества

## Хорошо, если
- relevant context selection заметно уменьшает шум;
- код остаётся простым и понятным;
- нет лишней архитектурной тяжести;
- causal diff объясняет изменения человеческим языком;
- шаг реально усиливает `Decision Workspace`.

## Плохо, если
- появляется избыточная сложность;
- делается heavy semantic system ради 5–10 сфер;
- контекст просто обрезается без логики;
- causal diff звучит как декоративная магия;
- меняется много несвязанных частей продукта.

---

# Формат отчёта после выполнения

После выполнения отчитайся строго по структуре:

## 1. Что изменил
- какие файлы поменял
- какие новые функции / методы / структуры добавил
- как теперь устроен relevance selection
- как теперь устроен compact sphere digest
- как теперь устроен better causal diff

## 2. Почему это усиливает новый core
Объясни через:
- Decision Workspace
- prediction usefulness
- progressive precision
- reduced prompt noise
- better user understanding of why prediction changed

## 3. Как проверить
Дай конкретный сценарий локальной проверки:
- вопрос
- сферы
- добавление контекста
- re-run
- что именно должно измениться в UI и/или в backend behavior

## 4. Что осталось слабым
Честно перечисли ограничения v1.
Например:
- rule-based relevance ограничен;
- digest ещё не идеален;
- causal diff всё ещё вероятностный, а не fully grounded;
- и т.д.

## 5. Решение по architecture boundaries
Отдельно напиши:
- что ты осознанно НЕ стал делать;
- почему это пока overkill;
- когда к этому стоит вернуться.

## 6. Следующий лучший шаг
Предложи следующий логичный шаг после этого — но только если он действительно следует из сделанного состояния проекта.

---

# Главный фильтр

Перед каждым изменением проверяй:

## “Это делает Runa сильнее как personal decision intelligence system?”

И ещё конкретнее:

## “Это помогает человеку лучше моделировать важные решения своей жизни?”

Если нет — не туда идёшь.
