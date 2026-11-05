"""Контроллер статистики - управляет отображением таблицы рекордов."""

from typing import List
from view import StatisticsDisplay
from model.game_statistics import SessionStatistics


class StatisticsController:
    """Управляет отображением и взаимодействием с таблицей статистики.

    Отвечает за:
    - Отображение таблицы рекордов
    - Обработку ввода в таблице статистики
    - Сортировку и фильтрацию данных статистики
    """

    def __init__(self, statistics_display: StatisticsDisplay):
        """Инициализирует контроллер статистики.

        Args:
            statistics_display: компонент отображения статистики
        """
        self.statistics_display = statistics_display

    def show_scoreboard(self, stdscr, sessions: List[SessionStatistics]) -> None:
        """Отображает таблицу рекордов со статистикой всех прохождений.

        Args:
            stdscr: объект окна curses
            sessions: список SessionStatistics, отсортированный по сокровищам (по убыванию)
        """
        # Преобразуем SessionStatistics в список словарей для отображения
        sessions_data = [session.to_dict() for session in sessions]

        # Показываем таблицу
        self.statistics_display.draw_statistics(stdscr, sessions_data)
