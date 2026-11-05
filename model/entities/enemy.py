import random
from enum import Enum
from typing import Tuple, Optional
from constants import *


class EnemyType(Enum):
    """Перечисление типов врагов с их характеристиками."""

    ZOMBIE = {
        "name": "Зомби",
        "symbol": "z",
        "color_pair": 2,  # зелёный
        "health": 60,      # высокое
        "agility": 5,      # низкая
        "strength": 12,    # средняя
        "hostility": 4,    # средняя (кол-во клеток для радиуса враждебности)
        "special_ability": None
    }

    VAMPIRE = {
        "name": "Вампир",
        "symbol": "v",
        "color_pair": 1,  # красный
        "health": 45,      # высокое
        "agility": 18,     # высокая
        "strength": 14,    # средняя
        "hostility": 6,    # высокая (кол-во клеток для радиуса враждебности)
        "special_ability": "drain_max_hp"  # отнимает максимальное HP
    }

    GHOST = {
        "name": "Привидение",
        "symbol": "g",
        "color_pair": 4,  # белый
        "health": 20,      # низкое
        "agility": 16,     # высокая
        "strength": 6,     # низкая
        "hostility": 2,    # низкая (кол-во клеток для радиуса враждебности)
        "special_ability": "teleport_turn_invisible"
    }

    OGRE = {
        "name": "Огр",
        "symbol": "O",
        "color_pair": 3,  # жёлтый
        "health": 80,      # очень высокое
        "agility": 4,      # низкая
        "strength": 22,    # очень высокая
        "hostility": 4,    # средняя (кол-во клеток для радиуса враждебности)
        "special_ability": "rest_after_attack"
    }

    SNAKE_MAGE = {
        "name": "Змей-маг",
        "symbol": "s",
        "color_pair": 4,  # белый
        "health": 35,      # среднее
        "agility": 20,     # очень высокая
        "strength": 10,    # средняя
        "hostility": 6,    # высокая (кол-во клеток для радиуса враждебности)
        "special_ability": "sleep_attack"
    }

    @property
    def display_name(self) -> str:
        """Возвращает имя врага."""
        return self.value["name"]

    @property
    def symbol(self) -> str:
        """Возвращает символ для отображения."""
        return self.value["symbol"]

    @property
    def color_pair(self) -> int:
        """Возвращает ID цветовой пары для curses."""
        return self.value["color_pair"]

    @property
    def base_health(self) -> int:
        """Возвращает базовое здоровье."""
        return self.value["health"]

    @property
    def base_agility(self) -> int:
        """Возвращает базовую ловкость."""
        return self.value["agility"]

    @property
    def base_strength(self) -> int:
        """Возвращает базовую силу."""
        return self.value["strength"]

    @property
    def base_hostility(self) -> int:
        """Возвращает базовую враждебность."""
        return self.value["hostility"]

    @property
    def special_ability(self) -> Optional[str]:
        """Возвращает особую способность врага."""
        return self.value["special_ability"]

    @classmethod
    def get_random(cls) -> "EnemyType":
        """Возвращает случайный тип врага."""
        return random.choice(list(cls))


class Enemy:
    """Представляет врага."""

    def __init__(self, enemy_type: EnemyType):
        self.type = enemy_type
        self._current_health = enemy_type.base_health
        self.max_health = enemy_type.base_health
        self.agility = enemy_type.base_agility
        self.strength = enemy_type.base_strength
        self.hostility = enemy_type.base_hostility
        self._position = (0, 0)
        self._color_pair = enemy_type.color_pair

        # Дополнительные состояния для особых способностей
        self._resting = False      # для Огра (отдыхает после атаки)
        self._invisible = False    # для Привидения
        self._first_attack_miss = True  # для Вампира (первый удар - промах)
        self._has_moved_this_turn = False  # флаг для предотвращения движения после атаки

    def set_position(self, x: int, y: int) -> None:
        """Устанавливает позицию врага"""
        self._position = (x, y)

    def get_position(self) -> Tuple[int, int]:
        """Получает текущую позицию врага"""
        return self._position

    @property
    def health(self) -> int:
        """Возвращает значение здоровья."""
        return self._current_health

    @property
    def symbol(self) -> str:
        """Возвращает символ для отображения (с учётом невидимости)."""
        if self.type == EnemyType.GHOST and self._invisible:
            return ' '  # невидим
        return self.type.symbol

    @property
    def color_pair(self) -> int:
        """Возвращает цветовую пару для отображения."""
        return self._color_pair

    def take_damage(self, damage: int) -> int:
        """Наносит урон врагу. Возвращает фактический урон."""
        self._current_health -= damage
        if self._current_health < 0:
            self._current_health = 0
        return damage

    def is_alive(self) -> bool:
        """Проверяет, жив ли враг."""
        return self.health > 0

    def attack(self, hero) -> int:
        """Враг атакует героя. Возвращает урон, который был нанесен.

        Args:
            hero: герой для атаки

        Returns:
            Урон, нанесенный герою
        """
        # Проверка для Вампира: первый удар всегда промах
        if self.type == EnemyType.VAMPIRE and self._first_attack_miss:
            self._first_attack_miss = False
            return 0  # Промах - урон не нанесён

        # Расчет вероятности промаха
        miss_chance = MISS_CHANCE_BASE
        miss_chance -= self.agility * AGILITY_MISS_REDUCTION
        if hasattr(hero, 'agility'):
            miss_chance += hero.agility * AGILITY_MISS_REDUCTION
        miss_chance = max(0, min(0.5, miss_chance))

        # Проверка на промах
        if random.random() < miss_chance:
            return 0  # Промах, урон не нанесен

        # Базовый урон на основе силы
        base_damage = self.strength

        # Случайная вариация (±25%)
        variation = random.randint(-25, 25)
        damage = base_damage + (base_damage * variation // 100)

        # Минимум 1 урон
        damage = max(1, damage)

        # Шанс крита в зависимости от типа врага
        crit_chance = 0.3
        if self.type == EnemyType.SNAKE_MAGE:
            crit_chance = 0.4  # Змей-маг чаще критует
        elif self.type == EnemyType.VAMPIRE:
            crit_chance = 0.25  # Вампир реже

        if random.random() < crit_chance:
            damage = int(damage * 1.5)

        # Наносим урон герою
        actual_damage = hero.take_damage(damage)

        return actual_damage

    def can_attack(self) -> bool:
        """Может ли враг атаковать в этом ходу."""
        if self.type == EnemyType.OGRE and self._resting:
            self._resting = False
            return False
        return True

    def after_attack(self) -> None:
        """Действия после атаки (для особых способностей)."""
        if self.type == EnemyType.OGRE:
            self._resting = True  # Огр отдыхает после атаки

    def special_attack_effect(self, hero) -> Optional[str]:
        """Применяет особый эффект атаки. Возвращает описание эффекта."""
        if self.type == EnemyType.VAMPIRE:
            # Отнимает максимальное здоровье
            drain = 5
            hero.max_health = max(10, hero.max_health - drain)
            if hero.health > hero.max_health:
                hero.health = hero.max_health
            return f"Вампир отнимает {drain} максимального здоровья!"

        elif self.type == EnemyType.SNAKE_MAGE:
            # Вероятность усыпления (30%)
            if random.random() < 0.3:
                hero.sleep_turns = 1
                return "Змей-маг усыпляет вас на 1 ход!"

        return None

    def mark_as_moved(self) -> None:
        """Отмечает врага как уже совершившего движение на этом ходу."""
        self._has_moved_this_turn = True

    def reset_moved_flag(self) -> None:
        """Сбрасывает флаг движения на начало нового хода."""
        self._has_moved_this_turn = False

    def has_moved_this_turn(self) -> bool:
        """Проверяет, уже ли враг двигался на этом ходу."""
        return self._has_moved_this_turn

    def get_info(self) -> dict:
        """Возвращает информацию о враге для отображения."""
        return {
            "name": self.type.display_name,
            "symbol": self.symbol,
            "health": self.health,
            "max_health": self.max_health,
            "agility": self.agility,
            "strength": self.strength,
            "hostility": self.hostility,
            "color_pair": self.color_pair
        }

    def to_dict(self) -> dict:
        return {
            'type': self.type.name,
            'current_health': self._current_health,
            'max_health': self.max_health,
            'agility': self.agility,
            'strength': self.strength,
            'hostility': self.hostility,
            'position': list(self._position),
            'color_pair': self._color_pair,
            'resting': self._resting,
            'invisible': self._invisible,
            'first_attack_miss': self._first_attack_miss,
            'has_moved_this_turn': self._has_moved_this_turn
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Enemy':
        enemy_type = EnemyType[data['type']]
        enemy = cls(enemy_type)
        enemy._current_health = data['current_health']
        enemy.max_health = data['max_health']
        enemy.agility = data['agility']
        enemy.strength = data['strength']
        enemy.hostility = data['hostility']
        enemy.set_position(*data['position'])
        enemy._color_pair = data['color_pair']
        enemy._resting = data.get('resting', False)
        enemy._invisible = data.get('invisible', False)
        enemy._first_attack_miss = data.get('first_attack_miss', True)
        enemy._has_moved_this_turn = data.get('has_moved_this_turn', False)
        return enemy
