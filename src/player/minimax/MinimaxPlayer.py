import math
import random
import sys
import os
import time
from typing import List, Optional, Tuple, Dict

# 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sim.BattleEngine.SimplifiedBattleEngine import SimplifiedBattleEngine
from sim.BattleClass.SimplifiedBattle import SimplifiedBattle
from sim.BattleClass.SimplifiedPokemon import SimplifiedPokemon
from poke_env.player import Player
from poke_env.battle import Battle


class MinimaxPlayer(Player):
    """
    2턴 뒤의 미래까지 내다보고 최적의 수를 찾기
    """
    
    def __init__(self, battle_format="gen9randombattle", max_concurrent_battles=1, depth=2, **kwargs):
        super().__init__(battle_format=battle_format, max_concurrent_battles=max_concurrent_battles, **kwargs)
        self.depth = depth # 기본 2턴 추천
        self.engine = SimplifiedBattleEngine()

    def choose_move(self, battle: Battle):
        if not battle.available_moves and not battle.available_switches:
            return self.choose_random_move(battle)
        
        # 1. 현재 상태 변환
        root_state = SimplifiedBattle(battle, fill_unknown_data=True)
        self.engine._sync_references(root_state)

        # 2. 미니맥스 탐색 (재귀)
        best_action = self._max_value(root_state, self.depth, -float('inf'), float('inf'))[1]

        # 3. 결과 실행
        return self._convert_to_order(battle, best_action)

    # =================================================================
    # [Core] Minimax Recursive Logic
    # =================================================================
    def _max_value(self, state: SimplifiedBattle, depth: int, alpha: float, beta: float):
        """Max Node (나의 턴)"""
        if depth == 0 or state.finished:
            return self._evaluate_state(state), None

        best_value = -float('inf')
        best_action = None
        
        actions = self._get_smart_actions(state, is_player=True)

        for action in actions:
            # Min Node로 넘김 (내 행동을 고정하고 상대 턴 예측)
            val = self._min_value(state, action, depth, alpha, beta)
            
            if val > best_value:
                best_value = val
                best_action = action
            
            alpha = max(alpha, best_value)
            if beta <= alpha:
                break
        
        return best_value, best_action

    def _min_value(self, state: SimplifiedBattle, my_action, depth: int, alpha: float, beta: float):
        """Min Node (상대 턴)"""
        if state.finished:
             return self._evaluate_state(state)

        min_val = float('inf')
        
        opp_actions = self._get_smart_actions(state, is_player=False)

        for opp_action in opp_actions:
            next_state = state.clone()
            
            p_idx, p_sw = self._parse_action(next_state, my_action, is_player=True)
            o_idx, _    = self._parse_action(next_state, opp_action, is_player=False)
            
            self.engine.simulate_turn(
                next_state,
                player_move_idx=p_idx, player_switch_to=p_sw,
                opponent_move_idx=o_idx
            )
            
            # 다음 Depth의 Max Node 호출
            val, _ = self._max_value(next_state, depth - 1, alpha, beta)
            
            if val < min_val:
                min_val = val
            
            beta = min(beta, min_val)
            if beta <= alpha:
                break
                
        return min_val

    # =================================================================
    # [Helpers] 행동 가지치기 & 평가
    # =================================================================
    def _get_smart_actions(self, state: SimplifiedBattle, is_player: bool) -> list:
        """[가지치기] 유의미한 행동만 추려냄"""
        actions = []
        active = state.active_pokemon if is_player else state.opponent_active_pokemon
        opp_active = state.opponent_active_pokemon if is_player else state.active_pokemon
        switches = state.available_switches if is_player else [] 

        # 1. 기술 (Moves) - 상위 3개만
        if active and active.moves:
            scored_moves = []
            for m in active.moves:
                if m.current_pp <= 0: continue
                score = 0
                if m.category.name == 'STATUS':
                    score = 10 
                else:
                    score = m.base_power
                    if opp_active:
                        mult = opp_active.damage_multiplier(m.type)
                        if mult == 0: score = -999 
                        else: score *= mult
                        if m.type in active.types: score *= 1.5 # 자속
                
                if score > 0:
                    scored_moves.append((score, m))
            
            scored_moves.sort(key=lambda x: x[0], reverse=True)
            actions.extend([m for s, m in scored_moves[:3]])
        
        # 2. 교체 (Switches) - 위기일 때만 (방어 상성 좋은 2마리)
        if is_player and switches:
            is_danger = False
            if active and opp_active:
                for t in opp_active.types:
                    if active.damage_multiplier(t) >= 2.0: is_danger = True
                if (active.current_hp / active.max_hp) < 0.3: is_danger = True
            
            if is_danger:
                scored_switches = []
                for p in switches:
                    if p.current_hp <= 0: continue
                    threat_score = 0
                    if opp_active:
                        for t in opp_active.types:
                            threat_score += p.damage_multiplier(t)
                    scored_switches.append((threat_score, p))
                
                scored_switches.sort(key=lambda x: x[0]) 
                actions.extend([p for s, p in scored_switches[:2]])

        if not actions and active and active.moves:
             actions.append(active.moves[0])
             
        return actions

    def _evaluate_state(self, battle: SimplifiedBattle) -> float:
        """[평가 함수] 승패 + 체력 + 스피드 + 상성"""
        if battle.won: return 10000.0
        if battle.lost: return -10000.0
        
        score = 0.0
        # 내 팀 점수 - 상대 팀 점수
        score += self._calc_detailed_score(battle.team, battle.opponent_active_pokemon)
        score -= self._calc_detailed_score(battle.opponent_team, battle.active_pokemon)
        
        return score

    def _calc_detailed_score(self, team, opponent_active):
        side_score = 0.0
        active_poke = None
        for p in team.values(): 
            if p.active: active_poke = p

        for p in team.values():
            if p.current_hp > 0:
                # A. HP 점수
                hp_ratio = p.current_hp / p.max_hp
                side_score += 100 * hp_ratio
                
                # B. 상태이상 페널티
                if p.status == 'par': side_score -= 20
                elif p.status in ['frz', 'slp']: side_score -= 30
                elif p.status in ['brn', 'psn', 'tox']: side_score -= 15
                
                # C. 랭크업 보너스
                boosts = sum(p.boosts.values())
                side_score += boosts * 5

                # D. 활성 포켓몬 특수 평가 (스피드 & 상성)
                if p == active_poke and opponent_active:
                    # 1. 스피드 우위 (+50점)
                    my_spe = p.stats['spe'] * (0.5 if p.status == 'par' else 1.0)
                    opp_spe = opponent_active.stats['spe'] * (0.5 if opponent_active.status == 'par' else 1.0)
                    if my_spe > opp_spe: side_score += 50
                    
                    # 2. 상성 우위 (최대 데미지 배율 확인)
                    max_mult = 0.0
                    for m in p.moves:
                        if m.category.name != 'STATUS':
                            mult = opponent_active.damage_multiplier(m.type)
                            if mult > max_mult: max_mult = mult
                    
                    if max_mult >= 2.0: side_score += 40  # 약점 찌름
                    elif max_mult >= 4.0: side_score += 80 # 4배 약점
                    elif max_mult == 0: side_score -= 20   # 때릴 게 없음
                
        return side_score

    def _parse_action(self, state, action, is_player):
        idx = None
        sw = None
        active = state.active_pokemon if is_player else state.opponent_active_pokemon
        if hasattr(action, 'id') and active:
            for i, m in enumerate(active.moves):
                if m.id == action.id: idx = i; break
        else:
            sw = action.species if hasattr(action, 'species') else action
        return idx, sw
    
    def _convert_to_order(self, battle, action):
        if action is None: return self.choose_random_move(battle)
        if hasattr(action, 'id'):
            for m in battle.available_moves:
                if m.id == action.id: return self.create_order(m)
        else:
            for p in battle.available_switches:
                if p.species == action.species: return self.create_order(p)
        return self.choose_random_move(battle)