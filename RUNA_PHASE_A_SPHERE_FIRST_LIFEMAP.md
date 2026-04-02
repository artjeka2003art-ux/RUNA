# RUNA — PHASE A: SPHERE-FIRST LIFE MAP

## Что это за этап

Это первая реализация новой продуктовой модели Runa.

Цель этого этапа:
**превратить Runa из dashboard + общего check-in в живую карту сфер жизни пользователя.**

Мы НЕ делаем сейчас 3D-граф.
Мы НЕ делаем сейчас полный deep graph UI.
Мы НЕ делаем новый большой редизайн всего продукта.

Мы делаем **ядро новой модели**:

1. после онбординга появляется reveal сфер
2. появляется новый экран Life Map
3. сферы становятся редактируемыми
4. пользователь может добавить и удалить сферу
5. можно провалиться в отдельную сферу
6. у каждой сферы есть свой AI-чат
7. после sphere chat обновляется не только эта сфера, а вся модель

---

## Очень важный контекст проекта

Runa — это персональная AI prediction-система.

Главная задача продукта:
**дать человеку ясность, из чего состоит его жизнь, что с ней происходит и что делать дальше.**

Текущая версия уже имеет:
- onboarding
- Today
- Path
- Life Score
- prediction
- personal graph
- analyst / companion / scenario logic

Но сейчас сферы не живут как реальные продуктовые сущности.

После этого этапа сферы должны стать центральной частью опыта.

---

## Что нужно помнить при работе

### 1. Сферы индивидуальны
AI должен создавать сферы из разговора пользователя.
Не шаблонные 7 категорий.
У одного пользователя может быть 4 сферы, у другого 7, у другого 9.

Правило для MVP:
- минимум: 3
- обычно: 4–8
- максимум: 10

### 2. Пользователь может исправлять AI
Если AI назвал сферу плохо или неполно — пользователь должен мочь:
- переименовать сферу
- удалить сферу
- добавить новую
- уточнить смысл сферы через разговор внутри неё

### 3. Sphere chat — не изолированная заметка
Это отдельный разговор по конкретной теме, но изменения после него могут обновлять:
- эту сферу
- связанные сферы
- блокеры, цели, паттерны, ценности
- общий граф

### 4. Фаза A важнее 3D
Не уходи сейчас в сложную графовую визуализацию.
Нужно сначала сделать так, чтобы сами сферы жили как сущности и продуктовая логика работала.

---

## Что именно строим в Phase A

## 1. Reveal сфер после онбординга
После завершения онбординга пользователь должен увидеть:
- отдельный reveal state / screen
- визуальную композицию сфер
- 4–10 сфер, извлечённых из разговора
- короткую подпись, что это карта его жизни, которую AI построил из разговора

Это не должен быть просто redirect в Today.

---

## 2. Новый экран Life Map
Добавляем новый главный экран / tab:
- Today
- Life Map
- Path

Life Map должен стать центральным экраном новой модели.

На нём пользователь:
- видит свои сферы
- может открыть сферу
- может быстро переименовать
- может удалить
- может нажать "Добавить сферу"

На этом этапе можно сделать Life Map в 2D / circle / constellation layout.
3D будет позже.

---

## 3. Управление сферами

### Обязательно
- rename sphere
- delete sphere
- add sphere
- open sphere detail

### Важно
Удаление в UI называется "Удалить", но на backend лучше делать soft delete / archived, а не жёсткое удаление из графа навсегда.

### Add sphere flow
1. пользователь нажимает "Добавить сферу"
2. вводит рабочее название / тему
3. создаётся новая сфера
4. пользователь попадает в Sphere Detail / Sphere Chat
5. AI помогает уточнить смысл сферы через разговор

---

## 4. Sphere Detail
Для каждой сферы нужен отдельный экран / view.

Он должен показывать:
- название сферы
- краткий смысл / описание
- что влияет на неё
- что она поддерживает
- чат по теме этой сферы
- действия rename / delete

Не надо сейчас перегружать экран всеми возможными графовыми сущностями.
Но смысл сферы и её связи должны быть читаемыми.

---

## 5. Sphere Chat
Нужен отдельный чат внутри сферы.

### Входные данные для AI
Не только сама сфера.
Нужно передавать:
- primary context: текущая сфера
- secondary context: связанные сферы и самые важные связанные узлы
- global context: краткий summary состояния пользователя

### После сообщения в sphere chat
Нужно:
1. получить ответ AI
2. обновить граф через analyst logic
3. вернуть пользователю:
   - reply
   - updated sphere context
   - graph updates / summary

Важно:
sphere chat не должен быть тупо отдельным локальным чатом.
Это часть общей модели личности.

---

## Что НЕ делать в этой фазе

- не делать 3D graph
- не переписывать весь onboarding с нуля
- не удалять Today и Path
- не превращать Life Map в debug graph tool
- не показывать сразу все типы узлов графа на главном экране
- не тащить новые библиотеки без необходимости
- не разносить логику по 20 местам без структуры

---

# BACKEND — что нужно изменить

## Новые и изменённые возможности

### 1. Сферы должны стать редактируемыми сущностями
Нужны операции:
- list spheres for user
- get sphere detail
- rename sphere
- create sphere
- delete/archive sphere

### 2. Sphere detail contract
Для одной сферы frontend должен уметь получить:
- id
- name
- description / interpretation
- score if available
- related blockers
- related goals
- related patterns
- related values
- related spheres
- recent updates if available

Если части данных пока нет — возвращай минимально полезную структуру, но не выдумывай.

### 3. Sphere chat endpoint
Нужен endpoint вроде:
- `POST /api/spheres/{sphere_id}/message`

Вход:
- user_id
- message

Выход:
- reply
- sphere
- graph_updates
- maybe life_score / score_delta if already easy to return

### 4. Sphere creation endpoint
Нужен endpoint вроде:
- `POST /api/spheres`

Вход:
- user_id
- name

Выход:
- created sphere
- maybe redirect target / sphere detail payload

### 5. Sphere update endpoint
Нужен endpoint вроде:
- `PATCH /api/spheres/{sphere_id}`

Для MVP достаточно:
- rename sphere
- maybe update description later if already simple

### 6. Sphere delete endpoint
Нужен endpoint вроде:
- `DELETE /api/spheres/{sphere_id}`

Но внутри лучше:
- archived = true / deleted_at
а не физическое удаление всего следа.

### 7. Graph queries / builder
Вероятно понадобится расширить graph layer:
- получать список сфер пользователя
- получать одну сферу с соседними связями
- создавать сферу
- архивировать сферу
- обновлять имя сферы
- получать связанные сущности для sphere detail
- получать соседние узлы для sphere chat context

Если возможно, держи Cypher только в `graph_queries.py`, как и раньше.

### 8. Analyst / Companion / Conversation logic
Нужно определить новый flow:
- sphere chat использует отдельный prompt или отдельный режим существующего companion
- после ответа запускается analyst update
- analyst может обновлять не только эту сферу, а весь граф

Не делай отдельного “мёртвого” чата без интеграции с графом.

---

# FRONTEND — что нужно изменить

## Новый IA / структура экранов

Текущая структура:
- Today
- Check-in
- Path

Новая структура:
- Today
- Life Map
- Path

Что делать с Check-in:
- общий daily check-in остаётся из Today / отдельного CTA
- отдельную вкладку Check-in можно убрать или встроить, если это улучшает продукт
- не держи отдельный экран только потому, что он уже существует

---

## Нужные frontend-экраны и компоненты

### 1. Reveal state after onboarding
После завершения онбординга должен быть первый экран reveal:
- “Вот как Runa увидела твою жизнь”
- визуальная композиция сфер
- CTA перейти в Life Map / Today

Это можно сделать:
- отдельным route/state
или
- специальным post-onboarding mode внутри Life Map

### 2. LifeMap.tsx
Новый основной экран.

Он должен:
- загружать список сфер
- показывать их визуально
- давать открыть сферу
- давать добавить сферу
- давать быстрые действия rename/delete

### 3. SphereDetail.tsx
Новый экран детали сферы.

Он должен:
- показывать название
- описание / interpretation
- связанные элементы
- чат внутри сферы
- rename/delete actions

### 4. SphereChat composer / message list
Можно встроить в SphereDetail.
Не нужно делать отдельную большую универсальную систему сверх нужного.

### 5. API client
Нужно добавить методы:
- getSpheres(userId)
- getSphereDetail(userId, sphereId)
- createSphere(userId, name)
- renameSphere(userId, sphereId, name)
- deleteSphere(userId, sphereId)
- sendSphereMessage(userId, sphereId, message)

### 6. State and mapping layer
Если нужно, создай mapper / VM слой для:
- life map view model
- sphere detail view model
- sphere chat summary model

Не размазывай transform logic по JSX.

---

# ПРИОРИТЕТ ФАЙЛОВ — BACKEND

Работай примерно в таком порядке:

1. `backend/models/schemas.py`
   - добавить схемы Sphere, SphereDetail, SphereMessageRequest, SphereMessageResponse и т.д.

2. `backend/graph/graph_queries.py`
   - все новые Cypher для list/create/update/archive/detail sphere

3. `backend/graph/graph_builder.py`
   - high-level helpers for sphere operations if needed

4. `backend/api/routes/`
   - добавить новый route file, например `spheres.py`
   - подключить routes в main app

5. `backend/agents/`
   - решить, как реализовать sphere chat:
     - либо новый `sphere_agent.py`
     - либо новый режим в companion agent
   - главное: чёткая логика и отдельный prompt file

6. `backend/prompts/`
   - если делаешь новый режим, prompt должен быть отдельным файлом, не инлайн

7. `backend/api/routes/onboarding.py`
   - добавить reveal-ready response if needed
   - убедиться, что после completed onboarding фронт может перейти в reveal state с реальными сферами

8. `backend/api/routes/checkin.py`
   - не ломать текущий общий check-in
   - только аккуратно встроить новую модель продукта

---

# ПРИОРИТЕТ ФАЙЛОВ — FRONTEND

Работай примерно в таком порядке:

1. `frontend/src/api.ts`
2. `frontend/src/App.tsx`
3. новый файл `frontend/src/LifeMap.tsx`
4. новый файл `frontend/src/SphereDetail.tsx`
5. возможно `frontend/src/components/` для sphere nodes / dialogs / quick actions
6. `frontend/src/App.css`
7. мапперы / utils если нужны
8. текущие `Dashboard.tsx`, `Chat.tsx`, `PredictionView.tsx` — только там, где нужно для интеграции

---

# Предлагаемый API контракт для MVP

## GET spheres
`GET /api/spheres/{user_id}`

Ответ:
```json
{
  "spheres": [
    {
      "id": "sphere-1",
      "name": "Восстановление",
      "description": "Сфера про возвращение энергии и устойчивости",
      "score": 47.2,
      "archived": false
    }
  ]
}
```

## GET sphere detail
`GET /api/spheres/{user_id}/{sphere_id}`

Ответ:
```json
{
  "sphere": {
    "id": "sphere-1",
    "name": "Восстановление",
    "description": "Сфера про возвращение энергии и устойчивости",
    "score": 47.2,
    "related_blockers": [],
    "related_goals": [],
    "related_patterns": [],
    "related_values": [],
    "related_spheres": []
  }
}
```

## CREATE sphere
`POST /api/spheres`

Вход:
```json
{
  "user_id": "user-test123",
  "name": "Отношения с братом"
}
```

## PATCH sphere
`PATCH /api/spheres/{sphere_id}`

Вход:
```json
{
  "user_id": "user-test123",
  "name": "Отношения с семьёй"
}
```

## DELETE sphere
`DELETE /api/spheres/{sphere_id}?user_id=user-test123`

Или body — выбери consistent вариант и придерживайся его.

## SEND sphere message
`POST /api/spheres/{sphere_id}/message`

Вход:
```json
{
  "user_id": "user-test123",
  "message": "Я снова избегаю этой темы и не понимаю почему"
}
```

Ответ:
```json
{
  "reply": "Твой ответ AI...",
  "sphere": {
    "id": "sphere-1",
    "name": "Отношения с семьёй",
    "description": "..."
  },
  "graph_updates": {
    "weights_updated": 2,
    "nodes_created": 1,
    "resolved": 0
  }
}
```

Если полезно, можешь вернуть и `life_score`, но только если это не ломает текущую архитектуру.

---

# UX требования для Phase A

## Reveal
Reveal должен быть эмоциональным, а не техническим.

Пользователь должен увидеть:
- что AI построил карту из разговора
- что карта индивидуальна
- что её можно дальше уточнять

## Life Map
Life Map не должен выглядеть как скучный список JSON-сущностей.
Сделай визуальную композицию:
- круг
- constellation
- orbit
- мягкий layout
- ощущение живой системы

## Sphere detail
Должен ощущаться как:
- “вот отдельная часть моей жизни”
а не просто карточка объекта.

## Sphere chat
Должен звучать как AI, который понимает тему этой сферы и помнит связь с общей жизнью.

---

# Ограничения и правила

1. Не ломай текущий Today и Path
2. Не убивай текущую prediction систему
3. Не переписывай всё сразу без необходимости
4. Не добавляй тяжёлые зависимости, если можно без них
5. Все prompt files — отдельно в `backend/prompts/`
6. Все Cypher — только в `graph_queries.py`
7. TypeScript и схемы держать в порядке
8. Не делай фейковые данные, если можно поднять реальные
9. Если для какой-то части данных пока нет — сделай честный empty state, а не галлюцинацию

---

# Как думать при реализации

На каждом шаге проверяй вопрос:

**Это усиливает ощущение, что Runa понимает, из чего состоит жизнь человека?**

Если нет — не делай.

---

# Что должно получиться в конце

После Phase A пользователь должен мочь:

1. пройти onboarding
2. увидеть reveal своих сфер
3. открыть Life Map
4. переименовать сферу
5. удалить сферу
6. добавить новую сферу
7. открыть любую сферу
8. поговорить с AI внутри неё
9. почувствовать, что после этого обновляется вся модель

Если это достигнуто — Phase A успешна.

---

# Формат отчёта после работы

После завершения обязательно покажи:

1. список изменённых файлов
2. какие backend endpoints добавлены
3. какие новые схемы / модели добавлены
4. как устроен sphere chat flow
5. как после sphere chat обновляется graph
6. какие новые экраны / компоненты добавлены на frontend
7. как проверить локально
8. что пока intentionally не реализовано и почему

---

# Очень важно

Не делай всё молча огромной пачкой.

После каждого крупного блока кратко сообщай:
- что сделал
- какие файлы изменил
- как это проверить
- что идёт следующим

Работай как техпартнёр, а не как исполнитель.
