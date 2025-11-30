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
# 1. [Helper] 배틀 계산/판단 로직 (Pure Logic)
# =============================================================================
class BattleHeuristics:
    """배틀 관련 순수 계산 로직 집합 (Stateless)"""

    @staticmethod
    def get_valid_attack_indices(pokemon: SimplifiedPokemon, opponent: Optional[SimplifiedPokemon]) -> List[int]:
        """
        유효한 공격 기술의 인덱스를 반환
        조건: 변화기 아님 + PP 있음 + 상성 0배(무효) 아님
        """
        if not pokemon or not pokemon.moves:
            return []
        
        valid_indices = []
        for i, m in enumerate(pokemon.moves):
            # 1. 변화기(STATUS) 제외, PP 없는 기술 제외
            if m.category.name == 'STATUS' or m.current_pp <= 0:
                continue
            
            # 2. 상성 0배(무효) 제외 (반감은 허용)
            if opponent:
                mult = opponent.damage_multiplier(m.type)
                if mult == 0: continue
            
            valid_indices.append(i)
        return valid_indices

    @staticmethod
    def calculate_team_health(team_dict: Dict[str, SimplifiedPokemon]) -> float:
        """팀 평균 체력 비율 계산"""
        total = 0.0
        count = 0
        for p in team_dict.values():
            if p.current_hp > 0 and p.max_hp > 0:
                total += (p.current_hp / p.max_hp)
                count += 1
        return total / max(1, count) if count > 0 else 0.0

    @staticmethod
    def evaluate_state(battle: SimplifiedBattle) -> float:
        """
        [보상 함수] 승패 + 체력/상태이상/랭크업 종합 평가 (0.0 ~ 1.0)
        """
        # 1. 승패 확정 시
        if battle.won: return 1.0
        if battle.lost:
            # 졌어도 상대 체력을 많이 깎았으면 부분 점수 (최대 0.2)
            opp_hp = BattleHeuristics.calculate_team_health(battle.opponent_team)
            return (1.0 - opp_hp) * 0.2

        # 2. 진행 중일 때 점수 계산
        my_score = BattleHeuristics._calculate_side_score(battle.team)
        opp_score = BattleHeuristics._calculate_side_score(battle.opponent_team)

        if my_score + opp_score == 0: return 0.5
        return my_score / (my_score + opp_score)

    @staticmethod
    def _calculate_side_score(team: Dict[str, SimplifiedPokemon]) -> float:
        score = 0.0
        for p in team.values():
            if p.current_hp > 0 and p.max_hp > 0:
                # 기본 점수: 생존(1.0) + 체력 비율
                p_score = 1.0 + (p.current_hp / p.max_hp)
                
                # 상태이상 페널티
                if p.status is not None: p_score -= 0.5
                
                # 랭크업 보너스 (공격적 스탯)
                boosts = p.boosts.get('atk', 0) + p.boosts.get('spa', 0) + p.boosts.get('spe', 0)
                if boosts > 0: p_score += (boosts * 0.1)
                
                score += max(0.1, p_score)
        return score


# =============================================================================
# 2. [Strategy] 롤아웃 정책 (The "Champion Logic")
# =============================================================================
class BullyRolloutPolicy:
    """
    [전략: 양학(Bully) 모드]
    - 나: 80% 확률로 공격 지향 (똑똑함)
    - 상대: 100% 확률로 랜덤 (멍청함 가정 - RandomBot 상대로 최적)
    - 턴 수: 1턴
    """
    def __init__(self, max_turns=1):
        self.max_turns = max_turns

    def run(self, state: SimplifiedBattle, engine: SimplifiedBattleEngine) -> float:
        # 이미 끝났으면 바로 평가
        if state.finished:
            return BattleHeuristics.evaluate_state(state)

        rollout_state = state.clone()
        
        for _ in range(self.max_turns):
            if rollout_state.finished: break
            
            # --- [1] 내 행동: 80% 공격 지향 ---
            my_move_idx = self._select_my_action(rollout_state)

            # --- [2] 상대 행동: 100% 완전 랜덤 ---
            opp_move_idx = self._select_opponent_action(rollout_state)
            
            # 턴 실행
            engine.simulate_turn(
                rollout_state,
                player_move_idx=my_move_idx,
                opponent_move_idx=opp_move_idx
            )

        return BattleHeuristics.evaluate_state(rollout_state)

    def _select_my_action(self, state):
        """내 행동 선택 로직"""
        me = state.active_pokemon
        opp = state.opponent_active_pokemon
        
        if not me or not me.moves: return None

        # BattleHeuristics를 이용해 유효 공격 기술만 가져옴
        valid_attacks = BattleHeuristics.get_valid_attack_indices(me, opp)
        
        # 80% 확률로 유효 공격 선택
        if valid_attacks and random.random() < 0.8:
            return random.choice(valid_attacks)
        
        # 나머지: 전체 중 랜덤
        return random.randint(0, len(me.moves) - 1)

    def _select_opponent_action(self, state):
        """상대 행동 선택 로직 (완전 랜덤)"""
        opp = state.opponent_active_pokemon
        if not opp or not opp.moves: return None
        return random.randint(0, len(opp.moves) - 1)


# =============================================================================
# 3. [Data Structure] MCTS 노드 (트리 관리)
# =============================================================================
class MCTSNode:
    def __init__(self, state: SimplifiedBattle, parent=None, action=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.visits = 0
        self.wins = 0.0
        self.action = action  # 이 노드에 도달하게 한 행동
        
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
        
        # 로그 계산 최적화
        log_n = math.log(self.visits)
        
        choices_weights = [
            (child.wins / child.visits) + c_param * math.sqrt(log_n / child.visits)
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]


# =============================================================================
# 4. [Orchestrator] MCTS 실행기 (알고리즘 흐름 제어)
# =============================================================================
class MCTSSearcher:
    def __init__(self, root_battle: SimplifiedBattle):
        self.engine = SimplifiedBattleEngine()
        
        # 상태 변환
        if isinstance(root_battle, SimplifiedBattle):
            self.root_state = root_battle
        else:
            self.root_state = SimplifiedBattle(root_battle, fill_unknown_data=True)
            
        self.engine._sync_references(self.root_state)
        self.root = MCTSNode(self.root_state)
        
        # [중요] 전략 주입: 여기서 다른 정책으로 갈아끼울 수 있음
        self.policy = BullyRolloutPolicy(max_turns=1)

    def search(self, iterations):
        # Fast Fail (선택지가 1개면 즉시 반환)
        all_actions = self.root.untried_actions
        if not all_actions: return None
        if len(all_actions) == 1: return all_actions[0]

        for _ in range(iterations):
            node = self.root
            
            # 1. Selection
            while not node.state.finished and not node.untried_actions and node.children:
                node = node.best_child()
                if node is None: break 
            
            # 2. Expansion
            if not node.state.finished and node.untried_actions:
                node = self._expand(node)
            
            # 3. Simulation & Backpropagation
            if node:
                # 정책(Policy)에게 시뮬레이션 위임
                reward = self.policy.run(node.state, self.engine)
                self._backpropagate(node, reward)

        # 결과 선택
        if not self.root.children:
            return random.choice(all_actions)

        best_child = max(self.root.children, key=lambda c: c.visits)
        return best_child.action

    def _expand(self, node: MCTSNode) -> MCTSNode:
        action = random.choice(node.untried_actions)
        node.untried_actions.remove(action)

        new_state = node.state.clone()
        
        p_move_idx, p_switch = self._parse_action(new_state, action)
        
        # 확장 단계에서의 상대 행동은 랜덤 가정
        o_move_idx = None
        if new_state.opponent_active_pokemon and new_state.opponent_active_pokemon.moves:
            o_move_idx = random.randint(0, len(new_state.opponent_active_pokemon.moves) - 1)

        self.engine.simulate_turn(
            new_state,
            player_move_idx=p_move_idx,
            player_switch_to=p_switch,
            opponent_move_idx=o_move_idx
        )

        child_node = MCTSNode(new_state, parent=node, action=action)
        node.children.append(child_node)
        return child_node

    def _backpropagate(self, node: MCTSNode, reward: float):
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
# 5. 외부 인터페이스 함수 (기존 코드와의 호환성 유지)
# =============================================================================
def mcts_search(root_battle, iterations=100, verbose=False, n_workers=1):
    """
    외부에서 호출하는 진입점.
    반환값: Action 객체 (단일 값)
    """
    searcher = MCTSSearcher(root_battle)
    best_action = searcher.search(iterations)
    
    if verbose and best_action:
        action_name = best_action.id if hasattr(best_action, 'id') else best_action.species
        # print(f"⚡ [MCTS] 결정: {action_name}")

    return best_action