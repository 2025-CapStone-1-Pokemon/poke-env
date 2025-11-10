import math
import random
import sys
import os

# SimplifiedBattle 시뮬레이터 import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sim'))
from SimplifiedBattle import SimplifiedBattle
from battle.SimplifiedBattleEngine import SimplifiedBattleEngine

class MCTSNode:
    def __init__(self, state, parent=None, action=None, is_simplified=False):
        """
        Args:
            state: Battle 객체 또는 SimplifiedBattle 객체
            parent: 부모 노드
            action: 이 노드로 오게 한 액션
            is_simplified: state가 이미 SimplifiedBattle인지 여부
        """
        # state가 Battle 객체면 SimplifiedBattle로 변환, 아니면 그대로 사용
        if not is_simplified and hasattr(state, 'team'):  # Battle 객체 확인
            self.state = SimplifiedBattle(state, fill_unknown_data=True)
        else:
            self.state = state
            
        self.parent = parent                  # 부모 노드
        self.children = []                    # 자식 노드 목록
        self.visits = 0                       # 방문 횟수
        self.wins = 0                         # 승리 횟수
        self.action = action                  # 이 노드로 오게 한 액션
        self.available_actions = self.get_actions()  # 가능한 이동
        self.untried_actions = self.available_actions.copy()  # 아직 시도하지 않은 액션들

    def best_child(self, exploration_weight=1.4):
        # UCT(Upper Confidence Bound for Trees) 공식을 사용하여 최적의 자식 노드를 선택합니다.
        if not self.children:
            return None
        
        # 방문 횟수가 0인 자식들을 필터링
        valid_children = [child for child in self.children if child.visits > 0]
        if not valid_children:
            return self.children[0] if self.children else None
            
        return max(valid_children, key=lambda child:
                   (child.wins / child.visits) +
                   exploration_weight * math.sqrt(math.log(max(1, self.visits)) / child.visits))

    def is_fully_expanded(self):
        # 모든 가능한 액션이 시도되었는지 확인
        return len(self.untried_actions) == 0

    def expand(self):
        """새로운 자식 노드를 생성하고 추가"""
        if not self.untried_actions:
            return None
            
        action = self.untried_actions.pop()
        
        try:
            # 현재 상태에서 action을 적용한 1턴 시뮬레이션
            engine = SimplifiedBattleEngine()
            
            # action을 move_idx로 변환
            player_move_idx = None
            if hasattr(action, 'id'):  # Move 객체인 경우
                # active_pokemon의 moves에서 action의 인덱스 찾기
                if self.state.active_pokemon and self.state.active_pokemon.moves:
                    for idx, move in enumerate(self.state.active_pokemon.moves):
                        if move.id == action.id:
                            player_move_idx = idx
                            break
            
            # 1턴 시뮬레이션 (상대는 랜덤)
            new_state = engine.simulate_turn(
                self.state,
                player_move_idx=player_move_idx,
                opponent_move_idx=None  # 상대는 랜덤
            )
            
            # 새로운 노드 생성 (SimplifiedBattle을 그대로 사용)
            child_node = MCTSNode(new_state, parent=self, action=action, is_simplified=True)
            self.children.append(child_node)
            return child_node
            
        except Exception as e:
            # 시뮬레이션 실패 시 현재 상태 복사
            import copy
            new_state = copy.deepcopy(self.state)
            child_node = MCTSNode(new_state, parent=self, action=action, is_simplified=True)
            self.children.append(child_node)
            return child_node

    def update(self, reward):
        # 노드의 방문 횟수와 가치를 업데이트하는 로직을 구현합니다.
        self.visits += 1
        self.wins += reward

    def is_terminal(self):
        # 현재 상태가 종료 상태인지 확인하는 로직
        # 게임이 종료되었는지 확인
        return self.state.finished

    def rollout(self):
        """배틀 시뮬레이터를 사용한 rollout"""
        
        # 이미 종료된 상태면 즉시 반환
        if self.is_terminal():
            if self.state.won:
                return 1.0
            elif self.state.lost:
                return 0.0
            else:
                return 0.5
        
        try:
            # 시뮬레이션 엔진 생성
            engine = SimplifiedBattleEngine()
            
            # 배틀 시뮬레이션 실행 (최대 100턴)
            # self.state는 이미 SimplifiedBattle 객체임
            result = engine.simulate_full_battle(self.state, max_turns=100, verbose=False)
            
            # 결과 평가
            if result.finished:
                if result.won:
                    return 1.0  # 승리
                else:
                    return 0.0  # 패배
            else:
                # 무승부인 경우
                return 0.5
                
        except Exception as e:
            # 시뮬레이션 실패 시 휴리스틱 평가로 fallback
            print(f"[MCTS] 시뮬레이션 실패: {e}, 휴리스틱 평가 사용")
            return self._heuristic_evaluation()
    
    def _heuristic_evaluation(self):
        """휴리스틱 기반 평가 (fallback용)"""
        
        if self.is_terminal():
            if self.state.won:
                return 1.0
            elif self.state.lost:
                return 0.0
            else:
                return 0.5
        
        try:
            # 포켓몬 상태 분석
            my_team = list(self.state.team.values())
            opp_team = list(self.state.opponent_team.values())
            
            # 살아있는 포켓몬 수
            my_alive = sum(1 for p in my_team if not p.fainted)
            opp_alive = sum(1 for p in opp_team if not p.fainted)
            
            # 기본 승패 판정
            if my_alive == 0:
                return 0.0
            elif opp_alive == 0:
                return 1.0
            
            score = 0.5  # 기본 점수
            
            # 1. 포켓몬 수 우세도 (40% 가중치)
            pokemon_advantage = (my_alive - opp_alive) / 6.0  # 최대 6마리
            score += pokemon_advantage * 0.4
            
            # 2. HP 우세도 (30% 가중치)
            my_total_hp = sum(p.current_hp_fraction for p in my_team if not p.fainted)
            opp_total_hp = sum(p.current_hp_fraction for p in opp_team if not p.fainted)
            
            if my_alive > 0 and opp_alive > 0:
                my_avg_hp = my_total_hp / my_alive
                opp_avg_hp = opp_total_hp / opp_alive
                hp_advantage = (my_avg_hp - opp_avg_hp)
                score += hp_advantage * 0.3
            
            # 3. 현재 활성 포켓몬 HP 비교 (20% 가중치)
            if (hasattr(self.state, 'active_pokemon') and self.state.active_pokemon and
                hasattr(self.state, 'opponent_active_pokemon') and self.state.opponent_active_pokemon):
                
                my_active_hp = self.state.active_pokemon.current_hp_fraction
                opp_active_hp = self.state.opponent_active_pokemon.current_hp_fraction
                active_hp_diff = my_active_hp - opp_active_hp
                score += active_hp_diff * 0.2
            
            # 4. 타입 상성 간단 평가 (10% 가중치)
            type_bonus = self.simple_type_evaluation()
            score += type_bonus * 0.1
            
            # 점수를 0-1 범위로 제한
            return max(0.1, min(0.9, score))  # 극단값 방지
            
        except Exception as e:
            # 오류 발생시 중립적 평가
            return 0.5

    def backpropagate(self, result):
        # 결과를 바탕으로 노드와 그 부모 노드들의 값을 업데이트하는 로직을 구현합니다.
        self.visits += 1
        self.wins += result
        if self.parent:
            self.parent.backpropagate(1 - result)  # 부모는 반대 플레이어이므로 1-result

    def simple_type_evaluation(self):
        """타입 상성에 기반한 간단한 평가"""
        try:
            if (not hasattr(self.state, 'active_pokemon') or not self.state.active_pokemon or
                not hasattr(self.state, 'opponent_active_pokemon') or not self.state.opponent_active_pokemon):
                return 0.0
            
            my_pokemon = self.state.active_pokemon
            opp_pokemon = self.state.opponent_active_pokemon
            
            # 내가 상대에게 줄 수 있는 피해량 추정
            my_damage_multiplier = 1.0
            for move in self.state.available_moves:
                if hasattr(move, 'type') and hasattr(move.type, 'damage_multiplier'):
                    try:
                        multiplier = move.type.damage_multiplier(
                            opp_pokemon.type_1,
                            opp_pokemon.type_2 if hasattr(opp_pokemon, 'type_2') else None
                        )
                        my_damage_multiplier = max(my_damage_multiplier, multiplier)
                    except:
                        continue
            
            # 상대가 나에게 줄 수 있는 피해량 추정 (보수적으로)
            opp_damage_multiplier = 1.5  # 기본값을 약간 높게 설정
            
            # 타입 우세도 계산 (-0.3 ~ 0.3)
            type_advantage = (my_damage_multiplier - opp_damage_multiplier) / 3.0
            return max(-0.3, min(0.3, type_advantage))
            
        except Exception:
            return 0.0

    def get_actions(self):
        # 현재 상태에서 가능한 모든 이동을 반환하는 로직을 구현합니다.
        try:
            actions = []
            if hasattr(self.state, 'available_moves'):
                actions.extend(list(self.state.available_moves))
            if hasattr(self.state, 'available_switches'):
                actions.extend(list(self.state.available_switches))
            return actions if actions else [None]  # 빈 리스트 방지
        except:
            return [None]

# 여기서 root_state는 최초의 battle 객체를 의미한다.
def mcts_search(root_state, iterations=1000):
    """개선된 MCTS 검색 알고리즘"""
    root = MCTSNode(root_state)
    
    # 최소한의 exploration을 보장
    min_visits_per_child = max(1, iterations // 50)

    for i in range(iterations):
        node = root

        # Selection - UCB1을 사용한 최적 노드 선택
        while not node.is_terminal() and node.is_fully_expanded():
            # exploration weight를 동적으로 조정
            exploration_weight = 1.4 * (1 - i / iterations)  # 시간이 지날수록 exploitation 증가
            node = node.best_child(exploration_weight)
            if node is None:
                break

        # Expansion - 새로운 자식 노드 생성
        if not node.is_terminal() and not node.is_fully_expanded():
            node = node.expand()
            if node is None:
                continue

        # Simulation - 게임 끝까지 시뮬레이션
        result = node.rollout()

        # Backpropagation - 결과를 부모 노드들에게 전파
        if node:
            node.backpropagate(result)

    # 최적의 행동 선택 - 가장 많이 방문된 노드 선택 (더 안정적)
    if root.children:
        # 방문 횟수 기준으로 선택 (exploitation)
        best_child = max(root.children, key=lambda child: child.visits)
        
        # 승률도 고려한 혼합 선택
        if best_child.visits >= min_visits_per_child:
            return best_child.action
        else:
            # 충분히 탐색되지 않았다면 승률 기준으로 선택
            viable_children = [child for child in root.children if child.visits > 0]
            if viable_children:
                best_child = max(viable_children, key=lambda child: child.wins / child.visits)
                return best_child.action
    
    # 대안: 사용 가능한 행동 중 랜덤 선택
    if root.available_actions:
        return random.choice(root.available_actions)
    
    return None