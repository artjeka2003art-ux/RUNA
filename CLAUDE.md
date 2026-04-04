# RUNA — Claude Code Instructions (New Core)

## Что это за проект

Runa — это **personal decision intelligence system**.

Пользователь не просто “общается с AI” и не просто смотрит на красивые prediction-карточки.
Runa строит **живую модель его жизни**, помогает формулировать важные вопросы о будущем,
моделирует **альтернативные сценарии решений** и показывает:

- что вероятнее всего произойдёт
- какие риски основные
- какие факторы сильнее всего меняют исход
- каких данных не хватает для точности
- какие сферы жизни потянут последствия

Главная идея продукта:

## **Runa помогает моделировать жизненные решения до того, как человек их совершит.**

Не абстрактно.
Не “как у всех”.
А **на основе личного контекста, паттернов, среды, документов и внешнего мира**.

Короткая продуктовая формула:

## **Simulate your life decisions before you make them.**

---

# Что мы строим теперь

## Старый слабый подход
- система сама выдаёт prediction
- пользователь это не всегда запрашивал
- prediction выглядит как декоративная или натянутая фича
- ценность неочевидна

## Новый core
Prediction в Runa должен быть **query-based** и **scenario-based**.

То есть:
1. пользователь проходит онбординг
2. у него появляются уникальные сферы жизни
3. он дополняет сферы фактами о своей реальной жизни
4. он задаёт важный вопрос
5. Runa строит **несколько вариантов сценария**
6. пользователь сравнивает их в **Decision Workspace**
7. система показывает:
   - most likely outcome
   - risks
   - leverage factors
   - confidence
   - what changed between variants
   - context gaps

---

# Новый core продукта

## Runa = Personal Decision Workspace

Это не просто чат.
Не просто life map.
Не просто dashboard.

Это рабочее пространство, где человек может:

- задавать вопрос о будущем
- моделировать несколько жизненных сценариев
- менять параметры
- добавлять новые факты
- загружать документы
- видеть, как меняется прогноз
- понимать, какие факторы самые критичные
- понимать, каких данных не хватает
- возвращаться позже и обновлять сценарии

---

# Главные сущности продукта

## 1. Personal Graph
Живая модель жизни пользователя.

Содержит:
- сферы
- паттерны
- блокеры
- ценности
- цели
- события
- recent check-ins
- recent action feedback
- давление / ресурс / динамику
- связи между сферами

Это НЕ декоративный граф.
Это база для прогнозов и симуляции решений.

---

## 2. Sphere
Отдельная часть жизни пользователя.

Примеры:
- карьера
- здоровье
- режим
- отношения
- финансы
- новый проект
- семья
- обучение

Важно:
сфера — это не просто карточка.
Сфера — это контейнер для **контекста, который повышает точность prediction**.

Внутри сферы пользователь может:
- уточнять факты
- добавлять персональную информацию
- загружать документы
- вести chat по сфере
- фиксировать изменения
- указывать внешнюю среду (работодатель, учеба, режим, рынок и т.д.)

---

## 3. Prediction Question
Вопрос пользователя о будущем, решении, риске, паттерне или траектории.

Примеры:
- Что будет, если я уволюсь в июне?
- Что будет, если останусь ещё на 3 месяца?
- Стоит ли идти в магистратуру в этом году?
- Если я продолжу жить в таком режиме, к чему это ведёт?
- Что изменится, если я начну терапию / спорт / новый проект?
- Почему у меня снова повторяется этот социальный паттерн и к чему он ведёт?

Prediction всегда должен рождаться из **живого вопроса пользователя**.

---

## 4. Scenario Variant
Один вариант сценария внутри вопроса.

Примеры:
- уволиться в июне
- уволиться в сентябре
- остаться, но уменьшить нагрузку
- перейти в другой отдел
- сначала собрать финансовую подушку

У каждого сценария есть:
- название
- условия
- параметры
- горизонт
- допущения
- specific context
- прогнозируемый исход

---

## 5. Context Completeness
Критически важная сущность.

Runa должна уметь отвечать не только:
- “вот прогноз”

Но и:
## “я не могу дать сильный прогноз, потому что мне не хватает вот этих данных”

Примеры недостающего контекста:
- размер финансовой подушки
- текущая роль и формат работы
- реальные требования работодателя
- наличие поддержки
- текущий режим сна
- степень выгорания
- документы компании
- offer / contract / расписание / регламент
- фактическая нагрузка
- статус отношений / среды

Runa должна уметь говорить:
- чего не хватает
- почему это важно
- в какую сферу пойти
- что именно добавить, чтобы повысить точность прогноза

Это один из ключевых product loops.

---

## 6. Prediction Report
Структурированный результат по сценарию.

Не просто “ответ модели”.

Каждый prediction report должен содержать:
- restated question
- scenario label / variant
- short conclusion
- most likely outcome
- alternative / downside / failure mode if relevant
- main risks
- leverage factors
- confidence
- affected spheres
- what changed
- depends_on
- next step
- external context synthesis
- missing context / confidence gaps if relevant

---

## 7. Scenario Comparison
Сравнение нескольких вариантов.

Это один из главных новых элементов продукта.

Пользователь должен уметь сравнивать:
- что меняется между сценариями
- где выше риск
- где больше upside
- где confidence выше
- какие сферы пострадают
- какие факторы сильнее всего меняют исход

---

## 8. External Context
Внешний мир, который усиливает prediction.

Это не просто web search.

External context делится на несколько уровней:

### A. General professional context
- статьи
- исследования
- frameworks
- expert long-form materials
- behavioural science
- management / career / health / relationship knowledge

### B. Domain-specific context
- индустрия
- рынок
- профессия
- образовательная среда
- карьерная траектория
- компания / тип компании
- регламенты, если доступны законно и этично

### C. User-supplied context
Самый сильный слой:
- документы пользователя
- рабочие регламенты
- offer / CV / job description
- заметки
- расписания
- договоры
- финансовые данные
- медицинские рекомендации
- любые материалы, которые сам пользователь хочет использовать для повышения точности

Важно:
внешний контекст должен усиливать reasoning, а не превращать продукт в свалку источников.

---

# Главный опыт продукта

## Decision Workspace

Это центральный новый UX-модуль Runa.

Decision Workspace позволяет:
- задать вопрос
- создать несколько scenario variants
- менять параметры
- добавлять новые факты
- видеть, как меняется прогноз
- видеть confidence
- понимать leverage factors
- понимать missing context
- сравнивать варианты
- возвращаться позже и обновлять расчёт

### Примеры сценариев
- “уволиться в июне”
- “уволиться в сентябре”
- “остаться, но уменьшить нагрузку”
- “перейти в другой отдел”
- “сначала закрыть финансовую подушку”

### По каждому сценарию пользователь должен видеть
- most likely outcome
- main risks
- leverage factors
- confidence
- affected spheres
- what changed relative to other scenarios
- next step
- missing context that would improve precision

---

# Что такое вау в Runa

Вау — это НЕ:
- много графа
- много AI-слов
- много сущностей
- длинные отчёты
- магическое “я знаю твоё будущее”

Вау — это когда пользователь чувствует:

## “это реально помогает мне думать о моей жизни как о системе”

И ещё сильнее:

## “система показала, какие 2–3 фактора реально меняют исход именно в моём случае”

То есть ключ к вау:
- conditioned prediction
- scenario comparison
- leverage factors
- missing context detection
- progressive precision
- grounded external context
- ощущение, что прогноз становится точнее по мере добавления реальных данных

---

# Core product loops

## Loop 1 — Question → Prediction
1. Пользователь задаёт вопрос
2. Runa строит prediction
3. Показывает outcome, risks, leverage factors, confidence

---

## Loop 2 — Missing context → Better prediction
1. Runa говорит, каких данных не хватает
2. Пользователь идёт в нужную сферу
3. Добавляет факты / документы / параметры
4. Prediction пересчитывается
5. Confidence растёт

Это один из самых важных retention loops.

---

## Loop 3 — Scenario comparison
1. Пользователь создаёт несколько вариантов
2. Сравнивает исходы
3. Понимает, что реально меняет исход
4. Возвращается, чтобы прокрутить ещё один вариант

---

## Loop 4 — Prediction vs Reality
1. Пользователь возвращается позже
2. Обновляет факты
3. Сравнивает старый прогноз с новой реальностью
4. Пересчитывает сценарии
5. Использует Runa как живой decision simulator

---

# Роль текущих частей продукта

## Today
Today остаётся, но не как главный смысл продукта.

Today нужен для:
- состояния
- давления
- фокуса
- краткой daily clarity
- удержания и возврата

Но новый core не Today.
Today теперь — вход в более глубокое decision пространство.

Он может:
- подсвечивать риск
- подталкивать к вопросу
- напоминать об incomplete prediction
- предлагать обновить scenario after change

---

## Life Map
Life Map остаётся и становится более осмысленным.

Он нужен как:
- карта жизни
- структура сфер
- объяснение, из чего вообще состоит модель пользователя
- база для перехода в сферы и наращивания контекста

---

## Sphere
Сфера становится главным местом **сбора точного контекста**.

Не просто “поговорить про сферу”.
А:
- уточнить вводные
- загрузить реальную информацию
- сделать prediction точнее

Сферы теперь критичны для progressive precision.

---

## Path
Path в старом смысле как auto-generated future mode больше не является главным.

Path можно переосмыслить в одно из двух:
1. как history of prediction reports
2. как entrypoint в Decision Workspace

Если между ними конфликт — приоритет у Decision Workspace.

---

# Архитектура продукта

## Слой 1 — Personal World Model
Живая модель пользователя.

Содержит:
- graph entities
- sphere state
- recent changes
- action history
- dynamic weights
- context completeness signals

Это фундамент.

---

## Слой 2 — Context Acquisition Layer
Отвечает за сбор и улучшение контекста.

Источники:
- onboarding
- sphere chats
- user edits
- uploaded files
- structured data fields
- daily updates
- future follow-ups

Этот слой должен уметь:
- обнаруживать missing context
- направлять пользователя в нужную сферу
- предлагать, что добавить

---

## Слой 3 — Prediction Question Engine
Принимает пользовательский вопрос и превращает его в prediction job.

Задачи:
- question classification
- scenario framing
- parameter extraction
- horizon detection
- identify ambiguity
- identify context gaps

---

## Слой 4 — External Context Engine
Подтягивает внешний мир.

Источники:
- open web
- professional articles
- domain materials
- user-supplied documents
- later: structured providers / domain APIs

Задачи:
- retrieval
- filtering
- quality scoring
- source transparency
- synthesis support

Важно:
не собирать всё подряд, а усиливать personal prediction reasoning.

---

## Слой 5 — Scenario Engine
Ядро системы.

Строит:
- most likely scenario
- alternative scenario(s)
- downside / failure mode
- leverage factors
- affected spheres
- dependencies
- uncertainty / confidence

Это не “магия”.
Это engine личной симуляции вариантов.

---

## Слой 6 — Comparison Engine
Сравнивает варианты между собой.

Показывает:
- what changed
- what matters most
- which factor is bottleneck
- trade-offs between scenarios
- confidence differences
- sphere impact deltas

Это один из будущих сильнейших differentiators продукта.

---

## Слой 7 — Interface Layer
Frontend должен перестать быть просто набором экранов.

Главная цель UI:
## помогать человеку мыслить вариантами, параметрами, рисками и изменяемыми факторами

Главные поверхности:
- Today
- Life Map
- Sphere Detail
- Prediction
- Decision Workspace
- Comparison view
- later: 3D consequence map / simulation view

---

# Роль 3D и граф-визуализации

3D / graph visualization допустимы и желательны, НО:

## Только если они усиливают Decision Workspace.

Мы не делаем 3D ради “вау-графа”.

3D имеет смысл, если он показывает:
- как решение влияет на сферы
- где растёт риск
- где есть опоры
- какие узлы самые критичные
- как меняется форма модели при переключении сценария
- где самая высокая неопределённость

То есть:
## 3D = interactive consequence map
а не просто красивый graph mode

---

# Куда мы идём: beyond MVP

Важно:
мы больше НЕ мыслим только как “минимально доказать MVP любой ценой”.

Мы всё ещё должны быть умными и последовательными.
Но у нас есть пространство думать глубже и строить сильную архитектуру.

Это значит:
- можно закладывать мощные сущности заранее
- можно строить serious prediction system
- можно делать deeper modeling
- можно проектировать scenario comparison как ядро продукта
- можно думать о user-supplied docs, domain context и progressive precision

Но:
## complexity должна быть осмысленной, а не декоративной

Каждое решение проверяется вопросом:
**это делает prediction реально полезнее и прикладнее для жизни пользователя?**

Если нет — не делаем.

---

# Какие prediction modes особенно важны

Фокусироваться не на всём мире, а на самых сильных классах вопросов.

Приоритетные modes:
1. career / work decisions
2. burnout / lifestyle trajectory
3. relationship / social pattern decisions
4. startup / risk decisions
5. education / path choice

Эти modes самые прикладные и понятные.

---

# Confidence architecture

Prediction обязательно должен быть вероятностным и честным.

У каждого prediction должны быть:
- confidence level
- confidence reasons
- what is known
- what is missing
- what would improve precision

Нельзя делать вид, что система “знает будущее”.

Правильный подход:
- вероятностный вывод
- conditioned outcome
- explicit assumptions
- clear missing context
- honest uncertainty

---

# Что Prediction НЕ должен делать

Prediction не должен:
- изображать оракула
- говорить с фальшивой уверенностью
- подменять врача / юриста / терапевта
- строиться только на красивом тексте LLM
- перегружать человека гигантскими отчётами без смысла
- опираться на внешний шум без фильтрации
- строиться из complexity ради complexity

---

# Что для нас now counts as success

Успех — это не “много AI”.
И не “много архитектуры”.

Успех — это когда пользователь:
- задаёт реальный вопрос
- получает прогноз по своему случаю
- понимает, что влияет на исход
- видит, чего не хватает для точности
- добавляет контекст
- пересчитывает прогноз
- сравнивает варианты
- возвращается снова

Если это происходит — продукт становится реально нужным.

---

# Техническая архитектура (high-level)

## Backend
- Python / FastAPI
- prediction engine
- scenario engine
- context completeness logic
- retrieval / external context layer
- graph logic
- file ingestion / extraction
- future comparison layer

## AI layer
- structured prompts
- scenario synthesis
- question classification
- missing context detection
- external evidence synthesis
- comparison reasoning

## Personal model layer
- graph DB / graph queries
- sphere state
- recent check-ins
- recent action feedback
- dynamic weights / relationships
- event and pattern memory

## Retrieval layer
- web retrieval
- source filtering
- full-text extraction
- later: documents / PDFs / domain providers
- later: user-supplied files ingestion

## Frontend
- React / TypeScript
- Today
- Life Map
- Sphere Detail
- Prediction
- Decision Workspace
- Scenario Comparison
- later: 3D consequence map

---

# Product priorities now

Приоритет №1:
## Decision Workspace

Приоритет №2:
## Progressive precision through missing context

Приоритет №3:
## Stronger scenario comparison

Приоритет №4:
## Better external and document grounding

Приоритет №5:
## 3D / consequence visualization only when it supports decisions

---

# Как тебе работать со мной

Я не просто хочу “чтобы код работал”.

Я хочу, чтобы ты думал как:
- продуктовый архитектор
- технический кофаундер
- системный дизайнер

### Твои задачи
- не просто выполнять задачу
- а думать, усиливает ли это новый core Runa
- если видишь, что решение не усиливает Decision Workspace — говори
- если видишь путь сильнее — предлагай
- если видишь риск декоративной complexity — тормози

---

# Общение со мной

- Всегда отвечай на русском
- Объясняй простыми словами, что делаешь и зачем
- После каждого блока говори:
  - что изменил
  - почему
  - как проверить
- Не уходи в технический жаргон без необходимости
- Думай как кофаундер, а не как “junior executor”

---

# Правила работы с кодом

## Общее
- типизация везде
- осмысленные схемы данных
- никаких magic strings без причины
- чистые contracts между backend и frontend
- если вводим новую продуктовую сущность — формализуем её явно

## Промпты
- все промпты отдельно
- не инлайн в коде
- prompts versionable
- prompts должны отражать новый core: scenario reasoning, missing context, confidence, leverage factors

## API
- structured responses
- понятные схемы
- желательно проектировать API вокруг новых сущностей:
  - PredictionQuestion
  - ScenarioVariant
  - PredictionReport
  - ContextCompleteness
  - ComparisonResult

## Граф
- граф нужен для prediction usefulness
- не плодить сущности ради graph beauty
- каждая сущность графа должна усиливать decision reasoning

---

# Главный фильтр для всех решений

Перед любым изменением задавай вопрос:

## “Это делает Runa сильнее как personal decision intelligence system?”

И ещё конкретнее:

## “Это помогает человеку лучше моделировать важные решения своей жизни?”

Если нет — не туда идём.

---

# Что делать после каждого шага

После каждого заметного изменения:
1. коротко объясни, что сделал
2. скажи, зачем это усиливает новый core
3. скажи, как проверить
4. предложи следующий логичный шаг
5. честно укажи ограничения / риск / техдолг

---

# Финальный принцип

Runa — это не mental wellness toy.
Не self-help dashboard.
Не граф ради графа.

## Это система личного моделирования решений.

Она должна помогать человеку:
- видеть варианты
- понимать последствия
- понимать, что реально меняет исход
- добирать недостающий контекст
- принимать более сильные решения о своей жизни
