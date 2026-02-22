# Game

## Events

The game is driven by a sequence of events.

### Basics

All events inherit from the `Event` base class and use the `sid` as event ID.
This is monotonically increasing and sorted by creation time.

An event is handled when it is sent to its specific handler function. An event
is processed when it is fully taken care of, which includes both the
event-specific handling and generic processing logic.

### Queue

The game uses a queue to manage events. Each item in the queue is a tuple
`(priority: int, eid: int, event: Event)`. The main game loop is getting the top
event from the queue and processing it.

### Reacts

The game will send notif of each event to relevant players. Players can react to
the events by returning a list of react events.

An interrupt is a special kind of react that only applies to speech events. It
takes precedence over other kind of reacts.

### Subevents

Sometimes the processing of an event necessitates processing another event
before it finishes. In this case the subevent is created and directly processed
without going through the queue.

## State

The game's internal state is kept in a `GameState` object. It should keep any
and all internal attributes that's serializable. During the program, read or
write access to any field of the game state must pass through an async context
manager to ensure concurrency safety.

## History

Each event is snapshotted on the game's history multiple times throughout that
event's life cycle. Each occurrence of the same event in history will show
different stages.

### Extending the Game

To create a custom game:

1. Subclass `Game` and override `_handle_event()` to add new event types.
2. Override specific handlers to customize existing event handling.
