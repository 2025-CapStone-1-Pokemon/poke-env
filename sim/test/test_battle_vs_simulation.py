"""
실제 전투 vs 시뮬레이션 승패 비교 통합 테스트

실제 전투를 진행하면서 매 턴을 기록하고,
각 턴에서 시뮬레이션을 돌려서 최종 승패가 같은지 확인합니다.
"""

import sys
import os
import asyncio
import copy
import random

# 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sim_dir = os.path.dirname(current_dir)
poke_env_dir = os.path.dirname(sim_dir)
sys.path.insert(0, sim_dir)
sys.path.insert(0, poke_env_dir)

from poke_env.player import Player
from SimplifiedBattle import SimplifiedBattle
from sim.battle.SimplifiedBattleEngine import SimplifiedBattleEngine


# === 전투 기록 및 검증 함수 ===

def test_battle_simulation(n_battles: int = 5, battle_format: str = "gen9randombattle"):
    """
    실제 전투와 시뮬레이션 승패 비교 테스트
    
    Args:
        n_battles: 테스트할 배틀 수
        battle_format: 배틀 포맷
    """
    print("=" * 60)
    print(f"실제 전투 vs 시뮬레이션 승패 비교 테스트")
    print(f"배틀 수: {n_battles}, 포맷: {battle_format}")
    print("=" * 60)
    
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
                return self.create_order(random.choice(battle.available_moves))
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
    
    # 시뮬레이션 검증
    print("=" * 60)
    print("시뮬레이션 검증 시작")
    print("=" * 60)
    
    engine = SimplifiedBattleEngine(gen=9)
    results = []
    
    for i, record in enumerate(battle_records):
        print(f"\n[배틀 {i+1}/{len(battle_records)}]")
        real_won = record['real_won']
        
        # 각 턴에서 시뮬레이션 실행
        for snapshot in record['snapshots']:
            turn = snapshot['turn']
            battle_state = snapshot['battle']
            
            print(f"  턴 {turn}: 시뮬레이션 실행 중...", end=" ")
            
            # 시뮬레이션 실행 (배틀 끝까지)
            sim_battle = copy.deepcopy(battle_state)
            sim_result = engine.simulate_full_battle(sim_battle, max_turns=100, verbose=False)
            sim_won = sim_result.won
            
            # 승패 비교
            match = (real_won == sim_won)
            match_str = "✓" if match else "✗"
            
            print(f"{match_str} (실제: {'승' if real_won else '패'}, 시뮬: {'승' if sim_won else '패'})")
            
            results.append({
                'battle_id': i + 1,
                'turn': turn,
                'real_won': real_won,
                'sim_won': sim_won,
                'match': match
            })
    
    # 결과 요약 및 통계
    print("\n" + "=" * 60)
    print("검증 결과 통계")
    print("=" * 60)
    
    total_tests = len(results)
    match_count = sum(1 for r in results if r['match'])
    match_rate = (match_count / total_tests * 100) if total_tests > 0 else 0
    
    # 배틀별 통계
    battles_stat = {}
    for r in results:
        bid = r['battle_id']
        if bid not in battles_stat:
            battles_stat[bid] = {'total': 0, 'match': 0, 'turns': []}
        battles_stat[bid]['total'] += 1
        battles_stat[bid]['turns'].append(r['turn'])
        if r['match']:
            battles_stat[bid]['match'] += 1
    
    # 전체 통계
    print(f"\n📊 전체 통계")
    print(f"  총 배틀 수: {len(battles_stat)}개")
    print(f"  총 테스트 수: {total_tests}턴")
    print(f"  승패 일치: {match_count}/{total_tests} ({match_rate:.1f}%)")
    print(f"  승패 불일치: {total_tests - match_count}/{total_tests} ({100-match_rate:.1f}%)")
    
    # 배틀별 상세 통계
    print(f"\n📈 배틀별 통계")
    for bid in sorted(battles_stat.keys()):
        stat = battles_stat[bid]
        rate = (stat['match'] / stat['total'] * 100) if stat['total'] > 0 else 0
        min_turn = min(stat['turns'])
        max_turn = max(stat['turns'])
        print(f"  배틀 {bid}:")
        print(f"    - 테스트 턴: {min_turn}~{max_turn}턴 (총 {stat['total']}턴)")
        print(f"    - 일치율: {stat['match']}/{stat['total']} ({rate:.1f}%)")
    
    # 승패 패턴 분석
    real_won_count = sum(1 for r in results if r['real_won'])
    real_lost_count = total_tests - real_won_count
    sim_won_count = sum(1 for r in results if r['sim_won'])
    sim_lost_count = total_tests - sim_won_count
    
    # 혼동 행렬 (Confusion Matrix)
    true_positive = sum(1 for r in results if r['real_won'] and r['sim_won'])  # 실제 승, 시뮬 승
    false_positive = sum(1 for r in results if not r['real_won'] and r['sim_won'])  # 실제 패, 시뮬 승
    true_negative = sum(1 for r in results if not r['real_won'] and not r['sim_won'])  # 실제 패, 시뮬 패
    false_negative = sum(1 for r in results if r['real_won'] and not r['sim_won'])  # 실제 승, 시뮬 패
    
    print(f"\n🎯 승패 패턴 분석")
    print(f"  실제 전투:")
    print(f"    - 승리: {real_won_count}턴 ({real_won_count/total_tests*100:.1f}%)")
    print(f"    - 패배: {real_lost_count}턴 ({real_lost_count/total_tests*100:.1f}%)")
    print(f"  시뮬레이션:")
    print(f"    - 승리: {sim_won_count}턴 ({sim_won_count/total_tests*100:.1f}%)")
    print(f"    - 패배: {sim_lost_count}턴 ({sim_lost_count/total_tests*100:.1f}%)")
    
    print(f"\n📋 혼동 행렬 (Confusion Matrix)")
    print(f"                    시뮬레이션")
    print(f"                승리        패배")
    print(f"  실제  승리    {true_positive:3d}         {false_negative:3d}")
    print(f"       패배    {false_positive:3d}         {true_negative:3d}")
    
    # 정확도, 정밀도, 재현율 계산
    accuracy = (true_positive + true_negative) / total_tests if total_tests > 0 else 0
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\n📐 성능 지표")
    print(f"  정확도 (Accuracy):  {accuracy*100:.1f}%")
    print(f"  정밀도 (Precision): {precision*100:.1f}% (시뮬이 승리라고 예측한 것 중 실제 승리 비율)")
    print(f"  재현율 (Recall):    {recall*100:.1f}% (실제 승리 중 시뮬이 맞춘 비율)")
    print(f"  F1 Score:          {f1_score*100:.1f}%")
    
    # 불일치 케이스 출력
    mismatch_results = [r for r in results if not r['match']]
    if mismatch_results:
        print(f"\n❌ 승패 불일치 케이스 ({len(mismatch_results)}개):")
        # 배틀별로 그룹화
        mismatch_by_battle = {}
        for r in mismatch_results:
            bid = r['battle_id']
            if bid not in mismatch_by_battle:
                mismatch_by_battle[bid] = []
            mismatch_by_battle[bid].append(r)
        
        for bid in sorted(mismatch_by_battle.keys()):
            mismatches = mismatch_by_battle[bid]
            print(f"  배틀 {bid} ({len(mismatches)}개):")
            for r in mismatches[:5]:  # 처음 5개만 표시
                real_str = "승리" if r['real_won'] else "패배"
                sim_str = "승리" if r['sim_won'] else "패배"
                print(f"    턴 {r['turn']}: 실제={real_str}, 시뮬={sim_str}")
            if len(mismatches) > 5:
                print(f"    ... 외 {len(mismatches)-5}개")
    else:
        print("\n✅ 모든 테스트에서 승패가 일치합니다!")
    
    print("\n" + "=" * 60)
    
    return results


if __name__ == "__main__":
    # 테스트 실행
    results = test_battle_simulation(n_battles=3, battle_format="gen9randombattle")
    
    print("\n테스트 완료!")
