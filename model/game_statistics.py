"""Управление статистикой игровых прохождений."""

from dataclasses import dataclass, asdict
from typing import List
from datetime import datetime


@dataclass
class SessionStatistics:
    """Статистика одного игрового прохождения."""
    
    # Базовая информация
    timestamp: str  # Дата и время прохождения
    
    # Основные показатели (сортировка по сокровищам)
    treasures_collected: int = 0
    
    # Уровни и враги
    max_level_reached: int = 1
    enemies_defeated: int = 0
    
    # Предметы использованные
    food_eaten: int = 0
    elixirs_drunk: int = 0
    scrolls_read: int = 0
    
    # Боевые показатели
    hits_dealt: int = 0
    hits_missed: int = 0
    
    # Движение
    cells_traversed: int = 0
    
    # Финальное состояние
    hero_final_health: int = 0
    hero_final_gold: int = 0

    def to_dict(self) -> dict:
        """Преобразует статистику в словарь."""
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> 'SessionStatistics':
        """Создает статистику из словаря."""
        return SessionStatistics(**data)


class GameStatistics:
    """Управляет всеми статистиками прохождений игры."""

    def __init__(self):
        """Инициализирует менеджер статистики."""
        self.current_session: SessionStatistics = SessionStatistics(
            timestamp=datetime.now().isoformat()
        )
        self.all_sessions: List[SessionStatistics] = []

    def reset_current_session(self) -> None:
        """Сбрасывает текущую сессию для нового прохождения."""
        self.current_session = SessionStatistics(
            timestamp=datetime.now().isoformat()
        )

    def save_current_session(self) -> None:
        """Сохраняет текущую сессию в историю."""
        self.all_sessions.append(self.current_session)

    def get_all_sessions_sorted_by_treasures(self) -> List[SessionStatistics]:
        """Возвращает все сессии, отсортированные по количеству сокровищ (по убыванию).

        Returns:
            Список статистик, отсортированный по сокровищам
        """
        return sorted(
            self.all_sessions,
            key=lambda s: s.treasures_collected,
            reverse=True
        )

    def add_treasure(self, item) -> None:
        """Регистрирует найденное сокровище."""
        self.current_session.treasures_collected += item.price

    def update_max_level(self, level: int) -> None:
        """Обновляет максимально достигнутый уровень.

        Args:
            level: текущий уровень игрока
        """
        if level > self.current_session.max_level_reached:
            self.current_session.max_level_reached = level

    def add_defeated_enemy(self) -> None:
        """Регистрирует побежденного противника."""
        self.current_session.enemies_defeated += 1

    def add_eaten_food(self) -> None:
        """Регистрирует съеденную еду."""
        self.current_session.food_eaten += 1

    def add_drunk_elixir(self) -> None:
        """Регистрирует выпитый эликсир."""
        self.current_session.elixirs_drunk += 1

    def add_read_scroll(self) -> None:
        """Регистрирует прочитанный свиток."""
        self.current_session.scrolls_read += 1

    def add_hit_dealt(self) -> None:
        """Регистрирует нанесенный удар."""
        self.current_session.hits_dealt += 1

    def add_hit_missed(self) -> None:
        """Регистрирует пропущенный удар."""
        self.current_session.hits_missed += 1

    def add_cell_traversed(self) -> None:
        """Регистрирует пройденную клетку."""
        self.current_session.cells_traversed += 1

    def set_final_hero_state(self, health: int, gold: int) -> None:
        """Устанавливает финальное состояние героя при завершении прохождения.

        Args:
            health: финальное здоровье героя
            gold: финальное количество золота
        """
        self.current_session.hero_final_health = health
        self.current_session.hero_final_gold = gold

    def to_dict_list(self) -> List[dict]:
        """Преобразует все сессии в список словарей для сохранения."""
        return [session.to_dict() for session in self.all_sessions]

    @staticmethod
    def from_dict_list(data: List[dict]) -> 'GameStatistics':
        """Создает GameStatistics из списка словарей.

        Args:
            data: список словарей со статистикой

        Returns:
            Новый объект GameStatistics с загруженными данными
        """
        stats = GameStatistics()
        stats.all_sessions = [SessionStatistics.from_dict(item) for item in data]
        return stats
