import math
import random
import copy
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
        # state가 이미 SimplifiedBattle이면 그대로 사용, 아니면 변환
        if isinstance(state, SimplifiedBattle):
            self.state = state
        else:
            # Battle 객체면 SimplifiedBattle로 변환
            self.state = SimplifiedBattle(state, fill_unknown_data=True)
            
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
            
        # pop() 대신 random.choice()를 사용하여 순서 편향 제거
        action = random.choice(self.untried_actions)
        self.untried_actions.remove(action)
        
        try:
            # 현재 상태를 복사 (simulate_turn이 in-place 수정하므로)
            new_state = copy.deepcopy(self.state)
            
            # 현재 상태에서 action을 적용한 1턴 시뮬레이션
            engine = SimplifiedBattleEngine()
            
            # action을 move_idx로 변환
            player_move_idx = None
            if hasattr(action, 'id'):  # Move 객체인 경우
                # active_pokemon의 moves에서 action의 인덱스 찾기
                if new_state.active_pokemon and new_state.active_pokemon.moves:
                    for idx, move in enumerate(new_state.active_pokemon.moves):
                        if move.id == action.id:
                            player_move_idx = idx
                            break
            
            # 1턴 시뮬레이션 (상대는 랜덤) - new_state를 직접 수정
            engine.simulate_turn(
                new_state,
                player_move_idx=player_move_idx,
                opponent_move_idx=None  # 상대는 랜덤
            )
            
            # 새로운 노드 생성 (SimplifiedBattle을 그대로 사용)
            child_node = MCTSNode(new_state, parent=self, action=action, is_simplified=True)
            self.children.append(child_node)
            return child_node
            
        except Exception as e:
            # 시뮬레이션 실패 시 현재 상태 복사 (fallback)
            print(f"[MCTS] Expand 실패: {e}, deepcopy fallback")
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

    def rollout(self, engine=None, verbose=False):
        """배틀 시뮬레이터를 사용한 rollout"""
        
        # 이미 종료된 상태면 즉시 반환
        if self.is_terminal():
            if self.state.won:
                if verbose:
                    print(f"[Rollout] 이미 종료: 승리")
                return 1.0
            elif self.state.lost:
                if verbose:
                    print(f"[Rollout] 이미 종료: 패배")
                return 0.0
            else:
                if verbose:
                    print(f"[Rollout] 이미 종료: 무승부")
                return 0.5
        
        # 엔진이 없으면 생성
        if engine is None:
            engine = SimplifiedBattleEngine()
        
        if verbose:
            # 상대 팀 상태 확인
            opponent_alive = sum(1 for p in self.state.opponent_team.values() if p.current_hp > 0)
            print(f"[Rollout] 시뮬레이션 시작 - 상대 팀: {opponent_alive}/{len(self.state.opponent_team)} 생존")
        
        # 배틀 시뮬레이션 실행 (최대 100턴)
        result = engine.simulate_full_battle(self.state, max_turns=100, verbose=False)
        
        if verbose:
            opponent_alive_after = sum(1 for p in result.opponent_team.values() if p.current_hp > 0)
            print(f"[Rollout] 시뮬레이션 완료: finished={result.finished}, won={result.won}, turn={result.turn}, 상대 생존={opponent_alive_after}")
        
        # 결과 평가
        if result.finished:
            if result.won:
                return 1.0  # 승리
            else:
                return 0.0  # 패배
        else:
            # 무승부인 경우
            return 0.5
    
    def backpropagate(self, result):
        # 결과를 바탕으로 노드와 그 부모 노드들의 값을 업데이트하는 로직을 구현합니다.
        self.visits += 1
        self.wins += result
        if self.parent:
            self.parent.backpropagate(1 - result)  # 부모는 반대 플레이어이므로 1-result

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
def mcts_search(root_state, iterations=30, verbose=False):
    """개선된 MCTS 검색 알고리즘"""
    root = MCTSNode(root_state)
    
    # 최소한의 exploration을 보장
    min_visits_per_child = max(1, iterations // 50)
    
    # 엔진 한 번만 생성
    engine = SimplifiedBattleEngine()
    
    if verbose:
        print(f"[MCTS] 검색 시작 (iterations={iterations})")
        print(f"[MCTS] Root actions: {len(root.available_actions)}")

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
        result = node.rollout(engine=engine, verbose=verbose)
        
        if verbose and i % 10 == 0:
            print(f"[MCTS] Iteration {i+1}/{iterations}: result={result}, children={len(root.children)}")

        # Backpropagation - 결과를 부모 노드들에게 전파
        if node:
            node.backpropagate(result)

    # 최적의 행동 선택 - 가장 많이 방문된 노드 선택 (더 안정적)
    if verbose:
        print(f"\n[MCTS] 최종 통계:")
        print(f"  Root children: {len(root.children)}")
        if root.children:
            sorted_children = sorted(root.children, key=lambda c: c.visits, reverse=True)
            for idx, child in enumerate(sorted_children[:5]):
                win_rate = (child.wins / child.visits * 100) if child.visits > 0 else 0
                print(f"  {idx+1}. visits={child.visits}, wins={child.wins}, rate={win_rate:.1f}%, action={child.action}")
    
    if root.children:
        # 방문 횟수 기준으로 선택 (exploitation)
        best_child = max(root.children, key=lambda child: child.visits)
        
        if verbose:
            best_rate = (best_child.wins / best_child.visits * 100) if best_child.visits > 0 else 0
            print(f"[MCTS] 선택된 행동: visits={best_child.visits}, rate={best_rate:.1f}%")
        
        # 승률도 고려한 혼합 선택
        if best_child.visits >= min_visits_per_child:
            return best_child.action
        else:
            # 충분히 탐색되지 않았다면 승률 기준으로 선택
            viable_children = [child for child in root.children if child.visits > 0]
            if viable_children:
                best_child = max(viable_children, key=lambda child: child.wins / child.visits)
                if verbose:
                    best_rate = (best_child.wins / best_child.visits * 100) if best_child.visits > 0 else 0
                    print(f"[MCTS] 재선택 (낮은 탐색): rate={best_rate:.1f}%")
                return best_child.action
    
    # 대안: 사용 가능한 행동 중 랜덤 선택
    if root.available_actions:
        if verbose:
            print(f"[MCTS] 랜덤 선택 (no children)")
        return random.choice(root.available_actions)
    
    if verbose:
        print(f"[MCTS] None 반환 (no actions available)")
    return None