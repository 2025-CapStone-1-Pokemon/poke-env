"""
실제 전투 vs 시뮬레이션 승패 비교 통합 테스트 (병렬 처리)

실제 전투를 진행하면서 각 턴에서 시뮬레이션을 돌려서 최종 승패가 같은지 확인합니다.
병렬 처리로 빠른 검증을 수행합니다.
"""

import sys
import os
import asyncio
import copy
import random
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from collections import defaultdict
from typing import Optional, Dict
from poke_env.battle.pokemon import Pokemon
from datetime import datetime
import importlib.util

# 경로 추가 (먼저 경로 설정)
current_dir = os.path.dirname(os.path.abspath(__file__))
test_dir = os.path.dirname(current_dir)  # test/
sim_dir = os.path.dirname(test_dir)      # sim/
poke_env_dir = os.path.dirname(sim_dir)  # poke-env/
player_dir = os.path.join(poke_env_dir, 'player')

sys.path.insert(0, poke_env_dir)
sys.path.insert(0, sim_dir)

# 배틀 데이터 저장 관련 함수 import
from battle_data_saver import (
    simplified_pokemon_to_dict,
    simplified_battle_to_dict,
    save_turn_simulation_data,
    save_battle_turn_inputs,
    save_battle_turn_results,
    print_turn_result
)

# BattleLogMixin import (battle_logger.py에서 동적 로드)
battle_logger_path = os.path.join(player_dir, 'battle_logger.py')
spec = importlib.util.spec_from_file_location("battle_logger", battle_logger_path)
battle_logger_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(battle_logger_module)
BattleLogMixin = battle_logger_module.BattleLogMixin

from poke_env.player import Player
from poke_env.battle import Battle
from sim.SimplifiedBattle import SimplifiedBattle
from sim.battle.SimplifiedBattleEngine import SimplifiedBattleEngine

# 스냅샷 구조체 정의
class BattleSnapshot:
    def __init__(self, turn: int, battle, 
                 active_pokemon: Optional[Pokemon], 
                 active_opponent_pokemon: Optional[Pokemon], 
                 team: Dict, opponent_team: Dict, 
                 order_type: Optional[str] = None, 
                 move_idx: Optional[int] = None, 
                 switch_to: Optional[Pokemon] = None,
                 opponent_action_info: Optional[Dict] = None):
        self.turn = turn
        self.battle = battle
        self.active_pokemon = active_pokemon
        self.active_opponent_pokemon = active_opponent_pokemon
        self.team = team
        self.opponent_team = opponent_team
        self.order_type = order_type
        self.move_idx = move_idx
        self.switch_to = switch_to
        self.opponent_action_info = opponent_action_info or {}


# === 시뮬레이션 함수 (병렬 처리용) ===

def _simulate_turn(args):
    """시뮬레이션 함수 - current_snapshot 상태에서 1턴 시뮬레이션, next_snapshot의 실제 결과와 비교"""
    
    # ✅ 튜플 언팩
    i, turn, current_battle_state, player_action_info, opponent_action_info, actual_next_snapshot = args
    
    # 🔴 디버깅: 첫 턴에만 opponent_action_info 상세 출력
    if i == 0 and turn == 1:
        print(f"\n【 디버깅: opponent_action_info 구조 확인 】")
        print(f"  opponent_action_info: {opponent_action_info}")
        print(f"  - order_type: {opponent_action_info.get('order_type')}")
        print(f"  - move_idx: {opponent_action_info.get('move_idx')} (타입: {type(opponent_action_info.get('move_idx'))})")
        print(f"  - move_name: {opponent_action_info.get('move_name')}")
        print(f"  - switch_to: {opponent_action_info.get('switch_to')}")
        print()
    
    # 플레이어 move_idx 추출
    player_move_idx = None
    if player_action_info.get('order_type') == 'move':
        player_move_idx = player_action_info.get('move_idx')
    
    # 상대 move_idx 추출
    opponent_move_idx = None
    if opponent_action_info.get('order_type') == 'move':
        opponent_move_idx = opponent_action_info.get('move_idx')
        
        # 🔴 디버깅: opponent_move_idx 상세 정보
        if i == 0 and turn == 1:
            print(f"【 디버깅: move_idx 추출 결과 】")
            print(f"  player_move_idx: {player_move_idx} (타입: {type(player_move_idx).__name__})")
            print(f"  opponent_move_idx: {opponent_move_idx} (타입: {type(opponent_move_idx).__name__})")
            if opponent_move_idx is None:
                print(f"  ⚠️ opponent_move_idx가 None입니다!")
                print(f"    -> move_name: {opponent_action_info.get('move_name')}")
            print()
    
    # 현재 상태에서 1턴 시뮬레이션 (실제 선택한 기술로)
    engine = SimplifiedBattleEngine(gen=9)

    # 1회만 시뮬레이션
    one_result : SimplifiedBattle = engine.simulate_turn(
        copy.deepcopy(current_battle_state),
        player_move_idx=player_move_idx,
        opponent_move_idx=opponent_move_idx,
        verbose=False
    )
        
    # 첫 번째 시뮬레이션만 디버깅
    if i == 0 and turn == 1:
        print(f"\n【 디버깅: 1회 시뮬레이션 결과 】")
        print(f"  Turn: {turn}")
        print(f"  현재 배틀 상태:")
        print(f"    - 플레이어 활성 포켓몬: {current_battle_state.active_pokemon.species if current_battle_state.active_pokemon else 'None'} (HP: {current_battle_state.active_pokemon.current_hp}/{current_battle_state.active_pokemon.max_hp if current_battle_state.active_pokemon else 0})")
        print(f"    - 상대 활성 포켓몬: {current_battle_state.opponent_active_pokemon.species if current_battle_state.opponent_active_pokemon else 'None'} (HP: {current_battle_state.opponent_active_pokemon.current_hp}/{current_battle_state.opponent_active_pokemon.max_hp if current_battle_state.opponent_active_pokemon else 0})")
        print(f"  시뮬레이션 결과:")
        print(f"    - 플레이어 활성 포켓몬: {one_result.active_pokemon.species if one_result.active_pokemon else 'None'} (HP: {one_result.active_pokemon.current_hp}/{one_result.active_pokemon.max_hp if one_result.active_pokemon else 0})")
        print(f"    - 상대 활성 포켓몬: {one_result.opponent_active_pokemon.species if one_result.opponent_active_pokemon else 'None'} (HP: {one_result.opponent_active_pokemon.current_hp}/{one_result.opponent_active_pokemon.max_hp if one_result.opponent_active_pokemon else 0})")
        print(f"  플레이어 액션: {player_action_info.get('order_type')} (move_idx: {player_move_idx})")
        print(f"  상대 액션: {opponent_action_info.get('order_type')} (move_idx: {opponent_move_idx})")
        print()
    
    # 1회 시뮬 결과
    one_player_hp = one_result.active_pokemon.current_hp if one_result.active_pokemon else 0
    one_opponent_hp = one_result.opponent_active_pokemon.current_hp if one_result.opponent_active_pokemon else 0
    
    one_player_status = one_result.active_pokemon.status.name if one_result.active_pokemon and one_result.active_pokemon.status else None
    one_opponent_status = one_result.opponent_active_pokemon.status.name if one_result.opponent_active_pokemon and one_result.opponent_active_pokemon.status else None

    # 1회 active pokemon
    one_active_pokemon = one_result.active_pokemon.species if one_result.active_pokemon else None
    one_active_opponent_pokemon = one_result.opponent_active_pokemon.species if one_result.opponent_active_pokemon else None
    
    # 실제 결과 (턴 n+1 실제) - active_pokemon이 None일 때 처리
    actual_player_hp = actual_next_snapshot.active_pokemon.current_hp if actual_next_snapshot.active_pokemon else 0
    actual_opponent_hp = actual_next_snapshot.active_opponent_pokemon.current_hp if actual_next_snapshot.active_opponent_pokemon else 0
    actual_player_status = actual_next_snapshot.active_pokemon.status.name if actual_next_snapshot.active_pokemon and actual_next_snapshot.active_pokemon.status else None
    actual_opponent_status = actual_next_snapshot.active_opponent_pokemon.status.name if actual_next_snapshot.active_opponent_pokemon and actual_next_snapshot.active_opponent_pokemon.status else None
    actual_active_pokemon_species = actual_next_snapshot.active_pokemon.species if actual_next_snapshot.active_pokemon else None
    actual_active_opponent_pokemon_species = actual_next_snapshot.active_opponent_pokemon.species if actual_next_snapshot.active_opponent_pokemon else None
    
    # HP 오차 계산 (1회 결과 사용)
    one_player_hp_error = abs(one_player_hp - actual_player_hp)
    one_opponent_hp_error = abs(one_opponent_hp - actual_opponent_hp)
    
    # 디버깅: 첫 번째 턴만 실제 스냅샷 출력
    if i == 0 and turn == 1:
        print(f"\n【 디버깅: 실제 스냅샷 (턴 n+1) 】")
        print(f"  플레이어: {actual_active_pokemon_species} (HP: {actual_player_hp}, 상태: {actual_player_status})")
        print(f"  상대: {actual_active_opponent_pokemon_species} (HP: {actual_opponent_hp}, 상태: {actual_opponent_status})")
    
    return {
        'turn': turn,
        'one_player_hp_error': one_player_hp_error,
        'one_opponent_hp_error': one_opponent_hp_error,
        'one_player_hp': one_player_hp,
        'actual_player_hp': actual_player_hp,
        'one_opponent_hp': one_opponent_hp,
        'actual_opponent_hp': actual_opponent_hp,
        'one_player_status': one_player_status,
        'one_opponent_status': one_opponent_status,
        'actual_player_status': actual_player_status,
        'actual_opponent_status': actual_opponent_status,
        'player_action': player_action_info.get('order_type'),
        'one_active_pokemon': one_active_pokemon,
        'actual_active_pokemon': actual_active_pokemon_species,
        'one_active_opponent_pokemon': one_active_opponent_pokemon,
        'actual_active_opponent_pokemon': actual_active_opponent_pokemon_species,
        'one_player_status_match': (one_player_status == actual_player_status),
        'one_opponent_status_match': (one_opponent_status == actual_opponent_status),
    }


# === 전투 기록 및 검증 함수 ===

def test_battle_simulation(n_battles: int = 100, battle_format: str = "gen9randombattle", n_workers: int = 10):
    """
    실제 전투와 시뮬레이션 승패 비교 테스트 (병렬 처리)
    
    Args:
        n_battles: 테스트할 배틀 수
        battle_format: 배틀 포맷
        n_workers: 병렬 처리 워커 수
    """
    print("=" * 70)
    print(f"실제 전투 vs 시뮬레이션 검증 (병렬 처리: {n_workers}개 워커)")
    print("=" * 70)
    
    # 전투 기록을 저장할 리스트
    battle_records = []
    
    # 비동기 테스트 실행
    async def run_battles():
        player1 = RecordingPlayer(battle_format=battle_format, max_concurrent_battles=1)
        player2 = RecordingPlayer(battle_format=battle_format, max_concurrent_battles=1)
        
        print(f"\n배틀 시작...")
        await player1.battle_against(player2, n_battles=n_battles)
        
        # 배틀 기록 수집 - 완료된 배틀만
        completed_battles = 0

        for battle_tag, battle in player1._battles.items():
            if battle.finished:
                # 스냅샷을 배틀별로 그룹화
                battle_snapshots = [s for s in player1.turn_snapshots if s.battle_tag == battle_tag]

                if battle_snapshots:
                    battle_records.append({
                        'battle_tag': battle_tag,
                        'snapshots': battle_snapshots,
                        'real_won': battle.won,
                        'real_lost': battle.lost,
                    })
                    completed_battles += 1
        
        print(f"✓ {completed_battles}개 배틀 완료\n")    # 실행

    asyncio.run(run_battles())
    
    # 시뮬레이션 작업 준비
    print("시뮬레이션 검증 시작 (병렬 처리)...")
    simulation_tasks = []
    
    for i, record in enumerate(battle_records):
        snapshots = record['snapshots']
        
        # 턴 n의 선택으로 1턴 시뮬레이션 → 턴 n+1 실제와 비교
        for j in range(len(snapshots) - 1):
            current_snapshot = snapshots[j]  # 턴 n: 시뮬레이션 시작점
            next_snapshot = snapshots[j + 1]  # 턴 n+1: 실제 결과 (비교 대상)
            
            turn = current_snapshot.turn
            current_battle_state = current_snapshot.battle  # 턴 n의 배틀 상태
            
            # 플레이어 행동 정보
            player_action_info = {
                'order_type': current_snapshot.order_type,
                'move_idx': current_snapshot.move_idx,
                'switch_to': current_snapshot.switch_to,
            }
            
            # 상대 행동 정보 (같은 snapshot에서 추출 또는 기본값)
            opponent_action_info = {
                'order_type': current_snapshot.opponent_order_type if hasattr(current_snapshot, 'opponent_order_type') else 'move',
                'move_idx': current_snapshot.opponent_move_idx if hasattr(current_snapshot, 'opponent_move_idx') else None,
                'switch_to': current_snapshot.opponent_switch_to if hasattr(current_snapshot, 'opponent_switch_to') else None,
            }
            
            # (배틀인덱스, 턴번호, 턴n의배틀상태, 플레이어행동정보, 상대행동정보, 턴n+1실제스냅샷)
            simulation_tasks.append((i, turn, current_battle_state, player_action_info, opponent_action_info, next_snapshot))
    
    # 병렬 처리로 시뮬레이션 실행
    results = []
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        completed = 0
        total = len(simulation_tasks)
        for result in executor.map(_simulate_turn, simulation_tasks):
            results.append(result)
            completed += 1
            # 진행률 표시 (매 10%마다)
            if completed % max(1, total // 10) == 0 or completed == total:
                print(f"  진행률: {completed}/{total} ({completed*100//total}%)")
    
    print()
    
    # 결과 요약 및 통계
    print("=" * 70)
    print("정확성 비교 통계")
    print("=" * 70)
    
    total_comparisons = len(results)
    if total_comparisons == 0:
        print("비교 결과가 없습니다.")
        return results
    
    # HP 오차 통계
    player_hp_errors = [r['one_player_hp_error'] for r in results]
    opponent_hp_errors = [r['one_opponent_hp_error'] for r in results]
    
    avg_player_hp_error = sum(player_hp_errors) / len(player_hp_errors) if player_hp_errors else 0
    avg_opponent_hp_error = sum(opponent_hp_errors) / len(opponent_hp_errors) if opponent_hp_errors else 0
    max_player_hp_error = max(player_hp_errors) if player_hp_errors else 0
    max_opponent_hp_error = max(opponent_hp_errors) if opponent_hp_errors else 0
    
    # 상태이상 일치율
    player_status_matches = sum(1 for r in results if r['one_player_status_match'])
    opponent_status_matches = sum(1 for r in results if r['one_opponent_status_match'])
    
    player_status_match_rate = (player_status_matches / total_comparisons * 100) if total_comparisons > 0 else 0
    opponent_status_match_rate = (opponent_status_matches / total_comparisons * 100) if total_comparisons > 0 else 0
    
    # 결과 출력
    print(f"\n【 비교 통계 】")
    print(f"  총 비교 턴: {total_comparisons}개")
    print(f"  배틀 수: {len(battle_records)}개")
    
    print(f"\n【 플레이어 HP 정확도 】")
    print(f"  평균 오차: {avg_player_hp_error:.1f} HP")
    print(f"  최대 오차: {max_player_hp_error:.1f} HP")
    
    print(f"\n【 상대 HP 정확도 】")
    print(f"  평균 오차: {avg_opponent_hp_error:.1f} HP")
    print(f"  최대 오차: {max_opponent_hp_error:.1f} HP")
    
    print(f"\n【 상태이상 예측 정확도 】")
    print(f"  플레이어: {player_status_matches}/{total_comparisons} ({player_status_match_rate:.1f}%)")
    print(f"  상대: {opponent_status_matches}/{total_comparisons} ({opponent_status_match_rate:.1f}%)")
    
    # 상태이상 발생 횟수 통계
    player_status_times_list = [r.get('one_player_status', None) for r in results]
    opponent_status_times_list = [r.get('one_opponent_status', None) for r in results]
    
    avg_player_status_times = sum(player_status_times_list) / len(player_status_times_list) if player_status_times_list else 0
    avg_opponent_status_times = sum(opponent_status_times_list) / len(opponent_status_times_list) if opponent_status_times_list else 0
    
    print(f"\n【 상태이상 발생 횟수 (100회 시뮬 기준) 】")
    print(f"  플레이어: 평균 {avg_player_status_times:.1f}회/100회 시뮬")
    print(f"  상대: 평균 {avg_opponent_status_times:.1f}회/100회 시뮬")
    
    print(f"\n【 액티브 포켓몬 예측 정확도 】")
    # 활성 포켓몬이 일치하는지 확인
    pokemon_match_count = sum(1 for r in results if r['sim_active_pokemon'] == r['actual_active_pokemon'])
    opponent_pokemon_match_count = sum(1 for r in results if r['sim_active_opponent_pokemon'] == r['actual_active_opponent_pokemon'])
    
    pokemon_match_rate = (pokemon_match_count / total_comparisons * 100) if total_comparisons > 0 else 0
    opponent_pokemon_match_rate = (opponent_pokemon_match_count / total_comparisons * 100) if total_comparisons > 0 else 0
    
    print(f"  플레이어: {pokemon_match_count}/{total_comparisons} ({pokemon_match_rate:.1f}%)")
    print(f"  상대: {opponent_pokemon_match_count}/{total_comparisons} ({opponent_pokemon_match_rate:.1f}%)")
    
    print(f"\n【 행동 종류별 통계 】")
    # 기술/교체별 통계
    action_types = defaultdict(lambda: {'count': 0, 'hp_errors': [], 'status_matches': 0})
    for result in results:
        action_type = result.get('player_action', 'unknown')
        action_types[action_type]['count'] += 1
        action_types[action_type]['hp_errors'].append(result['one_player_hp_error'])
        if result['one_player_status_match']:
            action_types[action_type]['status_matches'] += 1
    
    for action_type, stats in sorted(action_types.items()):
        count = stats['count']
        avg_error = sum(stats['hp_errors']) / len(stats['hp_errors']) if stats['hp_errors'] else 0
        status_rate = (stats['status_matches'] / count * 100) if count > 0 else 0
        print(f"  {action_type}: {count}회, 평균HP오차={avg_error:.1f}")
    
    print(f"\n【 상세 결과 (처음 10개) 】")
    for idx, result in enumerate(results[:10]):
        print(f"  T{result['turn']}: "
              f"Player({result['one_active_pokemon']} vs {result['actual_active_pokemon']}) HP {result['one_player_hp']:.1f}/{result['actual_player_hp']} (오차:{result['one_player_hp_error']:.1f}), "
              f"Status({result['one_player_status']} vs {result['actual_player_status']}) | "
              f"Opponent({result['one_active_opponent_pokemon']} vs {result['actual_active_opponent_pokemon']}) HP {result['one_opponent_hp']:.1f}/{result['actual_opponent_hp']} (오차:{result['one_opponent_hp_error']:.1f}), "
              f"Status({result['one_opponent_status']} vs {result['actual_opponent_status']})")
    
    print("\n" + "=" * 70)
    
    return results


# === RecordingPlayer 클래스 (전역) ===
class RecordingPlayer(BattleLogMixin, Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.turn_snapshots = []  # 각 턴의 스냅샷 저장
        
    def choose_move(self, battle : Battle):
        # 🔴 battle_tag와 turn을 BattleLogMixin에 제공 (opponent 행동 수집용)
        self._current_battle_tag = battle.battle_tag
        self._current_battle_turn = battle.turn
        
        # 모든 턴에서 snapshot 생성
        snapshot = BattleSnapshot(
            turn=battle.turn,
            battle=SimplifiedBattle(battle, fill_unknown_data=True),
            active_pokemon=battle.active_pokemon,
            active_opponent_pokemon=battle.opponent_active_pokemon,
            team=battle.team,
            opponent_team=battle.opponent_team
        )

        if battle.available_moves:
            move = random.choice(battle.available_moves)
            move_idx = battle.available_moves.index(move)
            order = self.create_order(move)
            
            snapshot.order_type = 'move'
            snapshot.move_idx = move_idx
            self.turn_snapshots.append(snapshot)
            return order
        
        elif battle.available_switches:
            switch_to = random.choice(battle.available_switches)
            order = self.create_order(switch_to)
            
            snapshot.order_type = 'switch'
            snapshot.switch_to = switch_to
            self.turn_snapshots.append(snapshot)
            return order
        else:
            snapshot.order_type = 'unknown'
            self.turn_snapshots.append(snapshot)
            return self.choose_random_move(battle)


if __name__ == "__main__":
    # 테스트 실행 (병렬 처리: 10개 워커)
    # results = test_battle_simulation(n_battles=10, battle_format="gen9randombattle", n_workers=5)
    
    # 간단한 1배틀 비교 모드
    print("=" * 70)
    print("1배틀 Turn-by-Turn 비교 모드")
    print("=" * 70)
    
    async def run_single_battle():
        player1 = RecordingPlayer(battle_format="gen9randombattle", max_concurrent_battles=1)
        player2 = RecordingPlayer(battle_format="gen9randombattle", max_concurrent_battles=1)
        
        print("\n배틀 시작...\n")
        await player1.battle_against(player2, n_battles=1)
        
        # 완료된 배틀 가져오기
        for battle_tag, battle in player1._battles.items():
            if battle.finished:
                # 모든 스냅샷을 가져옴 (battle_tag 필터링 없음)
                battle_snapshots = player1.turn_snapshots
                
                # 🔴 opponent_action_store에서 일괄적으로 스냅샷에 opponent 행동 추가
                # 모든 스냅샷에 대해 처리
                for snapshot in battle_snapshots:
                    turn = snapshot.turn
                    
                    # opponent_action_store에서 현재 턴의 상대 행동 찾기
                    # 모든 배틀의 opponent_action_store를 검색
                    action = None
                    for stored_battle_tag, action_dict in player1.opponent_action_store.items():
                        if turn in action_dict:
                            action = action_dict[turn].copy()
                            break
                    
                    if action:
                        
                        # move_name이 있으면 move_idx로 변환
                        if action.get('move_name') and action.get('move_idx') is None:
                            move_name = action['move_name']
                            # snapshot.battle (SimplifiedBattle)의 opponent_active_pokemon에서 move_idx 찾기
                            if snapshot.battle and snapshot.battle.opponent_active_pokemon:
                                opponent_pokemon = snapshot.battle.opponent_active_pokemon
                                if hasattr(opponent_pokemon, 'moves') and opponent_pokemon.moves:
                                    # 정규화된 move_name (공백 및 하이픈 제거, 소문자 변환)
                                    normalized_move_name = move_name.lower().replace(' ', '').replace('-', '')
                                    
                                    # moves는 SimplifiedMove 객체의 리스트
                                    for idx, move in enumerate(opponent_pokemon.moves):
                                        # move.id는 소문자 move name (예: "swordsdance")
                                        normalized_move_id = move.id.lower().replace(' ', '').replace('-', '')
                                        
                                        if normalized_move_id == normalized_move_name:
                                            action['move_idx'] = idx
                                            break
                        
                        # opponent_action_info에 저장
                        snapshot.opponent_action_info = action
                    else:
                        # turn이 없으면 빈 dict 저장
                        snapshot.opponent_action_info = {}
                
                print(f"✓ 배틀 완료! 총 {len(battle_snapshots)}턴 진행")
                
                # 상대 행동 로그 출력
                # 모든 배틀의 move_log 수집
                all_move_logs = []
                for stored_battle_tag in player1.opponent_move_log:
                    all_move_logs.extend(player1.get_opponent_move_log(stored_battle_tag))
                
                move_log = all_move_logs
                print(f"📋 상대 행동 로그 (총 {len(move_log)}개)")
                print(f"   opponent_action_store 개수: {sum(len(v) for v in player1.opponent_action_store.values())}\n")
                
                print("=" * 70)
                print("Turn-by-Turn 비교 결과")
                print("=" * 70)
                
                # 🔴 턴 데이터 저장을 위한 리스트 초기화
                turn_inputs = []
                turn_results = []
                
                # 시뮬레이션 엔진 생성 (모든 턴에서 재사용하고 통계 누적)
                engine = SimplifiedBattleEngine(gen=9)
                
                # 각 턴 비교
                for j in range(len(battle_snapshots) - 1):
                    current_snapshot = battle_snapshots[j]
                    next_snapshot = battle_snapshots[j + 1]
                    
                    turn = current_snapshot.turn
                    current_battle_state = current_snapshot.battle
                    
                    # 플레이어 행동
                    player_action_info = {
                        'order_type': current_snapshot.order_type,
                        'move_idx': current_snapshot.move_idx,
                        'move_name': None,  # ← 추가
                        'switch_to': current_snapshot.switch_to,
                    }
                    
                    # 플레이어 move_name 추출 (현재 상태의 available_moves에서)
                    if current_snapshot.order_type == 'move' and current_snapshot.move_idx is not None:
                        if current_battle_state.available_moves and current_snapshot.move_idx < len(current_battle_state.available_moves):
                            player_action_info['move_name'] = current_battle_state.available_moves[current_snapshot.move_idx].id
                    
                    # 🔴 opponent_action_info는 snapshot에서 가져옴
                    opponent_action_info = current_snapshot.opponent_action_info or {
                        'order_type': 'move',
                        'move_idx': None,
                        'move_name': None,
                        'switch_to': None,
                    }
                    
                    player_move_idx = None
                    if player_action_info.get('order_type') == 'move':
                        player_move_idx = player_action_info.get('move_idx')
                    
                    opponent_move_idx = None
                    opponent_move_name = None
                    if opponent_action_info.get('order_type') == 'move':
                        opponent_move_name = opponent_action_info.get('move_name')
                    
                    # 🔴 디버깅: 첫 턴에만 opponent_action_info 상세 출력
                    if j == 0 and turn == 1:
                        print(f"\n【 디버깅: opponent_action_info 구조 확인 】")
                        print(f"  opponent_action_info: {opponent_action_info}")
                        print(f"  - order_type: {opponent_action_info.get('order_type')}")
                        print(f"  - move_idx: {opponent_action_info.get('move_idx')} (타입: {type(opponent_action_info.get('move_idx')).__name__})")
                        print(f"  - move_name: {opponent_action_info.get('move_name')}")
                        print(f"  - switch_to: {opponent_action_info.get('switch_to')}")
                        
                        # move_name을 사용하는 경우
                        if opponent_move_name:
                            print(f"\n  ✅ opponent_move_name 사용: '{opponent_move_name}'")
                            print(f"  -> 시뮬레이션에서 opponent_move_name으로 정확한 기술 선택 시도")
                        elif opponent_action_info.get('move_idx') is None and opponent_action_info.get('move_name'):
                            print(f"\n  ⚠️ move_idx를 찾을 수 없음 (SimplifiedBattle의 opponent_active_pokemon.moves에 없음)")
                            print(f"  -> 시뮬레이션에서는 opponent_move_idx=None으로 랜덤 기술 선택됨")
                        print()
                    
                    # 100번 시뮬레이션
                    sim_results = []
                    for _ in range(1):
                        # 첫 턴에만 verbose=True로 설정해서 opponent_move_name 매칭 디버깅
                        verbose_mode = (j == 0 and turn == 1)
                        result = engine.simulate_turn(
                            copy.deepcopy(current_battle_state),
                            player_move_idx=player_move_idx,
                            opponent_move_idx=opponent_move_idx,
                            opponent_move_name=opponent_move_name,
                            verbose=verbose_mode
                        )
                        sim_results.append(result)
                    
                    # 시뮬 결과 (1회만 사용)
                    # 첫 번째 시뮬 결과만 사용 (sim_results[0])
                    # 플레이어 측
                    if sim_results[0].active_pokemon and getattr(sim_results[0].active_pokemon, 'max_hp', 0) > 0:
                        one_player_hp_frac = sim_results[0].active_pokemon.current_hp / sim_results[0].active_pokemon.max_hp
                        # clamp to [0,1]
                        one_player_hp_fraction = max(0.0, min(1.0, one_player_hp_frac))
                    else:
                        # 포켓몬이 없거나 max_hp 정보가 없으면 0 (기절 등)
                        one_player_hp_fraction = 0.0

                    # 상대 측
                    if sim_results[0].opponent_active_pokemon and getattr(sim_results[0].opponent_active_pokemon, 'max_hp', 0) > 0:
                        one_opponent_hp_frac = sim_results[0].opponent_active_pokemon.current_hp / sim_results[0].opponent_active_pokemon.max_hp
                        one_opponent_hp_fraction = max(0.0, min(1.0, one_opponent_hp_frac))
                    else:
                        one_opponent_hp_fraction = 0.0
                    
                    from collections import Counter
                    player_statuses = [r.active_pokemon.status.name if r.active_pokemon and r.active_pokemon.status else None for r in sim_results]
                    opponent_statuses = [r.opponent_active_pokemon.status.name if r.opponent_active_pokemon and r.opponent_active_pokemon.status else None for r in sim_results]
                    
                    sim_player_status = Counter(player_statuses).most_common(1)[0][0] if player_statuses else None
                    sim_opponent_status = Counter(opponent_statuses).most_common(1)[0][0] if opponent_statuses else None
                    
                    # 시뮬 결과 포켓몬 이름
                    sim_player_pokemon_list = [r.active_pokemon.species if r.active_pokemon else None for r in sim_results]
                    sim_opponent_pokemon_list = [r.opponent_active_pokemon.species if r.opponent_active_pokemon else None for r in sim_results]
                    
                    sim_player_pokemon_counter = Counter([p for p in sim_player_pokemon_list if p is not None])
                    sim_opponent_pokemon_counter = Counter([p for p in sim_opponent_pokemon_list if p is not None])
                    
                    sim_player_pokemon = sim_player_pokemon_counter.most_common(1)[0][0] if sim_player_pokemon_counter else 'None'
                    sim_opponent_pokemon = sim_opponent_pokemon_counter.most_common(1)[0][0] if sim_opponent_pokemon_counter else 'None'
                    
                    # 실제 결과는 next_snapshot의 battle에서 가져와야 함 (Turn n+1 시작 직전의 상태)
                    # 즉, Turn n의 행동 후 결과 상태
                    actual_battle_state = next_snapshot.battle
                    
                    # 실제 HP를 백분율로 추출 (SimplifiedBattle에서 직접)
                    # next_snapshot.battle이 SimplifiedBattle이므로 정수 HP를 백분율로 계산
                    actual_player_hp_max = actual_battle_state.active_pokemon.max_hp if actual_battle_state.active_pokemon else 100
                    actual_player_hp = actual_battle_state.active_pokemon.current_hp if actual_battle_state.active_pokemon else 0
                    actual_player_hp_fraction = actual_player_hp / actual_player_hp_max if actual_player_hp_max > 0 else 1.0
                    
                    actual_opponent_hp_max = actual_battle_state.opponent_active_pokemon.max_hp if actual_battle_state.opponent_active_pokemon else 100
                    actual_opponent_hp = actual_battle_state.opponent_active_pokemon.current_hp if actual_battle_state.opponent_active_pokemon else 0
                    actual_opponent_hp_fraction = actual_opponent_hp / actual_opponent_hp_max if actual_opponent_hp_max > 0 else 1.0
                    
                    actual_player_status = actual_battle_state.active_pokemon.status.name if actual_battle_state.active_pokemon and actual_battle_state.active_pokemon.status else None
                    actual_opponent_status = actual_battle_state.opponent_active_pokemon.status.name if actual_battle_state.opponent_active_pokemon and actual_battle_state.opponent_active_pokemon.status else None
                    
                    player_poke = actual_battle_state.active_pokemon.species if actual_battle_state.active_pokemon else 'None'
                    opponent_poke = actual_battle_state.opponent_active_pokemon.species if actual_battle_state.opponent_active_pokemon else 'None'
                    
                    # 현재 상태 추출 (Turn n 시작 시점)
                    # current_snapshot.battle이 Turn n의 상태이므로 여기서 가져옴
                    current_battle_state_at_turn_start = current_snapshot.battle
                    current_player_poke = current_battle_state_at_turn_start.active_pokemon.species if current_battle_state_at_turn_start.active_pokemon else 'None'
                    current_player_max_hp = current_battle_state_at_turn_start.active_pokemon.max_hp if current_battle_state_at_turn_start.active_pokemon else 100
                    current_player_hp = current_battle_state_at_turn_start.active_pokemon.current_hp if current_battle_state_at_turn_start.active_pokemon else 0
                    current_player_hp_fraction = current_player_hp / current_player_max_hp if current_player_max_hp > 0 else 1.0
                    current_player_status = current_battle_state_at_turn_start.active_pokemon.status.name if current_battle_state_at_turn_start.active_pokemon and current_battle_state_at_turn_start.active_pokemon.status else None
                    
                    current_opponent_poke = current_battle_state_at_turn_start.opponent_active_pokemon.species if current_battle_state_at_turn_start.opponent_active_pokemon else 'None'
                    current_opponent_max_hp = current_battle_state_at_turn_start.opponent_active_pokemon.max_hp if current_battle_state_at_turn_start.opponent_active_pokemon else 100
                    current_opponent_hp = current_battle_state_at_turn_start.opponent_active_pokemon.current_hp if current_battle_state_at_turn_start.opponent_active_pokemon else 0
                    current_opponent_hp_fraction = current_opponent_hp / current_opponent_max_hp if current_opponent_max_hp > 0 else 1.0
                    current_opponent_status = current_battle_state_at_turn_start.opponent_active_pokemon.status.name if current_battle_state_at_turn_start.opponent_active_pokemon and current_battle_state_at_turn_start.opponent_active_pokemon.status else None
                    
                    # 출력
                    print(f"\n【 Turn {turn} 】")
                    
                    # 플레이어 행동 상세 정보
                    action_str = f"{player_action_info.get('order_type')}"
                    if player_action_info.get('order_type') == 'move':
                        if player_action_info.get('move_name'):
                            action_str += f" ({player_action_info.get('move_name')})"
                        elif player_move_idx is not None:
                            if current_battle_state_at_turn_start.available_moves and player_move_idx < len(current_battle_state_at_turn_start.available_moves):
                                move_name = current_battle_state_at_turn_start.available_moves[player_move_idx].id
                                action_str += f" ({move_name})"
                    elif player_action_info.get('order_type') == 'switch' and player_action_info.get('switch_to'):
                        switch_to = player_action_info.get('switch_to')
                        # switch_to가 객체인 경우 .species, 문자열인 경우 그대로 사용
                        switch_to_name = switch_to.species if hasattr(switch_to, 'species') else switch_to
                        action_str += f" ({switch_to_name})"
                    
                    print(f"  플레이어 행동: {action_str}")
                    
                    # 상대 행동 상세 정보
                    opponent_action_str = f"{opponent_action_info.get('order_type')}"
                    if opponent_action_info.get('order_type') == 'move':
                        if opponent_action_info.get('move_name'):
                            opponent_action_str += f" ({opponent_action_info.get('move_name')})"
                        elif opponent_action_info.get('move_idx') is not None:
                            opponent_action_str += f" (move_idx: {opponent_action_info.get('move_idx')})"
                    elif opponent_action_info.get('order_type') == 'switch' and opponent_action_info.get('switch_to'):
                        switch_to = opponent_action_info.get('switch_to')
                        # switch_to가 객체인 경우 .species, 문자열인 경우 그대로 사용
                        switch_to_name = switch_to.species if hasattr(switch_to, 'species') else switch_to
                        opponent_action_str += f" ({switch_to_name})"
                    
                    print(f"  상대의 행동: {opponent_action_str}")
                    print(f"\n  【 현재 상태 】")
                    print(f"    플레이어: {current_player_poke} | HP: {current_player_hp_fraction:.1%} | 상태: {current_player_status}")
                    print(f"    상대: {current_opponent_poke} | HP: {current_opponent_hp_fraction:.1%} | 상태: {current_opponent_status}")
                    print(f"\n  【 실제 결과 】")
                    print(f"    플레이어: {player_poke} | HP: {actual_player_hp_fraction:.1%} | 상태: {actual_player_status}")
                    print(f"    상대: {opponent_poke} | HP: {actual_opponent_hp_fraction:.1%} | 상태: {actual_opponent_status}")
                    print(f"\n  【 시뮬 결과 (1회) 】")
                    one_player_poke = sim_results[0].active_pokemon.species if sim_results[0].active_pokemon else 'None'
                    one_player_status_name = sim_results[0].active_pokemon.status.name if sim_results[0].active_pokemon and sim_results[0].active_pokemon.status else None
                    one_opponent_poke = sim_results[0].opponent_active_pokemon.species if sim_results[0].opponent_active_pokemon else 'None'
                    one_opponent_status_name = sim_results[0].opponent_active_pokemon.status.name if sim_results[0].opponent_active_pokemon and sim_results[0].opponent_active_pokemon.status else None
                    
                    print(f"    플레이어: {one_player_poke} | HP: {one_player_hp_fraction:.1%} | 상태: {one_player_status_name}")
                    print(f"    상대: {one_opponent_poke} | HP: {one_opponent_hp_fraction:.1%} | 상태: {one_opponent_status_name}")
                    print(f"\n  【 차이 】")
                    print(f"    플레이어 HP 오차: {abs(one_player_hp_fraction - actual_player_hp_fraction)*100:.1f}%")
                    print(f"    상대 HP 오차: {abs(one_opponent_hp_fraction - actual_opponent_hp_fraction)*100:.1f}%")
                    print(f"    플레이어 포켓몬: {player_poke} → {one_player_poke} (일치: {player_poke == one_player_poke})")
                    print(f"    상대 포켓몬: {opponent_poke} → {one_opponent_poke} (일치: {opponent_poke == one_opponent_poke})")
                    print(f"    플레이어 상태 일치: {one_player_status_name == actual_player_status}")
                    print(f"    상대 상태 일치: {one_opponent_status_name == actual_opponent_status}")
                    print("-" * 70)
                    
                    # 🔴 턴 결과 저장
                    error_metrics = {
                        'player_hp_error': abs(one_player_hp_fraction - actual_player_hp_fraction) * 100,
                        'opponent_hp_error': abs(one_opponent_hp_fraction - actual_opponent_hp_fraction) * 100,
                        'player_pokemon_match': player_poke == one_player_poke,
                        'opponent_pokemon_match': opponent_poke == one_opponent_poke,
                        'player_status_match': one_player_status_name == actual_player_status,
                        'opponent_status_match': one_opponent_status_name == actual_opponent_status,
                    }
                    
                    input_turn_data, result_turn_data = save_turn_simulation_data(
                        battle_tag, turn,
                        current_battle_state_at_turn_start,
                        player_action_info, opponent_action_info,
                        actual_battle_state,
                        sim_results[0],  # 1회 시뮬 결과
                        error_metrics
                    )
                    turn_inputs.append(input_turn_data)
                    turn_results.append(result_turn_data)
                
                break
        
        # 📊 opponent_move_name 매칭 통계
        print(f"\n【 opponent_move_name 매칭 통계 】")
        print(f"  성공: {getattr(engine, '_move_name_match_success', 0)}회")
        print(f"  실패 (fallback): {getattr(engine, '_move_name_match_failure', 0)}회")
        total_matches = getattr(engine, '_move_name_match_success', 0) + getattr(engine, '_move_name_match_failure', 0)
        if total_matches > 0:
            success_rate = (getattr(engine, '_move_name_match_success', 0) / total_matches) * 100
            print(f"  성공률: {success_rate:.1f}%")
        
        # 배틀 완료 후 입력값과 결과값 분리 저장
        if turn_inputs:
            inputs_file = save_battle_turn_inputs(battle_tag, turn_inputs)
            print(f"\n💾 턴 입력값 저장: {inputs_file}")
            print(f"   총 {len(turn_inputs)}개 턴의 입력 데이터 저장됨")
        
        if turn_results:
            results_file = save_battle_turn_results(battle_tag, turn_results)
            print(f"💾 턴 결과값 저장: {results_file}")
            print(f"   총 {len(turn_results)}개 턴의 결과 데이터 저장됨")
    
    asyncio.run(run_single_battle())
    print("\n✓ 비교 완료!")
