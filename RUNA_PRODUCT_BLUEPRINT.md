# RUNA — Product Blueprint v2

## Статус документа

Это обновлённый стратегический документ нового ядра продукта Runa.

Он НЕ заменяет `CLAUDE.md`.
Он существует рядом с ним и отвечает на другой вопрос:

- `CLAUDE.md` = как Claude должен думать и работать внутри проекта
- `RUNA_PRODUCT_BLUEPRINT.md` = что именно мы строим, зачем, из каких сущностей и слоёв, и куда это должно прийти

Этот v2 сохраняет правильное ядро предыдущей версии, но делает архитектуру полной и более взрослой:

- сохраняет центральность **Decision Workspace**
- сохраняет **Personal World Model**
- добавляет **Personal OSINT Layer** как ключевой differentiator
- разводит архитектурные слои более строго
- фиксирует конкретный **tech stack** по слоям
- фиксирует разницу между **RAG**, **OSINT** и **Signal Fusion**

---

# 1. Новая суть продукта

## Коротко

Runa — это **personal decision intelligence system**.

Она помогает человеку моделировать важные жизненные решения на основе:
- его личной модели жизни
- его сфер
- его паттернов и ограничений
- его среды
- его документов и фактов
- внешнего профессионального и публичного контекста
- живых сигналов из внешнего мира, которые реально влияют на исход решения

Главная идея:

## **Simulate your life decisions before you make them.**

Но теперь точнее:

## **Use your personal context + the real outside world to make stronger life decisions.**

---

# 2. Почему мы меняем фокус

## Что было слабым раньше

Старый prediction-layer был недостаточно сильным, потому что:
- система сама генерировала prediction без достаточного запроса пользователя
- prediction ощущался как декоративная фича
- сценарии выглядели “умно”, но не всегда были реально прикладными
- пользователь не чувствовал, что это прогноз именно под его случай и его реальные вводные
- внешний контекст был слишком слабым и часто выглядел как декоративный блок со ссылками
- web-grounding не превращался в decision-grade usefulness

В итоге продукт был умным, но не обязательно нужным.

## Что мы поняли

По-настоящему цепляет не абстрактный AI-коучинг и не общий dashboard of life.

Цепляет вот что:

## **персонализированный прогноз по моему реальному вопросу, моей реальной жизни, моим реальным ограничениям и реальному внешнему миру вокруг этого вопроса**

То есть человек хочет:
- задать важный вопрос
- получить прогноз именно под свой случай
- понять, что сильнее всего влияет на исход
- увидеть, чего не хватает для точности
- добавить данные и сделать прогноз сильнее
- прокрутить альтернативные сценарии своей жизни
- чувствовать, что система учла не только его контекст, но и реальную ситуацию снаружи

---

# 3. Новый продуктовый core

## Новый core Runa

Runa — это не просто чат, не просто life map и не просто prediction card.

Runa — это:

## **Decision Workspace + Personal World Model + Personal OSINT Layer**

Где:
- **Personal World Model** = живая модель жизни пользователя
- **Decision Workspace** = пространство, где пользователь моделирует варианты решений
- **Personal OSINT Layer** = внешний intelligence layer, который понимает, что происходит в мире вокруг конкретного вопроса пользователя, и вшивает это в prediction

Важно:
OSINT здесь понимается **не как серая зона и не как незаконный сбор данных**.

Мы имеем в виду:
- open web
- новости
- рыночные сигналы
- погоду
- официальные API и публичные датасеты
- публичные policy / industry / company / macro signals
- later: lawful paid providers under clear product need
- user-supplied documents and materials

То есть:

## только законный, этичный и product-useful external intelligence

---

# 4. Главный пользовательский опыт

## Decision Workspace

Decision Workspace — это центральный модуль продукта.

В нём пользователь может:
- задать важный вопрос о будущем
- создать несколько сценариев
- менять параметры сценария
- добавлять новые факты
- видеть, как меняется прогноз
- понимать, какие факторы самые критичные
- понимать, каких данных не хватает
- видеть, какие сферы потянут последствия
- видеть, какие внешние сигналы реально влияют на вывод
- сравнивать сценарии
- возвращаться позже и обновлять прогноз на новых вводных и новых внешних условиях

### Пример
Пользователь задаёт вопрос:
**“Что будет, если я уволюсь?”**

Дальше он создаёт варианты:
- уволиться в июне
- уволиться в сентябре
- остаться, но уменьшить нагрузку
- перейти в другой отдел
- сначала собрать финансовую подушку

И по каждому варианту Runa показывает:
- most likely outcome
- main risks
- leverage factors
- confidence
- affected spheres
- what changed
- depends_on
- missing context
- external signals that matter
- next step

---

# 5. Что создаёт вау

Вау не в количестве AI.
И не в количестве источников.
И не в красоте графа.

Вау появляется, когда пользователь чувствует:

## “эта система реально помогает мне думать о своей жизни как о системе вариантов, последствий и внешних условий”

И ещё сильнее:

## “она показала, какие 2–3 фактора реально меняют исход именно в моём случае”

И ещё сильнее:

## “этот прогноз стал сильнее, потому что Runa реально посмотрела мир вокруг моего вопроса и встроила это в вывод”

Главный вау-эффект дают:

### 1. Conditioned prediction
Не просто “что будет”, а:
- что будет **при определённых условиях**
- что изменится, если параметр X другой
- в каком случае риск растёт
- в каком случае исход улучшается
- какие внешние изменения перевернут решение

### 2. Scenario comparison
Пользователь может сравнить несколько вариантов одной жизни.

### 3. Missing context detection
Система говорит, чего ей не хватает для более сильного прогноза.

### 4. Progressive precision
Чем больше релевантного контекста добавлено, тем точнее и полезнее prediction.

### 5. Leverage factors
Система показывает, какие факторы реально двигают исход.

### 6. Decision-specific external intelligence
Система не просто “ищет статьи”, а вытаскивает **релевантные сигналы**, которые действительно влияют на outcome.

---

# 6. Основные сущности продукта

## 6.1 Personal Graph
Живая модель жизни пользователя.

Содержит:
- сферы
- паттерны
- блокеры
- ценности
- цели
- события
- последние изменения
- динамику
- связи между узлами
- recent action feedback
- recent check-ins
- влияние одной сферы на другую

Personal Graph нужен не ради визуализации, а как база личного reasoning.

## 6.2 Sphere
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

Новая роль сферы:

## сфера — это место, где собирается контекст, повышающий точность prediction

Внутри сферы могут быть:
- facts
- structured inputs
- free-form notes
- chats
- uploaded files
- specific environment context
- timelines
- responsibilities
- constraints

## 6.3 Prediction Question
Вопрос пользователя, который запускает prediction.

Типы вопросов:
- decision
- trajectory
- change impact
- relationship
- pattern risk
- later: more domain-specific categories

Prediction всегда должен запускаться по реальному вопросу пользователя, а не навязываться системой.

## 6.4 Scenario Variant
Один вариант внутри одного вопроса.

У варианта есть:
- label
- name
- description
- assumptions
- parameters
- horizon
- related spheres
- relevant constraints
- user-specified changes

Примеры:
- “уволиться в июне”
- “уволиться в сентябре”
- “остаться и снизить нагрузку”
- “уйти после накопления подушки”
- “сменить отдел, не увольняясь”

## 6.5 Context Completeness
Оценка того, насколько система может дать сильный прогноз.

Context Completeness должен отвечать на вопросы:
- чего не хватает?
- почему это важно?
- в какой сфере это нужно добавить?
- какой тип данных нужен?
- насколько это повысит confidence?
- не хватает ли также внешних сигналов?

Примеры недостающего контекста:
- финансовая подушка
- реальный формат работы
- условия контракта
- текущая медицинская нагрузка
- режим сна
- support system
- карьерная среда
- семейный контекст
- документ работодателя
- offer / расписание / финансовые цифры

## 6.6 External Signal
Новая центральная сущность.

External Signal — это не просто ссылка и не просто статья.

Это нормализованный сигнал из внешнего мира.

У сигнала могут быть поля:
- source_type
- source_name
- timestamp
- freshness_score
- domain
- relevance_score
- signal_type
- extracted_claim
- impact_direction
- confidence
- linked_question_mode
- why_it_matters

## 6.7 Prediction Report
Структурированный выход по сценарию.

Поля могут включать:
- question
- restated_question
- scenario label
- summary
- most_likely_outcome
- alternative_outcomes
- main_risks
- leverage_factors
- confidence
- confidence_reason
- affected_spheres
- what_changed
- depends_on
- next_step
- external_signal_synthesis
- conditions_that_flip_the_answer
- missing_context
- source_transparency metadata

## 6.8 Scenario Comparison
Сравнение нескольких Scenario Variants по одному Question.

Показывает:
- где выше риск
- где выше upside
- где выше confidence
- какие сферы выигрывают
- какие сферы проседают
- какие leverage factors самые чувствительные
- какие trade-offs есть между вариантами
- как внешние условия меняют привлекательность каждого сценария

## 6.9 Retrieval Plan
Промежуточная сущность между вопросом и retrieval.

Система должна уметь формировать план:
- какой question mode определён
- какие source families нужны
- какая freshness критична
- какие сигналы нужны
- что уже известно из personal model
- чего не хватает

## 6.10 Signal Bundle
Набор нормализованных сигналов, уже отобранных под конкретный вопрос и готовых для fusion.

---

# 7. Core product loops

## 7.1 Question → Prediction
1. Пользователь задаёт вопрос
2. Runa читает личный контекст
3. Подключает decision-specific external signals
4. Формирует prediction report

Ценность:
- быстрый полезный прогноз по реальному вопросу

## 7.2 Missing Context → Better Prediction
1. Runa говорит, чего не хватает
2. Пользователь идёт в нужную сферу
3. Добавляет данные / документы / параметры
4. Prediction пересчитывается
5. Confidence растёт

Это один из главных retention loops.

## 7.3 Scenario Comparison Loop
1. Пользователь создаёт несколько вариантов
2. Сравнивает исходы
3. Понимает, где реальные trade-offs
4. Возвращается, чтобы прокрутить ещё один вариант

Это один из главных вау-loop’ов.

## 7.4 External World Update → Prediction Update
1. Во внешнем мире меняется значимый сигнал
2. Это может менять полезность сценария
3. Пользователь пересматривает прогноз
4. Runa помогает переоценить решение на новых условиях

## 7.5 Prediction vs Reality Loop
1. Пользователь возвращается через время
2. Обновляет жизненные вводные
3. Смотрит, как изменился прогноз
4. Сверяет старые сценарии с новой реальностью
5. Использует Runa как живую decision system

---

# 8. Роль текущих поверхностей продукта

## 8.1 Today
Today остаётся, но перестаёт быть главным смыслом продукта.

Роль Today:
- daily clarity
- state summary
- pressure / focus
- reminder of unfinished decisions
- quick entry into active prediction questions
- quick entry into missing context requests
- quick entry into outdated predictions after external change

Today — это лёгкая ежедневная поверхность, а не центр всей ценности.

## 8.2 Life Map
Life Map остаётся как карта жизни пользователя.

Роль:
- показать структуру жизни
- объяснить, из чего состоит модель
- быть визуальной картой сфер
- служить входом в уточнение контекста

Life Map нужен как объясняющий и структурирующий слой.

## 8.3 Sphere Detail
Одна из ключевых поверхностей нового продукта.

Sphere Detail должен стать местом, где пользователь:
- уточняет факты
- добавляет structured data
- загружает документы
- формирует domain context
- закрывает missing context gaps

## 8.4 Prediction
Prediction больше не должен быть просто экраном с одиночным ответом.

Prediction становится entrypoint / container для:
- вопроса
- scenario variants
- report
- confidence
- missing context
- external signals
- comparison

## 8.5 Path
Path в старом виде больше не главный.

Есть два варианта его эволюции:
1. сделать его historical view всех prediction reports
2. превратить его в вход в Decision Workspace

Если они конфликтуют — приоритет у Decision Workspace.

---

# 9. Decision Workspace: UX blueprint

## Главные блоки интерфейса

### 1. Question Input
Пользователь формулирует вопрос.

### 2. Scenario Builder
Пользователь создаёт и редактирует варианты.

### 3. Parameters Panel
Пользователь меняет условия:
- даты
- финансовые условия
- режим
- support
- workload
- constraints
- assumptions

### 4. Prediction Reports
Карточки / панели с результатом по каждому сценарию.

### 5. Comparison View
Сводный экран различий между сценариями.

### 6. Missing Context Prompts
Подсказки:
- чего не хватает
- куда пойти
- что добавить

### 7. External Signal Influence Block
В самом основном отчёте должно быть видно:
- какие внешние сигналы реально повлияли на вывод
- почему они важны
- как они изменили risk / upside / confidence

### 8. Source Transparency Layer in UI
Рядом можно раскрыть:
- signal source
- freshness
- confidence
- why it matters

Прозрачность должна объяснять reasoning, а не просто показывать bibliography.

---

# 10. Decision-specific OSINT architecture

Мы не хотим просто “подключить больше источников”.

Это слабый путь.
Он ведёт к:
- шуму
- дорогой сложности
- плохому signal-to-noise ratio
- generic answers с большим количеством ссылок

Вместо этого Runa должна строить:

## **decision-specific OSINT architecture**

То есть для каждого класса вопроса система должна понимать:
- какие сигналы реально важны
- какие источники для этого нужны
- как взвешивать свежесть
- как отделять decision signals от шума
- как связывать эти сигналы с личным контекстом пользователя
- как превращать всё это в usable prediction

Это серьёзная архитектурная ставка.
Именно она должна отличать Runa от generic AI tools.

---

# 11. Архитектурные слои системы

## 11.1 Question Intelligence Layer
Сначала система должна понять не просто “текст вопроса”, а **класс решения**.

Примеры question modes:
- investment
- career
- health/activity
- relocation
- startup
- education
- relationship
- burnout / lifestyle trajectory
- later: other specific modes

Задачи слоя:
- question classification
- mode routing
- ambiguity detection
- intent detection
- horizon detection
- parameter hints
- initial retrieval plan generation

Без этого нельзя понять, какие внешние сигналы вообще нужны.

## 11.2 Personal Model Retrieval Layer
После классификации подтягивается личный контекст, релевантный именно для этого вопроса.

Слой должен вытаскивать:
- relevant spheres
- structured inputs
- recent changes
- constraints
- values
- patterns
- blockers
- documents
- missing context

То есть prediction строится не “про биткоин вообще”, а “про биткоин для этого пользователя при его runway, опыте, рискотерпимости и текущем состоянии”.

## 11.3 Personal OSINT Layer
Вот здесь главное отличие будущей Runa.

Не “ищем 5 статей”, а:
- определяем, какие сигналы важны для этого класса вопроса
- выбираем нужные source families
- учитываем freshness
- достаём не страницы, а decision signals
- даём signal quality score
- нормализуем всё в единый формат

Например, для investment-вопроса это должны быть не просто новости, а разные типы сигналов:
- live/near-live market data
- volatility regime
- macro / regulation / geopolitical events
- sentiment / news shocks
- later: ETF / flows / exchange / public metrics if useful

Для “идти ли на бокс” это уже другой пакет:
- weather
- air quality
- schedule / logistics
- health / load context
- maybe local disruptions

То есть OSINT слой должен быть маршрутизатором по типу решения, а не “поиском в интернете”.

## 11.4 Signal Fusion Layer
Это центральный слой будущей магии.

Именно здесь система должна:
- соединять external signals с personal constraints
- понимать, какие сигналы реально меняют outcome
- выкидывать шум
- строить “conditions under which prediction changes”
- превращать множество сигналов в usable decision logic

То есть не:
> рынок волатилен

А:
> для тебя покупка BTC сейчас выглядит слабее, потому что у тебя нет достаточной подушки, горизонт короткий, а внешний фон сейчас high-volatility / high-uncertainty

Вот это и есть usable prediction.

## 11.5 Scenario Engine
После fusion строятся не один ответ, а сценарии.

Например:
- купить сейчас
- подождать 2 недели
- взять меньшую позицию
- не входить до X
- выбрать ETH вместо BTC
- не покупать ничего

И для каждого сценария внешний мир должен быть встроен в:
- most likely outcome
- main risks
- leverage factors
- confidence reasoning
- conditions that would flip the answer

## 11.6 Source Transparency Layer
Очень важно: не прятать источники внизу как бессмысленный appendix.
Но и не делать свалку ссылок.

Нужен другой UX:
- в основном отчёте прямо видно, какие внешние сигналы повлияли на вывод
- рядом можно раскрыть:
  - signal source
  - freshness
  - confidence
  - why it matters

Прозрачность должна объяснять reasoning, а не просто показывать bibliography.

## 11.7 Comparison Engine
Сравнивает сценарии между собой.

Показывает:
- what changed
- what matters most
- trade-offs
- confidence differences
- sphere impact deltas
- how external conditions affect each variant differently

## 11.8 Evaluation / Quality Layer
Нужен слой, который не даст OSINT превратиться в красивую иллюзию.

Он должен отвечать:
- prediction стал реально полезнее или просто длиннее?
- retrieval дал signal или шум?
- свежесть учтена корректно?
- ответ стал менее generic?

## 11.9 Interface Layer
UI должен помогать человеку мыслить:
- вариантами
- параметрами
- рисками
- изменяемыми факторами
- личным контекстом
- влиянием внешнего мира

Главные поверхности:
- Today
- Life Map
- Sphere Detail
- Prediction
- Decision Workspace
- Comparison view
- later: consequence map / simulation view

---

# 12. RAG vs OSINT vs Fusion

Это критическая развилка.

## RAG ≠ OSINT

### RAG нужен для:
- user documents
- long-form domain knowledge
- archived research
- policies
- company docs
- historical memory

### OSINT нужен для:
- live / near-live external signals
- freshness-aware polling
- structured / public APIs
- news / macro / market / weather / public context
- event extraction
- signal typing
- timelines and changelogs where useful

### Fusion нужен для:
- соединения personal constraints и external signals
- выкидывания шума
- построения usable prediction logic

То есть:
- **RAG = память и глубокий контекст**
- **OSINT = живые decision signals**
- **Fusion = место, где это превращается в prediction**

---

# 13. Prediction architecture

## 13.1 High-level flow

1. **Question intake**
   - пользователь задаёт вопрос
   - система определяет тип вопроса
   - система выделяет горизонт, ambiguity, intent

2. **Question Intelligence**
   - система определяет question mode
   - формирует retrieval plan

3. **Personal model retrieval**
   - извлекается релевантный кусок graph / sphere context
   - recent events
   - patterns
   - blockers
   - values
   - action feedback
   - check-ins
   - sphere dynamics
   - documents

4. **Context completeness assessment**
   - система оценивает, чего не хватает
   - формирует список missing inputs

5. **Decision-specific OSINT retrieval**
   - выбираются source families
   - запускается retrieval
   - собираются signals
   - считается freshness and quality

6. **Signal normalization**
   - retrieved items превращаются в External Signals

7. **Signal fusion**
   - personal constraints + external signals → usable decision logic

8. **Scenario synthesis**
   - строится prediction report по каждому сценарию на основе:
     - personal graph
     - scenario assumptions
     - external signals
     - uncertainty

9. **Comparison synthesis**
   - строится сравнительный вывод между вариантами

10. **UI rendering**
   - user sees scenario-level output
   - user sees confidence and missing context
   - user sees external signal influence
   - user can iterate

## 13.2 Prediction output principles

Prediction output должен быть:
- structured
- probabilistic
- conditioned
- comparative when relevant
- honest about uncertainty
- useful for action
- explicit about why external world matters here

Prediction НЕ должен:
- звучать как оракул
- скрывать missing context
- маскировать слабую уверенность под сильную
- быть просто красивым эссе
- быть generic web-grounded answer with citations at the bottom

---

# 14. Confidence architecture

Confidence — это отдельный важный слой.

Каждый prediction должен иметь:

### Confidence level
- low
- medium
- high

### Confidence reasons двух типов

#### A. Personal confidence reasons
Почему confidence такой со стороны личного контекста:
- хороший личный контекст
- сильные user documents
- слабые user inputs
- missing personal data
- высокий уровень неопределённости по реальной жизни пользователя

#### B. External confidence reasons
Почему confidence такой со стороны внешнего мира:
- сигналы сильные или слабые
- сигналы свежие или устаревшие
- сигналы согласованы или конфликтуют
- сигналы реально связаны с вопросом или слишком косвенные

### Precision improvement suggestions
Что повысит точность:
- добавь финансовые данные
- уточни формат работы
- загрузи job description
- добавь расписание
- уточни текущую нагрузку
- заполни missing field in sphere
- дай более точный горизонт решения
- дождись обновления внешних условий, если signal freshness критична

---

# 15. Leverage factors

Leverage factors — одна из самых сильных частей продукта.

Система должна показывать:

## какие 2–3 фактора сильнее всего меняют исход

Примеры:
- размер финансовой подушки
- текущая степень выгорания
- наличие внешней структуры
- support system
- реальность карьерных альтернатив
- качество режима
- наличие времени на переходный период
- регуляторная неопределённость
- состояние рынка / найма / погоды / логистики в зависимости от mode

Это делает prediction прикладным.

---

# 16. Decision-specific OSINT modes

Не нужно сразу пытаться покрыть весь мир.

Нужно строить по классам вопросов.

## Для каждого класса вопроса система должна знать:
- какие сигналы важны
- какие источники нужны
- какой уровень свежести критичен
- какие внешние факторы действительно двигают outcome
- как эти факторы соединяются с личными ограничениями

### 16.1 Investment / financial decisions
Сигналы могут включать:
- текущую цену
- trend / volatility context
- macro news
- regulation signals
- geopolitical events
- market sentiment proxies

Но финальный вывод должен зависеть и от:
- подушки пользователя
- горизонта
- tolerance to drawdown
- уровня знаний
- эмоциональной устойчивости

### 16.2 Health / activity decisions
Сигналы могут включать:
- weather
- location-dependent conditions
- air quality
- schedule
- public health context
- training intensity / constraints if available

Но финальный вывод должен зависеть и от:
- состояния пользователя
- сна
- нагрузки
- recovery
- цели

### 16.3 Career decisions
Сигналы могут включать:
- market conditions
- hiring environment
- company context
- role demand
- industry signals

Но финальный вывод должен зависеть и от:
- burnout
- finances
- runway
- alternatives
- support system

### 16.4 Later mode packs
Потом можно добавлять:
- relocation
- startup
- education
- relationship / social context where lawful external signals are meaningful

---

# 17. Paid data providers and source strategy

Платные источники — **да, но не как первый принцип**.

Сначала надо спроектировать **signal architecture**, а уже потом подбирать, какие источники действительно усиливают каждый mode.

Иначе можно купить много данных и всё равно получать общие ответы.

Правильный принцип:
- сначала question-type routing
- потом signal taxonomy
- потом freshness logic
- потом personal-signal fusion
- потом выбор платных провайдеров там, где это реально усиливает usefulness

---

# 18. Technical architecture by layer

## 18.1 Interface Layer

### Frontend stack
- React + TypeScript + Vite
- TanStack Query
- Zustand
- shadcn/ui + Tailwind
- Recharts
- later: React Flow or Three.js only if consequence map is actually useful

### Why
- нужен быстрый современный frontend для product surfaces
- TanStack Query нужен для prediction jobs, reruns, source expansion, OSINT refresh, polling
- Zustand удобен для локального UI-state без излишнего Redux overhead
- Tailwind / shadcn ускоряют сборку интерфейсов

## 18.2 API / Application Layer

### Backend stack
- Python 3.12+
- FastAPI
- Pydantic v2
- uvicorn / gunicorn
- httpx
- orjson
- tenacity
- structlog

### Why
- FastAPI = typed async API core
- Pydantic v2 = строгие схемы и structured contracts
- httpx = внешние API и source adapters
- tenacity = retries для нестабильных источников
- structlog = наблюдаемость retrieval / signal pipelines

## 18.3 Workflow / Orchestration Layer

### Stack
- Temporal
- Temporal Python SDK
- dedicated workers for:
  - retrieval
  - extraction
  - reranking
  - summarization
  - signal fusion

### Why
- для реального OSINT engine недостаточно FastAPI background tasks
- нужны fan-out workflows, retries, schedules, timeouts, partial failures, periodic refresh, cancellation and restart semantics

### Not primary choice
- Celery не должен быть core orchestrator для stateful multi-step pipelines

## 18.4 Personal World Model Layer

### A. Graph memory
- Neo4j
- Cypher
- later selectively: Neo4j Graph Data Science

### B. Relational system-of-record
- PostgreSQL
- SQLAlchemy 2.0 or SQLModel

### Why
- Neo4j = личная world model, сферы, связи, pattern relations, affected_spheres
- Postgres = prediction jobs, source runs, user settings, signal records, audit tables, telemetry, evaluation data

### Design principle
- Neo4j = personal world model
- Postgres = system-of-record
- не надо делать Neo4j единственным хранилищем всего

## 18.5 Retrieval / RAG Layer

### Vector store
- Qdrant

### Embeddings
- strong hosted embeddings API for quality
- later or cheaper paths: FastEmbed / sentence-transformers for selected pipelines

### Reranking
- cross-encoder reranker for quality-sensitive retrieval
- later: ColBERT-like late interaction only if it gives real uplift

### Document extraction / parsing
- Unstructured
- PyMuPDF
- Trafilatura
- readability-lxml
- BeautifulSoup

### Why
- RAG нужен для user documents, deep knowledge, archived memory, policies, job docs
- просто dense retrieval не даст decision-grade quality

## 18.6 Personal OSINT Layer

### Source adapters
- httpx
- Playwright where browser rendering is necessary
- RSS / Atom parsers
- official APIs where available
- later: paid providers only for specific high-value modes

### Cache / freshness / hot data
- Redis

Redis нужен для:
- query result caching
- freshness windows
- dedupe
- hot signals
- rate-limit shields

### Search entrypoint principle
На старте не строим свой web crawler.

Нужны:
- general search adapter
- news adapter
- market / weather / structured adapter
- site-specific adapters for high-value domains

### Event extraction / signal normalization
- Python services
- Pydantic schemas
- optional lightweight NLP pipeline
- LLM extraction only where rules do not suffice

Каждый retrieved item должен приводиться к сущности `ExternalSignal`.

## 18.7 Signal Fusion / Reasoning Layer

### LLM stack principle
- one strong reasoning model for final synthesis
- one cheaper model for extraction / labeling / classification

### Framework principle
- no heavy LangChain-first architecture
- prefer own services + typed prompts
- thin orchestration layer
- instructor / structured outputs pattern

### Structured outputs
Все ключевые стадии должны возвращать схемы:
- QuestionMode
- RetrievalPlan
- ExternalSignal
- SignalBundle
- PredictionReport
- ComparisonResult

Нельзя делать:
- “просто много текста и как-нибудь распарсим”

## 18.8 Evaluation / Quality Layer

### Stack
- Postgres tables for evaluation runs
- Langfuse or equivalent for traces / observability
- Braintrust or own eval harness
- golden question sets by mode:
  - investment
  - career
  - health/activity
  - education
  - startup

### What to measure
- source usefulness
- signal relevance
- freshness correctness
- contradiction rate
- genericness score
- improvement over baseline
- user-perceived usefulness

Без eval нельзя понять, делает ли новый OSINT слой prediction сильнее или просто делает его длиннее.

## 18.9 Infra / Deployment Layer

### Stack
- Docker
- Docker Compose locally
- later Kubernetes only if scale or ops complexity truly justifies it
- PostgreSQL
- Neo4j
- Qdrant
- Redis
- Temporal server
- S3-compatible object storage for files and source snapshots

Это серьёзный, но понятный стек.

---

# 19. Mode-specific source packs

Не всё сразу.
Нужно делать **mode packs**.

## 19.1 Investment / crypto pack
- market price API
- macro / news API
- regulatory / news feeds
- curated financial articles
- user financial sphere + risk profile

## 19.2 Health / activity pack
- weather API
- air quality API
- calendar / schedule
- user health / recovery sphere
- later: wearable integrations if ever justified

## 19.3 Career pack
- hiring / market signals
- company news
- industry demand signals
- user burnout / runway sphere
- uploaded JD / offer / policy docs

Вот так OSINT становится decision-specific, а не “поиск в интернете вообще”.

---

# 20. 3D и граф-визуализация

3D и graph mode допустимы, но только если усиливают core.

## Правильная роль 3D
3D = **interactive consequence map**

Он должен показывать:
- как решение влияет на сферы
- где растёт риск
- где опора
- где неопределённость
- как меняется graph shape при переключении сценариев
- какие узлы критичны

## Неправильная роль 3D
- просто красивый graph
- complexity ради вау
- визуализация без decision utility

---

# 21. Beyond MVP — как мы теперь думаем

Мы больше не думаем только как “сделать маленький MVP любой ценой”.

У нас есть пространство строить глубже.
Но это НЕ значит строить всё подряд.

Новый принцип:

## complexity допустима только тогда, когда она усиливает prediction usefulness

То есть:
- мощная архитектура — да
- продуманная система — да
- лишняя декоративная сложность — нет

Мы можем идти дальше MVP, если:
- это строит strong decision system
- это усиливает progressive precision
- это делает scenario comparison сильнее
- это создаёт реальную reason to return
- это делает personal OSINT layer полезнее, а не просто шире

---

# 22. What success looks like

Успех нового ядра Runa выглядит так:

Пользователь:
1. задаёт важный вопрос
2. получает полезный personal prediction
3. понимает, какие факторы реально двигают исход
4. видит, чего не хватает для точности
5. добавляет контекст
6. пересчитывает прогноз
7. сравнивает несколько вариантов
8. чувствует, что система учла и его жизнь, и внешний мир
9. возвращается позже, чтобы обновить ситуацию

Если prediction по внешне-зависимым вопросам всё ещё звучит как generic advice,
значит система ещё не дошла до нужного уровня.

---

# 23. What we must avoid

Нельзя:
- делать AI-магический театр
- перегружать человека псевдоумными отчётами
- строить graph ради graph
- строить 3D ради 3D
- превращать external context в свалку ссылок
- делать вид, что система знает будущее наверняка
- гнаться за количеством источников вместо качества signals
- строить retrieval engine ради retrieval engine
- путать RAG и OSINT
- маскировать слабый retrieval под “intelligence”
- гнаться за complexity, которая не усиливает decision usefulness

---

# 24. Главный фильтр для всех решений

Перед любой продуктовой или технической идеей задаём вопрос:

## **Это делает Runa сильнее как personal decision intelligence system?**

И ещё конкретнее:

## **Это помогает человеку лучше моделировать важные решения своей жизни за счёт сильного соединения личного контекста и внешнего мира?**

Если нет — значит не туда идём.

---

# 25. Куда идти дальше

Самые логичные следующие большие направления:

### A. Закрепить новую сущностную модель в коде
- PredictionQuestion
- ScenarioVariant
- ContextCompleteness
- ExternalSignal
- RetrievalPlan
- SignalBundle
- PredictionReport
- ScenarioComparison

### B. Построить первый настоящий decision-specific OSINT pipeline
- question routing
- source family selection
- signal normalization
- freshness scoring
- signal quality scoring

### C. Построить первый настоящий Signal Fusion layer
- personal constraints + external signals
- conditions that flip the answer
- scenario-level risk changes

### D. Усилить source transparency inside main prediction
- not appendix
- but reasoning-explaining transparency

### E. Усилить evaluation harness
- golden questions
- baseline vs new architecture
- usefulness measurements

### F. Потом усиливать comparison, advanced retrieval, consequence map

---

# 26. Финальная формулировка

Runa — это не mental wellness toy.
Не dashboard.
Не graph demo.
И не generic web-grounded chatbot.

## Это система личного моделирования решений,
## усиленная personal OSINT intelligence.

Она должна помогать человеку:
- видеть варианты
- понимать последствия
- понимать, что реально меняет исход
- добирать недостающий контекст
- учитывать реальный внешний мир
- сравнивать сценарии
- принимать более сильные решения о своей жизни

---

# 27. Итоговая формула

## Personal World Model
+
## Decision Workspace
+
## Decision-specific Personal OSINT
=
## Prediction, который реально ощущается полезным именно мне



 # Rule: Every New Feature Must Be i18n-Ready by Default

  Runa is being built as a global product. Russian is the current primary working language, but English must be
  promotable to primary language without backend rewrites.

  Every new step must respect the following rules. If a step cannot respect them, the report must explicitly flag what
  was left as language-specific and why.

  ## Hard rules for any new code

  ### 1. Internal model stays canonical (English, language-agnostic)
  New entities, enums, states, keys, types, contracts, routing categories, schemas, database fields must use stable
  English-based canonical names.

  Forbidden:
  - Russian strings as enum values
  - Russian keys in JSON schemas
  - Russian-based fact_key / state / mode values
  - Business logic branching on Russian substrings as the source of truth

  Required:
  - Canonical English identifiers (`financial.base_salary`, `adoption_state = adopted`, `selected_by = primary_routing`,
   `state = invalidated_by_document`)
  - Constrained enums / Literal types over free text
  - Stable machine-readable values independent of display language

  ### 2. No hardcoded Russian in UI components
  New frontend code must not embed Russian strings directly in JSX/TSX component bodies.

  Required:
  - All user-visible strings go through a centralized labels layer (e.g. `frontend/src/labels.ts` or equivalent)
  - Components reference labels by stable keys: `t("promoted_facts.title")`, not `"Персистентные факты"` inline
  - Field `id` / `key` / `data-*` attributes stay canonical English, separate from display text

  If the labels layer does not yet exist when a step needs UI strings:
  - Still define a local constants block at the top of the component with English keys → Russian values
  - Report this as "temporary inline dictionary, should move to central labels layer later"
  - Do NOT scatter raw Russian strings across JSX

  ### 3. Prompts must not assume Russian-only operation
  LLM prompts may currently be written in Russian when helpful, but:

  Forbidden:
  - Prompt instructions that require the user input to be in Russian
  - Prompt outputs that return Russian free text as a system contract
  - Extraction targets that only work on Russian phrasing

  Required:
  - Prompt outputs constrained to canonical enums / keys / structured JSON
  - Extraction logic that works on the language of the document, not a fixed language
  - Prompts designed so that the same internal fact can come from an English, Russian, or Spanish document
  - Where classification is needed, use constrained output (enum choice) instead of free text

  ### 4. Heuristic keyword matching must be isolated and clearly labeled
  Sometimes a pragmatic step needs keyword matching in multiple languages (e.g. "accepted" / "принял" / "aceptado").

  Required:
  - Keep keyword lists in small isolated modules or constants, not spread across business logic
  - Clearly label them in comments as `# LANG-FALLBACK: keyword heuristic, replace with canonical classifier later`
  - Include multiple languages in the list when feasible (RU + EN minimum; ES if obvious)
  - Never make keyword matching the only path — always have an LLM classifier / canonical mapper on top when the signal
  matters for persistent state

  ### 5. Document language is independent of user language
  New document pipeline logic must not assume that documents are in the same language as the user question.

  Required:
  - Evidence extraction must work on any language the document is in
  - Canonical fact keys must normalize facts from different-language documents to the same key
  - UI rendering of facts must not depend on the document source language

  ### 6. New states, actions, fields must be canonical English
  When adding a new state, lifecycle transition, action type, or persistent field:

  Required:
  - Name it in canonical English (`invalidated_by_document`, `rescue_routing`, `pending_confirmation`)
  - Use it in the same form in backend, API, frontend types, and storage
  - Any user-visible label is a SEPARATE translation, not the canonical value itself

  Forbidden:
  - Russian state names even temporarily
  - Frontend types that mirror backend state with different (translated) values

  ### 7. New API endpoints and payloads stay canonical
  Required:
  - Endpoint paths in English: `/promoted-facts/invalidate-document`
  - Payload field names in English: `source_document_id`, `reason`
  - Response shapes in English keys
  - Optional `language` hint field if the behavior depends on user language

  ### 8. LLM outputs as system contracts must be constrained
  If an LLM output drives business logic (persistence, state change, routing, supersede, etc.):

  Required:
  - Constrain output to a fixed enum / canonical key / structured JSON
  - Validate output against the canonical set; reject free text
  - Never persist LLM free-text output as a system-of-record identifier

  Forbidden:
  - Saving the raw LLM Russian (or English) phrase as a canonical fact key
  - Routing logic that matches substrings of LLM Russian free text

  ### 9. Report must flag any Russian-specific code introduced
  At the end of every step report, include a section:

  "Russian-specific surface introduced in this step:
  - list each Russian string / keyword list / prompt / UI label
  - explain why it was necessary
  - describe how it should be generalized later (central labels, multilingual keywords, language-aware prompt, canonical
   classifier)"

  If nothing Russian-specific was introduced, state that explicitly.

  ### 10. Promotion path for any Russian-specific code
  Preferred progression for any temporary language-specific code:

  1. Temporary Russian-only heuristic (explicitly labeled `# LANG-FALLBACK`)
  2. Multilingual keyword set (RU + EN minimum)
  3. Canonical classifier / LLM mapping / structured extractor
  4. Fully i18n-safe version (central labels layer / language-aware prompts)

  A step may introduce level 1 or 2, but only if the code is isolated and the report explicitly notes what remains to be
   done.

  ### 11. Forbidden cross-cutting patterns
  These patterns must never be introduced, even as "temporary":

  - Russian-only branching inside core reasoning pipeline
  - Russian strings as dictionary keys or JSON field names
  - Russian state values in PromotedFact / ScenarioReport / WorkspaceResponse / any persistent model
  - Russian wording as the supersede / identity check for any entity
  - Russian-only prompt outputs that drive state transitions
  - Mixing Russian keys with English keys in the same structured schema

  ### 12. When in doubt
  If you are uncertain whether a new addition is i18n-safe, default to the stricter choice:
  - canonical English internal names
  - central labels layer for any UI string
  - constrained LLM output
  - multilingual keyword fallbacks
  - explicit report flag

  The goal is not "full i18n right now". The goal is: **no new step makes future English-first operation harder**.

  ### 13. Architecture target (keep this in mind every step)
  The target architecture is:

  multilingual input (RU/EN/ES documents, user messages)
      → canonical internal model (English keys, enums, states)
      → multilingual output (labels layer, language-aware prompts)                                                      
     
  Any step that makes this harder — even pragmatically — must be justified in the report and marked for later cleanup.  
                                         