"""Игровой движок - бизнес-логика и правила игры."""

import random
from typing import Tuple, Optional
from model.game_session import GameSession
from model.entities import Hero
from model.entities import Enemy, EnemyType
from model.entities import Item, ItemType, TemporaryEffect
from constants import *


class GameEngine:
    """Управляет бизнес-логикой игры и применением правил.

    Отвечает за:
    - Проверку возможности действий
    - Применение правил игры
    - Изменение состояния игры
    """

    def __init__(self, session: GameSession):
        """Инициализирует игровой движок.

        Args:
            session: текущий игровой сеанс
        """
        self.session = session

    def _check_game_state(self) -> bool:
        """Проверяет, готова ли игра к действиям."""
        return bool(self.session.hero and self.session.current_layer)

    def can_move_to(self, x: int, y: int) -> bool:
        """Проверяет возможность движения на позицию.

        Args:
            x: координата X
            y: координата Y

        Returns:
            True если движение возможно
        """
        if not self._check_game_state():
            return False

        layer = self.session.current_layer
        # Проверка границ карты
        if not (0 <= x < layer.width and 0 <= y < layer.height):
            return False

        # Проверка, что позиция проходима (в комнате или коридоре)
        if not layer.is_passable(x, y):
            return False

        # Проверка, что позиция не занята сущностями
        if not self.session.is_empty_position(x, y):
            return False

        return True

    def move_hero(self, dx: int, dy: int) -> bool:
        """Перемещает героя на относительные координаты.

        Args:
            dx: смещение по X (-1, 0, 1)
            dy: смещение по Y (-1, 0, 1)

        Returns:
            True если движение успешно, False если блокировано
        """
        if not self._check_game_state():
            return False

        hero = self.session.hero
        layer = self.session.current_layer
        x, y = hero.get_position()
        new_x, new_y = x + dx, y + dy

        if self.can_move_to(new_x, new_y):
            hero.set_position(new_x, new_y)
            self.pick_up_items()
            return True

        return False

    def pick_up_items(self) -> None:
        """Подбирает предметы на позиции героя и добавляет их в рюкзак.

        Если герой наступил на предмет, предмет автоматически добавляется
        в инвентарь и удаляется с карты.
        """
        if not self._check_game_state():
            return

        hero = self.session.hero
        hero_pos = hero.get_position()

        # Ищем все предметы на позиции героя
        items_to_remove = []
        for item in self.session.items:
            if item.get_position() == hero_pos:
                if item.type == ItemType.TREASURE:
                    if not hero.backpack.check_treasure():
                        hero.backpack.add_item(item)
                    hero.gold += item.price
                    # Отслеживаем собранное сокровище в статистике
                    self.session.statistics.add_treasure(item)
                    # Помечаем для удаления с карты
                    items_to_remove.append(item)
                elif len(hero.backpack.items) < BACKPACK_MAX_ITEMS:
                    # Добавляем предмет в рюкзак
                    hero.backpack.add_item(item)
                    items_to_remove.append(item)

        # Удаляем подобранные предметы из игровой сессии
        for item in items_to_remove:
            self.session.items.remove(item)

    def hero_interact(self) -> bool:
        """Герой взаимодействует с объектом на текущей позиции.

        Returns:
            True если взаимодействие успешно
        """
        if not self._check_game_state():
            return False

        # TODO: Реализовать логику взаимодействия с объектами
        # - Подобрать предмет
        # - Открыть дверь
        # - Активировать ловушку
        return True

    def check_level_completion(self) -> bool:
        """Проверяет, достигла ли цель игрока.

        Returns:
            True если уровень завершен
        """
        if not self._check_game_state():
            return False

        hero_pos = self.session.hero.get_position()
        finish_pos = self.session.current_layer.get_exit()

        return hero_pos == finish_pos

    def enemy_attack(self) -> None:
        """Враги атакуют героя, если тот находится в радиусе атаки.

        Каждый враг проверяет, находится ли герой на расстоянии атаки (1 клетка).
        Если да и враг может атаковать, враг наносит урон герою и помечается как двигавшийся.
        """
        if not self._check_game_state():
            return

        hero = self.session.hero
        hero_pos = hero.get_position()

        for enemy in self.session.enemies:
            if not enemy.is_alive():
                continue

            # Проверяем, находится ли враг на расстоянии атаки и может ли он атаковать
            distance = self._calculate_distance(hero_pos, enemy.get_position())
            if distance == ENEMY_ATTACK_RANGE and enemy.can_attack():
                if enemy.type == EnemyType.GHOST:
                    enemy.type.value["symbol"] = 'g'
                enemy.attack(hero)
                enemy.mark_as_moved()

    def move_enemies(self) -> None:
        """Перемещает всех врагов согласно их AI.

        Каждый враг:
        - Не двигается, если уже был атакован на этом ходу
        - По завершению хода: сбрасываются флаги движения
        - Если герой в радиусе враждебности: двигается в сторону героя
        - Иначе: двигается в случайном направлении
        """
        if not self._check_game_state():
            return

        for enemy in self.session.enemies:
            if not enemy.is_alive():
                continue

            # Этот враг если уже был атакован на этом ходу
            if enemy.has_moved_this_turn():
                continue

            dx, dy = self._get_enemy_move_direction(enemy)
            self._move_enemy(enemy, dx, dy)

        # Сбрасываем флаги мовента для следующего хода
        for enemy in self.session.enemies:
            enemy.reset_moved_flag()

    def _get_random_axis_direction(self, magnitude: int) -> Tuple[int, int]:
        """Возвращает случайное движение либо по X, либо по Y с указанной величиной.

        Args:
            magnitude: величина смещения (1, 2, и т.д.)

        Returns:
            Кортеж (dx, dy) - движение только по одной оси
        """
        axis = random.choice(['x', 'y'])
        direction = random.choice([-1, 1])
        if axis == 'x':
            return (direction * magnitude, 0)
        return (0, direction * magnitude)

    def _get_enemy_move_direction(self, enemy: Enemy) -> Tuple[int, int]:
        """Определяет направление движения врага в зависимости от его типа.

        Args:
            enemy: враг для которого определяется направление

        Returns:
            Кортеж (dx, dy) с смещением, зависит от типа врага
        """
        hero_pos = self.session.hero.get_position()
        enemy_pos = enemy.get_position()
        distance = self._calculate_distance(enemy_pos, hero_pos)

        if distance <= enemy.hostility:
            return self._get_direction_towards_hero(enemy_pos, hero_pos)

        # Специальное поведение для разных типов врагов
        if enemy.type == EnemyType.SNAKE_MAGE:
            # Случайное диагональное движение
            return (random.choice([-1, 1]), random.choice([-1, 1]))
        elif enemy.type == EnemyType.GHOST:
            # Привидение телепортируется случайно в комнате (обработка в _move_enemy)
            return (0, 0)
        elif enemy.type == EnemyType.OGRE:
            return self._get_random_axis_direction(2)
        else:
            # Зомби, Вампир - базовое поведение
            return self._get_random_axis_direction(1)

    def _get_direction_towards_hero(self, enemy_pos: Tuple[int, int],
                                    hero_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Вычисляет направление в сторону героя (ТОЛЬКО горизонтально ИЛИ вертикально).

        Args:
            enemy_pos: текущая позиция врага (x, y)
            hero_pos: текущая позиция героя (x, y)

        Returns:
            Кортеж (dx, dy) с смещением в сторону героя (только ОДНА ось: либо (1,0), (-1,0), (0,1), либо (0,-1))
        """
        ex, ey = enemy_pos
        hx, hy = hero_pos

        # Вычисляем расстояния по X и Y
        dist_x = hx - ex
        dist_y = hy - ey
        abs_dist_x = abs(dist_x)
        abs_dist_y = abs(dist_y)

        # Выбираем одну ось: по какой расстояние больше
        if abs_dist_x > abs_dist_y:
            # Движемся только по X
            return (1 if dist_x > 0 else -1, 0)
        else:
            # Движемся только по Y (если расстояния равны, тоже по Y)
            return (0, 1 if dist_y > 0 else -1)

    def _calculate_distance(self, pos1: Tuple[int, int],
                            pos2: Tuple[int, int]) -> float:
        """Вычисляет расстояние между двумя позициями (Манхэттенское расстояние).

        Args:
            pos1: первая позиция (x, y)
            pos2: вторая позиция (x, y)

        Returns:
            Расстояние между позициями
        """
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _teleport_ghost_randomly(self, ghost: Enemy) -> None:
        """Телепортирует привидение в случайную пустую позицию в текущей комнате.

        Args:
            ghost: враг типа GHOST для телепортации
        """
        x, y = ghost.get_position()
        # Получаем текущую комнату
        current_room = None
        for room in self.session.current_layer.rooms:
            if room.x <= x < room.x + room.width and room.y <= y < room.y + room.height:
                current_room = room
                break

        if not current_room:
            return

        # Телепортируемся в случайную пустую позицию в этой комнате
        for _ in range(10):
            new_x = random.randint(
                current_room.x, current_room.x + current_room.width - 1)
            new_y = random.randint(
                current_room.y, current_room.y + current_room.height - 1)

            if self.can_move_to(new_x, new_y) and self.session.is_empty_position(new_x, new_y):
                ghost.set_position(new_x, new_y)
                return

    def _move_enemy(self, enemy: Enemy, dx: int, dy: int) -> None:
        """Перемещает врага на относительные координаты в зависимости от его типа.

        Args:
            enemy: враг для перемещения
            dx: смещение по X
            dy: смещение по Y
        """
        # Специальное поведение для Привидения - телепортация в комнате
        if enemy.type == EnemyType.GHOST and dx == 0 and dy == 0:
            if enemy.type.value["symbol"] == 'g':
                enemy.type.value["symbol"] = '\u00B7'
            else:
                enemy.type.value["symbol"] = 'g'
            self._teleport_ghost_randomly(enemy)
            return

        # Стандартное движение для других врагов
        x, y = enemy.get_position()
        new_x, new_y = x + dx, y + dy

        # Для Огра: проверяем также промежуточную позицию (чтобы не перепрыгивал через стены)
        if enemy.type == EnemyType.OGRE and (abs(dx) == 2 or abs(dy) == 2):
            mid_x, mid_y = x + dx // 2, y + dy // 2
            if not self.can_move_to(mid_x, mid_y):
                return

        if self.can_move_to(new_x, new_y):
            enemy.set_position(new_x, new_y)

    def hero_attack(self, dx: int, dy: int) -> bool:
        """Пытается атаковать врага на смежной позиции при ошибке движения.

        Args:
            dx: смещение по X
            dy: смещение по Y
        """
        hero = self.session.hero
        x, y = hero.get_position()
        new_x, new_y = x + dx, y + dy

        # Пытаемся найти врага на этой позиции
        enemy = self.enemy_on_position(new_x, new_y)
        if enemy:
            # Герой атакует врага
            damage_dealt = hero.attack(enemy)
            
            # Отслеживаем в статистике
            if damage_dealt == 0:
                # Промах
                self.session.statistics.add_hit_missed()
            else:
                # Попадание
                self.session.statistics.add_hit_dealt()

            # Удаляем мёртвых врагов
            if enemy.health == 0:
                self._enemy_died(enemy)
                self.session.remove_enemy(enemy)

            return True

        return False

    def enemy_on_position(self, x: int, y: int) -> Optional[Enemy]:
        """Находит врага на указанной позиции.

        Args:
            x: координата X
            y: координата Y

        Returns:
            Враг на этой позиции или None если врага нет
        """
        for enemy in self.session.enemies:
            if enemy.get_position() == (x, y):
                return enemy

        return None

    def _enemy_died(self, enemy: Enemy) -> None:
        x, y = enemy.get_position()
        self.session.remove_enemy(enemy)
        new_item = Item.create_treasure_from_enemy(enemy)
        new_item.set_position(x, y)
        self.session.add_item(new_item)

    def _drop_item_near_hero(self, hero: Hero, item: Item) -> None:
        """Кладёт предмет на соседнюю проходимую клетку."""
        x, y = hero.get_position()
        for nx, ny in ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)):
            if self.can_move_to(nx, ny):
                item.set_position(nx, ny)
                self.session.add_item(item)
                return
        item.set_position(x, y)
        self.session.add_item(item)

    def unequip_weapon(self, hero: Hero) -> bool:
        """Снимает оружие: в рюкзак или на соседнюю клетку, если рюкзак полон."""
        if hero.weapon is None:
            return False

        weapon = hero.weapon
        hero.strength -= weapon.strength
        hero.weapon = None

        if len(hero.backpack.items) < BACKPACK_MAX_ITEMS:
            hero.backpack.add_item(weapon)
        else:
            self._drop_item_near_hero(hero, weapon)
        return True

    def use_item(self, item: Item, hero: Hero) -> None:
        """Использует предмет из рюкзака.

        Args:
            item: предмет для использования
            hero: герой который использует предмет
        """
        if item.price > 0:
            return
        # Применяем эффекты предмета
        if item.health > 0:
            hero.current_health = min(
                hero.current_health + item.health,
                hero.max_health
            )

        if item.duration > 0:
            bonuses = {}
            if item.agility > 0:
                bonuses['agility'] = item.agility
            if item.strength > 0:
                bonuses['strength'] = item.strength
            if item.max_health > 0:
                bonuses['max_health'] = item.max_health
                bonuses['current_health'] = item.max_health
            effect = TemporaryEffect(bonuses, item.duration)
            hero.apply_temporary_effect(effect)
        elif item.type == ItemType.WEAPON_STICK or item.type == ItemType.WEAPON_ROCK:
            if hero.weapon is None:
                hero.weapon = item
                hero.strength += item.strength
            elif hero.weapon:
                old_weapon = hero.weapon
                hero.strength -= old_weapon.strength
                self._drop_item_near_hero(hero, old_weapon)
                hero.weapon = item
                hero.strength += item.strength

        else:
            if item.agility > 0:
                hero.agility += item.agility
            if item.strength > 0:
                hero.strength += item.strength
            if item.max_health > 0:
                hero.max_health += item.max_health
                hero.current_health += item.max_health

        # Удаляем предмет из рюкзака после использования
        hero.backpack.remove_item(item)
