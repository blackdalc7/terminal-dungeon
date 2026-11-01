"""Game state and rules: entities, combat, items, monster turns and floors."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from dungeon import fov
from dungeon.mapgen import STAIRS, Map, Pos, generate

FINAL_DEPTH = 5

# name, symbol, hp, attack, defence, xp, first depth it can appear on
MONSTERS = [
    ("rat", "r", 4, 2, 0, 2, 1),
    ("bat", "b", 3, 3, 0, 3, 1),
    ("goblin", "g", 8, 3, 1, 5, 2),
    ("skeleton", "s", 10, 4, 2, 8, 3),
    ("orc", "o", 14, 5, 2, 12, 3),
    ("troll", "T", 24, 7, 3, 25, 4),
]

DIRECTIONS = {"w": (0, -1), "a": (-1, 0), "s": (0, 1), "d": (1, 0)}


@dataclass
class Entity:
    """The player or a monster."""
    name: str
    symbol: str
    pos: Pos
    hp: int
    max_hp: int
    attack: int
    defence: int
    xp: int = 0

    @property
    def alive(self) -> bool:
        return self.hp > 0


@dataclass
class Item:
    """Something lying on the floor that the player can pick up."""
    kind: str  # "potion", "gold", "sword", "shield"
    pos: Pos
    value: int = 0

    @property
    def symbol(self) -> str:
        return {"potion": "!", "gold": "$", "sword": "/", "shield": "]"}[self.kind]


@dataclass
class Game:
    """The whole game state, and the rules that change it each turn."""
    rng: random.Random
    depth: int = 1
    player: Entity = field(default_factory=lambda: Entity("you", "@", (0, 0), 20, 20, 4, 1))
    level: int = 1
    gold: int = 0
    potions: int = 1
    kills: int = 0
    turn: int = 0
    log: list[str] = field(default_factory=list)
    won: bool = False
    map: Map = None  # type: ignore[assignment]
    monsters: list[Entity] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)
    visible: set[Pos] = field(default_factory=set)

    # ---- setup -----------------------------------------------------------

    @classmethod
    def new(cls, seed: int | None = None) -> Game:
        game = cls(rng=random.Random(seed))
        game.new_floor()
        game.say("You enter the dungeon. Find the stairs (>) and go deeper.")
        return game

    def new_floor(self) -> None:
        """Generate a floor, put the player in the first room and scatter monsters and items."""
        self.map = generate(rng=self.rng)
        rooms = self.map.rooms
        self.player.pos = rooms[0].center
        self.monsters, self.items = [], []
        allowed = [m for m in MONSTERS if m[6] <= self.depth]
        for room in rooms[1:]:
            free = [c for c in room.cells() if self.map[c] != STAIRS]
            for _ in range(self.rng.randint(0, 1 + self.depth // 2)):
                name, sym, hp, atk, dfn, xp, _first = self.rng.choice(allowed)
                self.monsters.append(Entity(name, sym, self.rng.choice(free), hp, hp, atk, dfn, xp))
            if self.rng.random() < 0.6:
                kind = self.rng.choices(["gold", "potion", "sword", "shield"], [6, 3, 1, 1])[0]
                value = self.rng.randint(5, 15) * self.depth if kind == "gold" else 1
                self.items.append(Item(kind, self.rng.choice(free), value))
        self.update_fov()

    # ---- helpers ---------------------------------------------------------

    def say(self, message: str) -> None:
        self.log.append(message)
        del self.log[:-6]

    def monster_at(self, pos: Pos) -> Entity | None:
        return next((m for m in self.monsters if m.pos == pos and m.alive), None)

    def update_fov(self) -> None:
        self.visible = fov.visible(self.map, self.player.pos)
        self.map.seen |= self.visible

    @property
    def over(self) -> bool:
        return self.won or not self.player.alive

    @property
    def score(self) -> int:
        return self.gold + self.kills * 10 + (self.depth - 1) * 100 + (500 if self.won else 0)

    # ---- combat ----------------------------------------------------------

    def attack(self, attacker: Entity, target: Entity) -> int:
        damage = max(1, attacker.attack - target.defence + self.rng.randint(-1, 1))
        target.hp -= damage
        return damage

    def player_attacks(self, monster: Entity) -> None:
        dmg = self.attack(self.player, monster)
        if monster.alive:
            self.say(f"You hit the {monster.name} for {dmg}.")
            return
        self.say(f"You defeat the {monster.name}! (+{monster.xp} xp)")
        self.kills += 1
        self.player.xp += monster.xp
        while self.player.xp >= self.xp_needed():
            self.level_up()

    def xp_needed(self) -> int:
        return 10 * self.level * self.level

    def level_up(self) -> None:
        self.level += 1
        self.player.max_hp += 5
        self.player.hp = self.player.max_hp
        self.player.attack += 1
        self.say(f"Level up! You are now level {self.level}.")

    # ---- player actions --------------------------------------------------

    def act(self, command: str) -> bool:
        """Apply one command. Returns True if it took a turn."""
        if self.over:
            return False
        command = command.strip().lower()[:1]
        if command in DIRECTIONS:
            took_turn = self.move(*DIRECTIONS[command])
        elif command == "p":
            took_turn = self.drink_potion()
        elif command == ".":
            took_turn = True
        elif command == ">":
            took_turn = self.descend()
        else:
            self.say("Unknown command. Use w/a/s/d, p, . or >")
            took_turn = False
        if took_turn and not self.over:
            self.turn += 1
            self.monsters_act()
            self.update_fov()
        return took_turn

    def move(self, dx: int, dy: int) -> bool:
        x, y = self.player.pos
        target = (x + dx, y + dy)
        monster = self.monster_at(target)
        if monster:
            self.player_attacks(monster)
            return True
        if not self.map.walkable(target):
            return False
        self.player.pos = target
        self.pick_up()
        if self.map[target] == STAIRS:
            self.say("There are stairs here. Press > to go down.")
        return True

    def pick_up(self) -> None:
        for item in [i for i in self.items if i.pos == self.player.pos]:
            self.items.remove(item)
            if item.kind == "gold":
                self.gold += item.value
                self.say(f"You pick up {item.value} gold.")
            elif item.kind == "potion":
                self.potions += 1
                self.say("You pick up a healing potion.")
            elif item.kind == "sword":
                self.player.attack += 2
                self.say("You find a sharper sword! (+2 attack)")
            elif item.kind == "shield":
                self.player.defence += 1
                self.say("You strap on a sturdier shield. (+1 defence)")

    def drink_potion(self) -> bool:
        if not self.potions:
            self.say("You have no potions.")
            return False
        self.potions -= 1
        healed = min(12, self.player.max_hp - self.player.hp)
        self.player.hp += healed
        self.say(f"You drink a potion and heal {healed} HP.")
        return True

    def descend(self) -> bool:
        if self.map[self.player.pos] != STAIRS:
            self.say("There are no stairs here.")
            return False
        if self.depth == FINAL_DEPTH:
            self.won = True
            self.say("You climb out the bottom of the dungeon into daylight. You win!")
            return True
        self.depth += 1
        self.new_floor()
        self.say(f"You go down to depth {self.depth}. It smells worse here.")
        return True

    # ---- monsters --------------------------------------------------------

    def monsters_act(self) -> None:
        """Visible monsters attack when adjacent, otherwise step towards the player along a BFS path."""
        self.monsters = [m for m in self.monsters if m.alive]
        occupied = {m.pos for m in self.monsters}
        for m in self.monsters:
            if m.pos not in self.visible:
                continue  # monsters you can't see are asleep
            px, py = self.player.pos
            mx, my = m.pos
            if abs(px - mx) + abs(py - my) == 1:
                dmg = self.attack(m, self.player)
                self.say(f"The {m.name} hits you for {dmg}.")
                if not self.player.alive:
                    self.say(f"You were killed by a {m.name} on depth {self.depth}.")
                    return
                continue
            step = fov.bfs_next_step(self.map, m.pos, self.player.pos, occupied)
            if step and step != self.player.pos and step not in occupied:
                occupied.discard(m.pos)
                m.pos = step
                occupied.add(step)
