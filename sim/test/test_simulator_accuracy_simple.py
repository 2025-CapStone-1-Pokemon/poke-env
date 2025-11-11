"""
시뮬레이터 정확성 간단 체크

실제 배틀과 시뮬레이션 결과를 비교해서
시뮬레이터가 얼마나 정확한지 측정합니다.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import copy
from poke_env.player import Player
from poke_env.battle import Battle
from SimplifiedBattle import SimplifiedBattle
from battle.SimplifiedBattleEngine import SimplifiedBattleEngine


class TestPlayer(Player):
    """테스트용 플레이어 (Greedy 전략)"""
    
    def choose_move(self, battle: Battle):
        if battle.available_moves:
            best_move = max(battle.available_moves, key=lambda move: move.base_power)
            return self.create_order(best_move)
        
        if battle.available_switches:
            return self.create_order(battle.available_switches[0])
        
        return self.choose_random_move(battle)


async def test_simulator_accuracy():
    """시뮬레이터 정확성 테스트"""
    
    print("="*70)
    print("시뮬레이터 정확성 테스트 (여러 배틀)")
    print("="*70)
    
    # 5개 배틀 실행
    num_battles = 5
    print(f"\n1단계: 실제 배틀 진행 중 ({num_battles}개)...")
    player1 = TestPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1
    )
    player2 = TestPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1
    )
    
    await player1.battle_against(player2, n_battles=num_battles)
    
    # 정확도 통계
    correct_predictions = 0
    total_predictions = 0
    
    engine = SimplifiedBattleEngine()
    
    for i, (battle_tag, poke_env_battle) in enumerate(player1.battles.items(), 1):
        print(f"\n{'='*70}")
        print(f"배틀 {i}/{num_battles}: {battle_tag}")
        print(f"{'='*70}")
        
        # 실제 결과
        if poke_env_battle.won:
            actual_winner = "player1"
        elif poke_env_battle.lost:
            actual_winner = "player2"
        else:
            actual_winner = "draw"
        actual_turns = poke_env_battle.turn
        
        print(f"실제 결과: {actual_winner} 승리 ({actual_turns}턴)")
        
        # SimplifiedBattle 변환
        simplified_battle = SimplifiedBattle(poke_env_battle)
        
        # 시뮬레이션 (5회)
        sim_results = {'player1': 0, 'player2': 0, 'draw': 0}
        sim_turns = []
        
        print(f"시뮬레이션 5회 실행 중...")
        for j in range(5):
            battle_copy = copy.deepcopy(simplified_battle)
            result = engine.simulate_full_battle(battle_copy, max_turns=100, verbose=False)
            
            player_alive = sum(1 for p in result.team.values() if p.current_hp > 0)
            opponent_alive = sum(1 for p in result.opponent_team.values() if p.current_hp > 0)
            
            if player_alive > 0 and opponent_alive == 0:
                sim_results['player1'] += 1
                winner = "player1"
            elif opponent_alive > 0 and player_alive == 0:
                sim_results['player2'] += 1
                winner = "player2"
            else:
                sim_results['draw'] += 1
                winner = "draw"
            
            sim_turns.append(result.turn)
            print(f"  {j+1}: {winner} ({result.turn}턴)")
        
        # 예측
        if sim_results['draw'] > 2:
            predicted_winner = "draw"
        elif sim_results['player1'] > sim_results['player2']:
            predicted_winner = "player1"
        else:
            predicted_winner = "player2"
        
        accuracy_pct = max(sim_results.values()) * 20  # 5회 중 최대값
        is_correct = predicted_winner == actual_winner
        
        print(f"\n예측 결과: {predicted_winner} 승리 (정확도 {accuracy_pct:.0f}%)")
        print(f"시뮬레이션 분포: Player1 {sim_results['player1']}회, Player2 {sim_results['player2']}회, 무승부 {sim_results['draw']}회")
        print(f"시뮬레이션 턴: {min(sim_turns)}~{max(sim_turns)}턴 (평균 {sum(sim_turns)/len(sim_turns):.1f}턴)")
        
        if is_correct:
            print("✓ 정확!")
            correct_predictions += 1
        else:
            print("✗ 부정확")
        
        total_predictions += 1
    
    # 전체 통계
    print(f"\n{'='*70}")
    print("전체 결과")
    print(f"{'='*70}")
    print(f"정확도: {correct_predictions}/{total_predictions} ({correct_predictions*100//total_predictions}%)")
    
    if correct_predictions == total_predictions:
        print("✓ 모두 정확합니다!")
    elif correct_predictions >= total_predictions * 0.8:
        print("△ 대체로 정확합니다 (80% 이상)")
    else:
        print("✗ 정확도가 낮습니다")


if __name__ == "__main__":
    asyncio.run(test_simulator_accuracy())
