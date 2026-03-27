"""Mock Anthropic client for development without API key.
Returns realistic responses so the full onboarding + checkin cycle can be tested.
When ANTHROPIC_API_KEY is set — real client is used instead.
"""


class MockContent:
    def __init__(self, text: str):
        self.text = text


class MockResponse:
    def __init__(self, text: str):
        self.content = [MockContent(text)]


_ONBOARDING_STEP = {}

_ONBOARDING_RESPONSES = [
    "Привет. Расскажи мне — что сейчас происходит в твоей жизни? Не в общих чертах, а конкретно — что занимает голову прямо сейчас?",

    "Понял. А как давно это началось? Было ли что-то конкретное — момент, после которого всё пошло не так?",

    "Это серьёзно. А что ты делаешь когда становится совсем тяжело? Есть какой-то привычный способ справляться?",

    "Вижу паттерн. А если честно — чего ты хочешь? Не что \"надо\", а что ты реально хочешь чтобы изменилось?",

    "А что мешает? Что стоит между тобой сейчас и тем, чего ты хочешь?",

    "Слушай, а есть что-то что для тебя реально важно — не потому что \"так надо\", а потому что ты так чувствуешь?",

    "Окей. Давай посмотрю что я вижу после нашего разговора.\n\nВот что я заметила:\n- Ты сейчас в переходном моменте — старое не работает, новое ещё не началось\n- Есть паттерн: когда становится тяжело, ты уходишь в изоляцию\n- Главный блок — страх что снова не получится\n- При этом тебе важна независимость и возможность делать своё\n\nСферы которые я вижу: Работа/проект, Эмоциональное состояние, Отношения с людьми, Здоровье\n\nЭто похоже на правду? Что-то упустила?",

    """<extraction>
{
  "spheres": ["Работа и проект", "Эмоциональное состояние", "Отношения с людьми", "Здоровье"],
  "events": [{"name": "Кризис/переходный момент", "description": "Старое перестало работать, новое ещё не началось", "spheres": ["Работа и проект", "Эмоциональное состояние"]}],
  "patterns": [{"name": "Изоляция при стрессе", "description": "Когда тяжело — уходит в себя, перестаёт общаться", "spheres": ["Отношения с людьми", "Эмоциональное состояние"]}],
  "values": [{"name": "Независимость", "description": "Важно делать своё, не зависеть от чужих решений"}],
  "blockers": [{"name": "Страх повторного провала", "description": "Боится что снова не получится, поэтому откладывает действия", "spheres": ["Работа и проект"]}],
  "goals": [{"name": "Запустить новое дело", "description": "Хочет начать что-то своё, но пока не решается", "spheres": ["Работа и проект"]}]
}
</extraction>""",
]

_CHECKIN_RESPONSES = [
    "Ты вчера говорил про {topic}. Что-то изменилось с тех пор? Или всё на том же месте?",
    "Заметила что ты уже несколько дней не упоминаешь {topic}. Раньше это было главное. Что произошло?",
    "Окей. А конкретно — что ты можешь сделать сегодня по этому поводу? Одно действие.",
]


class MockMessages:
    async def create(self, model: str, max_tokens: int, system: str, messages: list[dict]) -> MockResponse:
        # Determine if this is onboarding or checkin
        is_onboarding = "onboarding" in system.lower() or "extraction" in system.lower()

        if is_onboarding:
            # Track progress per conversation based on message count
            user_messages = [m for m in messages if m["role"] == "user"]
            step = len(user_messages) - 1  # -1 because first "Привет" is automatic

            if step >= len(_ONBOARDING_RESPONSES):
                step = len(_ONBOARDING_RESPONSES) - 1

            return MockResponse(_ONBOARDING_RESPONSES[step])
        else:
            # Checkin — rotate through responses
            idx = len(messages) % len(_CHECKIN_RESPONSES)
            text = _CHECKIN_RESPONSES[idx].format(topic="работу")
            return MockResponse(text)


class MockAnthropic:
    """Drop-in replacement for anthropic.AsyncAnthropic when no API key is set."""

    def __init__(self):
        self.messages = MockMessages()
