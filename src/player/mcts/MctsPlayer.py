import math
import random
import sys
import os
import time
from typing import List, Optional, Tuple, Dict, Set

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from sim.BattleClass.SimplifiedBattle import SimplifiedBattle
from sim.BattleEngine.SimplifiedBattleEngine import SimplifiedBattleEngine
from sim.BattleClass.SimplifiedPokemon import SimplifiedPokemon
from sim.BattleClass.SimplifiedMove import SimplifiedMove
from player.mcts.llm_pruner import LLMPruner


class BattleHeuristics:
    """배틀 관련 순수 계산 로직"""

    @staticmethod
    def get_move_damage_score(move : SimplifiedMove, attacker : SimplifiedPokemon, defender: Optional[SimplifiedPokemon]) -> float:
        """
        기술의 기대 위력을 계산합니다.
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
        가장 기대 딜량이 높은 기술의 인덱스를 반환
        """
        # 예외 처리
        if not attacker or not attacker.moves: return None
        
        best_idx = 0
        max_score = -1.0
        
        random_fallback = random.randint(0, len(attacker.moves) - 1)
        has_valid_attack = False

        for i, move in enumerate(attacker.moves):
            if move.current_pp <= 0: continue
            
            # 기대치가 가장 높은 기술 선택
            score = BattleHeuristics.get_move_damage_score(move, attacker, defender)
            
            if move.category.name != 'STATUS':
                has_valid_attack = True

            if score > max_score:
                max_score = score
                best_idx = i
        
        # 공격 기술이 아예 없으면 랜덤 반환
        if not has_valid_attack and max_score <= 0.1:
            return random_fallback
            
        return best_idx

    @staticmethod
    def calculate_team_health(team_dict: Dict[str, SimplifiedPokemon]) -> float:
        """팀의 평균 체력 비율 계산 - 게임 종료 보상 함수에 사용"""
        total = 0.0
        count = 0
        for p in team_dict.values():
            if p.current_hp > 0 and p.max_hp > 0:
                total += (p.current_hp / p.max_hp)
                count += 1
        return total / max(1, count) if count > 0 else 0.0

    @staticmethod
    def evaluate_state(battle: SimplifiedBattle) -> float:
        """게임 종료 시 여러 상태를 고려한 보상 함수"""
        if battle.won: return 1.0

        # 패배 했더라도 상대 체력이 많이 남아있지 않다면 어느정도 보상
        if battle.lost:
            opp_hp = BattleHeuristics.calculate_team_health(battle.opponent_team)
            return (1.0 - opp_hp) * 0.2

        my_score = BattleHeuristics._calculate_side_score(battle.team)
        opp_score = BattleHeuristics._calculate_side_score(battle.opponent_team)

        # 균형 점수 계산
        if my_score + opp_score == 0: return 0.5
        return my_score / (my_score + opp_score)

    @staticmethod
    def _calculate_side_score(team: Dict[str, SimplifiedPokemon]) -> float:
        """체력 및 상태 (랭크) 기반 점수 계산"""
        score = 0.0
        for p in team.values():
            if p.current_hp > 0 and p.max_hp > 0:
                p_score = 1.0 + (p.current_hp / p.max_hp)
                if p.status is not None: p_score -= 0.5
                
                boosts = p.boosts.get('atk', 0) + p.boosts.get('spa', 0) + p.boosts.get('spe', 0)
                if boosts > 0: p_score += (boosts * 0.1)
                
                score += max(0.1, p_score)
        return score


class SmartRolloutPolicy:
    """
    MCTS 알고리즘에 사용되는 롤 아웃 정책. 완전 랜덤 선택이 아닌 휴리스틱 기반 선택을 함
    - 나: 가장 강한 기술 선택
    - 상대: 가장 강한 기술 선택 - 게임 이론 적용
    - 턴: 1턴 시뮬레이션 - 확률적인 요소로 인함
    - TODO : 더 정교한 정책 구현
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
            
            # 최선의 공격 찾기
            my_move_idx = BattleHeuristics.select_best_attack_idx(me, opp)

            # 최선의 공격 찾기 (상대)
            opp_move_idx = BattleHeuristics.select_best_attack_idx(opp, me)
            
            # 시뮬레이션 실행
            engine.simulate_turn(
                rollout_state,
                player_move_idx=my_move_idx,
                opponent_move_idx=opp_move_idx
            )

        return BattleHeuristics.evaluate_state(rollout_state)

class MCTSNode:
    """MCTS 트리의 노드 클래스"""
    def __init__(self, state: SimplifiedBattle, parent=None, action=None):
        self.state : SimplifiedBattle = state
        self.parent : SimplifiedBattle = parent
        self.action = action
        self.children : List[MCTSNode] = []
        self.visits = 0
        self.wins = 0.0
        self.untried_actions : List = self._get_available_actions()

    def _get_available_actions(self):
        actions = []
        # 가능한 모든 행동 (기술 사용 및 교체) 수집
        if hasattr(self.state, 'available_moves'):
            actions.extend(list(self.state.available_moves))
        if hasattr(self.state, 'available_switches'):
            actions.extend(list(self.state.available_switches))
        return actions

    # 선택 단계 - UCT 기준으로 최적 자식 노드 선택 (테스트 결과 1.4가 가장 적합)
    def best_child(self, c_param=1.4):
        if not self.children : return None

        log_n = math.log(self.visits)
        choices_weights = [
            (child.wins / child.visits) + c_param * math.sqrt(log_n / child.visits)
            for child in self.children
        ]

        return self.children[choices_weights.index(max(choices_weights))]

class MCTSSearcher:
    """MCTS 검색기 클래스"""
    def __init__(self, root_battle):
        self.engine = SimplifiedBattleEngine()
        if isinstance(root_battle, SimplifiedBattle):
            self.root_state = root_battle
        else:
            self.root_state = SimplifiedBattle(root_battle, fill_unknown_data=True)
            
        self.engine._sync_references(self.root_state)
        self.root = MCTSNode(self.root_state)
        
        self.policy = SmartRolloutPolicy(max_turns=1)
        self.llm_pruner = LLMPruner()

        self._apply_root_pruning()

    def search(self, iterations):
        # Fast Fail - 가능한 행동이 없으면 None 혹은 가능한 행동 하나 반환
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

    def _expand(self, node : MCTSNode) -> MCTSNode:
        action = random.choice(node.untried_actions)
        node.untried_actions.remove(action)

        new_state = node.state.clone()
        
        p_move_idx, p_switch = self._parse_action(new_state, action)
        
        # 확장 단계에서의 상대 행동도 휴리스틱으로 결정 - 최선의 선택을 한다고 가정
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

    def _backpropagate(self, node : MCTSNode, reward: float):
        while node:
            node.visits += 1
            node.wins += reward
            node = node.parent

    def _parse_action(self, state: SimplifiedBattle, action) -> Tuple[Optional[int], Optional[str]]:
        move_idx = None
        switch_name = None
        if hasattr(action, 'id'):  # Move
            if state.active_pokemon:
                for i, m in enumerate(state.active_pokemon.moves):
                    if m.id == action.id:
                        move_idx = i
                        break
        else:  # 교체의 경우
            switch_name = action.species
        return move_idx, switch_name
    
    def _apply_root_pruning(self):
        """루트 노드에서만 LLM 기반 프루닝 수행"""
        if not self.llm_pruner or not self.llm_pruner.is_available:
            return

        pruned_ids: Set[str] = self.llm_pruner.prune_actions(self.root_state, self.root.untried_actions)
        if not pruned_ids:
            return

        self.root.untried_actions = [
            action
            for action in self.root.untried_actions
            if self.llm_pruner.action_identifier(action) not in pruned_ids
        ]
    
def mcts_search(root_battle: SimplifiedBattle, iterations: int = 100, verbose: bool = False):
    
    searcher = MCTSSearcher(root_battle)
    best_action = searcher.search(iterations)
    
    if verbose:
        print(f"\n[MCTS 분석 결과] (총 반복: {iterations}회)")
        print("-" * 60)
        
        # 1. 자식 노드들을 '방문 횟수' 기준으로 정렬
        sorted_children = sorted(searcher.root.children, key=lambda c: c.visits, reverse=True)
        
        for i, child in enumerate(sorted_children):
            # 액션 이름 추출
            action = child.action
            if hasattr(action, 'id'):  # 기술
                action_type = "👊 Move"
                name = action.id
            else:  # 교체
                action_type = "🔄 Switch"
                name = action.species

            # 승률 계산
            win_rate = (child.wins / child.visits * 100) if child.visits > 0 else 0.0   
            
            print(f"[{i+1}] {action_type}: {name:<15} "
                  f"| 방문: {child.visits:3d}회 "
                  f"| 승률: {win_rate:5.1f}% ({child.wins:.1f}/{child.visits})")
        
        print("-" * 60)
        
        if best_action:
            final_name = best_action.id if hasattr(best_action, 'id') else best_action.species
            print(f"최종 선택: {final_name}")

    return best_action