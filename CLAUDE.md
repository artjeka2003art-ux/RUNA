# RUNA — Claude Code Instructions

## Что это за проект
Runa — персональная AI prediction-система. Пользователь разговаривает с AI,
AI строит живую модель его личности через граф, моделирует параллельные сценарии
будущего и ежедневно обновляет Life Score.

Главная формула: "Мне стало легче, потому что я понял что делать."

## Стек
- Backend: Python (FastAPI) — агенты и prediction engine
- AI: Claude API (claude-sonnet-4-5) — все агенты и разговоры
- Graph DB: Neo4j — граф личности
- Vector DB: Pinecone — эмбеддинги
- Memory: Zep — долгосрочная память агентов
- Main DB: PostgreSQL — пользовательские данные
- Frontend: React + Vite + TypeScript
- Infra: Docker Compose

## Структура проекта
```
runa/
├── backend/
│   ├── agents/          # AI агенты (conversation, analyst, scenario, predictor)
│   ├── graph/           # Neo4j queries + graph logic
│   ├── memory/          # Zep + Pinecone integration
│   ├── scoring/         # Life Score Engine
│   ├── api/             # FastAPI routes
│   ├── models/          # Pydantic schemas
│   └── prompts/         # все промпты отдельно, никогда не инлайн
├── frontend/            # React + Vite
└── docker-compose.yml
```

## Архитектура — 5 слоёв
1. Conversation Engine — онбординг (15 мин) + ежедневный чекин через Claude API
2. Personal Knowledge Graph — Neo4j + Pinecone + Zep
3. Multi-Agent Prediction Engine — 4 независимых агента
4. Life Score Engine — расчёт баллов сфер + агрегация (0-100)
5. Interface — React + Vite

## Агенты
- conversation_agent.py — онбординг и чекин
- analyst_agent.py — читает граф, обновляет веса рёбер
- scenario_agent.py — строит 3 сценария будущего
- predictor_agent.py — рассчитывает вероятности сценариев

## Правила кода

### Промпты
- Все промпты в папке prompts/ как отдельные файлы
- Никогда не инлайн в коде
- Агенты не общаются между собой напрямую

### Граф
- Все Cypher запросы ТОЛЬКО в graph_queries.py
- Каждый узел имеет: created_at, updated_at, user_id
- Рёбра имеют числовой weight (0.0–1.0)

### API
- Все эндпоинты возвращают { success: bool, data: {}, error: string }
- JWT авторизация на каждом эндпоинте
- Async везде

### Общее
- Типизация везде: Pydantic для Python, TypeScript для фронта
- Никаких magic strings — константы в constants.py
- Docker Compose для всей инфраструктуры

## Узлы графа
Person, Sphere, Event, Pattern, Value, Blocker, Goal, CheckIn

## Рёбра графа
AFFECTS, CAUSED_BY, CONFLICTS_WITH, SUPPORTS, CHANGED_ON, PREDICTS

## Фаза 1 MVP — строим только это
✅ Conversation Engine — онбординг + ежедневный чекин
✅ Personal Knowledge Graph — базовые узлы и рёбра
✅ Life Score — расчёт по сферам
✅ Минимальный UI — чат + дашборд

## Главный принцип Companion Agent
НЕ скриптует вопросы. Читает граф и замечает конкретное:
❌ "Как ты сегодня по шкале 1-10?"
✅ "Три недели назад ты говорил что боишься снова провалиться. Сегодня ты молчал два дня. Что происходит?"

## Целевой пользователь
Человек после провала, кризиса, выгорания. Застрял. Не знает что делать.
Ему нужна ясность и конкретный следующий шаг.
