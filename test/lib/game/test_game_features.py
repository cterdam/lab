import pytest

from src.core import group
from src.lib.game.event import AddPlayer, Event
from src.lib.game.game import Game
from src.lib.game.game_init_params import GameInitParams
from src.lib.game.game_state import GameStage
from src.lib.game.player import Player


class DummyPlayer(Player):
    async def ack_event(
        self, e: Event, *, can_react: bool, can_interrupt: bool
    ) -> list[Event]:
        return []


@pytest.mark.asyncio
async def test_add_player_immediate():
    """Test AddPlayer event processing when game is WAITING."""
    params = GameInitParams()
    game = Game(params=params, logname="test_game_immediate")

    player1 = DummyPlayer(logname="p1")

    # When WAITING, add_player should process the event immediately
    await game.add_player(player1)

    # Check if added to ALL_PLAYERS group
    assert player1.lid in group.children(game.gid(game.gona.ALL_PLAYERS))


@pytest.mark.asyncio
async def test_add_player_queued():
    """Test AddPlayer event enqueuing when game is ONGOING."""
    params = GameInitParams()
    game = Game(params=params, logname="test_game_queued")

    # Force game to ONGOING stage
    async with game.state() as state:
        state.stage = GameStage.ONGOING

    player1 = DummyPlayer(logname="p2")

    # When ONGOING, add_player should only enqueue the event
    await game.add_player(player1)

    # Should NOT be in ALL_PLAYERS group yet
    assert player1.lid not in group.children(game.gid(game.gona.ALL_PLAYERS))

    # Check event queue
    async with game.state() as state:
        assert len(state.event_queue) == 1
        _, _, event = state.event_queue[0]
        assert isinstance(event, AddPlayer)
        assert event.player_lid == player1.lid

    # Manually pop and process to finish the job
    e = await game._pop_event()
    await game._process_event(e)

    assert player1.lid in group.children(game.gid(game.gona.ALL_PLAYERS))


@pytest.mark.asyncio
async def test_arbitrary_grouping():
    """Test using gona and custom logical groups."""
    params = GameInitParams()
    game = Game(params=params, logname="test_game_groups")

    player = DummyPlayer(logname="p3")
    await game.add_player(player)

    # Custom logical group
    team_name = "blue_team"
    team_gid = game.gid(team_name)
    group.add(team_gid, player.lid)
    assert player.lid in group.children(team_gid)

    # Remove from group
    group.rm(team_gid, player.lid)
    assert player.lid not in group.children(team_gid)


@pytest.mark.asyncio
async def test_all_group_nesting():
    """Test that ALL group contains ALL_PLAYERS and ALL_ASSETS as sub-groups."""
    params = GameInitParams()
    game = Game(params=params, logname="test_game_nesting")

    # ALL should contain ALL_PLAYERS and ALL_ASSETS as children
    all_children = group.children(game.gid(game.gona.ALL))
    assert game.gid(game.gona.ALL_PLAYERS) in all_children
    assert game.gid(game.gona.ALL_ASSETS) in all_children

    # Add a player and verify resolvable from ALL
    player = DummyPlayer(logname="p4")
    await game.add_player(player)

    all_descendants = group.descendants(game.gid(game.gona.ALL))
    assert player.lid in all_descendants
