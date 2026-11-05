"""Контроллер геймплея - управляет основным игровым циклом."""

import random
from typing import Optional, Dict
from view import GameDisplay
from model import GameEngine, Enemy, EnemyType, DungeonGenerator, Item, ItemType, TemporaryEffect
from controller.tilemap_renderer import TilemapRenderer
from constants import *
from data.save_manager import SaveManager

# Константы для создания врагов
_FIRST_ROOM_INDEX = 1
_LAST_ROOM_INDEX = 8  # Исключающая граница


class GamePlayController:
    """Управляет основным циклом геймплея.

    Отвечает за:
    - Основной игровой цикл
    - Обработку действий игрока
    - Координацию обновления модели и представления
    """

    # Маппинг клавиш на действия
    KEY_BINDINGS: Dict[int, Dict] = {
        ord('w'): {'action': ACTION_MOVE, 'direction': 'up', 'dx': 0, 'dy': -1},
        ord('W'): {'action': ACTION_MOVE, 'direction': 'up', 'dx': 0, 'dy': -1},
        ord('s'): {'action': ACTION_MOVE, 'direction': 'down', 'dx': 0, 'dy': 1},
        ord('S'): {'action': ACTION_MOVE, 'direction': 'down', 'dx': 0, 'dy': 1},
        ord('a'): {'action': ACTION_MOVE, 'direction': 'left', 'dx': -1, 'dy': 0},
        ord('A'): {'action': ACTION_MOVE, 'direction': 'left', 'dx': -1, 'dy': 0},
        ord('d'): {'action': ACTION_MOVE, 'direction': 'right', 'dx': 1, 'dy': 0},
        ord('D'): {'action': ACTION_MOVE, 'direction': 'right', 'dx': 1, 'dy': 0},
        ord('j'): {'action': ACTION_INTERACT_FOOD},
        ord('J'): {'action': ACTION_INTERACT_FOOD},
        ord('h'): {'action': ACTION_INTERACT_WEAPON},
        ord('H'): {'action': ACTION_INTERACT_WEAPON},
        ord('k'): {'action': ACTION_INTERACT_ELIXIR},
        ord('K'): {'action': ACTION_INTERACT_ELIXIR},
        ord('e'): {'action': ACTION_INTERACT_SCROLL},
        ord('E'): {'action': ACTION_INTERACT_SCROLL},
        ord('i'): {'action': ACTION_INVENTORY},
        ord('I'): {'action': ACTION_INVENTORY},
        ord('b'): {'action': ACTION_SELECT_ITEM},
        ord('B'): {'action': ACTION_SELECT_ITEM},
        ord('m'): {'action': ACTION_MAP},
        ord('M'): {'action': ACTION_MAP},
        ord('p'): {'action': ACTION_PAUSE},
        ord('P'): {'action': ACTION_PAUSE},
    }

    def __init__(self, game_display: GameDisplay, game_engine: GameEngine, dungeon_generator: Optional[DungeonGenerator] = None):
        """Инициализирует контроллер геймплея.

        Args:
            game_display: компонент отображения игры
            game_engine: игровой движок с бизнес-логикой
            dungeon_generator: генератор подземелья для создания новых уровней
        """
        self.game_display = game_display
        self.game_engine = game_engine
        self.tilemap_renderer = TilemapRenderer()
        self.dungeon_generator = dungeon_generator

    def run_game_loop(self, stdscr) -> bool:
        """Запускает основной цикл геймплея."""
        game_session = self.game_engine.session

        try:
            while game_session.is_active:
                self._render_and_display_game_state(stdscr)
                turn_taken = self._process_player_turn(stdscr)

                self.game_engine.pick_up_items()
                game_session.hero.update_effects()

                if not turn_taken:
                    continue

                if not self._check_hero_alive():
                    break

                self._execute_enemy_turn()

                if not self._check_hero_alive():
                    break

                if self.game_engine.check_level_completion():
                    self._on_level_completed()

            return True

        except KeyboardInterrupt:
            game_session.end_session()
            return True
        except Exception as e:
            game_session.end_session()
            raise e

    def _render_and_display_game_state(self, stdscr) -> None:
        """Отрисовывает и выводит текущее состояние игры на экран."""
        game_session = self.game_engine.session

        tilemap = self.tilemap_renderer.render(
            game_session.current_layer,
            game_session.hero,
            game_session.enemies,
            game_session.items
        )

        self.game_display.display_map(
            stdscr,
            tilemap,
            game_session.current_layer.width,
            game_session.current_layer.height
        )

        self.game_display.display_stats(
            stdscr,
            game_session.hero,
            game_session.current_level,
            game_session.current_layer.width,
            game_session.current_layer.height
        )

    def _process_player_turn(self, stdscr) -> bool:
        """Обрабатывает ход игрока.

        Returns:
            True если ход был совершен, False если ход пропущен
        """
        key = stdscr.getch()
        action = self._parse_game_input(key)
        return self._process_game_action(action, stdscr)

    def _check_hero_alive(self) -> bool:
        """Проверяет, жив ли герой. Завершает сеанс если герой мертв.

        Returns:
            True если герой живой, False если мертв
        """
        is_alive = self.game_engine.session.hero.current_health > 0
        if not is_alive:
            self.game_engine.session.end_session()
        return is_alive

    def _execute_enemy_turn(self) -> None:
        """Выполняет ход врагов: атака и движение."""
        self.game_engine.enemy_attack()
        self.game_engine.move_enemies()

    def _parse_game_input(self, key: int) -> Optional[Dict]:
        """Преобразует клавишу в действие, используя маппинг KEY_BINDINGS.

        Args:
            key: код нажатой клавиши

        Returns:
            Словарь с информацией о действии или None если клавиша не известна
        """
        return self.KEY_BINDINGS.get(key)

    def _process_game_action(self, action: Optional[Dict], stdscr) -> bool:
        """Обрабатывает действие игрока через движок.

        Args:
            action: словарь с информацией о действии или None
            stdscr: объект окна curses

        Returns:
            True чтобы продолжить игру, False чтобы выйти
        """
        # Игнорируем пустые действия (неизвестные клавиши)
        if action is None:
            return False

        action_type = action.get('action')

        if action_type == ACTION_MOVE:
            return self._handle_move_action(action)

        elif action_type == ACTION_INTERACT_WEAPON:
            return self._select_weapon(stdscr)

        elif action_type == ACTION_INTERACT_FOOD or \
                action_type == ACTION_INTERACT_ELIXIR or \
                action_type == ACTION_INTERACT_SCROLL:
            return self._select_item_from_backpack(stdscr, action_type)

        else:
            return False

    def _handle_move_action(self, action: Dict) -> bool:
        """Обрабатывает действие движения героя.

        Args:
            action: словарь с информацией о движении (dx, dy)
        """
        dx = action.get('dx', 0)
        dy = action.get('dy', 0)

        # Пытаемся переместить героя
        if not self.game_engine.move_hero(dx, dy):
            # Если движение заблокировано, проверяем есть ли враг на этой позиции
            # return self._try_attack_adjacent_enemy(dx, dy)
            return self._handle_attack_action(dx, dy)

        # Отслеживаем пройденную клетку
        self.game_engine.session.statistics.add_cell_traversed()

        return True

    def _handle_attack_action(self, dx: int, dy: int) -> bool:
        """Обрабатывает действие атаки героя и отслеживает статистику.

        Args:
            dx: смещение по X
            dy: смещение по Y

        Returns:
            True если атака произошла, False иначе
        """
        hero = self.game_engine.session.hero
        layer = self.game_engine.session.current_layer
        enemies_before = len(self.game_engine.session.enemies)
        
        # Пытаемся атаковать врага
        attack_happened = self.game_engine.hero_attack(dx, dy)
        
        if attack_happened:
            # Проверяем количество врагов после атаки
            enemies_after = len(self.game_engine.session.enemies)
            
            if enemies_after < enemies_before:
                # Враг был убит
                enemies_killed = enemies_before - enemies_after
                for _ in range(enemies_killed):
                    self.game_engine.session.statistics.add_defeated_enemy()
        
        return attack_happened

    def _handle_interact_action(self) -> None:
        """Обрабатывает действие взаимодействия с объектом."""
        self.game_engine.hero_interact()

    def _select_weapon(self, stdscr) -> bool:
        """Меню оружия: 0 — снять, 1–9 — экипировать из рюкзака."""
        import curses

        hero = self.game_engine.session.hero
        weapons = [
            item for item in hero.backpack.get_items()
            if item.type.value['type'] == 'weapon'
        ][:9]

        if not weapons and hero.weapon is None:
            return False

        menu_slots = 1 + len(weapons)
        selected_index = 0

        try:
            while True:
                self.game_display.display_weapon_menu(
                    stdscr, weapons, selected_index, hero.weapon,
                )
                key = stdscr.getch()

                if key == ord('0'):
                    return self.game_engine.unequip_weapon(hero)

                if ord('1') <= key <= ord('9'):
                    slot = key - ord('0')
                    if 1 <= slot <= len(weapons):
                        self._use_item_with_tracking(weapons[slot - 1], hero)
                        return True
                    continue

                if key == curses.KEY_UP or key == ord('w') or key == ord('W'):
                    selected_index = (selected_index - 1) % menu_slots

                elif key == curses.KEY_DOWN or key == ord('s') or key == ord('S'):
                    selected_index = (selected_index + 1) % menu_slots

                elif key == ord('\n') or key == curses.KEY_ENTER:
                    if selected_index == 0:
                        return self.game_engine.unequip_weapon(hero)
                    self._use_item_with_tracking(weapons[selected_index - 1], hero)
                    return True

                elif key == 27:
                    return False

        except curses.error:
            return False

    def _select_item_from_backpack(self, stdscr, action_type: Optional[str] = None) -> bool:
        """Показывает меню выбора предмета из рюкзака.

        Позволяет игроку использовать предметы из инвентаря.
        Использует стрелки вверх/вниз для навигации, Enter для выбора, Esc для выхода.

        Args:
            stdscr: объект окна curses
            action_type: тип предмета для фильтрации ('food', 'elixir', 'scroll', и т.д.)
                         если None, показываются все предметы

        Returns:
            True если предмет был использован, False если меню было закрыто без использования
        """
        import curses

        hero = self.game_engine.session.hero
        items = hero.backpack.get_items()

        # Фильтруем предметы по типу, если указан
        if action_type is not None:
            items = [item for item in items if item.type.value['type']
                     == action_type]

        if not items:
            return False

        selected_index = 0

        try:
            while True:
                # Используем game_display для отрисовки
                self.game_display.display_backpack(
                    stdscr, items, selected_index)

                # Обработка ввода
                key = stdscr.getch()

                if key == curses.KEY_UP or key == ord('w') or key == ord('W'):
                    selected_index = (selected_index - 1) % len(items)

                elif key == curses.KEY_DOWN or key == ord('s') or key == ord('S'):
                    selected_index = (selected_index + 1) % len(items)

                elif key == ord('\n') or key == curses.KEY_ENTER:
                    # Выбран предмет
                    selected_item = items[selected_index]
                    self._use_item_with_tracking(selected_item, hero)
                    return True  # Предмет был использован

                elif key == 27:  # ESC
                    return False  # Меню закрыто без использования

        except curses.error:
            return False

    def _use_item_with_tracking(self, item: Item, hero) -> None:
        """Использует предмет и отслеживает статистику.

        Args:
            item: предмет для использования
            hero: герой который использует предмет
        """
        item_type = item.type.value.get('type')
        item_subtype = item.type.value.get('subtype', '')
        
        # Используем предмет через игровой движок
        self.game_engine.use_item(item, hero)
        
        # Отслеживаем использование предмета в статистике
        if item_type == 'food':
            self.game_engine.session.statistics.add_eaten_food()
        elif item_type == 'elixir':
            self.game_engine.session.statistics.add_drunk_elixir()
        elif item_type == 'scroll':
            self.game_engine.session.statistics.add_read_scroll()

    def _on_level_completed(self) -> None:
        """Обработчик завершения уровня. Генерирует новый уровень.

        При отсутствии генератора подземелья завершает игровой сеанс.
        Если игрок завершил последний уровень, игра завершается.
        """
        game_session = self.game_engine.session

        # Проверяем, прошел ли игрок последний уровень
        if game_session.current_level == LAST_LEVEL:
            game_session.end_session()
            return

        SaveManager.save_session(self.game_engine.session)

        if self._can_generate_new_level():
            self.game_engine.session.next_level()
            # Отслеживаем максимально достигнутый уровень
            self.game_engine.session.statistics.update_max_level(
                self.game_engine.session.current_level
            )
            self._load_next_level()
        else:
            self.game_engine.session.end_session()

    def _can_generate_new_level(self) -> bool:
        """Проверяет возможность генерации нового уровня.

        Returns:
            True если генератор доступен, False иначе
        """
        return self.dungeon_generator is not None

    def _load_next_level(self) -> None:
        """Загружает новый уровень подземелья."""
        game_session = self.game_engine.session
        hero = game_session.hero

        dungeon_layer = self._generate_dungeon()
        self._setup_level_from_dungeon(dungeon_layer, hero)
        self._spawn_enemies_for_level(dungeon_layer, game_session)
        self._spawn_items_for_level(dungeon_layer, game_session)

    def _generate_dungeon(self):
        """Генерирует новое подземелье.

        Returns:
            Слой подземелья
        """
        return self.dungeon_generator.generate(
            WIDTH,
            HEIGHT,
            TARGET_ROOMS
        )

    def _setup_level_from_dungeon(self, dungeon_layer, hero) -> None:
        """Настраивает уровень после генерации подземелья.

        Args:
            dungeon_layer: сгенерированный слой подземелья
            hero: объект героя
        """
        game_session = self.game_engine.session
        game_session.load_level(dungeon_layer)

        hero_spawn = dungeon_layer.get_player_spawn_position()
        hero.set_position(hero_spawn[0], hero_spawn[1])
        dungeon_layer.generate_exit_position()

    def _spawn_enemies_for_level(self, dungeon_layer, game_session) -> None:
        """Создает врагов на уровне.

        Args:
            dungeon_layer: слой подземелья
            game_session: игровой сеанс
        """
        for room_index in range(_FIRST_ROOM_INDEX, _LAST_ROOM_INDEX):
            if random.random() < game_session.enemy_probability:
                enemy = self._create_random_enemy(dungeon_layer, room_index)
                game_session.add_enemy(enemy)

    def _create_random_enemy(self, dungeon_layer, room_index) -> Enemy:
        """Создает врага с случайным типом в комнате.

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

    def _spawn_items_for_level(self, dungeon_layer, game_session) -> None:
        """Создает предметы на уровне.

        Args:
            dungeon_layer: слой подземелья
            game_session: игровой сеанс
        """
        for room_index in range(_FIRST_ROOM_INDEX, _LAST_ROOM_INDEX):
            if random.random() < game_session.item_probability:
                item = self._create_random_item(dungeon_layer, room_index)
                game_session.add_item(item)

    def _create_random_item(self, dungeon_layer, room_index) -> Item:
        """Создает предмет со случайным типом в комнате.

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