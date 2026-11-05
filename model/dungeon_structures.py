"""Структуры подземелья - комнаты, коридоры, слои."""

from typing import List, Tuple, Optional, Set, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from model.dungeon_structures import Layer as LayerType


def corridor_segment_connects_room(
    layer: "LayerType",
    room: "Room",
    x1: int,
    y1: int,
    x2: int,
    y2: int,
) -> bool:
    """Проверяет, соединён ли сегмент коридора со стеной комнаты."""
    if room.y - 1 >= 0:
        if ((y1 == room.y - 1 and room.x <= x1 < room.x + room.width) or
                (y2 == room.y - 1 and room.x <= x2 < room.x + room.width) or
                (y1 == room.y - 1 and room.x <= x2 < room.x + room.width) or
                (y2 == room.y - 1 and room.x <= x1 < room.x + room.width)):
            return True

    if room.y + room.height < layer.height:
        if ((y1 == room.y + room.height and room.x <= x1 < room.x + room.width) or
                (y2 == room.y + room.height and room.x <= x2 < room.x + room.width) or
                (y1 == room.y + room.height and room.x <= x2 < room.x + room.width) or
                (y2 == room.y + room.height and room.x <= x1 < room.x + room.width)):
            return True

    if room.x - 1 >= 0:
        if ((x1 == room.x - 1 and room.y <= y1 < room.y + room.height) or
                (x2 == room.x - 1 and room.y <= y2 < room.y + room.height) or
                (x1 == room.x - 1 and room.y <= y2 < room.y + room.height) or
                (x2 == room.x - 1 and room.y <= y1 < room.y + room.height)):
            return True

    if room.x + room.width < layer.width:
        if ((x1 == room.x + room.width and room.y <= y1 < room.y + room.height) or
                (x2 == room.x + room.width and room.y <= y2 < room.y + room.height) or
                (x1 == room.x + room.width and room.y <= y2 < room.y + room.height) or
                (x2 == room.x + room.width and room.y <= y1 < room.y + room.height)):
            return True

    return False


def find_room_doorways(room: "Room", layer: "LayerType") -> List[Tuple[int, int]]:
    """Возвращает координаты дверных проёмов комнаты (соединения с коридорами)."""
    doorways: List[Tuple[int, int]] = []

    for corridor in layer.corridors:
        for (x1, y1), (x2, y2) in corridor.segments:
            if not corridor_segment_connects_room(layer, room, x1, y1, x2, y2):
                continue

            if x1 == x2:
                if y1 == room.y - 1 or y2 == room.y - 1:
                    if room.x <= x1 < room.x + room.width:
                        doorways.append((x1, room.y - 1))
                elif y1 == room.y + room.height or y2 == room.y + room.height:
                    if room.x <= x1 < room.x + room.width:
                        doorways.append((x1, room.y + room.height))
            else:
                if x1 == room.x - 1 or x2 == room.x - 1:
                    if room.y <= y1 < room.y + room.height:
                        doorways.append((room.x - 1, y1))
                elif x1 == room.x + room.width or x2 == room.x + room.width:
                    if room.y <= y1 < room.y + room.height:
                        doorways.append((room.x + room.width, y1))

    if room.is_finish and layer.exit:
        doorways.append(layer.exit)

    return doorways


class Room:
    """Представляет комнату в подземелье."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_start = False
        self.is_finish = False
        self.is_visited = False
        self.visible_area = []
        self.saved_exits: List[Tuple[int, int]] = []

    def __repr__(self) -> str:
        return f"Room(x={self.x}, y={self.y}, w={self.width}, h={self.height})"

    def to_dict(self) -> dict:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'is_start': self.is_start,
            'is_finish': self.is_finish,
            'is_visited': self.is_visited,
            'visible_area': self.visible_area,
            'saved_exits': [list(pos) for pos in self.saved_exits],
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Room':
        room = cls(
            data['x'],
            data['y'],
            data['width'],
            data['height']
        )
        room.is_start = data.get('is_start', False)
        room.is_finish = data.get('is_finish', False)
        room.is_visited = data.get('is_visited', False)
        room.visible_area = data.get('visible_area', [])
        room.saved_exits = [
            tuple(pos) for pos in data.get('saved_exits', [])
        ]
        return room

    def remember_exit(self, x: int, y: int) -> None:
        """Сохраняет координату дверного проёма, если её ещё нет в списке."""
        position = (x, y)
        if position not in self.saved_exits:
            self.saved_exits.append(position)

    def discover_exits(self, layer: "LayerType") -> None:
        """Запоминает все выходы комнаты в коридоры и выход на следующий уровень."""
        for x, y in find_room_doorways(self, layer):
            self.remember_exit(x, y)

    def in_room(self, x: int, y: int) -> bool:
        """ Возвращает истину если координаты x,y принадлежат комнате
        """
        if (self.x <= x < self.x + self.width) and (self.y <= y < self.y + self.height):
            return True
        return False

    def get_cells(self) -> Set[Tuple[int, int]]:
        """Возвращает все клетки, принадлежащие комнате"""
        cells = set()
        for i in range(self.x, self.x + self.width):
            for j in range(self.y, self.y + self.height):
                cells.add((i, j))
        return cells

    def get_visible_area(self, x_hero: int, y_hero: int):
        """
        Определяет область прямой видимости из точки (x_hero, y_hero) в комнате

        Алгоритм:
        1. Определяем все клетки комнаты
        2. Для каждой клетки комнаты проводим луч от игрока до клетки
        3. Используем алгоритм Брезенхэма для проверки пересечений со стенами
        4. Добавляем клетку в видимую область, если луч не пересекает границы комнаты

        Аргументы:
            room: объект комнаты
            x_hero, y_hero: координаты игрока в дверном проеме (снаружи комнаты)

        Возвращает:
            список координат (x, y) видимых клеток ВНУТРИ комнаты
        """
        # Получаем все клетки комнаты
        room_cells = self.get_cells()

        visible_cells = []

        # Проверяем каждую клетку комнаты
        for cell_x, cell_y in room_cells:
            # Получаем линию от игрока до клетки
            line = bresenham_line(x_hero, y_hero, cell_x, cell_y)

            is_visible = True

            # Проверяем каждую точку на линии (кроме последней)
            # Если любая промежуточная точка находится вне комнаты - стена блокирует видимость
            for point_x, point_y in line[:-1]:
                # Точки снаружи комнаты считаем стенами, НО если это позиция игрока - игнорируем
                if (point_x, point_y) != (x_hero, y_hero) and (point_x, point_y) not in room_cells:
                    is_visible = False
                    break

            if is_visible:
                self.visible_area.append((cell_x, cell_y))


class Corridor:
    """Представляет коридор, соединяющий комнаты."""

    def __init__(self):
        self.segments: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []
        self.is_visited = False

    def add_segment(self, from_point: Tuple[int, int], to_point: Tuple[int, int]) -> None:
        """Добавляет сегмент коридора."""
        self.segments.append((from_point, to_point))

    def get_segments(self) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Возвращает все сегменты коридора."""
        return self.segments.copy()

    def to_dict(self) -> dict:
        return {
            'segments': [
                [list(from_point), list(to_point)] for from_point, to_point in self.segments
            ],
            'is_visited': self.is_visited
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Corridor':
        corridor = cls()
        corridor.is_visited = data.get('is_visited', False)
        for segment in data.get('segments', []):
            from_point = tuple(segment[0])
            to_point = tuple(segment[1])
            corridor.add_segment(from_point, to_point)
        return corridor

    def in_corridor(self, x: int, y: int) -> bool:
        """ Возвращает истину если координаты x,y принадлежат коридору
        """
        for segment in self.segments:
            from_point, to_point = segment

            # Вертикальный сегмент (x одинаковый, y меняется)
            if from_point[0] == to_point[0]:  # x фиксирован
                if from_point[0] == x:  # проверяем, что x совпадает
                    if min(from_point[1], to_point[1]) <= y <= max(from_point[1], to_point[1]):
                        return True
            # Горизонтальный сегмент (y одинаковый, x меняется)
            if from_point[1] == to_point[1]:  # y фиксирован
                if from_point[1] == y:  # проверяем, что y совпадает
                    if min(from_point[0], to_point[0]) <= x <= max(from_point[0], to_point[0]):
                        return True
        return False


class Layer:
    """Представляет слой подземелья (только коридоры и стены)."""

    def __init__(self, field_width: int, field_height: int, target_cells: int):
        self.width = field_width
        self.height = field_height
        self.target_cells = target_cells
        self.rows = int(self.target_cells ** 0.5)
        self.cols = (self.target_cells + self.rows - 1) // self.rows
        self.rooms: List[Room] = []
        self.corridors: List[Corridor] = []
        self.exit: Tuple[int, int]

    def get_exit(self) -> Tuple[int, int]:
        return self.exit

    def generate_exit_position(self) -> None:
        finish_room = self.get_finish_room()
        self.exit = (finish_room.x + random.randint(0, finish_room.width - 1),
                     finish_room.y + random.randint(0, finish_room.height - 1))

    def get_start_room(self) -> Optional[Room]:
        """Возвращает стартовую комнату."""
        for room in self.rooms:
            if room.is_start:
                return room
        return self.rooms[0] if self.rooms else None

    def get_finish_room(self) -> Optional[Room]:
        """Возвращает финишную комнату."""
        for room in self.rooms:
            if room.is_finish:
                return room
        return self.rooms[-1] if self.rooms else None

    def get_player_spawn_position(self) -> Tuple[int, int]:
        """Возвращает позицию спавна игрока (центр стартовой комнаты)."""
        room = self.get_start_room()
        room.is_visited = True
        if room:
            return (room.x + random.randint(0, room.width - 1), room.y + random.randint(0, room.height - 1))
        return (0, 0)

    def get_random_spawn_position_in_room(self, room_index: int = None) -> Tuple[int, int]:
        """Возвращает позицию спавна в центре случайной комнаты.

        Args:
            room_index: индекс комнаты (если None, выбирается случайная)

        Returns:
            Координаты центра комнаты
        """
        if not self.rooms:
            return (0, 0)

        if room_index is None:
            room_index = random.randint(0, len(self.rooms) - 1)

        room = self.rooms[room_index] if 0 <= room_index < len(
            self.rooms) else None
        if room:
            return (room.x + random.randint(0, room.width - 1),
                    room.y + random.randint(0, room.height - 1))
        return (0, 0)

    def get_finish_position(self) -> Tuple[int, int]:
        """Возвращает позицию финиша (центр финишной комнаты)."""
        room = self.get_finish_room()
        if room:
            return (room.x + room.width // 2, room.y + room.height // 2)
        return (self.width - 1, self.height - 1)

    def is_passable(self, x: int, y: int) -> bool:
        """Проверяет, проходима ли позиция (в коридорах или комнатах).

        Args:
            x: координата X
            y: координата Y

        Returns:
            True если позиция в коридоре или комнате
        """
        for corridor in self.corridors:
            for segment in corridor.segments:
                from_point, to_point = segment

                # Вертикальный сегмент (x одинаковый, y меняется)
                if from_point[0] == to_point[0]:  # x фиксирован
                    if from_point[0] == x:  # проверяем, что x совпадает
                        if min(from_point[1], to_point[1]) <= y <= max(from_point[1], to_point[1]):
                            return True

                # Горизонтальный сегмент (y одинаковый, x меняется)
                if from_point[1] == to_point[1]:  # y фиксирован
                    if from_point[1] == y:  # проверяем, что y совпадает
                        if min(from_point[0], to_point[0]) <= x <= max(from_point[0], to_point[0]):
                            return True

        for room in self.rooms:
            if (room.x <= x < room.x + room.width) and (room.y <= y < room.y + room.height):
                return True

        return False

    def add_room(self, room: Room) -> None:
        """Добавляет комнату на слой."""
        if room:
            self.rooms.append(room)

    def add_corridor(self, corridor: Corridor) -> None:
        """Добавляет коридор на слой."""
        if corridor:
            self.corridors.append(corridor)

    def get_rooms_count(self) -> int:
        """Возвращает количество комнат."""
        return len(self.rooms)

    def get_corridors_count(self) -> int:
        """Возвращает количество коридоров."""
        return len(self.corridors)

    def to_dict(self) -> dict:
        return {
            'width': self.width,
            'height': self.height,
            'target_cells': self.target_cells,
            'rows': self.rows,
            'cols': self.cols,
            'rooms': [room.to_dict() for room in self.rooms],
            'corridors': [corridor.to_dict() for corridor in self.corridors],
            'exit': list(self.exit) if self.exit else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Layer':
        layer = cls(
            data['width'],
            data['height'],
            data['target_cells']
        )
        layer.rows = data.get('rows', layer.rows)
        layer.cols = data.get('cols', layer.cols)
        for room in data.get('rooms', []):
            layer.rooms.append(Room.from_dict(room))
        for corridor in data.get('corridors', []):
            layer.corridors.append(Corridor.from_dict(corridor))
        exit_data = data.get('exit')
        layer.exit = tuple(exit_data) if exit_data else None
        return layer

    # Методы для тумана войны

    def war_fog(self, x: int, y: int) -> None:
        """ Основной метод, который запускает туман войны
        Используется послеи каждого шага героя в методе move_hero.
        Args:
            x: координата X героя
            y: координата Y героя
        """

        room = self.hero_visit(x, y)
        if room is not None:
            room.get_visible_area(x, y)

    def hero_visit(self, x: int, y: int) -> Optional[Room]:
        """Помечает комнату или коридор как просмотренные после посещения героя,
        возвращает комнату, если герой стоит на ее пороге (для тумана войны).

        Args:
            x: координата X
            y: координата Y
        Return:
            Room: если стоим на пороге этой комнаты
            None: во всех остальных случаях

        """
        for corridor in self.corridors:
            if corridor.in_corridor(x, y):
                corridor.is_visited = True
                # Проверим не в конце ли коридора мы стоим(т.е. в проеме стены неизведанной комнаты)
                for room in self.rooms:
                    if not room.is_visited and (room.in_room(x + 1, y) or room.in_room(x, y + 1) or room.in_room(x - 1, y) or room.in_room(x, y - 1)):
                        return room
                return None

        for room in self.rooms:
            if room.in_room(x, y):
                room.is_visited = True
                if not room.saved_exits:
                    room.discover_exits(self)
                return None

    def index_position(self, x: int, y: int) -> Tuple[int, int]:
        """Возвращает индекс комнаты или коридора по координатам (для тумана войны).
        Используется при создании тилемапа.

        Args:
            x: координата X
            y: координата Y

        """
        index_pos = (-1, -1)
        rooms = self.rooms
        for i in range(8):
            if rooms[i].in_room(x, y):
                index_pos = (i, -1)
                return index_pos
            else:
                corridors = self.corridors
                for i in range(len(corridors)):
                    if corridors[i].in_corridor(x, y):
                        index_pos = (-1, i)
                        return index_pos
        return index_pos


def bresenham_line(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """
    Алгоритм Брезенхэма для построения линии между двумя точками
    Возвращает список координат точек на линии (включая начальную и конечную)
    """
    points = []

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)

    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1

    err = dx - dy

    while True:
        points.append((x0, y0))

        if x0 == x1 and y0 == y1:
            break

        e2 = 2 * err

        if e2 > -dy:
            err -= dy
            x0 += sx

        if e2 < dx:
            err += dx
            y0 += sy

    return points
