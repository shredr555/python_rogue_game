"""Контроллер меню - управляет всеми операциями с меню."""

from constants import *
from typing import Optional
from view import MenuDisplay


class MenuController:
    """Управляет главным меню и навигацией по меню.

    Отвечает за:
    - Отображение меню
    - Обработку ввода меню
    - Управление состоянием выбора
    """

    def __init__(self, menu_display: MenuDisplay):
        """Инициализирует контроллер меню.

        Args:
            menu_display: компонент отображения меню
        """
        self.menu_display = menu_display
        self.current_option = 0

    def run_main_menu(self, stdscr) -> Optional[int]:
        """Отображает главное меню и ожидает выбора пользователя.

        Args:
            stdscr: объект окна curses

        Returns:
            Индекс выбранного пункта меню или None при выходе
        """
        while True:
            # Рисуем меню с текущей выделенной опцией
            self.menu_display.draw_menu(stdscr, self.current_option)

            # Получаем нажатую клавишу
            key = stdscr.getch()

            # Обрабатываем ввод
            self._handle_menu_input(key)

            # Если пользователь выбрал опцию, возвращаем индекс
            if self._is_option_selected(key):
                return self.current_option

            # Если нажал ESC, выходим из меню
            if key == 27:
                return None

    def _handle_menu_input(self, key: int) -> None:
        """Обрабатывает ввод в меню и обновляет выбор.

        Args:
            key: код нажатой клавиши
        """
        if key == ord('w') or key == ord('W'):
            # Движение вверх по меню
            self.current_option = (self.current_option - 1) % MAX_OPTIONS

        elif key == ord('s') or key == ord('S'):
            # Движение вниз по меню
            self.current_option = (self.current_option + 1) % MAX_OPTIONS

    def _is_option_selected(self, key: int) -> bool:
        """Проверяет, выбран ли пункт меню.

        Args:
            key: код нажатой клавиши

        Returns:
            True если пункт выбран
        """
        return key == ord('\n')

    def reset(self) -> None:
        """Сбрасывает меню в начальное состояние."""
        self.current_option = 0
