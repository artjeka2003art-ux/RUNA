# RUNA — Product Phase Freeze / Build Mode Policy

## Контекст

До этого момента мы целенаправленно усиливали reasoning core Runa.
Это было правильно и необходимо, потому что без этого продукт легко скатывался бы в:
- generic prediction
- fake confidence
- detached reasoning
- forced missing-context routing
- silent assumptions about user life
- decorative AI instead of decision intelligence

На текущем этапе reasoning core уже достаточно усилен, чтобы перестать улучшать его по умолчанию после каждого найденного изъяна.

Этот документ меняет режим работы проекта:

## Теперь основной режим — не endless reasoning polishing, а product build mode.

---

# 1. Что считаем уже достаточно сильным на текущем этапе

Ниже перечислены возможности, которые считаются **good enough for current phase**.
Они не идеальны, но уже достаточны, чтобы не блокировать переход к следующему продуктовому слою.

## 1.1 Decision Workspace core уже существует
У продукта уже есть:
- question input
- scenario variants
- scenario reports
- missing context prompts
- comparison-oriented reasoning base
- rerun loop after adding context

Это уже не raw prediction screen, а реальный каркас Decision Workspace.

## 1.2 Reasoning core уже не является наивным
Считаем достаточным на текущей фазе:
- prediction уже не должен быть откровенно generic by default
- sharpness / anti-generic constraints уже есть
- evidence-backed grounding уже есть
- claim-level support mapping уже есть
- claim-aware correction уже есть
- confidence calibration уже есть
- per-report confidence уже есть

## 1.3 Honest uncertainty уже присутствует
Считаем достаточным на текущей фазе:
- confidence должен быть explainable
- unsupported decisive claims должны понижать trust/confidence
- weak grounding не должен маскироваться под strong answer
- prediction может быть preliminary, если это явно обозначено

## 1.4 Missing context loop уже существует
Считаем достаточным на текущей фазе:
- система умеет находить missing context
- система умеет вести пользователя в сферу
- система умеет рекомендовать создать новую сферу
- rerun loop после обновления контекста уже работает

## 1.5 Context integrity layer уже в работе
Считаем достаточным на текущей фазе:
- forced weak routing признан плохим и должен устраняться
- silent assumptions о базовой реальности пользователя признаны плохими
- useful preliminary answer допустим, если assumptions маркированы честно

---

# 2. Что ещё несовершенно, но НЕ является blocker для перехода дальше

Ниже вещи, которые можно улучшать позже, но они **не должны автоматически тащить проект обратно в endless core-fixing mode**.

## 2.1 Reasoning imperfections accepted for now
Допускается на текущей фазе, что:
- claim granularity ещё грубая
- не все semantic paraphrases ловятся идеально
- evidence weighting пока эвристический
- routing validation и confidence logic могут быть прагматичными, а не совершенными
- retry loop может быть неидеальным
- comparison confidence может быть ещё не fully mature

## 2.2 Document layer accepted as partial
Допускается на текущей фазе, что:
- documents работают как precision booster, а не как full decision-grade knowledge system
- digest / extraction ещё не идеальны
- сложные PDF / таблицы / richer parsing могут быть отложены

## 2.3 UI transparency may remain lightweight
Допускается на текущей фазе, что:
- не вся внутренняя reasoning metadata fully surfaced in UI
- часть explainability пока остаётся в tooltip / devtools / minimal blocks

---

# 3. Freeze rule для reasoning core

## По умолчанию НЕ предлагать следующий шаг внутри deep reasoning core.

Это значит:
- не продолжать автоматически sharpening / support / calibration / correction / comparison logic
- не делать новый reasoning-fix только потому, что найдено ещё одно слабое место
- не открывать новый слой sophistication без явного product payoff

## Reasoning core считается frozen by default, если одновременно выполняется следующее:
- prediction уже не выглядит явно generic or fake by default
- confidence уже объясним
- unsupported decisive claims уже не проходят бесшумно
- missing context loop уже не абсурден
- система уже не молча притворяется, что знает неподтверждённый базовый контекст
- пользователь уже может пройти end-to-end путь: question → prediction → missing context → sphere/new sphere → rerun

Если это выполняется, reasoning core считается **достаточно хорошим, чтобы идти дальше**.

---

# 4. Когда freeze можно нарушать

Reasoning freeze можно нарушить только если найден **реальный blocker**, а не просто очередной improvement opportunity.

Размораживать reasoning core можно только в одном из случаев:

## 4.1 Trust-breaking bug
Например:
- система массово делает очевидно ложные выводы о жизни пользователя
- confidence системно врёт и вводит в заблуждение
- routing снова даёт абсурдные рекомендации
- model silently invents critical life facts as if they were known

## 4.2 Loop-breaking bug
Например:
- missing context loop не приводит к реальному улучшению prediction
- rerun path сломан
- user cannot resolve missing context in a meaningful way

## 4.3 Clear product-value delta
Разрешено вернуться к reasoning core, если improvement:
- заметно усиливает decision usefulness,
- а не просто делает внутреннюю механику “чуть умнее”.

Критерий:
## improvement must materially improve user decision experience, not just model elegance.

---

# 5. Новый основной приоритет проекта

## Теперь приоритет — собрать цельный продуктовый experience.

Это значит, что следующие шаги по умолчанию должны искать усиление здесь:

## 5.1 End-to-end user flow
- first-time onboarding
- first sphere creation
- first useful question
- first prediction experience
- missing context resolution
- rerun clarity
- scenario comparison usability
- clear next action

## 5.2 Product coherence
- surfaces should feel like one product, not disconnected smart modules
- Today, Life Map, Sphere Detail, Prediction / Workspace должны быть логически связаны
- пользователь должен понимать, что делать дальше на каждом шаге

## 5.3 Sphere workflows and context capture
- создание сфер
- удобство ввода фактов
- сфера как контейнер полезного контекста, а не просто карточка
- better guided enrichment

## 5.4 Decision Workspace usability
- better scenario building flow
- clearer comparison UX
- more intuitive parameter changes
- more understandable confidence and missing context presentation

## 5.5 Product continuity and return loops
- continuity between sessions / screens
- prediction history / decision thread continuity
- easier return to previous question and rerun

## 5.6 Product narrative and feeling of completeness
- product should feel coherent and intentional
- not like a collection of patches around a reasoning engine

---

# 6. Как теперь выбирать следующий шаг

Claude должен задавать себе новый главный вопрос:

## НЕ: “Какой следующий логичный фикс внутри reasoning stack?”

## А: “Какой следующий шаг сильнее продвинет Runa к ощущению цельного, готового personal decision intelligence product?”

Дополнительные guiding questions:
- улучшает ли это first useful user journey?
- делает ли это flow более понятным и естественным?
- усиливает ли это product coherence?
- помогает ли это пользователю быстрее почувствовать value?
- приближает ли это продукт к состоянию “этим уже хочется пользоваться как системой”, а не “интересный AI prototype”? 

---

# 7. Что теперь считается хорошим следующим шагом

Предпочтительные типы следующих шагов:
- onboarding and first-value UX
- sphere creation / sphere management UX
- guided context capture
- decision workspace polish
- scenario comparison UX
- continuity / history / revisit flows
- source transparency UX where it affects usability
- cleaner surface integration between Today / Life Map / Sphere / Workspace

Не предпочитать по умолчанию:
- deeper calibration sophistication
- more scoring layers
- richer internal reasoning abstractions
- more prompt surgery without visible UX/product benefit

---

# 8. Прямое правило для task planning

Если новый potential task относится к reasoning/core, Claude обязан сначала проверить:

1. Это trust-breaking issue?
2. Это loop-breaking issue?
3. Это materially improves decision usefulness?

Если ответ на все три вопроса “нет”,
то task **не должен становиться next priority**.
Вместо этого нужно предложить шаг в сторону product build mode.

---

# 9. Что считать “достаточно хорошим, чтобы идти дальше”

## Reasoning / prediction layer достаточно хорош, если:
- prediction useful enough to continue user journey
- confidence explainable enough to be trusted cautiously
- missing context actionable enough to resolve
- routing not absurd by default
- unsupported decisive reasoning not silently passed as strong truth
- preliminary answers possible without hard refusal, but with honest caveats

Если это состояние достигнуто, мы **не тонем дальше в фиксации каждой слабости reasoning core**.
Мы переходим к следующему продуктовому слою.

---

# 10. Как использовать этот файл в дальнейшей работе

С этого момента любой новый prompt для Claude Code должен ссылаться на 3 source-of-truth файла:
- `CLAUDE.md`
- `RUNA_PRODUCT_BLUEPRINT.md`
- `CLAUDE_PRODUCT_PHASE_FREEZE.md`

Третий файл нужен, чтобы Claude:
- не возвращался автоматически в endless reasoning-polish mode
- учитывал текущую фазу проекта
- предлагал следующие шаги в логике product build mode

---

# 11. Финальная формулировка

Мы признаём reasoning core текущей версии **достаточно сильным для этой фазы**.
Он не идеален.
Но теперь дальнейшие микроулучшения reasoning **не являются default priority**.

## Теперь главный фокус — не endlessly improve the brain, а собрать целостное тело продукта.

Возвращаться к deep reasoning fixes можно только по сильному основанию:
- trust-breaking bug
- loop-breaking bug
- or major product-value gain

Во всех остальных случаях следующий шаг должен вести Runa к более целостному, законченному, usable product experience.
