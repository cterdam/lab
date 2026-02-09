# Celery & RabbitMQ

## Overview

**RabbitMQ** is a message broker that accepts messages from producers and routes
them to consumers via queues. Think of it as a post office: the app drops off a
message (a task), RabbitMQ holds it in a queue, and a worker picks it up when
ready.

**Celery** is a distributed task queue framework for Python. It defines tasks as
decorated functions, then executes them asynchronously on separate worker
processes. Celery needs a broker (like RabbitMQ) to shuttle messages between the
caller and the workers, and optionally a *result backend* (like Redis) to store
return values.

Together: **the app sends a task → RabbitMQ queues it → a Celery worker picks it
up and executes it.**

## How This Repo Currently Works (Without Celery)

This project uses **asyncio + Redis** for concurrency and data storage. There is
no Celery or RabbitMQ integration today.

| Concern          | Current Approach                         | With Celery/RabbitMQ                    |
|------------------|------------------------------------------|-----------------------------------------|
| Task definition  | Plain functions in `src/task/*/main.py`  | `@app.task`-decorated functions         |
| Task dispatch    | CLI arg `task=demo` → `importlib` loader | `my_task.delay(args)` / `.apply_async()`|
| Concurrency      | `asyncio.gather()` in a single process   | Separate worker processes on queues     |
| Broker           | None — no message passing                | RabbitMQ (`amqp://rabbitmq:5672`)       |
| Data store       | Redis (`redis://redis:6379/0`)           | Redis remains (data + result backend)   |
| Infrastructure   | `compose.yml`: `redis` + `app`           | Add `rabbitmq` + `celery-worker`        |

### Current task system

Tasks live under `src/task/` and are dispatched by `src/__main__.py`:

```python
# src/__main__.py
module_name = f"src.task.{arg.task}"
module = importlib.import_module(module_name)
module.main()
```

Each task module exposes a `main()` function. For example, `src/task/demo/main.py`
runs synchronous and asynchronous API calls, then launches a game demo — all
within a single process using `asyncio.gather()`.

### Current Redis usage

Redis serves as a shared data store for counters, groups, and logger state. It is
**not** used as a message broker.

Key clients are in `src/core/environment.py`:

- `env.r` / `env.ar` — sync/async default Redis clients
- `env.cr` / `env.acr` — sync/async counter clients (with response callbacks)
- `env.coup()` / `env.acoup()` — pipeline context managers for batched counter
  updates

## When Would Celery & RabbitMQ Help?

1. **Distributed execution** — offloading work to multiple worker
   machines/containers, not just async within one process.
2. **Reliability** — RabbitMQ persists messages; if a worker crashes mid-task,
   the message returns to the queue and another worker retries it.
3. **Rate limiting & prioritization** — Celery supports rate limits, task
   priorities, and routing to specialized queues.
4. **Scheduled tasks** — Celery Beat runs tasks on a cron-like schedule (this
   repo currently has no scheduled tasks).
5. **Decoupling** — the caller fires and forgets; it can poll a result backend
   later.

## What Integration Would Look Like

### 1. Dependencies

Add to `requirements.txt`:

```
celery>=5.4
```

RabbitMQ is infrastructure (Docker image), not a Python package.

### 2. Docker Compose services

```yaml
# additions to compose.yml
rabbitmq:
  image: rabbitmq:3-management
  healthcheck:
    test: ["CMD", "rabbitmq-diagnostics", "check_running"]
    interval: 5s
    timeout: 5s
    retries: 3
  ports:
    - "5672:5672"      # AMQP protocol
    - "15672:15672"    # Management UI

celery-worker:
  build: .
  image: lab
  depends_on:
    rabbitmq:
      condition: service_healthy
    redis:
      condition: service_healthy
  env_file: .env
  command: celery -A src.celery_app worker --loglevel=info
```

### 3. Celery app configuration

```python
# src/celery_app.py
from celery import Celery

app = Celery(
    "lab",
    broker="amqp://guest:guest@rabbitmq:5672//",
    backend="redis://redis:6379/0",
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
)

# Auto-discover tasks in src/task/*/
app.autodiscover_tasks(["src.task.demo"])
```

### 4. Converting a task

Before (current pattern — direct call in-process):

```python
# src/task/demo/main.py
def run_sync(n_tasks, wb, model):
    for i in range(n_tasks):
        prompt = f"In 10 words, what is {wb.pick_word()}"
        result = model.gentxt(OpenAILMGentxtParams(prompt=prompt))
```

After (Celery task — executed by a remote worker):

```python
from src.celery_app import app

@app.task(bind=True, max_retries=3)
def run_gentxt(self, prompt: str) -> str:
    model = OpenAILM(params=OpenAILMInitParams(model_name="gpt-4.1"))
    result = model.gentxt(OpenAILMGentxtParams(prompt=prompt))
    return result.data.output_str
```

Invoking:

```python
# Fire-and-forget
run_gentxt.delay("In 10 words, what is Python?")

# With options
run_gentxt.apply_async(
    args=["In 10 words, what is Python?"],
    countdown=10,       # delay execution by 10 seconds
    expires=300,        # expire after 5 minutes
)

# Get result (blocks)
result = run_gentxt.delay("In 10 words, what is Python?")
output = result.get(timeout=30)
```

### 5. Periodic tasks (Celery Beat)

```python
# In src/celery_app.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    "nightly-cleanup": {
        "task": "src.task.cleanup.run",
        "schedule": crontab(hour=2, minute=0),
    },
}
```

Run the scheduler:

```bash
celery -A src.celery_app beat --loglevel=info
```

## Key Concepts

| Concept          | Description                                                      |
|------------------|------------------------------------------------------------------|
| **Broker**       | Transports task messages. The app publishes; workers consume.    |
| **Worker**       | Long-running process that pulls tasks from the broker.           |
| **Result backend** | Stores task return values (this repo's Redis would work).     |
| **Task**         | A Python function decorated with `@app.task`.                    |
| **Celery Beat**  | Scheduler that periodically pushes tasks into the broker.        |
| **Flower**       | Optional web UI for monitoring Celery workers and tasks.         |

## Architecture Diagram

```
                          ┌─────────────┐
                          │  RabbitMQ   │
                          │  (broker)   │
                          └──────┬──────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                   │
              ▼                  ▼                   ▼
       ┌─────────────┐   ┌─────────────┐    ┌─────────────┐
       │   Worker 1   │  │   Worker 2   │   │   Worker N   │
       └──────┬──────┘   └──────┬──────┘    └──────┬──────┘
              │                  │                   │
              └──────────────────┼───────────────────┘
                                 │
                          ┌──────▼──────┐
                          │    Redis    │
                          │  (results   │
                          │  + data)    │
                          └─────────────┘
```

**App** publishes task messages to RabbitMQ. **Workers** consume from queues and
execute the tasks. Results are stored in **Redis**, which continues to serve as
the shared data store.
