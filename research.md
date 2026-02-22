# Research: Open-Source Options for Celebrity Persona Game Agent

## Track 1: Agentic AI Frameworks

### PydanticAI (RECOMMENDED)
- **Stars:** ~15k | **License:** MIT | **Maturity:** Production-stable (v1.62+)
- Built by the Pydantic team. Lightweight, async-native, model-agnostic.
- First-class tool support with dependency injection. Dynamic system prompts.
- `agent.iter()` for async iteration over reasoning loop nodes.
- **Best fit** for embedding in a custom game engine — plain Python object, no
  heavyweight abstractions.
- https://github.com/pydantic/pydantic-ai

### OpenAI Agents SDK
- **Stars:** ~19k | **License:** MIT
- Clean, lightweight. `AgentHooks` lifecycle pattern. Model-agnostic via LiteLLM.
- Good alternative but lacks PydanticAI's dependency injection elegance.
- https://github.com/openai/openai-agents-python

### Smolagents (HuggingFace)
- **Stars:** ~25k | **License:** Apache 2.0
- Lightest framework (~1000 lines core). ReAct loop. CodeAgent paradigm.
- Sync-first design needs wrapping for async game engine.
- https://github.com/huggingface/smolagents

### CrewAI
- **Stars:** ~44k | **License:** MIT
- Best-in-class role/goal/backstory persona system. "Orchestrating role-playing
  AI agents."
- Overkill — Crew/Task abstraction adds overhead when you already have a game
  engine.
- https://github.com/crewAIInc/crewAI

### LangChain / LangGraph
- **Stars:** ~90k / ~15k | **License:** MIT
- Most mature, heaviest. Graph-based state machine. Production-grade durability.
- Too heavy for "LM with tools inside a Player."
- https://github.com/langchain-ai/langgraph

### AutoGen / AG2
- **Stars:** ~54k / ~4k | **License:** MIT / Apache 2.0
- Fragmenting ecosystem (AutoGen → AG2 → Microsoft Agent Framework). Not
  recommended for new projects.
- https://github.com/ag2ai/ag2

### Google ADK
- **Stars:** ~16k | **License:** Apache 2.0
- Gemini-first. Good `BaseAgent` subclass pattern. Only if in Google ecosystem.
- https://github.com/google/adk-python

### Claude Agent SDK
- **Stars:** ~4.5k | **License:** Commercial ToS
- 12s startup overhead (CLI subprocess). Claude-only. Poor fit for interactive
  games.
- https://github.com/anthropics/claude-agent-sdk-python

---

## Track 2: Persona / Character AI Libraries

### Microsoft TinyTroupe
- **Stars:** ~5k | **License:** MIT
- LLM-powered persona simulation. TinyPersons with detailed specs. Persona
  adherence validation.
- Closest to a reusable persona library, but no tool-calling or game integration.
- https://github.com/microsoft/TinyTroupe

### Letta (formerly MemGPT)
- **License:** Apache 2.0 | **Maturity:** Very mature
- Tiered memory system (persona blocks, self-editing memory). Long-running
  stateful agents.
- Good for persistent character memory, but heavy framework.
- https://github.com/letta-ai/letta

### Character-LLM
- **Stars:** ~368 | **EMNLP 2023**
- Pipeline: Wikipedia profile → scene extraction → experience reconstruction →
  fine-tune. Beethoven, Cleopatra, Caesar.
- **Key pattern to borrow:** biography → structured profile → system prompt.
- https://github.com/choosewhatulike/trainable-agents

### DITTO (Alibaba/OFA-Sys)
- **Stars:** ~191 | **License:** MIT | **ACL 2024**
- Self-alignment for role-play. 4,000 characters from Wikidata/Wikipedia.
- Dataset + fine-tuning pipeline, not a runtime agent library.
- https://github.com/OFA-Sys/Ditto

### CoSER
- **ICML 2025** | SOTA role-playing performance (surpasses GPT-4o)
- 29,798 conversations from 17,966 characters in 771 books. Given-Circumstance
  Acting evaluation.
- https://github.com/Neph0s/CoSER

### SimsChat
- Sims-inspired character construction (career, traits, skills). 68 characters,
  13k dialogues.
- Character construction pipeline is reusable as a pattern.
- https://github.com/Bernard-Yang/SimsChat

### RoleLLM
- **ACL 2024 Findings** | 100 roles, 168k benchmark samples
- Four-stage: Profile Construction → Instruction Generation → Role Prompting →
  Fine-tuning.
- https://github.com/InteractiveNLP-Team/RoleLLM-public

### SillyTavern / TavernAI
- Most feature-rich open-source character chat frontend.
- **Character card format** (W++, SBF, Boostyle) is the de facto community
  standard for persona definition. Worth adopting the field structure.
- Node.js-based, not directly embeddable. License: AGPL v3.0.
- https://docs.sillytavern.app/

### Gigax
- **Stars:** ~336 | **License:** MIT
- LLM-powered NPCs with structured game actions (`<say>`, `<jump>`, `<attack>`).
  Fine-tuned NPC models. Sub-second inference.
- Most directly game-ready, but focused on 3D game engines, not text-based games.
- https://github.com/GigaxGames/gigax

### AI Celebrity Models
- JSON knowledge bases for celebrity personas from podcasts/interviews.
- Small niche project but useful as data resource.
- https://github.com/FlDanyT/ai-celebrity-models

### PersonaGym
- Evaluation framework: 200 personas, 5 metrics (consistency, linguistic habits,
  action justification, toxicity, expected action).
- Useful for testing, not building.

### Mem0
- **License:** Apache 2.0 | Production-ready
- Universal memory layer for AI agents. Embeddable Python library.
- https://github.com/mem0ai/mem0

---

## Track 3: LLM Game Agent Frameworks

### Generative Agents (Stanford)
- **Stars:** ~20k | Seminal work (2023)
- Memory stream + Reflection + Planning — the gold standard cognitive
  architecture. Hugely influential.
- Code is tightly coupled to 2D tile world. **Pattern is highly extractable;
  code is not.**
- https://github.com/joonspk-research/generative_agents

### CAMEL
- **Stars:** ~15k | **License:** Apache 2.0 | Very active
- Role-playing multi-agent framework. Scales to 1M agents. OASIS, OWL (NeurIPS
  2025).
- General-purpose — good for multi-agent scenarios but adds framework weight.
- https://github.com/camel-ai/camel

### AgentVerse (OpenBMB)
- **Stars:** ~4.7k | **License:** Apache 2.0 | ICLR 2024
- Task-solving + Simulation dual framework. Prisoner's Dilemma, Pokemon, etc.
- https://github.com/OpenBMB/AgentVerse

### ChatArena (Farama)
- **Stars:** ~1.5k | **DEPRECATED** Aug 2025
- Gym-style step/observe for text games. Clean abstractions but abandoned.
- https://github.com/Farama-Foundation/chatarena

### Avalon-LLM / Strategist
- **Stars:** ~137 | **ICLR 2025**
- LLM strategy generation + MCTS execution + self-improvement loop.
- Novel pattern for imperfect-information games.
- https://github.com/jonathanmli/Avalon-LLM

### LLMafia
- **EMNLP 2025** | Generator + Scheduler dual-module for async communication
- Novel pattern: separates *what to say* from *when to say it*.
- https://github.com/niveck/LLMafia

### llm-mafia-game
- Cleanest modular separation: game engine + agent behaviors + LLM wrappers.
- https://github.com/bastoscostadavi/llm-mafia-game

### AmongAgents
- Memory + Reflection + Planning for Among Us. Richer action space than
  Werewolf.
- https://github.com/cyzus/among-agents

### CICERO (Meta)
- **Stars:** ~1.3k | **ARCHIVED** | Diplomacy
- 2.7B LM + RL planner hybrid. Science (2022). Top 10% human performance.
- Too specialized for reuse. Pattern (dialogue model + strategic planner)
  is influential.
- https://github.com/facebookresearch/diplomacy_cicero

### GamingAgent
- **Stars:** ~847 | **ICLR 2026**
- VLM-based video game agents (Tetris, Mario, 2048). Gym-style API.
- https://github.com/lmgame-org/GamingAgent

---

## Key Architectural Patterns (cross-cutting)

1. **Memory + Reflection + Planning** (Stanford) — most widely adopted cognitive
   architecture for game agents
2. **Prompt-only / Frozen LLM** — most accessible, no fine-tuning needed
3. **LLM + Strategic Planner** (CICERO, Strategist) — strongest game results but
   complex
4. **Generator + Scheduler** (LLMafia) — novel for async communication games
5. **Self-Play + Self-Improvement** (Strategist, GPT-Bargaining) — iterative
   strategy refinement

## Meta-Resources

- [awesome-llm-role-playing-with-persona](https://github.com/Neph0s/awesome-llm-role-playing-with-persona) — definitive paper list
- [awesome-LLM-game-agent-papers](https://github.com/git-disl/awesome-LLM-game-agent-papers) — updated weekly
- [PersonaPaper](https://github.com/Sahandfer/PersonaPaper) — persona dialogue systems
