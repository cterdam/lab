# Game

## Core Concepts

### Events

The game is driven by an event queue. All events inherit from the `Event` base
class and have an `event_id` (eid). This is monotonically increasing and sorted
by creation time.

### Event Queue

The game uses a priority queue to manage events. Each item in the queue is a
tuple `(priority: int, eid: int, event: Event)`.

### Extending the Game

To create a custom game:

1. Subclass `Game` and override `_do_handle_event()` to add new event types.
2. Override specific handlers to customize existing event handling.
