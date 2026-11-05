"""Отрисовка тилемапа подземелья."""

from typing import Optional, List, Tuple
from constants import *
from model import Layer
from model.dungeon_structures import find_room_doorways
from model.entities import Hero, Enemy, Item


class TilemapRenderer:
    """Преобразует слой подземелья в 2D тилемап для отрисовки."""

    def render(self, layer: Layer, hero: Optional[Hero] = None, enemies: Optional[List[Enemy]] = None, items: Optional[List[Item]] = None) -> list:
        """Преобразует объект Layer в 2D список тилемапа.

        Args:
            layer: объект слоя подземелья
            hero: объект героя для отрисовки (опционально)
            enemies: список врагов для отрисовки (опционально)

        Returns:
            2D список символов для отрисовки
        """
        tilemap = [[(EMPTY_SPACE, 0) for _ in range(
            layer.width)] for _ in range(layer.height)]

        # метод для тумана войны - решает что показывать
        x, y = hero.get_position()
        layer.war_fog(x, y)

        self._render_rooms(tilemap, layer, hero)
        self._render_corridors(tilemap, layer)
        if items:
            self._render_items(tilemap, layer, items, hero)
        if hero:
            self._render_hero(tilemap, layer, hero)
        if enemies:
            self._render_enemies(tilemap, layer, enemies, hero)
        # Очистить область видимости для всех комнат
        rooms = layer.rooms
        for room in rooms:
            room.visible_area = []

        return tilemap

    def _render_hero(self, tilemap: list, layer: Layer, hero: Hero) -> None:
        """Отрисовывает героя на карту.

        Args:
            tilemap: 2D список тилемапа
            layer: слой подземелья
            hero: объект героя
        """
        hero_position = hero.get_position()
        x, y = hero_position
        if 0 <= y < layer.height and 0 <= x < layer.width:
            tilemap[y][x] = ("@", 4)

    def _render_enemies(self, tilemap: list, layer: Layer, enemies: List[Enemy], hero: Hero) -> None:
        """Отрисовывает врагов на карту, если герой находится с ними в одной комнате
        или коридоре, а также если враг попадает в зону прямой видимости,
        когда герой стоит на пороге комнаты.

        Args:
            tilemap: 2D список тилемапа
            layer: слой подземелья
            enemies: список врагов
        """
        hero_position = hero.get_position()
        x_hero, y_hero = hero_position
        index_hero = layer.index_position(x_hero, y_hero)
        rooms = layer.rooms
        for enemy in enemies:
            enemy_position = enemy.get_position()
            x_enemy, y_enemy = enemy_position
            index_enemy = layer.index_position(x_enemy, y_enemy)
            index_room = index_enemy[0]
            if index_hero == index_enemy or in_visible_area(rooms[index_room].visible_area, enemy_position):
                if 0 <= y_enemy < layer.height and 0 <= x_enemy < layer.width:
                    tilemap[y_enemy][x_enemy] = (
                        enemy.symbol, enemy.color_pair)

    def _render_items(self, tilemap: list, layer: Layer, items: List[Item], hero: Hero) -> None:
        """Отрисовывает предметы на карту, если предмет находится в одной комнате с героем
        или попадает в зону прямой видимости, когда герой стоит на пороге комнаты.

        Args:
            tilemap: 2D список тилемапа
            layer: слой подземелья
            enemies: список предметов
        """
        hero_position = hero.get_position()
        x_hero, y_hero = hero_position
        index_hero = layer.index_position(x_hero, y_hero)
        rooms = layer.rooms
        for item in items:
            item_position = item.get_position()
            x_item, y_item = item_position
            index_item = layer.index_position(x_item, y_item)
            index_room = index_item[0]
            if index_hero == index_item or in_visible_area(rooms[index_room].visible_area, item_position):
                if 0 <= y_item < layer.height and 0 <= x_item < layer.width:
                    tilemap[y_item][x_item] = (item.symbol, item.color_pair)

    def _render_rooms(self, tilemap: list, layer: Layer, hero: Hero) -> None:
        """Отрисовывает все комнаты в тилемапе.

        Args:
            tilemap: 2D список тилемапа
            layer: слой подземелья
        """
        hero_position = hero.get_position()
        hero_x, hero_y = hero_position
        for room in layer.rooms:
            if room.is_visited or len(room.visible_area) > 0:
                # Рисует верхнюю и нижнюю стены
                for x in range(room.x, room.x + room.width):
                    if room.y - 1 >= 0:
                        tilemap[room.y - 1][x] = (HORIZONTAL_WALL, 4)
                    if room.y + room.height < layer.height:
                        tilemap[room.y + room.height][x] = (HORIZONTAL_WALL, 4)

                # Рисует левую и правую стены
                for y in range(room.y, room.y + room.height):
                    if room.x - 1 >= 0:
                        tilemap[y][room.x - 1] = (VERTICAL_WALL, 4)
                    if room.x + room.width < layer.width:
                        tilemap[y][room.x + room.width] = (VERTICAL_WALL, 4)

                # Рисует углы
                if room.y - 1 >= 0 and room.x - 1 >= 0:
                    tilemap[room.y - 1][room.x - 1] = (TOP_LEFT_CORNER, 4)

                if room.y - 1 >= 0 and room.x + room.width < layer.width:
                    tilemap[room.y - 1][room.x +
                                        room.width] = (TOP_RIGHT_CORNER, 4)

                if room.y + room.height < layer.height and room.x - 1 >= 0:
                    tilemap[room.y + room.height][room.x -
                                                  1] = (BOTTOM_LEFT_CORNER, 4)

                if room.y + room.height < layer.height and room.x + room.width < layer.width:
                    tilemap[room.y + room.height][room.x +
                                                  room.width] = (BOTTOM_RIGHT_CORNER, 4)

            if room.is_visited:
                if not room.saved_exits:
                    room.discover_exits(layer)
                self._render_saved_exits(tilemap, layer, room)

            if len(room.visible_area) > 0:
                # Рисует пол только видимой области, если герой на пороге комнаты
                visible_cells = room.visible_area
                for cell in visible_cells:
                    x = cell[0]
                    y = cell[1]
                    tilemap[y][x] = (ROOM_FLOOR, 4)
                
                # Открывает дверные проёмы, чтобы была видна комната из коридора
                if not room.in_room(hero_x, hero_y):
                    self._render_doorways(tilemap, layer, room)
                # room.visible_area = []

            if room.in_room(hero_x, hero_y):
                # Рисует пол всей комнаты, если герой внутри
                for y in range(room.y, room.y + room.height):
                    for x in range(room.x, room.x + room.width):
                        if 0 <= y < layer.height and 0 <= x < layer.width:
                            tilemap[y][x] = (ROOM_FLOOR, 4)
                
                # Рисует коридоры, видимые из текущей комнаты
                self._render_doorways(tilemap, layer, room)
                
                if room.is_finish and layer.exit:
                    tilemap[layer.exit[1]][layer.exit[0]] = (EXIT_DOOR, 1)

    def _render_saved_exits(self, tilemap: list, layer: Layer, room) -> None:
        """Отрисовывает сохранённые выходы посещённой комнаты."""
        for x, y in room.saved_exits:
            if not (0 <= y < layer.height and 0 <= x < layer.width):
                continue
            if room.is_finish and layer.exit and (x, y) == layer.exit:
                tilemap[y][x] = (EXIT_DOOR, 1)
            else:
                tilemap[y][x] = (INTERSECTION, 4)

    def _render_corridors(self, tilemap: list, layer: Layer) -> None:
        """Отрисовывает все коридоры в тилемапе.

        Args:
            tilemap: 2D список тилемапа
            layer: слой подземелья
        """
        for corridor in layer.corridors:
            if corridor.is_visited:
                for (x1, y1), (x2, y2) in corridor.segments:
                    if x1 == x2:
                        # Вертикальный коридор
                        for y in range(min(y1, y2), max(y1, y2) + 1):
                            if 0 <= y < layer.height and 0 <= x1 < layer.width:
                                if tilemap[y][x1][0] in WALL_SYMBOLS:
                                    tilemap[y][x1] = (INTERSECTION, 4)
                                elif tilemap[y][x1][0] == EMPTY_SPACE:
                                    tilemap[y][x1] = (CORRIDOR_FLOOR, 4)
                    else:
                        # Горизонтальный коридор
                        for x in range(min(x1, x2), max(x1, x2) + 1):
                            if 0 <= y1 < layer.height and 0 <= x < layer.width:
                                if tilemap[y1][x][0] in WALL_SYMBOLS:
                                    tilemap[y1][x] = (INTERSECTION, 4)
                                elif tilemap[y1][x][0] == EMPTY_SPACE:
                                    tilemap[y1][x] = (CORRIDOR_FLOOR, 4)

    def _render_doorways(self, tilemap: list, layer: Layer, room) -> None:
        """Отрисовывает дверные проёмы в тилемапе."""
        for x, y in find_room_doorways(room, layer):
            if 0 <= y < layer.height and 0 <= x < layer.width:
                if room.is_finish and layer.exit and (x, y) == layer.exit:
                    tilemap[y][x] = (EXIT_DOOR, 1)
                else:
                    tilemap[y][x] = (INTERSECTION, 4)

def in_visible_area(list: List[Tuple[int, int]], pos: Tuple[int, int]) -> bool:
    """ Проверяет попадает ли координата в видимую область
    (для тумана войны)
    """
    for element in list:
        if element == pos:
            return True
    return False
