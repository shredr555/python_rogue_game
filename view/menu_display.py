"""Отрисовка меню."""

import curses
from constants import *


class MenuDisplay:
    """Обрабатывает отрисовку главного меню.

    Отвечает за:
    - Построение текста меню
    - Отрисовку на экран curses
    - Позиционирование элементов
    """

    def __init__(self):
        """Инициализирует дисплей меню."""
        self.menu_builder = MenuBuilder()
        self.menu_renderer = MenuRenderer()

    def draw_menu(self, stdscr, current_option: int) -> None:
        """Рисует главное меню.

        Args:
            stdscr: объект окна curses
            current_option: индекс выбранного пункта меню (0-3)
        """
        menu_lines = self.menu_builder.build_menu_lines()
        self.menu_renderer.render_menu(stdscr, menu_lines, current_option)


class MenuBuilder:
    """Строит содержимое меню."""

    def build_menu_lines(self) -> list:
        """Строит строки отображения меню.

        Returns:
            Список строк меню
        """
        lines = [
            "           GAME  MENU           ",
            "+------------------------------+",
            "|                              |",
        ]

        for item in MENU_ITEMS:
            lines.append(f"|          {item:<20}|")

        lines.extend([
            "|                              |",
            "+------------------------------+",
        ])

        return lines


class MenuRenderer:
    """Отрисовывает меню на экран."""

    def render_menu(self, stdscr, menu_lines: list, current_option: int) -> None:
        """Отрисовывает строки меню на экран.

        Args:
            stdscr: объект окна curses
            menu_lines: список строк меню
            current_option: индекс выбранного пункта
        """
        try:
            stdscr.clear()
            stdscr.border()

            height, width = stdscr.getmaxyx()
            menu_height = len(menu_lines)
            menu_width = max(len(line) for line in menu_lines)

            start_y = (height - menu_height) // 2
            start_x = (width - menu_width) // 2

            # Отрисовываем меню
            for i, line in enumerate(menu_lines):
                try:
                    stdscr.addstr(start_y + i, start_x, line)
                except curses.error:
                    # Игнорируем ошибки при выходе за границы
                    pass

            # Рисует курсор (указатель)
            cursor_y = start_y + current_option + 3
            cursor_x = start_x + 5

            try:
                stdscr.addstr(cursor_y, cursor_x, ">>>")
            except curses.error:
                pass

            stdscr.refresh()
        except curses.error:
            pass
