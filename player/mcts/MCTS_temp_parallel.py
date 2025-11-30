import math
import random
import sys
import os
import time
from typing import List, Optional, Tuple, Dict

# 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from sim.SimplifiedBattle import SimplifiedBattle
from sim.battle.SimplifiedBattleEngine import SimplifiedBattleEngine
from sim.SimplifiedPokemon import SimplifiedPokemon


# =============================================================================
# 1. [Helper] 배틀 계산/판단 로직 (Advanced Heuristics)
# =============================================================================
class BattleHeuristics:
    """배틀 관련 순수 계산 로직"""

    @staticmethod
    def get_move_damage_score(move, attacker, defender) -> float:
        """
        기술의 기대 위력(Score)을 계산합니다.
        공식: 위력 * 자속보정 * 상성 * 명중률
        """
        # 변화기는 데미지가 없으므로 기본 점수 부여
        if move.category.name == 'STATUS':
            return 0.1
        
        # 1. 기본 위력
        score = move.base_power
        
        # 2. 자속 보정 (STAB)
        if move.type in attacker.types:
            score *= 1.5
            
        # 3. 상성 계산 (가장 중요!)
        if defender:
            mult = defender.damage_multiplier(move.type)
            score *= mult
            
        # 4. 명중률 기댓값 반영
        if move.accuracy:
            score *= move.accuracy
            
        return score

    @staticmethod
    def select_best_attack_idx(attacker: SimplifiedPokemon, defender: Optional[SimplifiedPokemon]) -> int:
        """
        [지능형 선택] 가장 기대 딜량이 높은 기술의 인덱스를 반환 (Greedy)
        """
        if not attacker or not attacker.moves: return None
        
        best_idx = 0
        max_score = -1.0
        
        random_fallback = random.randint(0, len(attacker.moves) - 1)
        has_valid_attack = False

        for i, move in enumerate(attacker.moves):
            if move.current_pp <= 0: continue
            
            score = BattleHeuristics.get_move_damage_score(move, attacker, defender)
            
            if move.category.name != 'STATUS':
                has_valid_attack = True

            if score > max_score:
                max_score = score
                best_idx = i
        
        # 공격 기술이 아예 없으면(변화기만 남음) 랜덤 반환
        if not has_valid_attack and max_score <= 0.1:
            return random_fallback
            
        return best_idx

    @staticmethod
    def calculate_team_health(team_dict: Dict[str, SimplifiedPokemon]) -> float:
        total = 0.0
        count = 0
        for p in team_dict.values():
            if p.current_hp > 0 and p.max_hp > 0:
                total += (p.current_hp / p.max_hp)
                count += 1
        return total / max(1, count) if count > 0 else 0.0

    @staticmethod
    def evaluate_state(battle: SimplifiedBattle) -> float:
        """[보상 함수] 승패 + 체력 점수"""
        if battle.won: return 1.0
        if battle.lost:
            opp_hp = BattleHeuristics.calculate_team_health(battle.opponent_team)
            return (1.0 - opp_hp) * 0.2

        my_score = BattleHeuristics._calculate_side_score(battle.team)
        opp_score = BattleHeuristics._calculate_side_score(battle.opponent_team)

        if my_score + opp_score == 0: return 0.5
        return my_score / (my_score + opp_score)

    @staticmethod
    def _calculate_side_score(team: Dict[str, SimplifiedPokemon]) -> float:
        score = 0.0
        for p in team.values():
            if p.current_hp > 0 and p.max_hp > 0:
                p_score = 1.0 + (p.current_hp / p.max_hp)
                if p.status is not None: p_score -= 0.5
                
                boosts = p.boosts.get('atk', 0) + p.boosts.get('spa', 0) + p.boosts.get('spe', 0)
                if boosts > 0: p_score += (boosts * 0.1)
                
                score += max(0.1, p_score)
        return score


# =============================================================================
# 2. [Strategy] 스마트 롤아웃 정책 (Smart Counter Strategy)
# =============================================================================
class SmartRolloutPolicy:
    """
    [전략: 지능형 맞불 작전]
    - 나: 100% 확률로 '가장 센 기술' 선택 (Deterministic)
    - 상대: 100% 확률로 '가장 센 기술' 선택 (Deterministic)
    - 턴: 1턴 (단기전 최적화)
    """
    def __init__(self, max_turns=1):
        self.max_turns = max_turns

    def run(self, state: SimplifiedBattle, engine: SimplifiedBattleEngine) -> float:
        if state.finished:
            return BattleHeuristics.evaluate_state(state)

        rollout_state = state.clone()
        
        # 1턴 시뮬레이션
        for _ in range(self.max_turns):
            if rollout_state.finished: break
            
            me = rollout_state.active_pokemon
            opp = rollout_state.opponent_active_pokemon
            
            # --- [1] 내 행동: 최선의 공격 ---
            my_move_idx = BattleHeuristics.select_best_attack_idx(me, opp)

            # --- [2] 상대 행동: 최선의 공격 ---
            opp_move_idx = BattleHeuristics.select_best_attack_idx(opp, me)
            
            engine.simulate_turn(
                rollout_state,
                player_move_idx=my_move_idx,
                opponent_move_idx=opp_move_idx
            )

        return BattleHeuristics.evaluate_state(rollout_state)


# =============================================================================
# 3. [Data Structure] MCTS 노드
# =============================================================================
class MCTSNode:
    def __init__(self, state: SimplifiedBattle, parent=None, action=None):
        self.state = state
        self.parent = parent
        self.action = action
        self.children = []
        self.visits = 0
        self.wins = 0.0
        self.untried_actions = self._get_available_actions()

    def _get_available_actions(self):
        actions = []
        if hasattr(self.state, 'available_moves'):
            actions.extend(list(self.state.available_moves))
        if hasattr(self.state, 'available_switches'):
            actions.extend(list(self.state.available_switches))
        return actions

    def best_child(self, c_param=1.4):
        if not self.children: return None
        log_n = math.log(self.visits)
        choices_weights = [
            (child.wins / child.visits) + c_param * math.sqrt(log_n / child.visits)
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]


# =============================================================================
# 4. [Orchestrator] MCTS 실행기
# =============================================================================
class MCTSSearcher:
    def __init__(self, root_battle):
        self.engine = SimplifiedBattleEngine()
        if isinstance(root_battle, SimplifiedBattle):
            self.root_state = root_battle
        else:
            self.root_state = SimplifiedBattle(root_battle, fill_unknown_data=True)
            
        self.engine._sync_references(self.root_state)
        self.root = MCTSNode(self.root_state)

        # root state의 가능한 액션들 가지치기
        
        # [전략] SmartRolloutPolicy (1턴) 사용
        self.policy = SmartRolloutPolicy(max_turns=1)

    def search(self, iterations):
        # Fast Fail
        all_actions = self.root.untried_actions
        if not all_actions: return None
        if len(all_actions) == 1: return all_actions[0]

        for _ in range(iterations):
            node = self.root
            
            # Selection
            while not node.state.finished and not node.untried_actions and node.children:
                node = node.best_child()
                if node is None: break 
            
            # Expansion
            if not node.state.finished and node.untried_actions:
                node = self._expand(node)
            
            # Simulation & Backpropagation
            if node:
                reward = self.policy.run(node.state, self.engine)
                self._backpropagate(node, reward)

        if not self.root.children:
            return random.choice(all_actions)

        best_child = max(self.root.children, key=lambda c: c.visits)
        return best_child.action

    def _expand(self, node):
        action = random.choice(node.untried_actions)
        node.untried_actions.remove(action)

        new_state = node.state.clone()
        
        p_move_idx, p_switch = self._parse_action(new_state, action)
        
        # 확장 단계에서의 상대 행동도 '스마트'하게 예측 (일관성 유지)
        o_move_idx = BattleHeuristics.select_best_attack_idx(
            new_state.opponent_active_pokemon, 
            new_state.active_pokemon
        )

        self.engine.simulate_turn(
            new_state,
            player_move_idx=p_move_idx,
            player_switch_to=p_switch,
            opponent_move_idx=o_move_idx
        )

        child_node = MCTSNode(new_state, parent=node, action=action)
        node.children.append(child_node)
        return child_node

    def _backpropagate(self, node, reward):
        while node:
            node.visits += 1
            node.wins += reward
            node = node.parent

    def _parse_action(self, state, action) -> Tuple[Optional[int], Optional[str]]:
        move_idx = None
        switch_name = None
        if hasattr(action, 'id'):  # Move
            if state.active_pokemon:
                for i, m in enumerate(state.active_pokemon.moves):
                    if m.id == action.id:
                        move_idx = i
                        break
        else:  # Switch
            switch_name = action.species
        return move_idx, switch_name


# =============================================================================
# 메인 함수
# =============================================================================
def mcts_search(root_battle, iterations=50, verbose=False, n_workers=1):
    searcher = MCTSSearcher(root_battle)
    best_action = searcher.search(iterations)
    
    if verbose and best_action:
        action_name = best_action.id if hasattr(best_action, 'id') else best_action.species
        # print(f"⚡ [MCTS] 결정: {action_name}")

    return best_action