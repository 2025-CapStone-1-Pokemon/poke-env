# SimplifiedMove.py
from poke_env.battle.move import Move
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

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
        
        # 정확도 정규화 (poke-env에서 0-100 또는 0-1.0으로 올 수 있음)
        raw_accuracy = poke_env_move.accuracy
        if raw_accuracy is None:
            self.accuracy = None  # 100% 명중
        elif raw_accuracy > 1:
            self.accuracy = raw_accuracy / 100.0  # 0-100 형식 → 0-1.0으로 변환
        else:
            self.accuracy = raw_accuracy  # 이미 0-1.0 형식
        
        # Priority (안전한 접근 - entry에 없을 수 있음)
        try:
            self.priority = poke_env_move.priority
        except (KeyError, AttributeError):
            self.priority = 0  # 기본값: 일반 우선도

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
        try:
            self.flags = poke_env_move.flags.copy() if poke_env_move.flags else {}
        except (KeyError, AttributeError):
            self.flags = {}
        
        try:
            self.breaks_protect = poke_env_move.breaks_protect
        except (KeyError, AttributeError):
            self.breaks_protect = False
        
        try:
            self.is_protect_move = poke_env_move.is_protect_move
        except (KeyError, AttributeError):
            self.is_protect_move = False

    def use(self):
        """PP 소모"""
        self.current_pp = max(0, self.current_pp - 1)