# RUNA — Claude Code Instructions (Decision Intelligence + Personal OSINT Core)

## Что это за проект

Runa — это **personal decision intelligence system**.

Но важное уточнение текущего этапа:
Runa должна эволюционировать не просто в Personal Decision Workspace,
а в **personal prediction engine, усиленный personal OSINT layer**.

Пользователь приходит не за абстрактным умным текстом.
Он приходит за ответом на реальный вопрос о своей жизни,
который учитывает одновременно:
- его личный контекст
- его ограничения
- его сферы жизни
- его документы и факты
- и **реальное состояние внешнего мира вокруг вопроса**

Главная идея продукта:

## **Simulate your life decisions before you make them.**

Но теперь ещё точнее:

## **Use your personal context + the real outside world to make stronger life decisions.**

---

# Что мы поняли сейчас

## Что уже стало сильнее
Мы уже усилили:
- query-based prediction
- scenario-based reasoning
- confidence
- missing context loop
- guided enrichment
- onboarding
- first decision handoff
- structured sphere inputs

Это было правильно и полезно.

## Где сейчас главный потолок
Текущий внешний контекст всё ещё слишком слабый.

Если Runa по вопросу пользователя:
- ищет несколько статей,
- вытаскивает куски текста,
- складывает их в отдельный нижний блок,
- а потом выдаёт общий вывод,

то это **не personal prediction engine**.
Это всё ещё слишком близко к:
- обычному AI summary
- generic web-grounded answer
- декоративному external context

Мы поняли, что это ограничение **не чинится одним промптом**.

Проблема не только в формулировке ответа.
Проблема в том, что внешний мир пока подключён как слабый текстовый appendage,
а не как decision-grade intelligence layer.

---

# Новый стратегический акцент

## Runa = Decision Workspace + Personal World Model + Personal OSINT Layer

Это значит:

- **Personal World Model** = живая модель жизни пользователя
- **Decision Workspace** = место, где моделируются варианты решений
- **Personal OSINT Layer** = слой внешней intelligence, который понимает,
  что происходит в мире вокруг конкретного вопроса пользователя,
  и вшивает это в prediction

Важно:
OSINT здесь понимается **не как серая зона и не как незаконный сбор данных**.

Мы имеем в виду:
- open web
- новости
- market signals
- weather
- public domain materials
- official datasets
- public policies
- public company / education / industry / macro context
- later: structured lawful data providers
- user-supplied documents and materials

То есть:
## только законный, этичный и product-useful external intelligence

---

# Главная новая ставка

## Decision-specific OSINT architecture

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
- какие сигналы реально важны;
- какие источники для этого нужны;
- как взвешивать свежесть;
- как отделять decision signals от шума;
- как связывать эти сигналы с личным контекстом пользователя;
- как превращать всё это в usable prediction.

Это серьёзная архитектурная ставка.
Именно она должна отличать Runa от generic AI tools.

---

# Personal OSINT Layer

## Что должен уметь этот слой

Runa должна построить **Personal OSINT Layer**, который:
- понимает тип решения;
- знает, какие внешние сигналы для него важны;
- тянет не просто статьи, а **релевантные decision signals**;
- сопоставляет их с личными ограничениями пользователя;
- вшивает это в главный prediction,
  а не выносит в подвальный блок “что говорят источники”.

Пользователь должен чувствовать:

## “этот прогноз стал сильнее, потому что Runa реально посмотрела мир вокруг моего вопроса”

И итоговый ответ должен ощущаться так:

## “С учётом того, что сейчас происходит во внешнем мире,
## и с учётом твоих личных вводных,
## наиболее разумный вывод такой-то.”

---

# Что мы строим теперь

## Старый слабый подход
- система сама выдаёт prediction
- prediction иногда был декоративным
- внешний контекст выглядел как приложение к ответу
- источники не становились ядром reasoning
- результат часто звучал умно, но обобщённо

## Новый подход
Prediction в Runa должен быть одновременно:
- **query-based**
- **scenario-based**
- **personally grounded**
- **externally intelligence-driven**

То есть:
1. пользователь задаёт живой вопрос
2. система определяет тип решения
3. система извлекает релевантный личный контекст
4. система определяет, каких личных данных не хватает
5. система активирует decision-specific OSINT retrieval
6. система извлекает не просто статьи, а сигналы
7. система связывает сигналы с контекстом пользователя
8. строит usable prediction
9. честно показывает uncertainty и missing context

---

# Новый core продукта

## Runa = Personal Decision Workspace

Это всё ещё верно.

Но теперь нужно понимать:
Decision Workspace сам по себе недостаточен,
если prediction остаётся слабо связанным с внешним миром.

Поэтому правильная формула теперь такая:

## Decision Workspace — это место, где человек моделирует решения,
## а Personal OSINT Layer делает prediction действительно grounded и useful.

Человек должен иметь возможность:
- задать вопрос о будущем
- создать несколько сценариев
- менять параметры
- добавлять личные факты
- загружать документы
- получать не просто reasoning,
  а reasoning, усиленный внешними сигналами,
  реально влияющими на исход

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

Это база для личного reasoning.

---

## 2. Sphere
Сфера — это контейнер для контекста, который повышает точность prediction.

Внутри сферы могут быть:
- facts
- structured inputs
- free-form notes
- chats
- uploaded files
- specific environment context
- constraints
- responsibilities
- domain parameters

Сфера нужна не ради разговора,
а ради **progressive precision**.

---

## 3. Prediction Question
Реальный вопрос пользователя о будущем, решении, риске или траектории.

Prediction всегда должен рождаться из **живого вопроса пользователя**.

---

## 4. Scenario Variant
Один вариант решения внутри вопроса.

Система должна помогать сравнивать несколько альтернатив,
а не давать один “магический” ответ.

---

## 5. Context Completeness
Система должна честно понимать:
- чего не хватает в личном контексте
- чего не хватает во внешнем контексте
- насколько этого хватает для сильного прогноза

---

## 6. External Signals
Новая важная сущность.

Это не просто список источников.

External Signals — это:
- новости
- рыночные движения
- погода
- расписания
- policy changes
- macro factors
- company / industry context
- public health context
- public event context
- other lawful relevant signals

Важно:
система должна извлекать **не просто документы**,
а именно **decision-relevant signals**.

---

## 7. Prediction Report
Prediction Report должен быть не просто красивым текстом,
а структурированным результатом, в который уже встроены:
- personal context
- scenario assumptions
- decision signals from outside world
- uncertainty
- confidence
- missing context

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
- missing_context
- source_transparency metadata

---

## 8. Scenario Comparison
Сравнение вариантов по одному вопросу.

Это остаётся одним из ядровых differentiators продукта.

---

# External Context больше не должен быть слабым appendage

## Плохой вариант
- “что говорят источники” отдельным блоком где-то внизу
- 2–3 поверхностные статьи
- generic synthesis
- внешние материалы не меняют основной вывод

## Правильный вариант
Внешний мир должен быть встроен в:
- most likely outcome
- main risks
- leverage factors
- conditions under which prediction changes
- confidence reasoning

То есть пользователь должен видеть не:
> источники говорят X

А:
> с учётом твоей ситуации и с учётом того,
> что сейчас происходит во внешнем мире,
> наиболее разумный прогноз такой-то.

---

# Что такое вау в Runa теперь

Вау — это НЕ:
- длинные summary блоки
- просто много источников
- список ссылок
- pseudo-smart essay

Вау — это когда пользователь чувствует:

## “Runa посмотрела не только на меня,
## но и на реальный мир вокруг моего вопроса,
## и дала вывод, который реально полезен именно мне.”

Ключ к вау теперь:
- conditioned prediction
- scenario comparison
- leverage factors
- missing context detection
- progressive precision
- strong personal grounding
- **decision-specific external intelligence**

---

# Core product loops

## Loop 1 — Question → Prediction
1. Пользователь задаёт вопрос
2. Runa читает личный контекст
3. Runa подключает decision-specific external signals
4. Формирует useful prediction

---

## Loop 2 — Missing Context → Better Prediction
1. Runa говорит, каких личных данных не хватает
2. Пользователь идёт в нужную сферу
3. Добавляет факты / документы / параметры
4. Prediction пересчитывается
5. Confidence растёт

---

## Loop 3 — Scenario Comparison
1. Пользователь создаёт несколько вариантов
2. Сравнивает исходы
3. Понимает реальные trade-offs
4. Возвращается, чтобы прокрутить ещё один вариант

---

## Loop 4 — External World Update → Prediction Update
1. Во внешнем мире меняется значимый сигнал
2. Это может менять полезность сценария
3. Пользователь пересматривает прогноз
4. Runa помогает переоценить решение на новых условиях

---

# Архитектура продукта

## Слой 1 — Personal World Model
Живая модель пользователя.

Содержит:
- graph entities
- sphere state
- recent changes
- action history
- context completeness signals

---

## Слой 2 — Context Acquisition Layer
Собирает и улучшает личный контекст.

Источники:
- onboarding
- sphere chats
- user edits
- uploaded files
- structured data fields
- daily updates
- future follow-ups

Должен уметь:
- обнаруживать missing context
- направлять пользователя в нужную сферу
- предлагать, что добавить

---

## Слой 3 — Prediction Question Engine
Принимает вопрос и превращает его в prediction job.

Задачи:
- question classification
- scenario framing
- parameter extraction
- horizon detection
- ambiguity detection
- context gap detection

---

## Слой 4 — Personal OSINT Layer
Новый ключевой слой.

Этот слой должен:
- определять тип решения
- выбирать нужный retrieval strategy
- понимать, какие external signals важны
- учитывать freshness
- собирать не просто страницы, а сигналы
- фильтровать шум
- оценивать signal quality
- строить decision-grade synthesis

Важно:
мы не строим “всё подряд retrieval engine”.
Мы строим **decision-specific external intelligence layer**.

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

Но теперь Scenario Engine должен синтезировать:
- personal model
- scenario assumptions
- external signals
- missing context
- uncertainty

---

## Слой 6 — Comparison Engine
Сравнивает варианты между собой.

Показывает:
- what changed
- what matters most
- trade-offs
- confidence differences
- sphere impact deltas
- how external conditions affect each variant differently

---

## Слой 7 — Interface Layer
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

# Decision-specific OSINT modes

Не нужно сразу пытаться покрыть весь мир.

Нужно строить по классам вопросов.

## Для каждого класса вопроса система должна знать:
- какие сигналы важны
- какие источники нужны
- какой уровень свежести критичен
- какие внешние факторы действительно двигают outcome
- как эти факторы соединяются с личными ограничениями

### Примеры

#### 1. Investment / financial decisions
Сигналы могут включать:
- текущую цену
- тренд / volatility context
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

#### 2. Health / activity decisions
Сигналы могут включать:
- weather
- location-dependent conditions
- schedule
- public health context
- training intensity / constraints if available

Но финальный вывод должен зависеть и от:
- состояния пользователя
- сна
- нагрузки
- recovery
- цели

#### 3. Career decisions
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

---

# Confidence architecture

Prediction обязательно должен быть:
- вероятностным
- conditioned
- честным
- explicit about uncertainty

У confidence должны быть причины двух типов:

## A. Personal confidence reasons
- сколько мы знаем о пользователе
- насколько сильный личный контекст
- какие missing inputs ещё остались

## B. External confidence reasons
- насколько сильны внешние сигналы
- насколько они свежие
- насколько они согласованы
- насколько они реально связаны с вопросом

Если внешние сигналы слабые или шумные,
система должна говорить это честно.

---

# Что Prediction НЕ должен делать

Prediction не должен:
- изображать оракула
- выдавать общие слова вместо useful synthesis
- строиться на слабом retrieval и делать вид, что это intelligence
- складывать внешние источники в декоративный нижний блок
- превращать продукт в свалку ссылок
- гнаться за количеством источников вместо качества signals
- строиться из complexity ради complexity

---

# Что для нас counts as success now

Успех — это когда пользователь:
- задаёт реальный вопрос
- получает прогноз по своему случаю
- чувствует, что система учла **и его жизнь, и внешний мир**
- понимает, какие факторы реально двигают исход
- видит, чего не хватает для точности
- добавляет контекст
- пересчитывает прогноз
- сравнивает варианты
- возвращается снова

Если prediction по внешне-зависимым вопросам всё ещё звучит как generic advice,
значит система ещё не дошла до нужного уровня.

---

# Product priorities now

Приоритет №1:
## Decision-grade prediction usefulness

Приоритет №2:
## Personal OSINT Layer

Приоритет №3:
## Better integration of external signals into main prediction

Приоритет №4:
## Progressive precision through missing context

Приоритет №5:
## Stronger scenario comparison

Важно:
мы не отказываемся от Decision Workspace.
Но теперь нужно понимать,
что без сильного Personal OSINT Layer prediction usefulness будет ограничен.

---

# Как тебе работать со мной

Я хочу, чтобы ты думал как:
- продуктовый архитектор
- технический кофаундер
- системный дизайнер

Но теперь особенно важно:
если внешний слой снова скатывается в decorative search + summary,
ты должен прямо это останавливать.

### Твои задачи
- не просто выполнять задачу
- а усиливать prediction usefulness
- проверять, не стал ли external context декоративным
- думать не “как добавить больше источников”,
  а “как извлечь более сильные decision signals”
- если видишь путь сильнее — предлагай
- если видишь декоративную complexity — тормози

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
- prompts должны отражать:
  - scenario reasoning
  - missing context
  - confidence
  - leverage factors
  - **external signal synthesis**
  - **decision-specific OSINT logic**

## API
- structured responses
- понятные схемы
- желательно проектировать API вокруг явных сущностей

## Граф
- граф нужен для prediction usefulness
- не плодить сущности ради graph beauty
- каждая сущность должна усиливать decision reasoning

## Retrieval / OSINT
- не собирать всё подряд
- предпочитать signal quality количеству результатов
- freshness учитывать там, где она реально влияет на исход
- source type подбирать под класс вопроса
- retrieval должен вести к лучшему prediction,
  а не к большему объёму текста

---

# Главный фильтр для всех решений

Перед любым изменением задавай вопрос:

## “Это делает Runa сильнее как personal decision intelligence system?”

И ещё конкретнее:

## “Это помогает человеку лучше моделировать важные решения своей жизни
## за счёт сильного соединения личного контекста и внешнего мира?”

Если нет — не туда идём.

---

# Что делать после каждого шага

После каждого заметного изменения:
1. коротко объясни, что сделал
2. скажи, зачем это усиливает новый core
3. скажи, как проверить
4. предложи следующий логичный шаг
5. честно укажи ограничения / риск / техдолг
6. отдельно укажи, усилился ли **personal OSINT usefulness**

---

# Финальный принцип

Runa — это не mental wellness toy.
Не self-help dashboard.
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
