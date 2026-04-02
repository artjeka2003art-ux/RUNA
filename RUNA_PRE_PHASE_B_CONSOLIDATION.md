# RUNA — PRE-PHASE B CONSOLIDATION

## Что это за этап

Это не Phase B и не 3D-граф.

Это последний обязательный слой перед Phase B.

Цель:
**сделать сферы устойчивыми как сущности, подключить к ним настоящую долговременную память и убрать опасные архитектурные слабости, чтобы на Phase B (graph/3D) опираться уже на надёжную основу.**

В этом этапе закрываем три задачи одним проходом:

1. **Zep integration for sphere chats**
2. **stable sphere identity** — отдельный `sphere_id`, не имя как псевдо-id
3. **ownership checks** — все операции со сферой должны проверять `user_id + sphere_id`

---

## Почему это нужно сейчас

Phase A и A.1 уже сделали важное:
- reveal сфер
- Life Map
- sphere detail
- sphere chat
- sphere descriptions
- sphere-specific context

Но сейчас ещё есть три слабых места:

### 1. Sphere chat без настоящей долговременной памяти
Сейчас сферы ещё недостаточно “помнят себя” во времени.

### 2. Идентичность сферы слишком хрупкая
Нельзя завязывать сущность сферы на её имя.
Имя должно быть редактируемым полем, а не основой identity.

### 3. Ownership checks ещё недостаточно жёсткие
Для Phase B и более глубоких сценариев нужно, чтобы все операции со сферой были привязаны к пользователю явно и безопасно.

---

# ЧАСТЬ 1 — ZEP INTEGRATION FOR SPHERE CHATS

## Цель

У каждой сферы должна появиться своя долговременная память.

Когда пользователь возвращается в сферу через несколько дней или недель, AI должен помнить:
- о чём уже говорили именно в этой сфере
- какие темы и напряжения там уже поднимались
- какие факты и паттерны уже всплывали

Но при этом sphere memory не должна быть полностью изолированной от общей модели пользователя.

---

## Как должно работать

## Уровень A — sphere thread
У каждой сферы должен быть свой отдельный Zep thread.

Предлагаемый thread id:
- `sphere-{user_id}-{sphere_id}`

В этом thread хранится память именно по этой сфере.

## Уровень B — global user memory
У пользователя уже есть общий memory layer.

Нужно сделать так, чтобы sphere chats:
- сохранялись в sphere thread
- и при этом важные факты из них были доступны общей модели пользователя, если это уже обеспечивается текущей user-level memory логикой

### Важно
Не превращай это в две полностью разорванные системы.
Сфера должна иметь свою память, но не быть островом.

---

## Что должен делать SphereAgent

### Перед ответом
SphereAgent должен собрать:
1. текущую сферу
2. связанные graph nodes / nearby context
3. краткий global context пользователя
4. **sphere-level Zep context** из thread этой сферы

### После ответа
SphereAgent должен:
1. сохранить exchange в sphere thread
2. не ломать текущую analyst / graph update logic
3. продолжать обновлять граф после sphere chat

### Что нельзя делать
- не пихать в prompt весь Zep history целиком
- не дублировать graph структуру в Zep
- не заменять graph памятью Zep

### Разделение ролей
- **Graph** = структура жизни
- **Zep** = эпизодическая / разговорная память

---

## Что нужно проверить после интеграции
- пользователь пишет в сфере
- выходит
- возвращается позже
- sphere chat помнит прошлый разговор именно по этой сфере
- companion / общая модель не ломаются
- graph updates после sphere chat продолжают работать

---

# ЧАСТЬ 2 — STABLE SPHERE IDENTITY

## Проблема
Сфера не должна определяться по имени.

Плохой вариант:
- `MERGE (s:Sphere {user_id, name})`

Почему это плохо:
- имя редактируемое
- повторное использование имени может ломать модель
- renamed / deleted / recreated flows становятся опасными
- имя начинает вести себя как id, а это неверно

---

## Что должно быть вместо этого

У каждой сферы должен быть отдельный стабильный `id`.

### Пример
- `id: "sphere-uuid-..."`

Имя сферы:
- обычное редактируемое поле `name`

### Правило
- create sphere = всегда создаёт новую сущность с новым `id`
- rename sphere = меняет только `name`
- delete/archive sphere = работает по `sphere_id`
- detail / message / update = работают по `sphere_id`

---

## Что нужно поменять

### Graph layer
Проверь и исправь:
- create sphere query
- detail query
- rename query
- archive/delete query
- list spheres query
- любые соседние запросы, где сфера ищется по имени как по identity

### Schemas / models
Убедись, что frontend и backend везде опираются на:
- `sphere_id`
а не на `name` как identity

### Migration / compatibility
Если нужно, сделай аккуратный migration path для уже существующих сфер:
- добавить `id` если его ещё нет
- не ломать старые данные

Для MVP допустим pragmatic migration, но без хаоса.

---

# ЧАСТЬ 3 — OWNERSHIP CHECKS

## Цель
Все операции со сферой должны явно проверять:
- `sphere_id`
- `user_id`

### Почему
Нельзя полагаться только на `sphere_id`.
Даже для MVP лучше сразу держать ownership модель чистой.

---

## Где это обязательно
Проверь и исправь все эти операции:

1. get sphere detail
2. rename sphere
3. archive/delete sphere
4. send sphere message
5. create sphere follow-up operations
6. любые graph queries, где читается / меняется конкретная сфера

### Правило
Везде, где есть операция с одной сферой, должен учитываться `user_id`.

---

# BACKEND — ПРИОРИТЕТ ФАЙЛОВ

Работай примерно в таком порядке:

1. `backend/graph/graph_queries.py`
   - исправить sphere identity queries
   - добавить ownership-safe queries

2. `backend/graph/graph_builder.py`
   - high-level helpers для sphere id / ownership

3. `backend/models/schemas.py`
   - если нужно, уточнить contracts

4. `backend/memory/zep_client.py`
   - расширить / использовать под sphere threads

5. `backend/agents/sphere_agent.py`
   - подключить zep_client
   - sphere thread flow
   - memory retrieval / save

6. `backend/api/routes/spheres.py`
   - убедиться, что routes используют `user_id + sphere_id`
   - не опираться на name как identity

7. `backend/api/main.py`
   - если нужна регистрация зависимостей

8. `backend/agents/analyst_agent.py`
   - не ломать sphere context logic при обновлении

---

# FRONTEND — ПРИОРИТЕТ ФАЙЛОВ

1. `frontend/src/api.ts`
   - убедиться, что все операции идут через real `sphere_id`

2. `frontend/src/LifeMap.tsx`
3. `frontend/src/SphereDetail.tsx`
4. `frontend/src/App.tsx`

### Что важно на frontend
- не завязывать ключевые операции на sphere name
- если backend response слегка изменится, адаптировать UI честно
- UX не переписывать заново — только адаптировать под надёжную модель

---

# ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

После этого этапа должно быть так:

## Sphere memory
- каждая сфера помнит свои разговоры через Zep
- пользователь может вернуться к сфере позже и продолжить разговор осмысленно

## Sphere identity
- каждая сфера имеет стабильный `id`
- rename / delete / recreate больше не завязаны на имя как identity

## Ownership
- все операции со сферой проверяют принадлежность пользователю

## Product readiness
- Phase B можно начинать уже на устойчивой модели, а не на хрупких костылях

---

# ЧТО НЕ ДЕЛАТЬ В ЭТОМ ЭТАПЕ

- не начинать 3D graph
- не делать большую новую визуализацию
- не переписывать Life Map UX заново
- не строить сложную новую memory architecture сверх нужного
- не ломать текущий working flow ради “идеальности”

---

# КАК ПРОВЕРЯТЬ

## Проверка sphere memory
1. открыть сферу
2. написать несколько сообщений
3. выйти
4. вернуться позже
5. проверить, что AI помнит контекст именно этой сферы

## Проверка stable id
1. создать сферу
2. переименовать
3. удалить / архивировать
4. создать новую с тем же именем
5. убедиться, что это новая сущность, а не resurrection старой по имени

## Проверка ownership
1. проверить detail / rename / delete / message flow
2. убедиться, что queries используют и `user_id`, и `sphere_id`

---

# ФОРМАТ ОТЧЁТА ПОСЛЕ РАБОТЫ

После завершения обязательно покажи:

1. список изменённых файлов
2. как теперь устроен sphere Zep memory flow
3. какой thread id используется для sphere memory
4. какие queries перестали опираться на sphere name как identity
5. как реализованы ownership checks
6. как проверить локально
7. что осталось на Phase B intentionally

---

# ФОРМАТ РАБОТЫ

После каждого крупного блока кратко сообщай:
- что сделал
- какие файлы изменил
- как проверить
- что идёт следующим

Работай как техпартнёр, а не как исполнитель.
