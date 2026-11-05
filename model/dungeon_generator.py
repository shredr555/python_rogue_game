"""Генераторы подземелья - комнаты, коридоры."""

import random
from typing import List, Tuple
from model.dungeon_structures import Room, Corridor, Layer
from constants import *


class SimpleRoomGenerator:
    """Генерирует простые случайные комнаты в сеточном макете."""

    def generate_rooms(self, layer: Layer) -> None:
        """Генерирует комнаты, случайно размещая их в ячейках сетки."""
        cell_width = (layer.width // layer.cols) - 1
        cell_height = (layer.height // layer.rows) - 1

        for r in range(layer.rows):
            for c in range(layer.cols):
                self._generate_room_in_cell(
                    layer, r, c, cell_width, cell_height
                )

    def _generate_room_in_cell(self, layer: Layer, r: int, c: int,
                               cell_width: int, cell_height: int) -> None:
        """Генерирует отдельную комнату в ячейке сетки."""
        cell_x = cell_width * c
        cell_y = cell_height * r
        cell_center_x = cell_x + cell_width // 2
        cell_center_y = cell_y + cell_height // 2

        room_x = random.randint(cell_x + 1, cell_center_x)
        room_y = random.randint(cell_y + 1, cell_center_y)

        room_width = self._calculate_dimension(cell_x, room_x, cell_width)
        room_height = self._calculate_dimension(cell_y, room_y, cell_height)

        layer.add_room(Room(room_x, room_y, room_width, room_height))

    @staticmethod
    def _calculate_dimension(cell_start: int, room_start: int, cell_size: int) -> int:
        """Вычисляет размер комнаты с минимальным ограничением."""
        max_size = cell_start - room_start + cell_size - 1
        return random.randint(MIN_ROOM_SIZE, max(MIN_ROOM_SIZE, max_size))


class DisjointSet:
    """Структура данных Union-Find для алгоритма Краскала."""

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        """Находит корень элемента со сжатием пути."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        """Объединяет два набора, используя эвристику ранга."""
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return False

        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1

        return True


class CorridorBuilder:
    """Генерирует коридоры, используя алгоритм Краскала с MST."""

    def __init__(self, extra_edges_percent: float = EXTRA_EDGES_DEFAULT_PERCENT):
        self.extra_edges_percent = extra_edges_percent

    def generate_corridors(self, layer: Layer) -> None:
        """Генерирует коридоры, соединяющие комнаты."""
        edges = self._build_edges(layer)
        edges.sort(key=lambda e: e[0])

        mst_edges, all_edges = self._compute_mst(edges, layer)
        selected_edges = self._select_edges(mst_edges, all_edges)

        for u, v in selected_edges:
            corridor = self._create_corridor_between(
                layer.rooms[u], layer.rooms[v], layer.width, layer.height)
            layer.add_corridor(corridor)

    def _build_edges(self, layer: Layer) -> List[Tuple[float, int, int]]:
        """Строит взвешенные ребра между соседними комнатами в сетке."""
        edges = []
        num_rooms = len(layer.rooms)

        # Горизонтальные рёбра
        for r in range(layer.rows):
            for c in range(layer.cols - 1):
                idx1, idx2 = r * layer.cols + c, r * layer.cols + c + 1
                if idx2 < num_rooms:
                    edges.append((random.random(), idx1, idx2))

        # Вертикальные рёбра
        for r in range(layer.rows - 1):
            for c in range(layer.cols):
                idx1, idx2 = r * layer.cols + c, (r + 1) * layer.cols + c
                if idx2 < num_rooms:
                    edges.append((random.random(), idx1, idx2))

        return edges

    def _compute_mst(self, edges: List[Tuple[float, int, int]],
                     layer: Layer) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """Вычисляет минимальное остовное дерево."""
        dsu = DisjointSet(len(layer.rooms))
        mst_edges = []
        all_edges = []

        for weight, u, v in edges:
            all_edges.append((u, v))
            if dsu.union(u, v):
                mst_edges.append((u, v))

        return mst_edges, all_edges

    def _select_edges(self, mst_edges: List[Tuple[int, int]],
                      all_edges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Выбирает MST ребра плюс дополнительные."""
        unused_edges = [e for e in all_edges if e not in mst_edges]
        extra_count = int(len(unused_edges) * self.extra_edges_percent)

        if extra_count > 0 and unused_edges:
            extra = random.sample(unused_edges, min(
                extra_count, len(unused_edges)))
            return mst_edges + extra

        return mst_edges

    def _create_corridor_between(self, room_a: Room, room_b: Room,
                                 max_x: int, max_y: int) -> Corridor:
        """Создает коридор, соединяющий две комнаты."""
        start, end = self._find_best_connection(room_a, room_b, max_x, max_y)
        wall_a = self._get_wall_point(room_a, start[0], start[1])
        wall_b = self._get_wall_point(room_b, end[0], end[1])

        return self._build_corridor_path(wall_a, start, end, wall_b)

    def _build_corridor_path(self, wall_a: Tuple[int, int], start: Tuple[int, int],
                             end: Tuple[int, int], wall_b: Tuple[int, int]) -> Corridor:
        """Строит путь коридора с L-образной формой."""
        corridor = Corridor()

        if random.choice([True, False]):
            # Сначала горизонтально, потом вертикально
            corridor.add_segment(wall_a, (start[0], start[1]))
            corridor.add_segment((start[0], start[1]), (end[0], start[1]))
            corridor.add_segment((end[0], start[1]), (end[0], end[1]))
            corridor.add_segment((end[0], end[1]), wall_b)
        else:
            # Сначала вертикально, потом горизонтально
            corridor.add_segment(wall_a, (start[0], start[1]))
            corridor.add_segment((start[0], start[1]), (start[0], end[1]))
            corridor.add_segment((start[0], end[1]), (end[0], end[1]))
            corridor.add_segment((end[0], end[1]), wall_b)

        return corridor

    def _find_best_connection(self, room_a: Room, room_b: Room,
                              max_x: int, max_y: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Находит лучшую пару точек для соединения комнат."""
        points_a = self._get_exit_points(room_a, max_x, max_y)
        points_b = self._get_exit_points(room_b, max_x, max_y)

        best_pair = min(
            ((pa, pb) for pa in points_a for pb in points_b),
            key=lambda pair: self._manhattan_distance(pair[0], pair[1])
        )
        return best_pair

    def _get_exit_points(self, room: Room, max_x: int, max_y: int) -> List[Tuple[int, int]]:
        """Создает список координат центров каждой стены у комнаты."""
        room_center_x = room.x + room.width // 2
        room_center_y = room.y + room.height // 2

        points = []
        if room.y >= WALL_BUFFER + 1:
            points.append((room_center_x, room.y - WALL_BUFFER - 1))
        if room.y + room.height + WALL_BUFFER < max_y:
            points.append((room_center_x, room.y + room.height + WALL_BUFFER))
        if room.x >= WALL_BUFFER + 1:
            points.append((room.x - WALL_BUFFER - 1, room_center_y))
        if room.x + room.width + WALL_BUFFER < max_x:
            points.append((room.x + room.width + WALL_BUFFER, room_center_y))
        return points

    @staticmethod
    def _manhattan_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
        """Вычисляет расстояние Манхэттена между двумя точками."""
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def _get_wall_point(self, room: Room, ext_x: int, ext_y: int) -> Tuple[int, int]:
        """Находит точку на стене комнаты."""
        room_center_x = room.x + room.width // 2
        room_center_y = room.y + room.height // 2

        if ext_x < room.x:
            return (room.x - 1, room_center_y)
        elif ext_x > room.x + room.width - 1:
            return (room.x + room.width, room_center_y)
        elif ext_y < room.y:
            return (room_center_x, room.y - 1)
        else:
            return (room_center_x, room.y + room.height)


class DungeonGenerator:
    """Высокоуровневый генератор подземелья."""

    def __init__(self, room_generator: SimpleRoomGenerator,
                 corridor_generator: CorridorBuilder):
        self.room_generator = room_generator
        self.corridor_generator = corridor_generator

    def generate(self, width: int, height: int, target_rooms: int) -> Layer:
        """Генерирует полный слой подземелья.

        Args:
            width: ширина подземелья
            height: высота подземелья
            target_rooms: целевое количество комнат

        Returns:
            Layer объект с комнатами и коридорами
        """
        layer = Layer(width, height, target_rooms)
        self.room_generator.generate_rooms(layer)
        self.corridor_generator.generate_corridors(layer)

        if layer.rooms:
            layer.rooms[0].is_start = True
            layer.rooms[-1].is_finish = True

        return layer
