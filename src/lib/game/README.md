# Game

## Events

The game is driven by a sequence of events.

### Basics

All events inherit from the `Event` base class and have an `event_id` (eid).
This is monotonically increasing and sorted by creation time.

An event is handled when it is sent to its specific handler function. An event
is processed when it is fully taken care of, which includes both the
event-specific handling and generic processing logic.

### Queue

The game uses a priority queue to manage events. Each item in the queue is a
tuple `(priority: int, eid: int, event: Event)`. The main game loop is getting
the top event from the queue and processing it.

### Subevents

Sometimes the processing of an event necessitates processing another event
before it finishes. In this case the subevent is created and directly processed
without going through the queue.

### Extending the Game

To create a custom game:

1. Subclass `Game` and override `_handle_event()` to add new event types.
2. Override specific handlers to customize existing event handling.
