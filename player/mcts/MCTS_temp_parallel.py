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
from sim.SimplifiedPokemon import SimplifiedPokemon
from typing import Dict


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
        new_state : SimplifiedBattle = self.state.clone()
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

        # 4. 1턴 시뮬레이션
        # [수정] 상대방 행동: Random -> Greedy (가장 아픈 기술)
        opp_move_idx = None
        if new_state.opponent_active_pokemon and new_state.opponent_active_pokemon.moves:
            # 50% 확률로 Greedy, 50% 확률로 Random (완전 Greedy로 하면 너무 쫄보가 될 수 있음)
            # 하지만 승률을 높이려면 일단 100% Greedy로 테스트해보는 게 좋아.
            opp_move_idx = self._select_greedy_opponent_action(new_state)
            
            # 만약 적절한 기술을 못 찾았으면(변화기뿐이거나 등) 랜덤
            if opp_move_idx is None:
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

    def rollout(self, engine: SimplifiedBattleEngine):
        """
        [개선된 롤아웃]
        1. 30턴 -> 10턴으로 단축 (먼 미래의 랜덤성은 노이즈임)
        2. 약한 휴리스틱 적용 (공격 기술 선호)
        """
        if self.state.finished:
            return self._evaluate_final_score(self.state)

        rollout_state : SimplifiedBattle = self.state.clone()
        
        # [핵심 변경] 30턴은 너무 깁니다. 10턴만 봅니다.
        # 그 이후는 _evaluate_final_score(체력 차이)가 판단하게 맡깁니다.
        for _ in range(5):
            if rollout_state.finished: break
            
            # --- 내 행동 (공격 지향 랜덤) ---
            my_move_idx = None
            if rollout_state.active_pokemon and rollout_state.active_pokemon.moves:
                # 가능한 기술 중 '공격기(Physical/Special)'만 추림
                attacks = [i for i, m in enumerate(rollout_state.active_pokemon.moves) 
                           if m.category.name != 'STATUS' and m.current_pp > 0]
                
                # 80% 확률로 공격기 중 랜덤 선택, 20%는 그냥 아무거나(변화기 포함)
                if attacks and random.random() < 0.8:
                    my_move_idx = random.choice(attacks)
                else:
                    my_move_idx = random.randint(0, len(rollout_state.active_pokemon.moves) - 1)

            # --- 상대 행동 (완전 랜덤 유지 - 네 요청대로) ---
            opp_move_idx = None
            if rollout_state.opponent_active_pokemon and rollout_state.opponent_active_pokemon.moves:
                opp_move_idx = random.randint(0, len(rollout_state.opponent_active_pokemon.moves) - 1)
            
            engine.simulate_turn(
                rollout_state,
                player_move_idx=my_move_idx,
                opponent_move_idx=opp_move_idx
            )

        return self._evaluate_final_score(rollout_state)

    def _evaluate_final_score(self, battle_state):
        """
        [보상 함수 v2] HP뿐만 아니라 상태이상, 랭크업까지 종합 평가
        """
        # 1. 승패가 났으면 절대적 점수 부여
        if battle_state.won: return 1.0
        if battle_state.lost: 
            # 졌어도 상대를 많이 잡았으면 약간의 점수 (최대 0.2)
            opp_hp = self._calculate_team_health(battle_state.opponent_team)
            return (1.0 - opp_hp) * 0.2

        # 2. 내 점수 계산
        my_score = 0
        for p in battle_state.team.values():
            if p.current_hp > 0 and p.max_hp > 0:
                # 기본 HP 점수 (마리당 1점 + 체력 비율)
                p_score = 1.0 + (p.current_hp / p.max_hp)
                
                # [추가] 상태이상 페널티 (마비/화상/수면 등은 0.5마리 잃은 셈 침)
                if p.status is not None:
                    p_score -= 0.5
                
                # [추가] 랭크업 보너스 (공격/특공/스피드가 오르면 유리함)
                # 너무 과하면 랭크업만 하다가 죽으니 0.1 정도로 소소하게
                offensive_boosts = p.boosts.get('atk', 0) + p.boosts.get('spa', 0) + p.boosts.get('spe', 0)
                if offensive_boosts > 0:
                    p_score += (offensive_boosts * 0.1)
                
                my_score += max(0.1, p_score) # 음수 방지

        # 3. 상대 점수 계산
        opp_score = 0
        for p in battle_state.opponent_team.values():
            if p.current_hp > 0 and p.max_hp > 0:
                p_score = 1.0 + (p.current_hp / p.max_hp)
                
                # 상대가 상태이상이면 내 이득
                if p.status is not None:
                    p_score -= 0.5
                
                # 상대가 랭크업 했으면 내 손해
                offensive_boosts = p.boosts.get('atk', 0) + p.boosts.get('spa', 0) + p.boosts.get('spe', 0)
                if offensive_boosts > 0:
                    p_score += (offensive_boosts * 0.1)
                    
                opp_score += max(0.1, p_score)

        # 4. 비율 계산 (0.0 ~ 1.0)
        if my_score + opp_score == 0: return 0.5
        return my_score / (my_score + opp_score)

    def _calculate_team_health(self, team_dict: Dict[str, SimplifiedPokemon]) -> float:
        """
        팀의 남은 체력 총합 비율 계산 (0.0 ~ 1.0)
        Args:
            team_dict: { 'p1: Pikachu': SimplifiedPokemon 객체, ... }
        """
        total_hp_ratio = 0.0
        count = 0
        
        # team_dict.values()의 요소가 SimplifiedPokemon임을 명시
        for p in team_dict.values():
            # [수정] 'if not p'는 p가 객체일 때 False가 되므로 삭제했습니다.
            # 대신 기절하지 않았는지(current_hp > 0) 확인합니다.
            if p.current_hp > 0 and p.max_hp > 0:
                total_hp_ratio += (p.current_hp / p.max_hp)
                count += 1
        
        # 살아있는 포켓몬들의 평균 체력 비율 (0으로 나누기 방지)
        return total_hp_ratio / max(1, count) if count > 0 else 0.0

    def backpropagate(self, reward):
        self.visits += 1
        self.wins += reward
        if self.parent:
            self.parent.backpropagate(reward)

        # 헬퍼 클래스
    def _select_greedy_opponent_action(self, battle : SimplifiedBattle):
        """
        [상대방 모델링] Greedy 전략 시뮬레이션
        상대가 쓸 수 있는 기술 중 가장 강력한(위력 * 상성) 기술의 인덱스를 반환
        """
        opponent = battle.opponent_active_pokemon
        me = battle.active_pokemon
        
        if not opponent or not me or not opponent.moves:
            return None

        best_move_idx = 0
        max_threat = -1.0
        
        # 상대의 모든 기술을 훑어봄
        for i, move in enumerate(opponent.moves):
            if move.current_pp <= 0: continue # PP 없으면 패스
            
            # 변화기는 위협도 0으로 취급 (단순화)
            if move.category.name == 'STATUS':
                threat = 0.0
            else:
                # 1. 위력
                threat = move.base_power
                
                # 2. 자속 보정 (STAB) - 1.5배
                if move.type in opponent.types:
                    threat *= 1.5
                
                # 3. 타입 상성 (약점 찌르기)
                # SimplifiedPokemon에 있는 damage_multiplier 메서드 활용
                # 주의: 내(me)가 방어자 입장이므로 내 타입에 대한 상성을 계산해야 함
                multiplier = me.damage_multiplier(move.type)
                threat *= multiplier
            
            if threat > max_threat:
                max_threat = threat
                best_move_idx = i
                
        return best_move_idx


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

    # 가능한 모든 행동(기술 + 교체)을 수집
    all_actions = []
    if hasattr(root_state, 'available_moves'): 
        all_actions.extend(root_state.available_moves)
    if hasattr(root_state, 'available_switches'): 
        all_actions.extend(root_state.available_switches)
    
    # 1-1. 선택지가 0개? (발버둥 상황 or 버그) -> None 반환하면 랜덤 플레이어가 알아서 처리
    if not all_actions:
        return None

    # 1-2. 선택지가 딱 1개? -> 고민하지 말고 바로 선택
    if len(all_actions) == 1:
        forced_action = all_actions[0]
        action_name = forced_action.id if hasattr(forced_action, 'id') else forced_action.species
        
        if verbose:
            print(f"⚡ [Fast-Skip] 강제된 행동이므로 MCTS 생략: {action_name}")
            
        return forced_action
    
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
