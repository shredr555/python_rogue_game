"""Управление игровым сеансом."""

from typing import Optional, List
from model.entities import Hero, Enemy, Item
from model.dungeon_structures import Layer
from model.game_statistics import GameStatistics


class GameSession:
    """Управляет состоянием текущего игрового сеанса."""

    def __init__(self):
        self.hero: Optional[Hero] = None
        self.current_level: int = 1
        self.current_layer: Optional[Layer] = None
        self.enemies: List[Enemy] = []
        self.items: List[Item] = []
        self.is_active: bool = False
        self.enemy_probability: float = 0.5
        self.item_probability: float = 0.5
        self.statistics: GameStatistics = GameStatistics()

    def start_new_session(self, hero: Hero) -> None:
        """Инициализирует новый сеанс с героем.

        Args:
            hero: объект героя

        Raises:
            ValueError: если hero = None или сеанс уже активен
        """
        if hero is None:
            raise ValueError("Hero cannot be None")

        if self.is_active:
            raise RuntimeError(
                "Session is already active. Call end_session() first")

        self._reset_session()
        self.hero = hero
        self.current_level = 1
        self.enemy_probability = 0.5
        self.item_probability = 0.5
        self.is_active = True
        self.statistics.reset_current_session()
        self._update_probabilities()

    def end_session(self) -> None:
        """Завершает текущий игровой сеанс и сохраняет статистику."""
        if self.hero:
            # Сохраняем финальное состояние героя в статистику
            self.statistics.set_final_hero_state(
                self.hero.current_health,
                self.hero.gold
            )
            # Сохраняем текущую сессию в историю
            self.statistics.save_current_session()
        self._reset_session()

    def load_level(self, layer: Layer) -> None:
        """Загружает новый уровень подземелья.

        Args:
            layer: слой подземелья для загрузки

        Raises:
            RuntimeError: если нет активного сеанса
        """
        if not self.is_active:
            raise RuntimeError("Cannot load level - no active session")

        self.current_layer = layer
        self.enemies = []
        self.items = []

    def next_level(self) -> None:
        """Переходит на следующий уровень.

        Raises:
            RuntimeError: если нет активного сеанса
        """
        if not self.is_active:
            raise RuntimeError("Cannot advance level - no active session")

        self.current_level += 1
        self._update_probabilities()
        self.enemies = []
        self.items = []
        self.current_layer = None

    def add_enemy(self, enemy: Enemy) -> None:
        """Добавляет врага на текущий уровень."""
        if enemy:
            self.enemies.append(enemy)

    def remove_enemy(self, enemy: Enemy) -> bool:
        """Удаляет врага со уровня.

        Returns:
            True если враг удален, False если его нет
        """
        try:
            self.enemies.remove(enemy)
            return True
        except ValueError:
            return False

    def add_item(self, item: Item) -> None:
        """Добавляет предмет на уровень."""
        if item:
            self.items.append(item)

    def remove_item(self, item: Item) -> bool:
        """Удаляет предмет со уровня.

        Returns:
            True если предмет удален, False если его нет
        """
        try:
            self.items.remove(item)
            return True
        except ValueError:
            return False

    def is_empty_position(self, x: int, y: int) -> bool:
        """Проверяет, не занята ли позиция сущностями (героем или врагами).

        Args:
            x: координата X
            y: координата Y

        Returns:
            True если позиция пуста (не занята героем или врагом)
        """
        if self.hero and self.hero.get_position() == (x, y):
            return False

        for enemy in self.enemies:
            if enemy.get_position() == (x, y):
                return False

        return True

    def get_status(self) -> dict:
        """Возвращает информацию о состоянии сеанса."""
        return {
            'is_active': self.is_active,
            'level': self.current_level,
            'enemies_count': len(self.enemies),
            'items_count': len(self.items),
            'hero': self.hero,
            'has_layer': self.current_layer is not None
        }

    def _reset_session(self) -> None:
        """Очищает состояние сеанса."""
        self.hero = None
        self.current_level = 1
        self.current_layer = None
        self.enemies.clear()
        self.items.clear()
        self.is_active = False

    def _update_probabilities(self) -> None:
        level = self.current_level
        self.enemy_probability = 0.35 + 0.025 * (level - 1)
        self.item_probability = 0.50 - 0.025 * (level - 1)
