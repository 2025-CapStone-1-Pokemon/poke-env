import math
import random
import copy
import sys
import os
import time

# SimplifiedBattle 시뮬레이터 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from sim.SimplifiedBattle import SimplifiedBattle
from sim.battle.SimplifiedBattleEngine import SimplifiedBattleEngine


class MCTSNode:
    def __init__(self, state, parent=None, action=None):
        self.state = state  # SimplifiedBattle 객체 (이미 변환되었다고 가정)
        self.parent = parent
        self.children = []
        self.visits = 0
        self.wins = 0
        self.action = action  # 이 노드에 도달하게 한 액션 (객체)
        
        # Action을 객체가 아닌 ID(문자열)로 관리하여 성능/안정성 확보
        self.available_actions = self._get_actions()
        # 아직 시도하지 않은 액션 (랜덤 선택을 위해 리스트 유지)
        self.untried_actions = list(self.available_actions)

    def _get_actions(self):
        """가능한 행동 목록 반환"""
        actions = []
        if hasattr(self.state, 'available_moves'):
            actions.extend(list(self.state.available_moves))
        if hasattr(self.state, 'available_switches'):
            actions.extend(list(self.state.available_switches))
        return actions if actions else []

    def best_child(self, exploration_weight=1.4):
        """UCT 기준 최적 자식 선택"""
        if not self.children:
            return None
        
        # 방문한 적 있는 자식만 계산 대상
        candidates = [c for c in self.children if c.visits > 0]
        if not candidates:
            return None

        # UCT 공식: WinRate + Exploration
        # log 계산을 한 번만 수행
        log_n = math.log(self.visits)
        
        return max(candidates, key=lambda c: (c.wins / c.visits) + 
                   exploration_weight * math.sqrt(log_n / c.visits))

    def expand(self):
        """자식 노드 확장 (Deepcopy 수행)"""
        if not self.untried_actions:
            return None

        # 1. 시도하지 않은 액션 중 하나 선택
        action = random.choice(self.untried_actions)
        self.untried_actions.remove(action)

        # 2. 상태 복제 (병목 지점 - 최적화 필요 시 clone() 구현 권장)
        new_state = copy.deepcopy(self.state)
        engine = SimplifiedBattleEngine()

        # 3. Action 적용을 위한 인덱스/ID 찾기
        player_move_idx = None
        player_switch_to = None

        if hasattr(action, 'id'):  # Move
            if new_state.active_pokemon:
                # for 루프 대신 next() 사용으로 속도 미세 최적화
                for i, m in enumerate(new_state.active_pokemon.moves):
                    if m.id == action.id:
                        player_move_idx = i
                        break
        else:  # Switch (Pokemon)
            # Species 대신 Identifier나 Species를 직접 사용
            # (SimplifiedBattleEngine이 species 문자열을 처리할 수 있어야 함)
            player_switch_to = action.species

        # 4. 1턴 시뮬레이션 (Expand 단계)
        # 상대방 행동: 랜덤 (추후 Heuristic으로 개선 가능)
        opp_move_idx = None
        if new_state.opponent_active_pokemon and new_state.opponent_active_pokemon.moves:
            opp_move_idx = random.randint(0, len(new_state.opponent_active_pokemon.moves) - 1)

        engine.simulate_turn(
            new_state,
            player_move_idx=player_move_idx,
            player_switch_to=player_switch_to,
            opponent_move_idx=opp_move_idx
        )

        # 5. 자식 노드 생성 및 연결
        child_node = MCTSNode(new_state, parent=self, action=action)
        self.children.append(child_node)
        
        return child_node

    def rollout(self, engine):
        """시뮬레이션 (끝까지 실행)"""
        # 이미 종료된 상태 체크
        if self.state.finished:
            return 1.0 if self.state.won else 0.0

        # 시뮬레이션용 상태 복제 (여기서도 deepcopy 발생 - 성능의 주범 2)
        # 롤아웃은 현재 노드 상태를 망가뜨리면 안 되므로 복사 필수
        # 하지만 expand 직후의 리프 노드라면 복사 없이 바로 써도 됨 (메모리 절약)
        # 여기서는 안전하게 복사
        rollout_state = copy.deepcopy(self.state)
        
        # verbose=False 강제
        result = engine.simulate_full_battle(rollout_state, max_turns=50, verbose=False)
        
        if result.won: return 1.0
        if result.lost: return 0.0
        return 0.5  # 무승부

    def backpropagate(self, reward):
        self.visits += 1
        self.wins += reward
        if self.parent:
            self.parent.backpropagate(reward)


def mcts_search(root_battle, iterations=50, verbose=False, n_workers=1):
    """
    최적화된 MCTS (Single Threaded) + 프로파일링
    """
    # === [프로파일링] 타이머 시작 ===
    t_start_total = time.time()
    perf_stats = {
        "init": 0.0,
        "selection": 0.0,
        "expansion": 0.0,
        "rollout": 0.0,
        "backprop": 0.0,
        "count_rollouts": 0
    }

    # 1. 초기 상태 변환
    t0 = time.time()
    if isinstance(root_battle, SimplifiedBattle):
        root_state = root_battle
    else:
        root_state = SimplifiedBattle(root_battle, fill_unknown_data=True)
    
    # 엔진 객체 재사용
    engine = SimplifiedBattleEngine()
    engine._sync_references(root_state)
    
    root = MCTSNode(root_state)
    perf_stats["init"] = time.time() - t0

    # 2. MCTS 루프
    for i in range(iterations):
        node = root

        # --- Selection ---
        t0 = time.time()
        while not node.state.finished and not node.untried_actions and node.children:
            node = node.best_child()
            if node is None: break 
        perf_stats["selection"] += time.time() - t0

        # --- Expansion ---
        t0 = time.time()
        if not node.state.finished and node.untried_actions:
            # expand 내부에서 deepcopy가 일어남
            node = node.expand()
        perf_stats["expansion"] += time.time() - t0

        # --- Simulation (Rollout) ---
        t0 = time.time()
        if node:
            # rollout 내부에서 deepcopy + simulate_full_battle 일어남
            reward = node.rollout(engine)
            perf_stats["count_rollouts"] += 1
        else:
            reward = 0
        perf_stats["rollout"] += time.time() - t0

        # --- Backpropagation ---
        t0 = time.time()
        if node:
            node.backpropagate(reward)
        perf_stats["backprop"] += time.time() - t0

    # 3. 최적 행동 선택
    if not root.children:
        return random.choice(root.available_actions) if root.available_actions else None

    best_child = max(root.children, key=lambda c: c.visits)
    
    # === [프로파일링] 결과 출력 ===
    t_total = time.time() - t_start_total
    if verbose:
        win_rate = (best_child.wins / best_child.visits) * 100
        action_name = best_child.action.id if hasattr(best_child.action, 'id') else best_child.action.species
        
        print(f"\n[MCTS 프로파일링 리포트] (Total: {t_total:.4f}s / Iterations: {iterations})")
        print(f" - Init       : {perf_stats['init']:.4f}s")
        print(f" - Selection  : {perf_stats['selection']:.4f}s")
        print(f" - Expansion  : {perf_stats['expansion']:.4f}s (1회 Deepcopy + 1턴 실행)")
        
        avg_rollout = (perf_stats['rollout'] / perf_stats['count_rollouts'] * 1000) if perf_stats['count_rollouts'] > 0 else 0
        print(f" - Rollout    : {perf_stats['rollout']:.4f}s (총 {perf_stats['count_rollouts']}회, 평균 {avg_rollout:.2f}ms/회)")
        print(f" - Backprop   : {perf_stats['backprop']:.4f}s")
        print(f"➜ 선택된 행동: {action_name} (승률: {win_rate:.1f}%, 방문: {best_child.visits})")

    return best_child.action