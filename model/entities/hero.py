from typing import Tuple, Optional
import random
from constants import *
from .backpack import Backpack
from .item import Item, TemporaryEffect


class Hero:
    """Представляет главного героя."""

    def __init__(self):
        self.max_health = 100
        self.current_health = 100
        self.active_effect = []
        self.agility = 10
        self.strength = 10
        self.gold = 0
        self.weapon = None
        self._position = (0, 0)
        self.backpack = Backpack()

    def set_position(self, x: int, y: int) -> None:
        """Устанавливает позицию героя."""
        self._position = (x, y)

    def get_position(self) -> Tuple[int, int]:
        """Получает текущую позицию героя."""
        return self._position

    def get_health(self) -> int:
        return self.current_health

    def take_damage(self, damage: int) -> int:
        """Герой получает урон. Возвращает фактический полученный урон.

        Args:
            damage: количество урона

        Returns:
            Фактический полученный урон
        """
        # Снижаем урон на основе ловкости
        actual_damage = max(MIN_DAMAGE, damage -
                            (self.agility // AGILITY_DAMAGE_REDUCTION_DIVISOR))
        self.current_health -= actual_damage

        if self.current_health < 0:
            self.current_health = 0

        return actual_damage

    def _check_miss(self, enemy) -> bool:
        """Проверяет, промахнется ли герой при атаке.

        Шанс промаха снижается с увеличением ловкости героя
        и увеличивается с увеличением ловкости врага.

        Args:
            enemy: враг, по которому происходит атака

        Returns:
            True если промах, False если попадание
        """
        # Базовая вероятность промаха
        miss_chance = MISS_CHANCE_BASE

        # Уменьшаем шанс промаха на основе ловкости героя
        miss_chance -= self.agility * AGILITY_MISS_REDUCTION

        # Увеличиваем шанс промаха на основе ловкости врага
        if hasattr(enemy, 'agility'):
            miss_chance += enemy.agility * AGILITY_MISS_REDUCTION

        # Ограничиваем шанс промаха от 0% до 50%
        miss_chance = max(0, min(0.5, miss_chance))

        # Определяем, промах ли
        return random.random() < miss_chance

    def attack(self, enemy) -> int:
        """Герой атакует врага. Возвращает урон, который был нанесен.

        Args:
            enemy: враг для атаки

        Returns:
            Урон, нанесенный врагу (0 если промах)
        """
        # Проверка на промах
        if self._check_miss(enemy):
            return 0  # Промах, урон не нанесен

        # Базовый урон на основе силы
        base_damage = self.strength

        # Случайная вариация (±ATTACK_DAMAGE_VARIANCE * 100%)
        variance_percent = random.randint(
            -int(100 * ATTACK_DAMAGE_VARIANCE),
            int(100 * ATTACK_DAMAGE_VARIANCE)
        )
        damage = base_damage + (base_damage * variance_percent // 100)

        # Минимум MIN_DAMAGE урона
        damage = max(MIN_DAMAGE, damage)

        # Шанс критического удара (только если попали)
        if random.random() < CRITICAL_HIT_CHANCE:
            damage = int(damage * CRITICAL_HIT_MULTIPLIER)

        # Наносим урон врагу
        actual_damage = enemy.take_damage(damage)

        return actual_damage

    def is_alive(self) -> bool:
        """Проверяет, жив ли герой.

        Returns:
            True если герой жив, False если мертв
        """
        return self.current_health > 0

    def apply_temporary_effect(self, effect: TemporaryEffect):
        for stat, value in effect.bonuses.items():
            current = getattr(self, stat, 0)
            setattr(self, stat, current + value)
        self.active_effect.append(effect)

    def update_effects(self):
        for effect in self.active_effect[:]:
            if effect.on_turn_end():
                for stat, value in effect.bonuses.items():
                    current = getattr(self, stat, 0)
                    setattr(self, stat, current - value)
                self.active_effect.remove(effect)
                if self.current_health <= 0:
                    self.current_health = 10

    def to_dict(self) -> dict:
        return {
            'max_health': self.max_health,
            'current_health': self.current_health,
            'active_effect': [effect.to_dict() for effect in self.active_effect],
            'agility': self.agility,
            'strength': self.strength,
            'gold': self.gold,
            'weapon': self.weapon.to_dict() if self.weapon else None,
            'position': list(self._position),
            'backpack': self.backpack.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Hero":
        hero = cls()
        hero.max_health = data['max_health']
        hero.current_health = data['current_health']
        hero.active_effect = [TemporaryEffect.from_dict(
            e) for e in data.get('active_effect', [])]
        hero.agility = data['agility']
        hero.strength = data['strength']
        hero.gold = data.get('gold', 0)
        hero.weapon = Item.from_dict(
            data['weapon']) if data.get('weapon') else None
        hero.set_position(*data['position'])
        hero.backpack = Backpack.from_dict(data['backpack'])
        return hero
