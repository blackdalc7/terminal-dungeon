from helpers import monster, open_room_game

from dungeon.game import FINAL_DEPTH, Game, Item
from dungeon.mapgen import STAIRS


def test_new_game_is_deterministic():
    a, b = Game.new(3), Game.new(3)
    assert a.player.pos == b.player.pos
    assert [m.pos for m in a.monsters] == [m.pos for m in b.monsters]


def test_new_floor_places_player_in_first_room():
    g = Game.new(1)
    assert g.player.pos == g.map.rooms[0].center
    assert g.player.pos in g.visible


def test_move_and_walls():
    g = open_room_game()
    assert g.act("d")
    assert g.player.pos == (3, 2)
    g.player.pos = (1, 1)
    assert not g.act("w")  # wall
    assert g.player.pos == (1, 1)
    assert g.turn == 1


def test_unknown_command_takes_no_turn():
    g = open_room_game()
    assert not g.act("x")
    assert "Unknown" in g.log[-1]


def test_bump_to_attack_and_kill_gives_xp():
    g = open_room_game()
    g.monsters = [monster((3, 2), hp=1)]
    g.act("d")
    assert g.kills == 1
    assert g.player.xp == 3
    assert g.player.pos == (2, 2)  # attacking doesn't move you
    assert "defeat" in " ".join(g.log)


def test_damage_is_at_least_one():
    g = open_room_game()
    tank = monster((3, 2), hp=50, defence=99)
    assert g.attack(g.player, tank) == 1


def test_level_up():
    g = open_room_game()
    g.player.hp = 5
    g.monsters = [monster((3, 2), hp=1, xp=10)]
    g.act("d")
    assert g.level == 2
    assert g.player.hp == g.player.max_hp == 25
    assert g.player.attack == 5


def test_monster_chases_and_attacks():
    g = open_room_game()
    rat = monster((6, 2), hp=50, attack=3)
    g.monsters = [rat]
    g.update_fov()
    g.act(".")
    assert rat.pos == (5, 2)
    rat.pos = (3, 2)
    hp = g.player.hp
    g.act(".")
    assert g.player.hp < hp


def test_monsters_out_of_sight_sleep():
    g = open_room_game(40, 5)
    far = monster((35, 2))
    g.monsters = [far]
    g.update_fov()
    g.act(".")
    assert far.pos == (35, 2)


def test_death_ends_game():
    g = open_room_game()
    g.player.hp = 1
    g.monsters = [monster((3, 2), hp=99, attack=10, name="troll")]
    g.act(".")
    assert g.over and not g.won
    assert "killed by a troll" in g.log[-1]
    assert not g.act("d")


def test_pickups():
    g = open_room_game()
    g.items = [
        Item("gold", (3, 2), 12),
        Item("potion", (4, 2)),
        Item("sword", (5, 2)),
        Item("shield", (6, 2)),
    ]
    for _ in range(4):
        g.act("d")
    assert g.gold == 12
    assert g.potions == 2
    assert g.player.attack == 6
    assert g.player.defence == 2
    assert g.items == []


def test_potion_heals_but_not_above_max():
    g = open_room_game()
    g.player.hp = 15
    assert g.act("p")
    assert g.player.hp == 20
    assert g.potions == 0
    assert not g.act("p")


def test_stairs_go_deeper_then_win():
    g = Game.new(4)
    g.player.pos = (0, 0)
    assert not g.act(">")
    g.player.pos = g.map.rooms[-1].center
    assert g.map[g.player.pos] == STAIRS
    g.act(">")
    assert g.depth == 2
    g.depth = FINAL_DEPTH
    g.player.pos = g.map.rooms[-1].center
    g.act(">")
    assert g.won
    assert g.score >= 500 + (FINAL_DEPTH - 1) * 100


def test_stepping_on_stairs_tells_you():
    g = open_room_game()
    g.map[(3, 2)] = STAIRS
    g.act("d")
    assert "stairs" in g.log[-1]
