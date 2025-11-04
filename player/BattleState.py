import copy
import json
import random
from typing import Dict, List, Optional, Any

class BattleState:
    """
    시뮬레이션용 경량 배틀 상태
    
    주요 기능:
    1. poke-env Battle 객체에서 정보 추출
    2. 상태 복사 가능 (clone)
    3. 액션 시뮬레이션 (apply_move, apply_switch)
    """
    
    # 타입 차트 로드 (클래스 변수)
    TYPE_CHART = None
    
    @classmethod
    def load_type_chart(cls):
        """타입 차트를 파일에서 로드"""
        if cls.TYPE_CHART is None:
            with open('type_chart.json', 'r') as f:
                cls.TYPE_CHART = json.load(f)
    
    def __init__(self, battle=None, state_dict=None):
        """
        초기화 방법:
        1. battle 객체에서 생성 (최초)
        2. state_dict로 복사 (시뮬레이션)
        """
        # 타입 차트 로드
        if BattleState.TYPE_CHART is None:
            BattleState.load_type_chart()
        
        if battle:
            # poke-env Battle에서 정보 추출
            self.my_team = self._extract_team(battle.team)
            self.opp_team = self._extract_team(battle.opponent_team)
            self.my_active_idx = self._find_active_index(battle.team)
            self.opp_active_idx = self._find_active_index(battle.opponent_team)
            self.weather = str(battle.weather) if battle.weather else None
        else:
            # 복사본 생성 (deepcopy된 데이터)
            self.my_team = state_dict['my_team']
            self.opp_team = state_dict['opp_team']
            self.my_active_idx = state_dict['my_active_idx']
            self.opp_active_idx = state_dict['opp_active_idx']
            self.weather = state_dict['weather']
    
    def _extract_team(self, team_dict: Dict) -> List[Dict]:
        """
        Pokemon 객체에서 필요한 정보만 추출
        
        추출하는 정보:
        - species, hp_fraction, fainted
        - types, stats, boosts
        - status, active
        """
        team = []
        for pokemon in team_dict.values():
            # types를 문자열로 변환 (PokemonType.FIRE -> 'fire')
            types = []
            for t in pokemon.types:
                if t is not None:
                    # PokemonType enum을 문자열로
                    type_name = str(t).split('.')[-1].lower()
                    types.append(type_name)
            
            team.append({
                'species': pokemon.species,
                'hp_fraction': pokemon.current_hp_fraction,  # 0.0 ~ 1.0
                'fainted': pokemon.fainted,
                'types': tuple(types),  # ('fire', 'flying')
                'stats': dict(pokemon.stats),  # {'atk': 100, 'def': 90, ...}
                'boosts': dict(pokemon.boosts),  # {'atk': 1, 'def': 0, ...}
                'status': str(pokemon.status) if pokemon.status else None,
                'active': pokemon.active,
            })
        return team
    
    def _find_active_index(self, team_dict: Dict) -> Optional[int]:
        """활성 포켓몬의 인덱스 찾기"""
        for idx, pokemon in enumerate(team_dict.values()):
            if pokemon.active:
                return idx
        return None
    
    def clone(self) -> 'BattleState':
        """
        현재 상태의 깊은 복사
        
        사용처: MCTS에서 시뮬레이션할 때
        """
        return BattleState(state_dict={
            'my_team': copy.deepcopy(self.my_team),
            'opp_team': copy.deepcopy(self.opp_team),
            'my_active_idx': self.my_active_idx,
            'opp_active_idx': self.opp_active_idx,
            'weather': self.weather,
        })
    
    def apply_move(self, move, is_my_turn=True):
        """
        기술 사용 시뮬레이션
        
        Parameters:
        - move: poke-env Move 객체
        - is_my_turn: True면 내가 공격, False면 상대가 공격
        
        처리 순서:
        1. 보조기 체크 (base_power == 0)
        2. 공격자/방어자 결정
        3. 데미지 계산
        4. HP 업데이트
        5. 기절 처리
        """
        if move.base_power == 0:
            # TODO: 보조기 효과 구현 (능력치 변화 등)
            return
        
        # 공격자와 방어자
        if is_my_turn:
            attacker = self.my_team[self.my_active_idx]
            defender = self.opp_team[self.opp_active_idx]
        else:
            attacker = self.opp_team[self.opp_active_idx]
            defender = self.my_team[self.my_active_idx]
        
        # 이미 기절했으면 무시
        if attacker['fainted'] or defender['fainted']:
            return
        
        # 데미지 계산
        damage_fraction = self._calculate_damage(attacker, defender, move)
        
        # HP 업데이트
        defender['hp_fraction'] = max(0.0, defender['hp_fraction'] - damage_fraction)
        
        # 기절 처리
        if defender['hp_fraction'] <= 0:
            defender['fainted'] = True
            defender['active'] = False
    
    def apply_switch(self, switch_idx: int, is_my_turn=True):
        """
        포켓몬 교체 시뮬레이션
        
        Parameters:
        - switch_idx: 교체할 포켓몬의 팀 내 인덱스 (0~5)
        - is_my_turn: 내 턴인지
        """
        if is_my_turn:
            team = self.my_team
            old_idx = self.my_active_idx
        else:
            team = self.opp_team
            old_idx = self.opp_active_idx
        
        # 교체할 포켓몬이 기절했으면 무시
        if team[switch_idx]['fainted']:
            return
        
        # 이전 포켓몬 비활성화
        if old_idx is not None:
            team[old_idx]['active'] = False
        
        # 새 포켓몬 활성화
        team[switch_idx]['active'] = True
        
        # 인덱스 업데이트
        if is_my_turn:
            self.my_active_idx = switch_idx
        else:
            self.opp_active_idx = switch_idx
    
    def _calculate_damage(self, attacker: Dict, defender: Dict, move) -> float:
        """
        Showdown 데미지 공식 구현
        
        공식:
        Damage = ((2*Level/5 + 2) * Power * A/D / 50 + 2) * Modifiers
        
        Modifiers:
        - 타입 상성
        - STAB (자속보정)
        - 랜덤 (0.85~1.0)
        - 날씨 (선택적)
        
        Returns: HP 감소 비율 (0.0 ~ 1.0)
        """
        level = 50
        power = move.base_power
        
        if power == 0:
            return 0.0
        
        # 공격/방어 스탯 선택
        move_category = str(move.category).upper()
        
        if 'PHYSICAL' in move_category:
            attack = attacker['stats']['atk']
            defense = defender['stats']['def']
            atk_boost = attacker['boosts'].get('atk', 0)
            def_boost = defender['boosts'].get('def', 0)
        elif 'SPECIAL' in move_category:
            attack = attacker['stats']['spa']
            defense = defender['stats']['spd']
            atk_boost = attacker['boosts'].get('spa', 0)
            def_boost = defender['boosts'].get('spd', 0)
        else:
            # STATUS 기술
            return 0.0
        
        # 능력치 변화 적용
        attack = self._apply_boost(attack, atk_boost)
        defense = self._apply_boost(defense, def_boost)
        
        # 기본 데미지 계산
        damage = ((2 * level / 5 + 2) * power * attack / defense / 50 + 2)
        
        # 타입 상성
        move_type = str(move.type).split('.')[-1].lower()
        type_multiplier = self._get_type_effectiveness(move_type, defender['types'])
        damage *= type_multiplier
        
        # STAB (자속보정) - 같은 타입이면 1.5배
        if move_type in attacker['types']:
            damage *= 1.5
        
        # 랜덤 (85% ~ 100%)
        damage *= random.uniform(0.85, 1.0)
        
        # TODO: 날씨 보정
        # if self.weather == 'SUNNYDAY' and move_type == 'fire':
        #     damage *= 1.5
        
        # HP 비율로 변환
        # 간단히 최대 HP를 200으로 가정 (실제로는 종족값마다 다름)
        estimated_max_hp = 200
        damage_fraction = damage / estimated_max_hp
        
        return min(1.0, max(0.0, damage_fraction))
    
    def _apply_boost(self, stat: int, boost: int) -> float:
        """
        능력치 변화 적용
        
        boost 범위: -6 ~ +6
        
        배율:
        - boost >= 0: (2 + boost) / 2
        - boost < 0: 2 / (2 - boost)
        
        예시:
        - +1: 1.5배
        - +2: 2배
        - -1: 0.67배
        - -2: 0.5배
        """
        if boost >= 0:
            multiplier = (2 + boost) / 2
        else:
            multiplier = 2 / (2 - boost)
        
        return stat * multiplier
    
    def _get_type_effectiveness(self, move_type: str, defender_types: tuple) -> float:
        """
        타입 상성 계산
        
        Parameters:
        - move_type: 'fire', 'water' 등
        - defender_types: ('grass', 'poison') 등
        
        Returns: 배율 (0, 0.25, 0.5, 1, 2, 4)
        
        처리:
        1. 타입 차트에서 각 타입별 배율 찾기
        2. 2개 타입이면 곱하기
        """
        if not defender_types:
            return 1.0
        
        # 타입 차트에서 배율 찾기
        multiplier = 1.0
        
        for def_type in defender_types:
            if move_type in self.TYPE_CHART and def_type in self.TYPE_CHART[move_type]:
                multiplier *= self.TYPE_CHART[move_type][def_type]
        
        return multiplier
    
    def is_terminal(self) -> bool:
        """
        게임 종료 여부
        
        조건: 한쪽 팀의 모든 포켓몬이 기절
        """
        my_all_fainted = all(p['fainted'] for p in self.my_team)
        opp_all_fainted = all(p['fainted'] for p in self.opp_team)
        
        return my_all_fainted or opp_all_fainted
    
    def get_winner(self) -> Optional[str]:
        """
        승자 반환
        
        Returns:
        - 'me': 내가 승리
        - 'opponent': 상대 승리
        - None: 아직 진행 중
        """
        my_all_fainted = all(p['fainted'] for p in self.my_team)
        opp_all_fainted = all(p['fainted'] for p in self.opp_team)
        
        if my_all_fainted:
            return 'opponent'
        elif opp_all_fainted:
            return 'me'
        return None
    
    def evaluate(self) -> float:
        """
        현재 상태를 점수로 평가 (MCTS rollout용)
        
        평가 요소:
        1. 살아있는 포켓몬 수
        2. 총 HP
        3. 타입 상성 (선택적)
        
        Returns: 0.0 ~ 1.0 (0.5가 중립)
        """
        # 게임 종료시
        winner = self.get_winner()
        if winner == 'me':
            return 1.0
        elif winner == 'opponent':
            return 0.0
        
        # 살아있는 포켓몬 수
        my_alive = sum(1 for p in self.my_team if not p['fainted'])
        opp_alive = sum(1 for p in self.opp_team if not p['fainted'])
        
        # 총 HP
        my_hp = sum(p['hp_fraction'] for p in self.my_team if not p['fainted'])
        opp_hp = sum(p['hp_fraction'] for p in self.opp_team if not p['fainted'])
        
        # 점수 계산
        score = 0.5
        score += (my_alive - opp_alive) * 0.15  # 포켓몬 수 차이
        score += (my_hp - opp_hp) * 0.15        # HP 차이
        
        return max(0.0, min(1.0, score))