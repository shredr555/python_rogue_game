import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from model.game_session import GameSession
from model.entities import Hero, Enemy, Item
from model.dungeon_structures import Layer
from model.game_statistics import GameStatistics


SAVEFILE = 'save_game.json'
STATSFILE = 'stats.json'


class SaveManager:
    @staticmethod
    def save_session(session: GameSession) -> None:
        data = {
            'current_level': session.current_level,
            'enemy_probability': session.enemy_probability,
            'item_probability': session.item_probability,
            'hero': session.hero.to_dict() if session.hero else None,
            'layer': session.current_layer.to_dict() if session.current_layer else None,
            'enemies': [enemy.to_dict() for enemy in session.enemies],
            'items': [item.to_dict() for item in session.items]
        }
        with open(SAVEFILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def load_session() -> Optional['GameSession']:
        if not os.path.exists(SAVEFILE):
            return None

        with open(SAVEFILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        from model.game_session import GameSession
        from model.entities import Hero, Enemy, Item
        from model.dungeon_structures import Layer

        session = GameSession()
        session.current_level = data['current_level']
        session.enemy_probability = data['enemy_probability']
        session.item_probability = data['item_probability']
        session.is_active = True
        if data['hero']:
            session.hero = Hero.from_dict(data['hero'])
        if data['layer']:
            session.current_layer = Layer.from_dict(data['layer'])
        session.enemies = [Enemy.from_dict(e) for e in data['enemies']]
        session.items = [Item.from_dict(e) for e in data['items']]
        return session

    @staticmethod
    def save_statistics(statistics: GameStatistics) -> None:
        """Сохраняет статистику всех прохождений.

        Args:
            statistics: объект с статистикой
        """
        data = {
            'sessions': statistics.to_dict_list()
        }
        with open(STATSFILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def load_statistics() -> GameStatistics:
        """Загружает статистику всех прохождений.

        Returns:
            Объект GameStatistics с загруженными данными
        """
        if not os.path.exists(STATSFILE):
            return GameStatistics()

        try:
            with open(STATSFILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return GameStatistics.from_dict_list(data.get('sessions', []))
        except (json.JSONDecodeError, IOError):
            return GameStatistics()
