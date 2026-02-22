# Plan: `src/lib/persona` — LM-backed Celebrity Persona Agent

## Research Summary

Thorough research across three tracks (agentic frameworks, persona/character AI,
game AI agents) identified **PydanticAI** as the best agentic harness for this
use case. Full research notes in `research.md`.

**Why PydanticAI:**
- Lightweight, MIT-licensed, async-native, model-agnostic
- Built-in agentic loop with tool-calling (no need to hand-roll one)
- Dependency injection for passing game state to tools and system prompts
- Dynamic system prompts (runtime-generated based on context) — perfect for
  persona + game state injection
- Pydantic-native — matches our codebase perfectly (we already use Pydantic
  everywhere)
- Designed to be embedded in larger applications (not an opinionated framework)

**Why not others:**
- *CrewAI*: Great role/goal/backstory but Crew/Task abstraction is overhead when
  we already have a game engine
- *LangGraph*: Too heavy — thick abstraction layer for what is "LM with tools
  inside a Player"
- *OpenAI Agents SDK*: Good but PydanticAI's dependency injection is a better
  fit for game state passing
- *TinyTroupe*: Persona simulation only, no tool-calling or game integration
- *Claude Agent SDK*: 12s startup, CLI subprocess, Claude-only — unsuitable for
  interactive games
- *Game-specific projects* (ChatArena, LLMafia, etc.): Research artifacts tied
  to specific games

**Persona layer** built ourselves (it's thin) — no existing library does
celebrity-profile + tool-calling + game-engine integration together. We borrow
patterns from:
- SillyTavern character card format (profile fields)
- Character-LLM pipeline (biography → structured profile → system prompt)
- Stanford Generative Agents (memory accumulation across events)

---

## Overview

A **Persona** is an LM-backed `Player` that participates in any game via the
existing game engine. It wraps a **PydanticAI Agent** and impersonates a
celebrity by combining a structured **Profile** (built from raw biographical
text) with PydanticAI's built-in agentic tool-calling loop — all in-character.

Architecture: **Perceive → Reason → Act → Remember**, where PydanticAI handles
the Reason+Act loop internally.

```
src/lib/persona/
├── __init__.py                  # Public exports
├── persona.py                   # Persona(Player) — wraps PydanticAI Agent
├── persona_init_params.py       # PersonaInitParams — creation config
├── persona_deps.py              # PersonaDeps — dependency injection context
├── profile.py                   # Profile — structured celebrity identity
├── profiler.py                  # Profiler(Logger) — builds Profile from raw text via LM
└── renderer.py                  # EventRenderer — converts Events → LM prompt text
```

No custom `tool/` directory needed — PydanticAI handles tool definition,
schema generation, execution, and the agentic loop natively.

---

## 1. Profile (`profile.py`)

A `Dataclass` holding the structured celebrity identity. Renders itself into the
system prompt that steers all LM behavior. Field design inspired by SillyTavern
character cards and the SimsChat character construction system.

```python
class Profile(Dataclass):
    name: str                # "Gordon Ramsay"
    background: str          # Bio, career highlights, key life events
    personality: str         # Traits, temperament, values, quirks
    speech_style: str        # Vocabulary, catchphrases, tone, patterns
    decision_style: str      # How they approach decisions, strategy, risk

    def render(self) -> str:
        """Produce the system prompt from this profile."""
```

The `render()` method produces a system prompt that instructs the LM to stay
in-character across all decision types (speech, game moves, negotiations, etc.),
not just dialogue.

## 2. PersonaDeps (`persona_deps.py`)

The dependency injection context passed to PydanticAI tools and system prompt
functions. This is the contract between the Persona and game-specific tools.

```python
@dataclass
class PersonaDeps:
    persona_lid: Lid               # This persona's lid
    profile: Profile               # Celebrity identity
    memory: list[Event]            # Events this persona has witnessed
    pending_events: list[Event]    # Tools append side-effect events here
    can_react: bool                # Whether reactions are allowed
    can_interrupt: bool            # Whether interrupts are allowed
```

Game-specific tools receive `RunContext[PersonaDeps]` and can:
- Read `ctx.deps.memory` for game context
- Read `ctx.deps.profile` for persona identity
- Append to `ctx.deps.pending_events` to produce game Events as side-effects
- Return a string that gets fed back to the LM

## 3. Event Renderer (`renderer.py`)

Converts game `Event`s into LM-readable prompt text. This is the perception
layer.

```python
class EventRenderer:
    def render_event(self, e: Event, persona_lid: Lid) -> str:
        """Convert a single Event to a text description."""

    def render_history(self, memory: list[Event], persona_lid: Lid) -> str:
        """Convert the persona's observed event history into a prompt section."""
```

- `Speech` events → "PlayerX said: ..." or "You said: ..."
- `GameStart`/`GameEnd` → "[Game started]" / "[Game ended]"
- Custom events → descriptive text
- The renderer knows the persona's `lid` to distinguish own actions from others'

## 4. Persona (`persona.py`)

The central class. Extends `Player`, wraps a PydanticAI `Agent`.

```python
from pydantic_ai import Agent

class Persona(Player):
    logspace_part = "persona"

    _agent: Agent[PersonaDeps, str]
    _profile: Profile
    _renderer: EventRenderer
    _memory: list[Event]

    def __init__(self, params: PersonaInitParams, profile: Profile,
                 tools: list, *, logname: str | None = None, **kwargs):
        super().__init__(logname=logname or profile.name, **kwargs)
        self._profile = profile
        self._renderer = EventRenderer()
        self._memory = []
        self._agent = Agent(
            params.model_name,
            system_prompt=self._system_prompt,  # Dynamic
            deps_type=PersonaDeps,
            tools=tools,                        # PydanticAI-native tools
            retries=params.max_tool_rounds,
        )

    def _system_prompt(self, ctx: RunContext[PersonaDeps]) -> str:
        """Dynamic system prompt from profile + game context."""
        history_text = self._renderer.render_history(
            ctx.deps.memory, ctx.deps.persona_lid
        )
        return ctx.deps.profile.render() + "\n\n" + history_text

    async def ack_event(self, e: Event, *, can_react: bool,
                        can_interrupt: bool) -> list[Event]:
        """Perceive an event, reason via PydanticAI agent, act via tools."""

        # 1. PERCEIVE: Accumulate memory
        self._memory.append(e)

        # 2. BUILD DEPS
        deps = PersonaDeps(
            persona_lid=self.lid,
            profile=self._profile,
            memory=list(self._memory),
            pending_events=[],
            can_react=can_react,
            can_interrupt=can_interrupt,
        )

        # 3. REASON + ACT: PydanticAI runs the agentic loop
        prompt = self._renderer.render_event(e, self.lid)
        result = await self._agent.run(prompt, deps=deps)

        # 4. COLLECT: Events from tool side-effects + final speech
        events = list(deps.pending_events)
        if result.output and can_react:
            events.append(Speech(
                src=self.lid,
                audience=[...],  # Determined from event context
                content=result.output,
                blocks=[e.sid],
            ))

        return events
```

### PersonaInitParams (`persona_init_params.py`)

```python
class PersonaInitParams(Dataclass):
    model_name: str = "openai:gpt-4.1"  # PydanticAI model string
    temperature: float = 0.8            # Slightly creative for personality
    max_new_tokens: int = 1024
    max_tool_rounds: int = 10           # Safety cap on agentic loop
```

## 5. Profiler (`profiler.py`)

A `Logger` that uses an existing `LM` instance to extract a structured `Profile`
from unstructured raw text (Wikipedia articles, interview transcripts, etc.).
Follows the Character-LLM pattern: biography → structured extraction → profile.

```python
class Profiler(Logger):
    logspace_part = "profiler"

    async def build(self, name: str, raw_text: str, lm: OpenAILM) -> Profile:
        """Extract structured profile fields from raw biographical text."""
```

- Calls `lm.agentxt()` with a structured extraction prompt
- Parses the LM output into `Profile` fields
- The caller is responsible for gathering the raw text — the Profiler structures
  it
- Reuses the existing `OpenAILM` and its metrics tracking

## 6. How it reuses existing + external code

| Component | Source |
|---|---|
| Agentic loop + tool-calling | **PydanticAI** (new dependency) |
| `Player` abstract base | Existing — `Persona` extends it directly |
| `Event`, `Speech`, `Interrupt` | Existing — Persona receives/produces these |
| `Game` event loop | Existing — no changes needed |
| `Logger` hierarchy | Existing — Persona inherits logging, counters |
| `Dataclass` | Existing — Profile, Params extend it |
| `OpenAILM` | Existing — Profiler uses it for profile extraction |
| `openai` SDK | Existing — PydanticAI uses it under the hood |
| `logspace_part` convention | Existing — `"persona"`, `"profiler"` |

**Changes to existing files:** Only `requirements.txt` (add `pydantic-ai`).
Everything else is additive.

## 7. Tool authoring (for game developers)

Games define tools as PydanticAI-native decorated functions. No custom tool
abstraction needed.

```python
from pydantic_ai import RunContext
from src.lib.persona.persona_deps import PersonaDeps

async def vote_to_eliminate(
    ctx: RunContext[PersonaDeps],
    target_name: str,
) -> str:
    """Vote to eliminate a player from the game (Mafia).

    Args:
        target_name: The name of the player to vote against.
    """
    vote_event = VoteEvent(
        src=ctx.deps.persona_lid,
        target=target_name,
        blocks=[...],
    )
    ctx.deps.pending_events.append(vote_event)
    return f"You voted to eliminate {target_name}."

async def check_hand(
    ctx: RunContext[PersonaDeps],
) -> str:
    """Look at your current hand of cards."""
    # Info-only tool — no events produced
    hand = get_hand_for(ctx.deps.persona_lid)
    return f"Your cards: {hand}"
```

## 8. Usage example

```python
# Build profile from raw text
profiler = Profiler()
lm = OpenAILM(params=OpenAILMInitParams(model_name="gpt-4.1"))
profile = await profiler.build(
    name="Gordon Ramsay",
    raw_text="Gordon James Ramsay is a British chef, restaurateur...",
    lm=lm,
)

# Create persona player with game-specific tools
ramsay = Persona(
    params=PersonaInitParams(model_name="openai:gpt-4.1"),
    profile=profile,
    tools=[vote_to_eliminate, check_hand],
)

# Add to game — works with existing game engine unchanged
await game.add_player(ramsay)
await game.start()
```

## 9. Implementation order

1. **`profile.py`** — Profile dataclass with render() (no dependencies)
2. **`persona_deps.py`** — PersonaDeps dataclass (depends on Profile + Event)
3. **`renderer.py`** — EventRenderer (depends on game events)
4. **`persona_init_params.py`** — PersonaInitParams dataclass
5. **`persona.py`** — Persona class wrapping PydanticAI Agent
6. **`profiler.py`** — Profiler that builds Profile from raw text
7. **`__init__.py`** — Public exports
8. **`requirements.txt`** — Add `pydantic-ai`
9. **Tests** — Unit tests for Profile rendering, event rendering, and the
   Persona (with mocked PydanticAI agent)
