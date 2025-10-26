"""
BattleState 기반 MCTS 구현
실제 시뮬레이션이 가능한 버전
"""

import math
import random
from typing import Optional, List, Union
from temp_battle_state import BattleState

class MCTSNode:
    def __init__(self, state: BattleState, parent=None, action=None):
        """
        MCTS 노드 초기화
        
        Parameters:
        - state: BattleState 객체 (복사 가능)
        - parent: 부모 노드
        - action: 이 노드에 도달한 액션
        """
        self.state = state  # BattleState (복사본)
        self.parent = parent
        self.action = action
        
        # MCTS 통계
        self.visits = 0
        self.wins = 0.0
        
        # 자식 노드
        self.children = []
        
        # 가능한 액션 (원본 Battle에서 가져와야 함)
        self.available_actions = []
        self.untried_actions = []
    
    def set_available_actions(self, actions: List):
        """
        사용 가능한 액션 설정
        
        Note: Battle 객체에서 가져온 액션을 여기에 설정
        """
        self.available_actions = actions.copy()
        self.untried_actions = actions.copy()
    
    def is_fully_expanded(self) -> bool:
        """모든 액션을 시도했는지"""
        return len(self.untried_actions) == 0
    
    def is_terminal(self) -> bool:
        """게임 종료 상태인지"""
        return self.state.is_terminal()
    
    def expand(self, original_battle) -> Optional['MCTSNode']:
        """
        새 자식 노드 생성
        
        핵심: 상태를 복사하고 액션을 적용
        
        Parameters:
        - original_battle: 원본 Battle 객체 (액션 정보 참조용)
        """
        if not self.untried_actions:
            return None
        
        # 아직 시도 안 한 액션 선택
        action = self.untried_actions.pop()
        
        # 상태 복사
        new_state = self.state.clone()
        
        # 액션 적용
        if hasattr(action, 'base_power'):
            # Move인 경우
            new_state.apply_move(action, is_my_turn=True)
        else:
            # Switch (Pokemon)인 경우
            # Pokemon 객체에서 인덱스 찾기
            switch_idx = self._find_pokemon_index(action, original_battle)
            if switch_idx is not None:
                new_state.apply_switch(switch_idx, is_my_turn=True)
        
        # 상대 턴 시뮬레이션 (간단 버전 - 랜덤 공격)
        self._simulate_opponent_turn(new_state, original_battle)
        
        # 새 자식 노드 생성
        child = MCTSNode(new_state, parent=self, action=action)
        
        # *** 중요: Child 노드도 available actions 설정 ***
        # 실제 배틀에서는 상황이 바뀌므로, 일단 같은 액션들 사용
        child.set_available_actions(self.available_actions)
        
        self.children.append(child)
        
        return child
    
    def _find_pokemon_index(self, pokemon, original_battle) -> Optional[int]:
        """
        Pokemon 객체의 팀 내 인덱스 찾기
        
        Parameters:
        - pokemon: poke-env Pokemon 객체
        - original_battle: Battle 객체
        """
        try:
            for idx, (name, p) in enumerate(original_battle.team.items()):
                if p.species == pokemon.species:
                    return idx
        except Exception:
            pass
        return None
    
    def _simulate_opponent_turn(self, state: BattleState, original_battle):
        """
        상대 턴 시뮬레이션 (간단 버전 - 랜덤 공격)
        
        실제 배틀에서는 상대의 기술을 모르므로:
        1. 상대 active pokemon의 타입으로 추정되는 기술 사용
        2. 랜덤한 위력(50~80) 선택
        """
        import random
        
        if state.is_terminal():
            return
        
        try:
            # 상대 active pokemon 찾기
            opp_active = next((p for p in state.opp_team if p['active']), None)
            my_active = next((p for p in state.my_team if p['active']), None)
            
            if not opp_active or not my_active:
                return
            
            # 간단한 가상 기술 생성 (상대 타입 기반)
            class FakeMove:
                def __init__(self, power, move_type, category):
                    self.base_power = power
                    self.type = f"PokemonType.{move_type.upper()}"
                    self.category = f"MoveCategory.{category.upper()}"
            
            # 상대 타입의 기술 사용 (STAB 보너스)
            opp_types = opp_active.get('types', ('normal',))
            move_type = opp_types[0] if opp_types else 'normal'
            
            # 물리/특수 랜덤 선택
            category = random.choice(['physical', 'special'])
            
            # 위력 랜덤 (50~80, 이전보다 약하게)
            power = random.randint(50, 80)
            
            fake_move = FakeMove(power, move_type, category)
            
            # 데미지 적용 (상대 -> 나)
            damage_fraction = state._calculate_damage(opp_active, my_active, fake_move)
            my_active['hp_fraction'] = max(0.0, my_active['hp_fraction'] - damage_fraction)
            
            if my_active['hp_fraction'] <= 0:
                my_active['fainted'] = True
                my_active['active'] = False
                
        except Exception:
            # 에러 발생시 무시
            pass
    
    def best_child(self, exploration_weight=1.4) -> Optional['MCTSNode']:
        """
        UCB1 공식으로 최선의 자식 선택
        """
        if not self.children:
            return None
        
        valid_children = [c for c in self.children if c.visits > 0]
        if not valid_children:
            return None
        
        def ucb_score(child):
            exploitation = child.wins / child.visits
            exploration = exploration_weight * math.sqrt(
                math.log(max(1, self.visits)) / child.visits
            )
            return exploitation + exploration
        
        return max(valid_children, key=ucb_score)
    
    def rollout(self) -> float:
        """
        시뮬레이션: BattleState 평가
        
        Returns: 0.0 ~ 1.0
        """
        return self.state.evaluate()
    
    def backpropagate(self, result: float):
        """
        결과를 루트까지 전파
        
        부모는 상대 플레이어이므로 1 - result
        """
        self.visits += 1
        self.wins += result
        
        if self.parent:
            self.parent.backpropagate(1.0 - result)


def mcts_search(battle, iterations=50, debug=False) -> Optional[Union[object, None]]:
    """
    BattleState 기반 MCTS 검색
    
    Parameters:
    - battle: poke-env Battle 객체
    - iterations: 시뮬레이션 반복 횟수
    - debug: 디버깅 정보 출력
    
    Returns: 최적의 액션
    """
    # 1. BattleState 생성
    initial_state = BattleState(battle)
    root = MCTSNode(initial_state)
    
    # 2. 사용 가능한 액션 설정
    available_actions = []
    try:
        if hasattr(battle, 'available_moves'):
            available_actions.extend(list(battle.available_moves))
        if hasattr(battle, 'available_switches'):
            available_actions.extend(list(battle.available_switches))
    except Exception:
        pass
    
    if not available_actions:
        return None
    
    root.set_available_actions(available_actions)
    
    if debug:
        print(f"\n[MCTS Debug] Available actions: {len(available_actions)}")
        print(f"[MCTS Debug] Initial evaluation: {initial_state.evaluate():.3f}")
    
    # 3. MCTS 반복
    successful_iterations = 0
    for i in range(iterations):
        node = root
        
        # Selection
        selection_depth = 0
        while not node.is_terminal() and node.is_fully_expanded():
            node = node.best_child()
            selection_depth += 1
            if node is None:
                if debug and i < 3:
                    print(f"  [Iter {i}] Selection failed at depth {selection_depth}")
                break
        
        if debug and i < 3:
            print(f"  [Iter {i}] Selection depth: {selection_depth}, is_terminal: {node.is_terminal() if node else 'None'}, is_fully_expanded: {node.is_fully_expanded() if node else 'None'}")
        
        # Expansion
        if node is not None and not node.is_terminal() and not node.is_fully_expanded():
            node = node.expand(battle)  # 원본 Battle 전달
        
        if node is None:
            if debug and i < 3:
                print(f"  [Iter {i}] Node is None after expansion")
            continue
        
        # Simulation
        result = node.rollout()
        
        # Backpropagation
        node.backpropagate(result)
        successful_iterations += 1
    
    if debug:
        print(f"[MCTS Debug] Successful iterations: {successful_iterations}/{iterations}")
        print(f"[MCTS Debug] Root visits: {root.visits}")
        print(f"[MCTS Debug] Children created: {len(root.children)}")
        if root.children:
            for i, child in enumerate(root.children[:3]):  # 상위 3개만
                win_rate = child.wins / child.visits if child.visits > 0 else 0
                print(f"  Child {i}: {child.action} - visits={child.visits}, win_rate={win_rate:.2%}")
    
    # 4. 최선의 액션 선택
    if root.children:
        # Win rate가 가장 높은 child 선택 (visits가 충분한 것 중)
        valid_children = [c for c in root.children if c.visits > 0]
        if valid_children:
            best_child = max(valid_children, key=lambda c: c.wins / c.visits)
            if debug:
                win_rate = best_child.wins / best_child.visits if best_child.visits > 0 else 0
                print(f"[MCTS Debug] Best action: {best_child.action} (win_rate={win_rate:.2%})")
            return best_child.action
    
    # Fallback
    if available_actions:
        if debug:
            print(f"[MCTS Debug] No children! Using first action")
        return available_actions[0]
    
    return None
