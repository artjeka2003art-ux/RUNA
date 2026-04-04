# RUNA — Product Blueprint

## Статус документа

Это стратегический документ нового ядра продукта Runa.

Он НЕ заменяет `CLAUDE.md`.
Он существует рядом с ним и отвечает на другой вопрос:

- `CLAUDE.md` = как Claude должен думать и работать внутри проекта
- `RUNA_PRODUCT_BLUEPRINT.md` = что именно мы строим, зачем, из каких сущностей и слоёв, и куда это должно прийти

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
- внешнего профессионального контекста

Главная идея:

## **Simulate your life decisions before you make them.**

---

# 2. Почему мы меняем фокус

## Что было слабым раньше

Старый prediction-layer был недостаточно сильным, потому что:
- система сама генерировала prediction без достаточного запроса пользователя
- prediction ощущался как декоративная фича
- path / сценарии выглядели “умно”, но не всегда были реально прикладными
- пользователь не чувствовал, что это прогноз именно под его случай и его реальные вводные

В итоге продукт был умным, но не обязательно нужным.

---

## Что мы поняли

По-настоящему цепляет не абстрактный AI-коучинг и не общий “dashboard of life”.

Цепляет вот что:

## **персонализированный прогноз по моему реальному вопросу, моей реальной жизни и моим реальным ограничениям**

То есть человек хочет:
- задать важный вопрос
- получить прогноз именно под свой случай
- понять, что сильнее всего влияет на исход
- увидеть, чего не хватает для точности
- добавить данные и сделать прогноз сильнее
- прокрутить альтернативные сценарии своей жизни

---

# 3. Новый продуктовый core

## Новый core Runa

Runa — это не просто чат, не просто life map и не просто prediction card.

Runa — это:

## **Decision Workspace + Personal World Model**

Где:
- **Personal World Model** = живая модель жизни пользователя
- **Decision Workspace** = пространство, где пользователь моделирует варианты решений

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
- сравнивать сценарии
- возвращаться позже и обновлять прогноз на новых вводных

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
- next step

---

# 5. Что создаёт вау

Вау не в количестве AI.
И не в количестве источников.
И не в красоте графа.

Вау появляется, когда пользователь чувствует:

## “эта система реально помогает мне думать о своей жизни как о системе вариантов и последствий”

И ещё сильнее:

## “она показала, какие 2–3 фактора реально меняют исход именно в моём случае”

То есть главный вау-эффект дают:

### 1. Conditioned prediction
Не просто “что будет”, а:
- что будет **при определённых условиях**
- что изменится, если параметр X другой
- в каком случае риск растёт
- в каком случае исход улучшается

### 2. Scenario comparison
Пользователь может сравнить несколько вариантов одной жизни.

### 3. Missing context detection
Система говорит, чего ей не хватает для более сильного прогноза.

### 4. Progressive precision
Чем больше релевантного контекста добавлено, тем точнее и полезнее prediction.

### 5. Leverage factors
Система показывает, какие факторы реально двигают исход.

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

---

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

---

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

---

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

---

## 6.5 Context Completeness
Оценка того, насколько система может дать сильный прогноз.

Context Completeness должен отвечать на вопросы:
- чего не хватает?
- почему это важно?
- в какой сфере это нужно добавить?
- какой тип данных нужен?
- насколько это повысит confidence?

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

---

## 6.6 Prediction Report
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
- external_context_summary
- missing_context
- source_transparency metadata

---

## 6.7 Scenario Comparison
Сравнение нескольких Scenario Variants по одному Question.

Показывает:
- где выше риск
- где выше upside
- где выше confidence
- какие сферы выигрывают
- какие сферы проседают
- какие leverage factors самые чувствительные
- какие trade-offs есть между вариантами

---

## 6.8 External Context
Внешний мир, который усиливает prediction.

Делится на 3 уровня:

### A. General professional context
- статьи
- исследования
- expert long-form materials
- behavioural science
- management / health / relationship / education frameworks

### B. Domain-specific context
- компания
- индустрия
- профессия
- образовательная программа
- рынок
- карьерная среда
- региональные правила
- рыночная конъюнктура

### C. User-supplied context
Самый сильный слой:
- job description
- CV
- contracts
- offer letters
- employer policies
- personal notes
- schedules
- financial spreadsheets
- medical instructions
- any relevant uploaded files

---

# 7. Core product loops

## 7.1 Question → Prediction
1. Пользователь задаёт вопрос
2. Runa читает личный контекст
3. Подключает внешний контекст
4. Формирует prediction report

Ценность:
- быстрый полезный прогноз по реальному вопросу

---

## 7.2 Missing Context → Better Prediction
1. Runa говорит, чего не хватает
2. Пользователь идёт в нужную сферу
3. Добавляет данные / документы / параметры
4. Prediction пересчитывается
5. Confidence растёт

Это один из главных retention loops.

---

## 7.3 Scenario Comparison Loop
1. Пользователь создаёт несколько вариантов
2. Сравнивает исходы
3. Понимает, где реальные trade-offs
4. Возвращается, чтобы прокрутить ещё один вариант

Это один из главных вау-loop’ов.

---

## 7.4 Prediction vs Reality Loop
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

Today — это лёгкая ежедневная поверхность, а не центр всей ценности.

---

## 8.2 Life Map
Life Map остаётся как карта жизни пользователя.

Роль:
- показать структуру жизни
- объяснить, из чего состоит модель
- быть визуальной картой сфер
- служить входом в уточнение контекста

Life Map нужен как объясняющий и структурирующий слой.

---

## 8.3 Sphere Detail
Одна из ключевых поверхностей нового продукта.

Sphere Detail должен стать местом, где пользователь:
- уточняет факты
- добавляет structured data
- загружает документы
- формирует domain context
- закрывает missing context gaps

---

## 8.4 Prediction
Prediction больше не должен быть просто экраном с одиночным ответом.

Prediction становится entrypoint / container для:
- вопроса
- scenario variants
- report
- confidence
- missing context
- comparison

---

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

### 7. Source Transparency
Минимальный блок:
- на какие внешние материалы опирался разбор

---

# 10. Prediction architecture

## 10.1 High-level flow

1. **Question intake**
   - пользователь задаёт вопрос
   - система определяет тип вопроса
   - система выделяет горизонт, ambiguity, intent

2. **Scenario framing**
   - система помогает выделить один или несколько вариантов сценария

3. **Personal context retrieval**
   - извлекается релевантный кусок graph / sphere context
   - recent events
   - patterns
   - blockers
   - values
   - action feedback
   - check-ins
   - sphere dynamics

4. **Context completeness assessment**
   - система оценивает, чего не хватает
   - формирует список missing inputs

5. **External context retrieval**
   - web
   - domain-specific materials
   - user files
   - future structured providers

6. **Scenario synthesis**
   - строится prediction report на основе:
     - personal graph
     - scenario assumptions
     - external context
     - uncertainty

7. **Comparison synthesis**
   - строится сравнительный вывод между вариантами

8. **UI rendering**
   - user sees scenario-level output
   - user sees confidence and missing context
   - user can iterate

---

## 10.2 Prediction output principles

Prediction output должен быть:
- structured
- probabilistic
- conditioned
- comparative when relevant
- honest about uncertainty
- useful for action

Prediction НЕ должен:
- звучать как оракул
- скрывать missing context
- маскировать слабую уверенность под сильную
- быть просто красивым эссе

---

# 11. Confidence architecture

Confidence — это отдельный важный слой.

Каждый prediction должен иметь:

### Confidence level
- low
- medium
- high

### Confidence reasons
Почему confidence именно такой:
- хороший личный контекст
- слабый внешний контекст
- слишком широкая неопределённость
- зависимость от поведения других людей
- недостаток пользовательских данных

### Precision improvement suggestions
Что повысит точность:
- добавь финансовые данные
- уточни формат работы
- загрузи job description
- добавь расписание
- уточни текущую нагрузку
- заполни missing field in sphere

---

# 12. Leverage factors

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

Это делает prediction прикладным.

---

# 13. 3D и граф-визуализация

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

# 14. Beyond MVP — как мы теперь думаем

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

---

# 15. Приоритетные prediction modes

Не всё подряд. В первую очередь — самые сильные.

## Priority 1 — Career / Work Decisions
- увольнение
- переход
- смена роли
- выгорание
- company fit
- timing of exit

## Priority 2 — Burnout / Lifestyle Trajectory
- к чему ведёт текущий режим
- какой фактор первым ломает систему
- как изменится исход при изменении режима

## Priority 3 — Relationship / Social Patterns
- повтор конфликтов
- восстановление отношений
- избегание
- trust / rupture / repair dynamics

## Priority 4 — Startup / Risk Decisions
- full-time vs part-time
- solo vs cofounder
- speed vs stability
- burn risk
- execution sustainability

## Priority 5 — Education / Path Choice
- магистратура vs стартап
- обучение vs работа
- переход в новую траекторию

---

# 16. Документы и external grounding

Одна из сильнейших ставок продукта:

## prediction должен уметь усиливаться за счёт реальных документов и реальной среды

Это значит, что в будущем Runa должна уметь работать с:
- policies
- offers
- job descriptions
- schedules
- financial sheets
- notes
- contracts
- user-supplied materials

Это намного сильнее, чем просто open web.

Важно:
- только законный и этичный контекст
- только то, что пользователь сам дал или разрешил использовать
- никакой мутной серой зоны

---

# 17. Technical architecture (high-level)

## Backend
- Python / FastAPI
- routes for prediction, spheres, context, comparisons
- orchestration of scenario jobs
- retrieval / extraction pipeline
- context completeness logic

## AI layer
- question classification
- scenario synthesis
- comparison reasoning
- missing context detection
- leverage factor extraction
- confidence reasoning
- external evidence synthesis

## Personal model layer
- graph DB / graph queries
- dynamic sphere states
- recent changes
- action loops
- memory integration
- structured and unstructured context

## Retrieval layer
- open web search
- source quality filtering
- HTML full-text extraction
- later: PDF / domain APIs / user-file parsing
- later: ranking / reranking / caching

## Frontend
- Today
- Life Map
- Sphere Detail
- Prediction
- Decision Workspace
- Comparison view
- later: 3D consequence map

---

# 18. What success looks like

Успех нового ядра Runa выглядит так:

Пользователь:
1. задаёт важный вопрос
2. получает полезный personal prediction
3. понимает, какие факторы реально двигают исход
4. видит, чего не хватает для точности
5. добавляет контекст
6. пересчитывает прогноз
7. сравнивает несколько вариантов
8. возвращается позже, чтобы обновить ситуацию

Если это начинает происходить — продукт становится реально нужным.

---

# 19. What we must avoid

Нельзя:
- делать AI-магический театр
- перегружать человека псевдоумными отчётами
- строить graph ради graph
- строить 3D ради 3D
- превращать external context в свалку ссылок
- делать вид, что система знает будущее наверняка
- гнаться за complexity, которая не усиливает decision usefulness

---

# 20. Главный фильтр для всех решений

Перед любой продуктовой или технической идеей задаём вопрос:

## **Это делает Runa сильнее как personal decision intelligence system?**

И ещё конкретнее:

## **Это помогает человеку лучше моделировать важные решения своей жизни?**

Если нет — значит не туда идём.

---

# 21. Куда идти дальше

Самые логичные следующие большие направления:

### A. Закрепить новую сущностную модель в коде
- PredictionQuestion
- ScenarioVariant
- ContextCompleteness
- PredictionReport
- ScenarioComparison

### B. Построить первый настоящий Decision Workspace
- question
- variants
- reports
- missing context prompts
- comparison block

### C. Усилить context acquisition
- structured inputs in spheres
- files
- domain-specific facts

### D. Усилить scenario comparison
- scenario-to-scenario delta
- trade-offs
- leverage comparison

### E. Только потом идти глубже в advanced retrieval / 3D / heavy architecture

---

# Финальная формулировка

Runa — это не mental wellness toy.
Не dashboard.
Не graph demo.

## Это система личного моделирования решений.

Она должна помогать человеку:
- видеть варианты
- понимать последствия
- понимать, что реально меняет исход
- добирать недостающий контекст
- сравнивать сценарии
- принимать более сильные решения о своей жизни
