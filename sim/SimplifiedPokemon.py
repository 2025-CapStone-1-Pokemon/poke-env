import copy
from typing import Optional, Tuple, Dict
from poke_env.battle.pokemon import Pokemon
# 포켓몬 타입 객체
from poke_env.battle.pokemon_type import PokemonType
# 포켓몬 기술 객체
from poke_env.battle.move import SPECIAL_MOVES, Move
# 포켓몬 성별 객체
from poke_env.battle.pokemon_gender import PokemonGender
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from supporting.PokemonStatus import Status
from SimplifiedMove import SimplifiedMove
from poke_env.data import GenData

class SimplifiedPokemon:
    _GEN_DATA_CACHE = {}
    
    def __init__(self, poke_env_pokemon: Pokemon, is_percentage_hp: bool = False):
        # 기본 정보
        self.species = poke_env_pokemon.species
        self.level = poke_env_pokemon.level
        self.gender = poke_env_pokemon.gender

        # 일시적인 배틀 상태 관리
        self.volatiles = {}

        # 타입
        self.type_1 = poke_env_pokemon.type_1
        self.type_2 = poke_env_pokemon.type_2
        self.types = poke_env_pokemon.types.copy()  # List

        # HP
        if is_percentage_hp:
            # poke_env_pokemon.current_hp가 백분율인 경우 레벨 기반으로 계산
            base_hp = poke_env_pokemon.base_stats.get('hp', 100)
            max_hp_calculated = (2 * base_hp * poke_env_pokemon.level / 100) + poke_env_pokemon.level + 26
            self.max_hp = int(max_hp_calculated)
            # current_hp가 백분율이면 max_hp 기준으로 계산
            self.current_hp = int(poke_env_pokemon.current_hp * self.max_hp / 100)
        else:
            # 실제 HP 값인 경우 그대로 사용
            self.current_hp = poke_env_pokemon.current_hp
            self.max_hp = poke_env_pokemon.max_hp

        # 상태이상
        self.status = poke_env_pokemon.status
        self.status_counter = poke_env_pokemon.status_counter
        self.toxic_counter = 0  # 강독 카운터

        # 스탯
        self.base_stats = poke_env_pokemon.base_stats.copy()
        self.stats = poke_env_pokemon.stats.copy()
        self.boosts = poke_env_pokemon.boosts.copy()
        
        # 능력치 변화 타이머 (해제될 때까지의 턴 수)
        # None = 배틀 종료까지 유지, 숫자 = N턴 지속
        self.boost_timers = {}  # {"atk": None, "spe": 5, ...}

        # 기술 (moves가 dict 또는 list일 수 있음)
        if isinstance(poke_env_pokemon.moves, dict):
            self.moves = [SimplifiedMove(move) for move in poke_env_pokemon.moves.values()]
        else:
            # list인 경우 그대로 사용
            self.moves = [SimplifiedMove(move) for move in poke_env_pokemon.moves]

        # 특성 및 아이템
        self.ability = poke_env_pokemon.ability
        self.item = poke_env_pokemon.item

        # 효과
        self.effects = poke_env_pokemon.effects.copy()

        # 배틀 상태
        self.active = poke_env_pokemon.active
        self.first_turn = poke_env_pokemon.first_turn
        self.must_recharge = poke_env_pokemon.must_recharge
        self.protect_counter = poke_env_pokemon.protect_counter
        
        # 성능 최적화: get_effective_stat() 캐싱
        self._stat_cache = {}


    def damage(self, amount: int):
        """데미지 받기"""
        self.current_hp = max(0, self.current_hp - amount)
        if self.current_hp == 0:
            self.faint()

    def heal(self, amount: int):
        """회복"""
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    def faint(self):
        """기절"""
        self.current_hp = 0
        self.status = Status.FNT
        self.active = False

    def boost(self, stat: str, amount: int):
        """능력치 변화"""
        current = self.boosts.get(stat, 0)
        self.boosts[stat] = max(-6, min(6, current + amount))

    def set_boost_with_timer(self, stat: str, amount: int, turns: Optional[int] = None):
        """능력치 변화 (타이머 포함)
        
        Args:
            stat: 능력치 ('atk', 'def', 'spe', 'spa', 'spd', 'accuracy', 'evasion')
            amount: 변화량 (+2, -1 등)
            turns: 지속 턴 수 (None = 배틀 종료까지 영구)
        """
        # deepcopy 후 boost_timers가 없으면 초기화
        if not hasattr(self, 'boost_timers'):
            self.boost_timers = {}
        
        self.boost(stat, amount)
        if turns is None:
            # 영구 유지 (해제하지 않음)
            self.boost_timers[stat] = None
        else:
            # N턴 지속
            self.boost_timers[stat] = turns

    def decrement_boost_timers(self):
        """턴 종료 시 능력치 타이머 감소 및 해제"""
        # boost_timers 없으면 초기화 (호환성)
        if not hasattr(self, 'boost_timers'):
            self.boost_timers = {}
        
        stats_to_reset = []
        
        for stat, turns_left in self.boost_timers.items():
            if turns_left is None:
                # 영구 유지
                continue
            
            # 턴 감소
            turns_left -= 1
            
            if turns_left <= 0:
                # 타이머 만료 → boost 해제
                stats_to_reset.append(stat)
            else:
                # 남은 턴 업데이트
                self.boost_timers[stat] = turns_left
        
        # 만료된 능력치 리셋
        for stat in stats_to_reset:
            current = self.boosts.get(stat, 0)
            self.boosts[stat] = 0
            del self.boost_timers[stat]

    def damage_multiplier(self, move_type: PokemonType) -> float:
        """타입 상성 계산"""
        
        # 캐시에서 GenData 가져오기
        if 9 not in self._GEN_DATA_CACHE:
            self._GEN_DATA_CACHE[9] = GenData.from_gen(9)
        
        gen_data = self._GEN_DATA_CACHE[9]
        
        # gen_data.type_chart 사용
        multiplier = 1.0
        for poke_type in self.types:
            multiplier *= poke_type.damage_multiplier(
                move_type,
                type_chart=gen_data.type_chart 
            )
        
        return multiplier

    # TODO 여기서 계산매번하는게 맞나
    def get_effective_stat(self, stat_name: str) -> float:
        """능력치 변화 반영한 실제 스탯"""

        base = self.stats.get(stat_name)
        
        # stats가 None이면 base_stats에서 가져오고 레벨 보정 적용
        if base is None:
            base = self.base_stats.get(stat_name, 100)  # 기본값 100
            # 레벨 보정 공식 적용
            if stat_name == 'hp':
                base = int(((2 * base * self.level) / 100) + self.level + 10)
            else:
                base = int(((2 * base * self.level) / 100) + 5)
        
        # 여전히 None이면 기본값 사용
        if base is None:
            base = 100
        
        boost = self.boosts.get(stat_name, 0)

        if boost >= 0:
            multiplier = (2 + boost) / 2
        else:
            multiplier = 2 / (2 - boost)

        # 상태이상 보정
        if stat_name == 'atk' and self.status == Status.BRN:
            multiplier *= 0.5
        if stat_name == 'spe' and self.status == Status.PAR:
            multiplier *= 0.5

        return base * multiplier
    
    def print_summary(self):
        """포켓몬 정보 출력"""
        
        print("Pokemon Summary:")
        print(f" Species: {self.species}")
        print(f" Level: {self.level}")
        print(f" Gender: {self.gender}")
        print(f" Types: {[t.name for t in self.types]}")
        print(f" HP: {self.current_hp}/{self.max_hp}")
        print(f" Status: {self.status}")
        print(f" Stats: {self.stats}")
        print(f" Boosts: {self.boosts}")
        print(f" Ability: {self.ability}")
        print(f" Item: {self.item}")
        print(" Moves:")
        for move in self.moves:
            print(move.id , move.current_pp, move.max_pp)