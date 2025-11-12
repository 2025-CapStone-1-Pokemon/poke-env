import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sim'))

from sim.SimplifiedBattle import SimplifiedBattle
from sim.SimplifiedMove import SimplifiedMove
from sim.SimplifiedPokemon import SimplifiedPokemon

class DumbActionsFilter:
    """
    포켓몬 배틀에 유용한 휴리스틱(전략)을 기반으로 액션을 필터링.
    
    전략들:
    1. 초반턴에는 무리한 교체 회피 (상성이 극도로 나쁘지 않은 이상)
    2. 현재 포켓몬이 높은 체력을 유지하면 교체 회피
    3. 공격기술이 있으면 우선적으로 시도
    4. 교체는 상성이 매우 나쁘거나 체력이 위험할 때만
    """
    
    # 클래스 변수: 타입 차트 (한 번만 로드)
    _type_chart = None

    def __init__(self, battle: SimplifiedBattle, actions):
        """
        Args:
            battle: SimplifiedBattle 객체
            actions: SimplifiedMove 또는 SimplifiedPokemon 리스트
        """
        self.battle = battle
        self.available_moves = [action for action in actions if isinstance(action, SimplifiedMove)]
        self.available_switches = [action for action in actions if isinstance(action, SimplifiedPokemon)]
        
        # 타입 차트 로드
        if DumbActionsFilter._type_chart is None:
            self._load_type_chart()

    
    @classmethod
    def _load_type_chart(cls):
        """poke-env의 type_chart.json 로드"""
        try:
            # type_chart.json 위치: poke-env/type_chart.json
            type_chart_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'type_chart.json'
            )
            with open(type_chart_path, 'r') as f:
                cls._type_chart = json.load(f)
        except Exception as e:
            print(f"경고: 타입 차트 로드 실패: {e}")
            cls._type_chart = {}

    
    def _get_type_effectiveness(self, attacking_type, defending_type):
        """
        공격 타입이 방어 타입에 얼마나 효과적인지 반환.
        
        Args:
            attacking_type: 공격 포켓몬의 타입 (string)
            defending_type: 방어 포켓몬의 타입 (string)
            
        Returns:
            float: 1.0 (보통), 2.0 (효과적), 0.5 (저항), 0 (면역)
        """
        if not DumbActionsFilter._type_chart:
            return 1.0
        
        attacking_type = attacking_type.lower() if attacking_type else None
        defending_type = defending_type.lower() if defending_type else None
        
        if attacking_type and defending_type:
            return DumbActionsFilter._type_chart.get(attacking_type, {}).get(defending_type, 1.0)
        
        return 1.0

    
    def _is_bad_matchup(self, my_pokemon, opp_pokemon, severity_threshold=0.5):
        """
        현재 포켓몬이 상대 포켓몬과의 상성이 나쁜지 판단.
        
        Args:
            my_pokemon: 내 포켓몬
            opp_pokemon: 상대 포켓몬
            severity_threshold: 상성이 '나쁜' 것으로 판단할 임계값
            
        Returns:
            bool: True면 상성이 나쁨
        """
        if not my_pokemon or not opp_pokemon:
            return False
        
        # 내 타입 vs 상대 타입 체크
        my_types = [getattr(my_pokemon, 'type_1', None), getattr(my_pokemon, 'type_2', None)]
        opp_type = getattr(opp_pokemon, 'type_1', None)
        
        # 상대 기술이 내 타입에 효과적인지 확인
        worst_effectiveness = 1.0
        for my_type in my_types:
            if my_type:
                effectiveness = self._get_type_effectiveness(opp_type, my_type)
                worst_effectiveness = max(worst_effectiveness, effectiveness)
        
        # 체력 비율 확인
        my_hp_ratio = my_pokemon.current_hp / max(my_pokemon.max_hp, 1) if hasattr(my_pokemon, 'current_hp') else 1.0
        my_speed = getattr(my_pokemon, 'speed', 1)
        opp_speed = getattr(opp_pokemon, 'speed', 1)
        
        # 상대가 훨씬 빠르고, 상성이 나쁘고, 체력이 낮으면 나쁜 매치업
        is_slow = opp_speed > my_speed * 1.2
        is_weak_type = worst_effectiveness >= 2.0
        is_low_hp = my_hp_ratio < 0.4
        
        return is_slow and is_weak_type and is_low_hp

    
    def filter(self, actions):
        """
        포켓몬 배틀 휴리스틱을 기반으로 액션을 필터링.
        
        Args:
            actions: SimplifiedMove 또는 SimplifiedPokemon 리스트
            
        Returns:
            필터링된 액션 리스트 (또는 원본 리스트)
        """
        if not actions:
            return actions
        
        moves = [a for a in actions if isinstance(a, SimplifiedMove)]
        switches = [a for a in actions if isinstance(a, SimplifiedPokemon)]
        
        current_turn = getattr(self.battle, 'turn', 0)
        my_pokemon = self.battle.active_pokemon if hasattr(self.battle, 'active_pokemon') else None
        opp_pokemon = self.battle.opponent_active_pokemon if hasattr(self.battle, 'opponent_active_pokemon') else None
        
        # 전략 1: 초반턴(1-2턴)에는 교체 회피
        if current_turn <= 2 and moves:
            return moves
        
        # 전략 2: 현재 포켓몬이 체력이 높으면 교체 회피
        if my_pokemon and hasattr(my_pokemon, 'current_hp') and hasattr(my_pokemon, 'max_hp'):
            hp_ratio = my_pokemon.current_hp / max(my_pokemon.max_hp, 1)
            if hp_ratio > 0.6 and moves:
                # 기술을 우선적으로 (MCTS에서 탐색)
                return moves
        
        # 전략 3: 상성이 극도로 나쁘면 교체 고려
        if self._is_bad_matchup(my_pokemon, opp_pokemon) and switches:
            # 교체를 우선적으로
            return switches + moves
        
        
        # 기본: 모든 액션 반환 (MCTS가 판단하도록)
        return actions