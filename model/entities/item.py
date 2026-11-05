from enum import Enum
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from constants import (
    LOOT_AGILITY_FACTOR,
    LOOT_HP_FACTOR,
    LOOT_HOSTILITY_FACTOR,
    LOOT_RANDOM_MAX,
    LOOT_STRENGTH_FACTOR,
)

if TYPE_CHECKING:
    from model.entities.enemy import Enemy


class ItemType(Enum):
    TREASURE = {
        'type': 'treasure',
        'subtype': 'dungeon treasure',
        "symbol": "$",
        "color_pair": 3,
        'health': 0,
        'max_health': 0,
        'agility': 0,
        'strength': 0,
        'price': 0,
        'duration': 0,
    }

    FOOD = {
        'type': 'food',
        'subtype': 'strange food',
        "symbol": "f",
        "color_pair": 4,
        'health': 10,
        'max_health': 0,
        'agility': 0,
        'strength': 0,
        'price': 0,
        'duration': 0,
    }

    AGILITY_ELIXIR = {
        'type': 'elixir',
        'subtype': 'elixir of agility',
        "symbol": "e",
        "color_pair": 2,
        'health': 0,
        'max_health': 0,
        'agility': 10,
        'strength': 0,
        'price': 0,
        'duration': 15,
    }

    STRENGTH_ELIXIR = {
        'type': 'elixir',
        'subtype': 'elixir of strength',
        "symbol": "e",
        "color_pair": 1,
        'health': 0,
        'max_health': 0,
        'agility': 0,
        'strength': 10,
        'price': 0,
        'duration': 15,
    }

    HEALTH_ELIXIR = {
        'type': 'elixir',
        'subtype': 'health boost elixir',
        "symbol": "e",
        "color_pair": 1,
        'health': 0,
        'max_health': 10,
        'agility': 0,
        'strength': 0,
        'price': 0,
        'duration': 15,
    }

    AGILITY_SCROLL = {
        'type': 'scroll',
        'subtype': 'scroll of agility',
        "symbol": "s",
        "color_pair": 2,
        'health': 0,
        'max_health': 0,
        'agility': 10,
        'strength': 0,
        'price': 0,
        'duration': 0,
    }

    STRENGTH_SCROLL = {
        'type': 'scroll',
        'subtype': 'scroll of strength',
        "symbol": "s",
        "color_pair": 1,
        'health': 0,
        'max_health': 0,
        'agility': 0,
        'strength': 10,
        'price': 0,
        'duration': 0,
    }

    HEALTH_SCROLL = {
        'type': 'scroll',
        'subtype': 'health boost scroll',
        "symbol": "s",
        "color_pair": 1,
        'health': 0,
        'max_health': 10,
        'agility': 0,
        'strength': 0,
        'price': 0,
        'duration': 0,
    }

    WEAPON_STICK = {
        'type': 'weapon',
        'subtype': 'wooden stick',
        "symbol": "w",
        "color_pair": 4,
        'health': 0,
        'max_health': 0,
        'agility': 0,
        'strength': 10,
        'price': 0,
        'duration': 0,
    }

    WEAPON_ROCK = {
        'type': 'weapon',
        'subtype': 'dangerous stone',
        "symbol": "w",
        "color_pair": 4,
        'health': 0,
        'max_health': 0,
        'agility': 0,
        'strength': 20,
        'price': 0,
        'duration': 0,
    }

    @property
    def base_subtype(self) -> str:
        return self.value['subtype']

    @property
    def symbol(self) -> str:
        return self.value['symbol']

    @property
    def color_pair(self) -> int:
        return self.value['color_pair']

    @property
    def base_health(self) -> str:
        return self.value['health']

    @property
    def base_max_health(self) -> str:
        return self.value['max_health']

    @property
    def base_agility(self) -> str:
        return self.value['agility']

    @property
    def base_strength(self) -> str:
        return self.value['strength']

    @property
    def base_price(self) -> str:
        return self.value['price']

    @property
    def base_duration(self) -> str:
        return self.value['duration']

    @classmethod
    def get_random(cls) -> "ItemType":
        """Возвращает случайный тип предмета."""
        items_List = [item for item in cls if item != cls.TREASURE]
        return random.choice(items_List)

    @classmethod
    def get_treasure(cls) -> "ItemType":
        return cls.TREASURE


def calculate_treasure_price(enemy: "Enemy") -> int:
    """Случайная стоимость сокровища на основе характеристик врага."""
    base = (
        enemy.max_health * LOOT_HP_FACTOR
        + enemy.agility * LOOT_AGILITY_FACTOR
        + enemy.strength * LOOT_STRENGTH_FACTOR
        + enemy.hostility * LOOT_HOSTILITY_FACTOR
    )
    return max(1, int(base) + random.randint(0, LOOT_RANDOM_MAX - 1))


@dataclass
class TemporaryEffect():
    bonuses: dict[str, int]
    remaining_turns: int

    def on_turn_end(self):
        self.remaining_turns -= 1
        return self.remaining_turns <= 0

    def to_dict(self) -> dict:
        return {
            'bonuses': self.bonuses,
            'remaining_turns': self.remaining_turns
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TemporaryEffect':
        return cls(
            data['bonuses'],
            data['remaining_turns']
        )


class Item:
    """Представляет предмет."""

    def __init__(self, item_type: ItemType):
        self.type = item_type
        self.subtype = item_type.base_subtype
        self.health = item_type.base_health
        self.max_health = item_type.base_max_health
        self.agility = item_type.base_agility
        self.strength = item_type.base_strength
        self.price = item_type.base_price
        self.duration = item_type.base_duration
        self._position = (0, 0)
        self._color_pair = item_type.color_pair

    def set_position(self, x: int, y: int) -> None:
        self._position = (x, y)

    def get_position(self) -> tuple[int, int]:
        return self._position

    @classmethod
    def create_treasure_from_enemy(cls, enemy: "Enemy") -> "Item":
        """Создаёт сокровище со случайной стоимостью по характеристикам врага."""
        item = cls(ItemType.get_treasure())
        item.price = calculate_treasure_price(enemy)
        return item

    @property
    def symbol(self) -> str:
        return self.type.symbol

    @property
    def color_pair(self) -> int:
        return self._color_pair

    def to_dict(self) -> dict:
        return {
            'type': self.type.name,
            'subtype': self.subtype,
            'health': self.health,
            'max_health': self.max_health,
            'agility': self.agility,
            'strength': self.strength,
            'price': self.price,
            'duration': self.duration,
            'position': list(self._position),
            'color_pair': self._color_pair
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Item':
        item_type = ItemType[data['type']]
        item = cls(item_type)
        item.subtype = data['subtype']
        item.health = data['health']
        item.max_health = data['max_health']
        item.agility = data['agility']
        item.strength = data['strength']
        item.price = data['price']
        item.duration = data['duration']
        item.set_position(*data['position'])
        item._color_pair = data['color_pair']
        return item
