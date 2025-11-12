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
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from collections import defaultdict

# 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sim_dir = os.path.dirname(current_dir)
poke_env_dir = os.path.dirname(sim_dir)
sys.path.insert(0, sim_dir)
sys.path.insert(0, poke_env_dir)

from poke_env.player import Player
from SimplifiedBattle import SimplifiedBattle
from sim.battle.SimplifiedBattleEngine import SimplifiedBattleEngine


# === 시뮬레이션 함수 (병렬 처리용) ===

def _simulate_turn(args):
    """병렬 처리를 위한 시뮬레이션 함수"""
    battle_idx, turn, battle_state, real_won = args
    
    engine = SimplifiedBattleEngine(gen=9)
    sim_battle = copy.deepcopy(battle_state)
    sim_result = engine.simulate_full_battle(sim_battle, max_turns=100, verbose=False)
    sim_won = sim_result.won
    
    return {
        'battle_idx': battle_idx,
        'turn': turn,
        'real_won': real_won,
        'sim_won': sim_won,
        'match': real_won == sim_won
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
    
    # 플레이어 클래스 정의
    class RecordingPlayer(Player):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.turn_snapshots = []  # 각 턴의 스냅샷 저장
            
        def choose_move(self, battle):
            # 턴 기록 (배틀 ID 포함)
            if battle.turn > 0:
                snapshot = {
                    'turn': battle.turn,
                    'battle': SimplifiedBattle(battle, fill_unknown_data=True),
                    'finished': battle.finished,
                    'won': battle.won if hasattr(battle, 'won') else None,
                    'battle_id': battle.battle_tag
                }
                self.turn_snapshots.append(snapshot)
            
            # 랜덤 행동 선택
            if battle.available_moves:
                # 그리디하게 가장 강한 공격 선택
                best_move = max(battle.available_moves, key=lambda move: move.base_power if move.base_power is not None else 0)
                return self.create_order(best_move)
            elif battle.available_switches:
                return self.create_order(random.choice(battle.available_switches))
            else:
                return self.choose_random_move(battle)
    
    # 비동기 테스트 실행
    async def run_battles():
        player1 = RecordingPlayer(battle_format=battle_format, max_concurrent_battles=1)
        player2 = RecordingPlayer(battle_format=battle_format, max_concurrent_battles=1)
        
        print(f"\n배틀 시작...")
        await player1.battle_against(player2, n_battles=n_battles)
        
        # 배틀 기록 수집 - 완료된 배틀만
        completed_battles = 0
        for battle_id, battle in player1._battles.items():
            if battle.finished:
                # 스냅샷을 배틀별로 그룹화
                battle_snapshots = [s for s in player1.turn_snapshots if s.get('battle_id') == battle_id]
                if battle_snapshots:
                    battle_records.append({
                        'battle_id': battle_id,
                        'snapshots': battle_snapshots,
                        'real_won': battle.won
                    })
                    completed_battles += 1
        
        # 스냅샷이 없으면 직접 현재 상태 기록
        if completed_battles == 0:
            for battle_id, battle in player1._battles.items():
                if battle.finished and battle.turn > 0:
                    snapshot = {
                        'turn': battle.turn,
                        'battle': SimplifiedBattle(battle, fill_unknown_data=True),
                        'finished': battle.finished,
                        'won': battle.won,
                        'battle_id': battle_id
                    }
                    battle_records.append({
                        'battle_id': battle_id,
                        'snapshots': [snapshot],
                        'real_won': battle.won
                    })
                    completed_battles += 1
        
        print(f"✓ {completed_battles}개 배틀 완료\n")
    
    # 실행
    asyncio.run(run_battles())
    
    # 시뮬레이션 작업 준비
    print("시뮬레이션 검증 시작 (병렬 처리)...")
    simulation_tasks = []
    
    for i, record in enumerate(battle_records):
        real_won = record['real_won']
        
        # 모든 턴의 스냅샷을 검증
        for snapshot in record['snapshots']:
            turn = snapshot['turn']
            battle_state = snapshot['battle']
            
            simulation_tasks.append((i, turn, battle_state, real_won))
    
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
    print("최종 통계")
    print("=" * 70)
    
    total_tests = len(results)
    if total_tests == 0:
        print("검증 결과가 없습니다.")
        return results
    
    match_count = sum(1 for r in results if r['match'])
    match_rate = (match_count / total_tests * 100) if total_tests > 0 else 0
    
    # 배틀 개수
    battle_count = len(battle_records)
    
    # 배틀별 승패 통계
    real_battle_won = sum(1 for record in battle_records if record['real_won'])
    real_battle_lost = battle_count - real_battle_won
    
    # 승패별 통계 (턴 기준)
    real_won_count = sum(1 for r in results if r['real_won'])
    real_lost_count = total_tests - real_won_count
    sim_won_count = sum(1 for r in results if r['sim_won'])
    sim_lost_count = total_tests - sim_won_count
    
    # 혼동 행렬
    true_positive = sum(1 for r in results if r['real_won'] and r['sim_won'])      # 실제 승, 시뮬 승
    false_positive = sum(1 for r in results if not r['real_won'] and r['sim_won'])  # 실제 패, 시뮬 승
    true_negative = sum(1 for r in results if not r['real_won'] and not r['sim_won']) # 실제 패, 시뮬 패
    false_negative = sum(1 for r in results if r['real_won'] and not r['sim_won'])  # 실제 승, 시뮬 패
    
    # 결과 테이블
    print("\n【 결과 요약 】")
    print(f"  실제 전투:   {battle_count}회")
    print(f"  시뮬 검증:   {total_tests}회 (총 {total_tests}턴 검증)")
    print(f"  일치:        {match_count}회 ({match_rate:.1f}%)")
    print(f"  불일치:     {total_tests - match_count}회 ({100-match_rate:.1f}%)")
    
    print("\n【 실제 전투 결과 】")
    print(f"  승리: {real_battle_won}회 ({real_battle_won/battle_count*100:.1f}%)")
    print(f"  패배: {real_battle_lost}회 ({real_battle_lost/battle_count*100:.1f}%)")
    
    print("\n【 시뮬레이션 결과 】")
    print(f"  승리: {sim_won_count}회 ({sim_won_count/total_tests*100:.1f}%)")
    print(f"  패배: {sim_lost_count}회 ({sim_lost_count/total_tests*100:.1f}%)")
    
    print("\n【 혼동 행렬 】")
    print(f"             시뮬-승   시뮬-패")
    print(f"  실제-승    {true_positive:4d}    {false_negative:4d}")
    print(f"  실제-패    {false_positive:4d}    {true_negative:4d}")
    
    # 성능 지표
    accuracy = (true_positive + true_negative) / total_tests if total_tests > 0 else 0
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print("\n【 성능 지표 】")
    print(f"  정확도:   {accuracy*100:.1f}%")
    print(f"  정밀도:   {precision*100:.1f}%")
    print(f"  재현율:   {recall*100:.1f}%")
    print(f"  F1 Score: {f1_score*100:.1f}%")
    
    print("\n" + "=" * 70)
    
    return results


if __name__ == "__main__":
    # 테스트 실행 (병렬 처리: 10개 워커)
    results = test_battle_simulation(n_battles=100, battle_format="gen9randombattle", n_workers=5)
    
    print("✓ 테스트 완료!")
