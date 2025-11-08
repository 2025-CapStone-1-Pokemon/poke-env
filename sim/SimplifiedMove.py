# SimplifiedMove.py
from poke_env.battle.move import Move
from supporting.PokemonType import PokemonType
from supporting.PokemonMoveCategory import MoveCategory
from typing import Dict, Optional

class SimplifiedMove:
    def __init__(self, poke_env_move: Move):
        # 기본 정보
        self.id = poke_env_move.id
        self.base_power = poke_env_move.base_power
        self.type = poke_env_move.type
        self.category = poke_env_move.category
        self.accuracy = poke_env_move.accuracy
        self.priority = poke_env_move.priority

        # PP
        self.current_pp = poke_env_move.current_pp
        self.max_pp = poke_env_move.max_pp

        # 추가 효과
        self.boosts = poke_env_move.boosts
        self.self_boost = poke_env_move.self_boost
        self.status = poke_env_move.status
        self.secondary = poke_env_move.secondary

        # 데미지 관련 (불변)
        self.crit_ratio = poke_env_move.crit_ratio
        self.expected_hits = poke_env_move.expected_hits
        self.recoil = poke_env_move.recoil
        self.drain = poke_env_move.drain

        # 플래그 (불변)
        self.flags = poke_env_move.flags.copy()
        self.breaks_protect = poke_env_move.breaks_protect
        self.is_protect_move = poke_env_move.is_protect_move

    def use(self):
        """PP 소모"""
        self.current_pp = max(0, self.current_pp - 1)