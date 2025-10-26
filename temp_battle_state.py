"""
BattleState - 시뮬레이션 가능한 경량 배틀 상태
"""

import copy
import json
import random
from typing import Dict, List, Optional, Any, Tuple

class BattleState:
    """
    시뮬레이션용 경량 배틀 상태
    
    주요 기능:
    1. poke-env Battle 객체에서 정보 추출
    2. 상태 복사 가능 (clone)
    3. 액션 시뮬레이션 (apply_move, apply_switch)
    """
    
    # 타입 차트 (클래스 변수)
    TYPE_CHART = None
    
    @classmethod
    def load_type_chart(cls):
        """타입 차트 로드"""
        if cls.TYPE_CHART is None:
            try:
                with open('type_chart.json', 'r') as f:
                    cls.TYPE_CHART = json.load(f)
            except FileNotFoundError:
                # 파일이 없으면 기본값 사용 (모두 1.0)
                cls.TYPE_CHART = {}
    
    def __init__(self, battle=None, state_dict=None):
        """
        초기화
        
        Parameters:
        - battle: poke-env Battle 객체 (최초 생성)
        - state_dict: 복사용 딕셔너리 (clone에서 사용)
        """
        # 타입 차트 로드
        if BattleState.TYPE_CHART is None:
            BattleState.load_type_chart()
        
        if battle:
            # Battle 객체에서 정보 추출
            self.my_team = self._extract_team(battle.team)
            self.opp_team = self._extract_team(battle.opponent_team)
            self.my_active_idx = self._find_active_index(battle.team)
            self.opp_active_idx = self._find_active_index(battle.opponent_team)
            self.weather = str(battle.weather) if battle.weather else None
            
            # 디버깅
            # print(f"[BattleState] My team: {len(self.my_team)}, Opp team: {len(self.opp_team)}")
        else:
            # 복사본 생성
            self.my_team = state_dict['my_team']
            self.opp_team = state_dict['opp_team']
            self.my_active_idx = state_dict['my_active_idx']
            self.opp_active_idx = state_dict['opp_active_idx']
            self.weather = state_dict['weather']
    
    def _extract_team(self, team_dict: Dict) -> List[Dict]:
        """
        Pokemon 객체에서 필요한 정보 추출
        
        Returns: 포켓몬 정보 딕셔너리 리스트
        """
        team = []
        for pokemon in team_dict.values():
            # 타입 추출
            types = []
            for t in pokemon.types:
                if t is not None:
                    # PokemonType enum을 문자열로
                    type_name = str(t).split('.')[-1].lower()
                    types.append(type_name)
            
            team.append({
                'species': pokemon.species,
                'hp_fraction': pokemon.current_hp_fraction,
                'fainted': pokemon.fainted,
                'types': tuple(types),
                'stats': dict(pokemon.stats),
                'boosts': dict(pokemon.boosts),
                'status': str(pokemon.status) if pokemon.status else None,
                'active': pokemon.active,
            })
        return team
    
    def _find_active_index(self, team_dict: Dict) -> Optional[int]:
        """활성 포켓몬 인덱스 찾기"""
        for idx, pokemon in enumerate(team_dict.values()):
            if pokemon.active:
                return idx
        return None
    
    def clone(self) -> 'BattleState':
        """
        현재 상태의 깊은 복사
        
        중요: MCTS에서 시뮬레이션할 때 사용
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
        - is_my_turn: True면 내가 공격
        """
        if move.base_power == 0:
            # TODO: 보조기 처리
            return
        
        # 공격자/방어자
        if is_my_turn:
            if self.my_active_idx is None or self.opp_active_idx is None:
                return
            attacker = self.my_team[self.my_active_idx]
            defender = self.opp_team[self.opp_active_idx]
        else:
            if self.my_active_idx is None or self.opp_active_idx is None:
                return
            attacker = self.opp_team[self.opp_active_idx]
            defender = self.my_team[self.my_active_idx]
        
        # 이미 기절했으면 무시
        if attacker['fainted'] or defender['fainted']:
            return
        
        # 데미지 계산
        damage = self._calculate_damage(attacker, defender, move)
        
        # HP 업데이트
        defender['hp_fraction'] = max(0.0, defender['hp_fraction'] - damage)
        
        # 기절 처리
        if defender['hp_fraction'] <= 0:
            defender['fainted'] = True
            defender['active'] = False
    
    def apply_switch(self, switch_idx: int, is_my_turn=True):
        """
        포켓몬 교체 시뮬레이션
        
        Parameters:
        - switch_idx: 교체할 포켓몬 인덱스
        - is_my_turn: 내 턴인지
        """
        if is_my_turn:
            team = self.my_team
            old_idx = self.my_active_idx
        else:
            team = self.opp_team
            old_idx = self.opp_active_idx
        
        # 유효성 검사
        if switch_idx >= len(team) or team[switch_idx]['fainted']:
            return
        
        # 이전 포켓몬 비활성화
        if old_idx is not None and old_idx < len(team):
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
        데미지 계산 (Showdown 공식)
        
        Returns: HP 감소 비율 (0.0 ~ 1.0)
        """
        level = 50
        power = move.base_power
        
        if power == 0:
            return 0.0
        
        # 공격/방어 스탯
        move_category = str(move.category).upper()
        
        if 'PHYSICAL' in move_category:
            attack = attacker['stats'].get('atk', 100) or 100
            defense = defender['stats'].get('def', 100) or 100
            atk_boost = attacker['boosts'].get('atk', 0)
            def_boost = defender['boosts'].get('def', 0)
        elif 'SPECIAL' in move_category:
            attack = attacker['stats'].get('spa', 100) or 100
            defense = defender['stats'].get('spd', 100) or 100
            atk_boost = attacker['boosts'].get('spa', 0)
            def_boost = defender['boosts'].get('spd', 0)
        else:
            return 0.0
        
        # 능력치 변화 적용
        attack = self._apply_boost(attack, atk_boost)
        defense = self._apply_boost(defense, def_boost)
        
        # 기본 데미지
        damage = ((2 * level / 5 + 2) * power * attack / defense / 50 + 2)
        
        # 타입 상성
        move_type = str(move.type).split('.')[-1].lower()
        type_mult = self._get_type_effectiveness(move_type, defender['types'])
        damage *= type_mult
        
        # STAB (자속보정)
        if move_type in attacker['types']:
            damage *= 1.5
        
        # 랜덤 (0.85 ~ 1.0)
        damage *= random.uniform(0.85, 1.0)
        
        # HP 비율로 변환
        max_hp = 200  # 간단히 고정
        damage_fraction = damage / max_hp
        
        return min(1.0, max(0.0, damage_fraction))
    
    def _apply_boost(self, stat: int, boost: int) -> float:
        """
        능력치 변화 적용
        
        boost: -6 ~ +6
        """
        # None 체크
        if stat is None:
            stat = 100
        
        if boost >= 0:
            multiplier = (2 + boost) / 2
        else:
            multiplier = 2 / (2 - boost)
        
        return stat * multiplier
    
    def _get_type_effectiveness(self, move_type: str, defender_types: Tuple[str, ...]) -> float:
        """
        타입 상성 계산
        
        Returns: 배율 (0, 0.25, 0.5, 1, 2, 4)
        """
        if not defender_types or not self.TYPE_CHART:
            return 1.0
        
        multiplier = 1.0
        
        for def_type in defender_types:
            if move_type in self.TYPE_CHART and def_type in self.TYPE_CHART[move_type]:
                multiplier *= self.TYPE_CHART[move_type][def_type]
        
        return multiplier
    
    def is_terminal(self) -> bool:
        """
        게임 종료 여부
        
        조건: 한쪽 팀 전멸
        """
        my_all_fainted = all(p['fainted'] for p in self.my_team)
        opp_all_fainted = all(p['fainted'] for p in self.opp_team)
        
        return my_all_fainted or opp_all_fainted
    
    def get_winner(self) -> Optional[str]:
        """
        승자 반환
        
        Returns: 'me', 'opponent', None
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
        현재 상태 평가 (MCTS rollout용)
        
        Returns: 0.0 ~ 1.0 (내 승리 확률)
        
        개선된 평가:
        1. 현재 필드 포켓몬의 HP 비율 (50% 가중치)
        2. 살아있는 포켓몬 수 비율 (30% 가중치)  
        3. 총 HP 비율 (20% 가중치)
        """
        # 살아있는 포켓몬 수
        my_alive = sum(1 for p in self.my_team if not p['fainted'])
        opp_alive = sum(1 for p in self.opp_team if not p['fainted'])
        
        # 게임 종료시
        if my_alive == 0:
            return 0.0
        elif opp_alive == 0:
            return 1.0
        
        # 상대 팀 정보가 없으면 현재 포켓몬만 비교
        if len(self.opp_team) == 0:
            return 0.5
        
        # 1. 현재 필드 포켓몬의 HP 비율 (가장 중요!)
        my_active = next((p for p in self.my_team if p['active']), None)
        opp_active = next((p for p in self.opp_team if p['active']), None)
        
        if my_active and opp_active:
            field_score = my_active['hp_fraction'] / (my_active['hp_fraction'] + opp_active['hp_fraction'])
        elif my_active:
            field_score = 1.0
        elif opp_active:
            field_score = 0.0
        else:
            field_score = 0.5
        
        # 2. 살아있는 포켓몬 수 비율
        alive_score = my_alive / (my_alive + opp_alive)
        
        # 3. 총 HP 비율
        my_hp = sum(p['hp_fraction'] for p in self.my_team if not p['fainted'])
        opp_hp = sum(p['hp_fraction'] for p in self.opp_team if not p['fainted'])
        
        if my_hp + opp_hp > 0:
            hp_score = my_hp / (my_hp + opp_hp)
        else:
            hp_score = 0.5
        
        # 가중치 합산
        final_score = (
            field_score * 0.5 +   # 현재 필드가 가장 중요
            alive_score * 0.3 +   # 포켓몬 수
            hp_score * 0.2        # 총 HP
        )
        
        return max(0.0, min(1.0, final_score))

