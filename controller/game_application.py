"""Главное приложение - координирует весь игровой процесс."""

import curses
import random
import sys
from constants import *
from controller.menu_controller import MenuController
from controller.gameplay_controller import GamePlayController
from controller.statistics_controller import StatisticsController
from view import GameDisplay, MenuDisplay, StatisticsDisplay
from model import (
    GameSession,
    GameEngine,
    Hero,
    SimpleRoomGenerator,
    CorridorBuilder,
    DungeonGenerator,
    Enemy,
    EnemyType,
    Item,
    ItemType
)
from data.save_manager import SaveManager


class GameApplication:
    """Главное приложение игры.

    Отвечает за:
    - Инициализацию всех компонентов
    - Управление основным потоком игры (меню -> игра -> выход)
    - Координацию контроллеров
    - Настройку окружения curses
    """

    def __init__(self, stdscr):
        """Инициализирует приложение.

        Args:
            stdscr: объект окна curses (предоставляется curses.wrapper)
        """
        self.stdscr = stdscr
        self._setup_curses()
        self._initialize_components()

    def _initialize_components(self) -> None:
        """Инициализирует все компоненты приложения."""
        # Инициализация компонентов View
        self.menu_display = MenuDisplay()
        self.game_display = GameDisplay()
        self.statistics_display = StatisticsDisplay()

        # Инициализация компонентов Model
        self.game_session = GameSession()
        self.game_engine = GameEngine(self.game_session)

        # Инициализация dungeon generator
        self.dungeon_generator = self._create_dungeon_generator()

        # Загружаем сохраненную статистику
        self.game_session.statistics = SaveManager.load_statistics()

        # Инициализация контроллеров
        self.menu_controller = MenuController(self.menu_display)
        self.gameplay_controller = GamePlayController(
            self.game_display,
            self.game_engine,
            self.dungeon_generator
        )
        self.statistics_controller = StatisticsController(
            self.statistics_display
        )

        # Инициализация цветов curses
        self._init_curses_colors()

    def run(self) -> None:
        """Запускает главный цикл приложения."""
        try:
            while True:
                # Показываем меню и ждем выбора
                user_choice = self.menu_controller.run_main_menu(self.stdscr)

                if user_choice is None:
                    break

                self._handle_menu_choice(user_choice)
                #self.menu_controller.reset()

        except KeyboardInterrupt:
            pass

    def _handle_menu_choice(self, user_choice: int) -> None:
        """Обрабатывает выбор пользователя в меню.

        Args:
            user_choice: выбранный пункт меню
        """
        if user_choice == MENU_OPTION_NEW_GAME:
            self._start_new_game()
        elif user_choice == MENU_OPTION_LOAD_GAME:
            self._load_saved_game()
        elif user_choice == MENU_OPTION_SCOREBOARD:
            self._show_scoreboard()
        elif user_choice == MENU_OPTION_EXIT:
            self._exit_game()

    def _start_new_game(self) -> None:
        """Запускает новую игру."""
        hero = Hero()
        self.game_session.start_new_session(hero)
        self._setup_and_run_first_level(hero)
        # Сохраняем статистику после завершения игры
        SaveManager.save_statistics(self.game_session.statistics)

    def _setup_and_run_first_level(self, hero: Hero) -> None:
        """Настраивает и запускает первый уровень.

        Args:
            hero: объект героя
        """
        dungeon_layer = self.dungeon_generator.generate(
            WIDTH,
            HEIGHT,
            TARGET_ROOMS
        )
        self._setup_level(dungeon_layer, hero)
        self._spawn_enemies_for_level(dungeon_layer)
        self._spawn_items_for_level(dungeon_layer)
        self.gameplay_controller.run_game_loop(self.stdscr)

    def _setup_level(self, dungeon_layer, hero: Hero) -> None:
        """Настраивает уровень: позицию героя и выход.

        Args:
            dungeon_layer: слой подземелья
            hero: объект героя
        """
        self.game_session.load_level(dungeon_layer)
        hero_spawn = dungeon_layer.get_player_spawn_position()
        hero.set_position(hero_spawn[0], hero_spawn[1])
        dungeon_layer.generate_exit_position()

    def _spawn_enemies_for_level(self, dungeon_layer) -> None:
        """Создает врагов на текущем уровне.

        Args:
            dungeon_layer: слой подземелья
        """
        for room_index in range(FIRST_ROOM_INDEX, LAST_ROOM_INDEX):
            if random.random() < self.game_session.enemy_probability:
                enemy = self._create_enemy_in_room(dungeon_layer, room_index)
                self.game_session.add_enemy(enemy)

    def _create_enemy_in_room(self, dungeon_layer, room_index) -> Enemy:
        """Создает врага в указанной комнате.

        Args:
            dungeon_layer: слой подземелья
            room_index: индекс комнаты

        Returns:
            Созданный враг
        """
        enemy = Enemy(EnemyType.get_random())
        enemy_spawn = dungeon_layer.get_random_spawn_position_in_room(
            room_index)
        enemy.set_position(enemy_spawn[0], enemy_spawn[1])
        return enemy

    def _spawn_items_for_level(self, dungeon_layer) -> None:
        """Создает предметы на текущем уровне.

        Args:
            dungeon_layer: слой подземелья
        """
        for room_index in range(FIRST_ROOM_INDEX, LAST_ROOM_INDEX):
            if random.random() < self.game_session.item_probability:
                item = self._create_item_in_room(dungeon_layer, room_index)
                self.game_session.add_item(item)

    def _create_item_in_room(self, dungeon_layer, room_index) -> Item:
        """Создает предмет в указанной комнате.

        Args:
            dungeon_layer: слой подземелья
            room_index: индекс комнаты

        Returns:
            Созданный предмет
        """
        item = Item(ItemType.get_random())
        item_spawn = dungeon_layer.get_random_spawn_position_in_room(
            room_index)
        item.set_position(item_spawn[0], item_spawn[1])
        return item

    def _create_dungeon_generator(self) -> DungeonGenerator:
        """Создает генератор подземелья с нужными компонентами.

        Returns:
            Инициализированный DungeonGenerator
        """
        room_generator = SimpleRoomGenerator()
        corridor_generator = CorridorBuilder()
        return DungeonGenerator(room_generator, corridor_generator)

    def _setup_curses(self) -> None:
        """Настраивает параметры curses для корректной работы."""
        curses.curs_set(0)              # Скрывает визуальный курсор
        curses.noecho()                 # Не выводит нажатые клавиши
        self.stdscr.keypad(True)        # Включает поддержку специальных клавиш
        self.stdscr.nodelay(False)      # Режим блокировки при ожидании ввода

    def _init_curses_colors(self) -> None:
        """Инициализирует цветовые пары для curses."""
        curses.start_color()
        curses.init_pair(COLOR_PAIR_VAMPIRE,
                         curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(COLOR_PAIR_ZOMBIE,
                         curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_PAIR_OGRE, curses.COLOR_YELLOW,
                         curses.COLOR_BLACK)
        curses.init_pair(COLOR_PAIR_NEUTRAL,
                         curses.COLOR_WHITE, curses.COLOR_BLACK)

    def _exit_game(self) -> None:
        """Выходит из игры с корректной очисткой ресурсов."""
        sys.exit(0)

    def _show_scoreboard(self) -> None:
        """Показывает таблицу рекордов со статистикой всех прохождений."""
        sessions = self.game_session.statistics.get_all_sessions_sorted_by_treasures()
        self.statistics_controller.show_scoreboard(self.stdscr, sessions)

    def _load_saved_game(self) -> None:
        session = SaveManager.load_session()
        if session is None:
            pass

        # Сохраняем статистику перед заменой game_session
        statistics = self.game_session.statistics
        
        self.game_session = session
        self.game_session.statistics = statistics  # Восстанавливаем статистику
        self.game_engine = GameEngine(self.game_session)
        self.gameplay_controller = GamePlayController(
            self.game_display,
            self.game_engine,
            self.dungeon_generator
        )
        self.gameplay_controller.run_game_loop(self.stdscr)
        # Сохраняем статистику после завершения игры
        SaveManager.save_statistics(self.game_session.statistics)