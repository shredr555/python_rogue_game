from .item import Item, ItemType
from typing import List


class Backpack:
    """Рюкзак для хранения предметов."""

    def __init__(self):
        self.items: List[Item] = []

    def add_item(self, item: Item) -> None:
        """Добавляет предмет в рюкзак."""
        if item:
            self.items.append(item)

    def remove_item(self, item: Item) -> bool:
        """Удаляет предмет из рюкзака.

        Returns:
            True если предмет удален, False если его нет
        """
        try:
            self.items.remove(item)
            return True
        except ValueError:
            return False

    def get_items(self) -> List[Item]:
        """Возвращает список всех предметов."""
        return self.items.copy()

    def clear(self) -> None:
        """Очищает рюкзак."""
        self.items.clear()

    def check_treasure(self) -> bool:
        for item in self.items:
            if item.type == ItemType.TREASURE:
                return True
        return False

    def to_dict(self) -> dict:
        return {
            'items': [item.to_dict() for item in self.items]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Backpack":
        backpack = cls()
        backpack.items = [Item.from_dict(i) for i in data.get('items', [])]
        return backpack
