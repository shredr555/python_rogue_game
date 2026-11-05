"""Отрисовка игровой карты."""

import curses
from typing import Optional, List, Tuple


class GameDisplay:
    """Обрабатывает отрисовку игровой карты подземелья.

    Отвечает за:
    - Отрисовку на экран curses
    - Обновление дисплея

    """

    def __init__(self):
        """Инициализирует дисплей игры."""
        pass

    def display_map(self, stdscr, tilemap: List[List[Tuple[str, int]]], width: int, height: int) -> None:
        """Отображает карту подземелья на экран.

        Args:
            stdscr: объект окна curses
            tilemap: 2D список кортежей (символ, номер цвета)
            width: ширина карты
            height: высота карты
        """
        if not tilemap:
            return

        self._render_tilemap_to_screen(stdscr, tilemap, width, height)

    def _render_tilemap_to_screen(self, stdscr, tilemap: List[List[Tuple[str, int]]], width: int, height: int) -> None:
        """Отрисовывает тилемап на экран curses.

        Args:
            stdscr: объект окна curses
            tilemap: 2D список кортежей (символ, номер цвета)
            width: ширина карты
            height: высота карты
        """
        stdscr.clear()

        try:
            for y, row in enumerate(tilemap):
                if y >= height:
                    break
                try:
                    for x, (symbol, color_pair) in enumerate(row):
                        if x >= width:
                            break
                        stdscr.addch(
                            y, x, symbol, curses.color_pair(color_pair))
                except curses.error:
                    pass
                stdscr.refresh()
        except curses.error:
            # Игнорируем ошибки curses
            pass

    def clear(self, stdscr) -> None:
        """Очищает экран.

        Args:
            stdscr: объект окна curses
        """
        try:
            stdscr.clear()
            stdscr.refresh()
        except curses.error:
            pass

    def refresh(self, stdscr) -> None:
        """Обновляет экран.

        Args:
            stdscr: объект окна curses
        """
        try:
            stdscr.refresh()
        except curses.error:
            pass

    def display_stats(self, stdscr, hero, level: int, width: int, height: int) -> None:
        """Отображает статистику героя в нижней части экрана.

        Args:
            stdscr: объект окна curses
            hero: объект героя с атрибутами (health, agility, strength, gold)
            level: текущий уровень
        """
        try:
            max_x, max_y = width, height
            stats_line = f"Уровень: {level}  Золото: {hero.gold}  Здоровье: {hero.current_health}/{hero.max_health}  Ловкость: {hero.agility}  Сила: {hero.strength}"

            # Обрезаем строку если она слишком длинная
            if len(stats_line) > max_x - 1:
                stats_line = stats_line[:max_x - 1]

            # Вычисляем позицию для центрирования
            x_pos = (max_x - len(stats_line)) // 2

            # Отображаем строку по центру
            stdscr.addstr(max_y - 1, x_pos, stats_line)
            stdscr.refresh()
        except curses.error:
            pass

    def display_backpack(self, stdscr, items: List, selected_index: int) -> None:
        """Отображает меню выбора предмета из рюкзака.

        Args:
            stdscr: объект окна curses
            items: список предметов в рюкзаке
            selected_index: индекс выбранного предмета
        """
        try:
            stdscr.clear()

            # Отрисовка заголовка
            stdscr.addstr(0, 0, "=== BACKPACK ===")
            stdscr.addstr(
                1, 0, "Use arrow keys to select, Enter to use, Esc to exit")
            stdscr.addstr(2, 0, "-" * 40)

            # Отрисовка списка предметов
            for i, item in enumerate(items):
                prefix = ">>> " if i == selected_index else "    "
                item_name = f"{item.type.value['subtype'].upper()}"

                # Добавляем статистику предмета
                stats = []
                if item.health > 0:
                    stats.append(f"+{item.health}HP")
                if item.agility > 0:
                    stats.append(f"+{item.agility}AGI")
                if item.strength > 0:
                    stats.append(f"+{item.strength}STR")

                stats_str = f" ({', '.join(stats)})" if stats else ""
                line = f"{prefix}{item_name}{stats_str}"

                stdscr.addstr(3 + i, 0, line)

            stdscr.refresh()
        except curses.error:
            pass

    def display_weapon_menu(
        self,
        stdscr,
        weapons: List,
        selected_index: int,
        equipped_weapon=None,
    ) -> None:
        """Меню выбора оружия: 0 — пустые руки, 1–9 — предметы из рюкзака."""
        try:
            stdscr.clear()
            stdscr.addstr(0, 0, "=== WEAPON ===")
            stdscr.addstr(
                1, 0,
                "0: empty hands | 1-9: equip | arrows/Enter | Esc: cancel",
            )
            stdscr.addstr(2, 0, "-" * 50)

            line = 3
            prefix = ">>> " if selected_index == 0 else "    "
            stdscr.addstr(line, 0, f"{prefix}0. EMPTY HANDS")
            line += 1

            for i, item in enumerate(weapons[:9]):
                slot = i + 1
                prefix = ">>> " if selected_index == slot else "    "
                stats = f" (+{item.strength} STR)" if item.strength > 0 else ""
                name = item.type.value['subtype'].upper()
                stdscr.addstr(line, 0, f"{prefix}{slot}. {name}{stats}")
                line += 1

            if equipped_weapon is not None:
                name = equipped_weapon.type.value['subtype'].upper()
                stdscr.addstr(
                    line + 1, 0,
                    f"Equipped: {name} (+{equipped_weapon.strength} STR)",
                )

            stdscr.refresh()
        except curses.error:
            pass
