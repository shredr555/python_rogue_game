"""Отображение статистики прохождений."""

import curses
from typing import List, Tuple
from constants import *


class StatisticsDisplay:
    """Управляет отображением статистики всех прохождений."""

    def __init__(self):
        """Инициализирует дисплей статистики."""
        pass

    def draw_statistics(self, stdscr, sessions_data: List[dict]) -> None:
        """Отображает таблицу со статистикой всех прохождений, отсортированной по сокровищам.

        Args:
            stdscr: объект окна curses
            sessions_data: список словарей со статистикой (отсортированный по сокровищам)
        """
        stdscr.clear()

        height, width = stdscr.getmaxyx()

        # Заголовок
        title = "═══ ТАБЛИЦА РЕКОРДОВ ═══ (Отсортирована по сокровищам)"
        try:
            stdscr.addstr(0, 15, title, curses.color_pair(1))
        except curses.error:
            pass
        
        # Если нет записей
        if not sessions_data:
            no_data = "Нет сохраненных прохождений"
            try:
                stdscr.addstr(2, 25, no_data)
                stdscr.addstr(4, 15, "Нажмите Q или ESC для возврата в меню...")
                stdscr.refresh()
                while True:
                    key = stdscr.getch()
                    if key in [ord('q'), ord('Q'), 27]:  # 27 = ESC
                        break
                return
            except curses.error:
                    pass

        # Рисуем заголовки колонок
        headers = [
            ("N", 2),
            ("Клады", 5),
            ("Уровень", 9),
            ("Враги", 8),
            ("Еда", 5),
            ("Эликсиры", 9),
            ("Свитки", 8),
            ("Попадания", 10),
            ("Промахи", 8),
            ("Клетки", 7),
        ]
        

        col_x = 1
        header_line = 2
        
        for header_text, width in headers:
            try:
                stdscr.addstr(header_line, col_x, header_text[:width].ljust(width), 
                         curses.color_pair(2) | curses.A_BOLD)
            except curses.error:
                    pass
            col_x += width + 1
        
        # Разделитель
        divider_line = 3
        try:
            stdscr.addstr(divider_line, 0, "═" * 82, curses.color_pair(2))
        except curses.error:
                    pass
        
        # Рисуем данные
        current_line = 4
        for idx, session in enumerate(sessions_data[:height - 8], 1):  # Оставляем место для заголовков и подвала
            col_x = 1
            
            
            stats_values = [
                (str(idx), 2),
                (str(session.get('treasures_collected', 0)), 5),
                (str(session.get('max_level_reached', 1)), 9),
                (str(session.get('enemies_defeated', 0)), 8),
                (str(session.get('food_eaten', 0)), 5),
                (str(session.get('elixirs_drunk', 0)), 9),
                (str(session.get('scrolls_read', 0)), 8),
                (str(session.get('hits_dealt', 0)), 10),
                (str(session.get('hits_missed', 0)), 8),
                (str(session.get('cells_traversed', 0)), 7),
            ]
            
            for value_text, width in stats_values:
                text = str(value_text)[:width].rjust(width)
                try:
                    stdscr.addstr(current_line, col_x, text)
                except curses.error:
                    pass
                col_x += width + 1
            
            current_line += 1
        
        # Подвал с инструкциями
        footer_line = height - 2
        footer_text = "Нажмите Q или ESC для возврата в меню"
        try:
            stdscr.addstr(footer_line, (width - len(footer_text)) // 2, footer_text)
        except curses.error:
            pass
        
        stdscr.refresh()
        
        # Ожидаем ввода пользователя
        while True:
            key = stdscr.getch()
            if key in [ord('q'), ord('Q'), 27]:  # 27 = ESC
                break

