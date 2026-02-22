# Plan: `src/lib/persona` — LM-backed Celebrity Persona Agent

## Overview

A **Persona** is an LM-backed `Player` that participates in any game via the existing game engine. It impersonates a celebrity by combining a structured **Profile** (built from raw biographical text) with an **agentic tool-calling loop** so it can reason, gather information, and take game-specific actions — all in-character.

Architecture: **Perceive → Reason → Act → Remember** — the standard agent loop, implemented as a `Player` subclass.

```
src/lib/persona/
├── __init__.py                  # Public exports
├── persona.py                   # Persona(Player) — the agentic celebrity player
├── persona_init_params.py       # PersonaInitParams — creation config
├── profile.py                   # Profile — structured celebrity identity
├── profiler.py                  # Profiler(Logger) — builds Profile from raw text via LM
├── renderer.py                  # EventRenderer — converts Events ↔ LM messages
└── tool/
    ├── __init__.py              # Public exports
    ├── tool.py                  # Tool — defines a callable tool for the LM
    └── tool_call.py             # ToolCall, ToolResult — dataclasses
```

---

## 1. Profile (`profile.py`)

A `Dataclass` holding the structured celebrity identity. Renders itself into the system prompt that steers all LM behavior.

```python
class Profile(Dataclass):
    name: str                # "Gordon Ramsay"
    background: str          # Bio, career highlights, key life events
    personality: str         # Traits, temperament, values, quirks
    speech_style: str        # Vocabulary, catchphrases, tone, patterns
    decision_style: str      # Strategic? Impulsive? Cautious? Competitive?

    def render(self) -> str:
        """Produce the system prompt from this profile."""
```

The `render()` method produces a carefully crafted system prompt that instructs the LM to stay in-character across all decision types (speech, game moves, negotiations, etc.), not just dialogue.

## 2. Profiler (`profiler.py`)

A `Logger` that uses an existing `LM` instance to extract a structured `Profile` from unstructured raw text (Wikipedia articles, interview transcripts, etc.).

```python
class Profiler(Logger):
    logspace_part = "profiler"

    async def build(self, name: str, raw_text: str, lm: OpenAILM) -> Profile:
        """Extract structured profile fields from raw biographical text."""
```

- Calls `lm.agentxt()` with a structured extraction prompt
- Parses the LM output into `Profile` fields
- The caller is responsible for gathering the raw text (web scraping, copy-paste, etc.) — the Profiler just structures it
- Reuses the existing `OpenAILM` and its metrics tracking

## 3. Tool System (`tool/`)

### `Tool` (`tool.py`)

Defines a callable tool the LM can invoke during its reasoning loop. Games provide their own tools.

```python
class Tool:
    name: str                              # "buy_property"
    description: str                       # "Buy an available property"
    parameters: dict                       # JSON Schema for arguments
    handler: Callable[..., Awaitable[ToolResult]]  # Async execution function

    def schema(self) -> dict:
        """Return the OpenAI function tool schema dict."""
```

Tools fall into two categories (both use the same `Tool` class):
- **Information tools**: query game state, check hand, look at board → return text to the LM
- **Action tools**: buy property, vote, trade → return text to the LM AND produce game `Event`s

### `ToolCall` / `ToolResult` (`tool_call.py`)

```python
class ToolCall(Dataclass):
    call_id: str          # From the API response
    tool_name: str
    arguments: dict       # Parsed from JSON

class ToolResult(Dataclass):
    call_id: str
    output: str           # Text fed back to the LM
    events: list[Event]   # Game events produced (empty for info-only tools)
```

The `events` field is key: it lets action tools produce arbitrary game events (Speech, custom game events, etc.) that the Persona collects and returns from `ack_event()`.

## 4. Event Renderer (`renderer.py`)

Converts between game `Event`s and LM message dicts. This is the perception layer.

```python
class EventRenderer:
    def render_event(self, e: Event, persona_lid: Lid) -> dict:
        """Convert a single Event to an OpenAI message dict."""

    def render_history(self, memory: list[Event], persona_lid: Lid) -> list[dict]:
        """Convert the persona's observed event history into a message list."""
```

- `Speech` events → user/assistant messages (depending on who spoke)
- `GameStart`/`GameEnd` → system notifications
- Custom events → descriptive text
- The renderer knows the persona's `lid` so it can distinguish "I said X" from "Player Y said X"

## 5. Persona (`persona.py`)

The central class. Extends `Player`, composes everything above.

```python
class Persona(Player):
    logspace_part = "persona"

    # Core components
    _profile: Profile
    _tools: list[Tool]
    _renderer: EventRenderer
    _aclient: openai.AsyncOpenAI     # Own client for tool-calling
    _memory: list[Event]             # Events this persona has witnessed

    # Config
    _model_name: str
    _temperature: float
    _max_new_tokens: int
    _max_tool_rounds: int            # Safety limit on agentic loop iterations

    def __init__(self, params: PersonaInitParams, profile: Profile,
                 tools: list[Tool], *, logname: str | None = None, **kwargs):
        ...

    async def ack_event(self, e: Event, *, can_react: bool,
                        can_interrupt: bool) -> list[Event]:
        """Perceive an event, reason via LM, and act via tools."""
```

### The agentic loop inside `ack_event()`:

```
1. PERCEIVE: Append event to _memory
2. RENDER: Convert _memory → LM messages via _renderer
3. REASON + ACT (loop up to max_tool_rounds):
   a. Call OpenAI Responses API with messages + tool schemas + profile system prompt
   b. Parse response output items:
      - function_call items → execute tool handler → collect ToolResult
        - Feed tool output back as function_call_output
        - Accumulate any events from ToolResult.events
      - message items → extract final text response
   c. If no more function_calls, break
4. RESPOND: If final text is non-empty and can_react, wrap it as a Speech event
5. RETURN: All accumulated events (from tools + final speech)
```

The Persona uses its own `openai.AsyncOpenAI` client (not reaching into `OpenAILM` internals). This keeps the existing `LM` hierarchy untouched while reusing the same OpenAI API patterns.

### `PersonaInitParams` (`persona_init_params.py`)

```python
class PersonaInitParams(Dataclass):
    model_name: str = "gpt-4.1"
    api_key: SecretStr | None = None   # Falls back to OPENAI_API_KEY env var
    temperature: float = 0.8           # Slightly creative for personality
    max_new_tokens: int = 1024
    max_tool_rounds: int = 10          # Safety cap on agentic loop
```

## 6. How it reuses existing code

| Existing code | How Persona reuses it |
|---|---|
| `Player` (abstract base) | `Persona` extends it directly — plugs into the game engine |
| `Event`, `Speech`, `Interrupt` | Persona receives/produces these via `ack_event()` |
| `Game` event loop | Persona participates as a regular player — no game engine changes |
| `Logger` hierarchy | Persona inherits full logging, counters, file sinks |
| `Dataclass` | All data objects (Profile, ToolCall, ToolResult, Params) extend it |
| `OpenAILM` + `OpenAILMInitParams` | Profiler uses the existing LM for profile extraction |
| OpenAI SDK | Persona uses the same `openai` package already in requirements |
| `LMGentxtParams` pattern | PersonaInitParams follows the same Pydantic params pattern |
| `logspace_part` convention | `"persona"` and `"profiler"` slot into the log directory tree |

**No modifications to any existing files.** The entire persona module is additive.

## 7. Usage example (conceptual)

```python
# Build profile from raw text
profiler = Profiler()
profile = await profiler.build(
    name="Gordon Ramsay",
    raw_text="Gordon James Ramsay is a British chef, restaurateur...",
    lm=model,
)

# Define game-specific tools
tools = [
    Tool(
        name="say",
        description="Say something to other players",
        parameters={"type": "object", "properties": {"message": {"type": "string"}}},
        handler=say_handler,
    ),
    Tool(
        name="vote",
        description="Vote to eliminate a player (Mafia)",
        parameters={"type": "object", "properties": {"target": {"type": "string"}}},
        handler=vote_handler,
    ),
]

# Create persona player
ramsay = Persona(
    params=PersonaInitParams(model_name="gpt-4.1"),
    profile=profile,
    tools=tools,
)

# Add to game — works with existing game engine unchanged
await game.add_player(ramsay)
await game.start()
```

## 8. Implementation order

1. **`tool/tool_call.py`** — ToolCall and ToolResult dataclasses (no dependencies)
2. **`tool/tool.py`** — Tool definition class (depends on tool_call)
3. **`tool/__init__.py`** — Exports
4. **`profile.py`** — Profile dataclass with render()
5. **`renderer.py`** — EventRenderer (depends on game events)
6. **`persona_init_params.py`** — PersonaInitParams dataclass
7. **`persona.py`** — Persona class with agentic loop (depends on everything above)
8. **`profiler.py`** — Profiler that builds Profile from raw text (depends on Profile + LM)
9. **`__init__.py`** — Public exports
10. **Tests** — Unit tests for Profile rendering, tool execution, event rendering, and the agentic loop (with mocked LM responses)
