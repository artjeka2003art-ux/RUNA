# CLAUDE_CODE_INVESTMENT_SENTIMENT_ADAPTER_V1

## Задача

Сделать следующий pragmatic шаг в новом OSINT-векторе Runa:

## **Investment Sentiment Adapter v1**

Цель шага:
усилить `investment` mode **вторым structured external signal**, чтобы investment prediction опирался уже не только на market snapshot / price data, но и на **market sentiment / risk state**.

Это НЕ giant finance platform.
Это НЕ massive provider integration.
Это НЕ новый UI.
Это НЕ refactor reasoning core.

Это **узкий архитектурный шаг**, который должен подтвердить, что новая adapter-first OSINT architecture масштабируется дальше одного structured source.

---

## Source of truth

Перед началом работы обязательно изучи:

- `CLAUDE.md`
- `RUNA_PRODUCT_BLUEPRINT.md`
- `CLAUDE_PRODUCT_PHASE_FREEZE.md`

Работай в логике:
- Decision Workspace остаётся ядром
- Personal OSINT Layer — стратегический differentiator
- reasoning core сейчас не трогаем без сильного основания
- идём дальше MVP, но complexity должна быть осмысленной

---

## Почему мы делаем этот шаг

Сейчас уже есть:
- QuestionMode
- RetrievalPlan
- SignalRegistry
- ExternalSignal
- SignalBundle
- первый structured market adapter для `investment` mode

Это хорошо, но пока investment mode всё ещё опирается в основном на:
- price snapshot
- web signals

Нам нужен **второй structured signal type**, чтобы investment OSINT уже выглядел как реально развивающаяся архитектура, а не как один случайный adapter.

Нужный эффект:
- investment prediction должен видеть не только “что происходит с ценой”
- но и “в каком состоянии сейчас находится рынок / sentiment / risk regime”

---

## Что нужно сделать

### 1. Добавить второй structured adapter для `investment` mode

Сделай **sentiment / risk adapter** для investment questions.

Предпочтительно:
- использовать **публичный / free источник**, если это возможно;
- если источник требует API key, **не стопорься** — реализуй через env config и graceful fallback.

Цель адаптера:
получать **один понятный structured sentiment signal** для investment mode.

Примеры допустимых signal types:
- `market_sentiment`
- `risk_sentiment`
- `fear_greed_state`

Важно:
не тащи giant dataset.
Нужен **один качественный structured signal**, который реально дополняет market price snapshot.

---

### 2. Встроить adapter в existing OSINT pipeline

Новый adapter должен встроиться в уже существующую цепочку:

- `QuestionMode`
- `RetrievalPlan`
- `ExternalSignal`
- `SignalBundle`
- synthesis

То есть:
- для `investment` mode adapter реально вызывается;
- его результаты превращаются в `ExternalSignal`;
- signals попадают в `SignalBundle`;
- synthesis получает их как часть основного external signal context.

---

### 3. Сохранить graceful fallback

Если:
- источник недоступен,
- rate limit,
- API key не задан,
- provider вернул ошибку,

pipeline **не должен ломаться**.

Нужно:
- вернуть пустой список сигналов или безопасный fallback;
- продолжить обычный investment pipeline;
- сохранить работоспособность search-based layer.

---

### 4. Сделать signal genuinely useful

Новый sentiment signal не должен быть декоративным.

У него должны быть:
- `source_type`
- `source_name`
- `signal_type`
- `timestamp`
- `freshness_score` / freshness label
- `quality_score`
- `relevance_score`
- `extracted_claim`
- `why_it_matters`

То есть сигнал должен быть пригоден для нормальной synthesis-интеграции, а не быть просто строкой “рынок боится”.

---

### 5. Обновить registry / retrieval logic

Если нужно:
- добавь новый `source_family`;
- обнови `signal_registry.py`;
- укажи, что `investment` mode теперь может использовать второй structured adapter;
- обнови retrieval / merge logic так, чтобы новый adapter корректно участвовал в bundle.

---

### 6. Не делать лишнего

Не нужно:
- делать новый UI;
- делать giant caching system;
- строить full finance analytics engine;
- добавлять 20 новых источников;
- лезть в другие modes;
- трогать reasoning core.

---

## Технические требования

### Предпочтения по источнику
- сначала попробуй **public/free source**
- если нужен ключ — реализуй через env config
- не завязывай весь шаг на платный provider

### Архитектурные требования
- новый adapter должен жить в `backend/osint/adapters/`
- использовать существующие OSINT models
- не ломать existing investment pipeline
- быть расширяемым для будущих investment adapters

### Код
- типизация везде
- без magic strings без причины
- осмысленные helper functions
- аккуратный graceful fallback
- не плодить дублирование

---

## Что считать успехом

Шаг считается успешным, если:

1. Для `investment` вопросов pipeline получает **не только market price signal**, но и **второй structured sentiment/risk signal**.
2. Новый signal реально превращается в `ExternalSignal`.
3. Signal попадает в `SignalBundle`.
4. Existing synthesis pipeline может использовать его как часть main reasoning.
5. При сбое provider pipeline не падает.
6. Для non-investment вопросов поведение не ломается.

---

## Как проверить

Прогони хотя бы такие кейсы:

### Тест 1 — BTC buy decision
Вопрос:
- `Стоит ли мне сейчас покупать BTC?`

Ожидание:
- investment mode
- market adapter signal
- sentiment adapter signal
- оба попали в signal bundle

### Тест 2 — BTC vs ETH
Вопрос:
- `Мне лучше купить BTC или ETH сейчас?`

Ожидание:
- market snapshot для активов
- sentiment/risk signal тоже есть
- pipeline не ломается

### Тест 3 — Provider unavailable fallback
Смоделируй сбой источника / отсутствие ключа / rate limit.

Ожидание:
- pipeline не падает
- search-based investment flow продолжает работать

### Тест 4 — Non-investment question
Вопрос:
- `Стоит ли мне увольняться в июле?`

Ожидание:
- новый adapter не вмешивается
- non-investment flow не ломается

---

## Чего не делать

Не уходить в:
- giant finance platform
- complex quant models
- macro engine
- multi-provider abstraction layer over everything
- новый frontend

Это должен быть:
## **узкий, прагматичный, архитектурно правильный шаг**

---

## Формат отчёта

После выполнения отчитайся строго так:

### 1. Что изменил
- новые файлы
- изменённые файлы
- что именно добавлено

### 2. Как теперь работает pipeline
- покажи flow для investment question
- отдельно укажи, где вызывается новый adapter
- отдельно укажи, как работает fallback

### 3. Что стало лучше product-wise
- почему это реально усиливает investment OSINT
- почему это уменьшает зависимость от DuckDuckGo-first логики

### 4. Что осталось слабым
- ограничения нового adapter
- риски
- техдолг
- чего пока нет

### 5. Что нужно сделать пользователю руками
Отдельным блоком обязательно напиши:
- нужен ли API key
- если нужен — где его получить и что добавить в env
- что пользователь должен сделать руками
- что ты смог протестировать без этого
- что ты не смог полностью проверить автоматически

### 6. Следующий лучший шаг
Но без ухода в giant scope.
