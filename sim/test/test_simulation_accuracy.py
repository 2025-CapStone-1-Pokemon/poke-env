"""
실제 배틀 결과 vs 시뮬레이션 결과 비교 테스트

목적:
- 특정 턴에서 실제 배틀 상태와 시뮬레이션 예측의 오차 측정
- 초기 턴일수록 오차가 크다는 가설 검증
- 정량적 지표로 시뮬레이션 정확도 평가
"""
import sys
import os
# 상위 디렉토리(sim)를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import numpy as np
from typing import List, Dict, Tuple
from poke_env.player import RandomPlayer, Player
from poke_env.battle import Battle
from SimplifiedBattle import SimplifiedBattle
from battle.SimplifiedBattleEngine import SimplifiedBattleEngine


class GreedyPlayer(Player):
    """가장 위력이 높은 기술을 선택하는 플레이어"""
    
    def choose_move(self, battle: Battle):
        # 사용 가능한 기술 중 위력이 가장 높은 것 선택
        if battle.available_moves:
            best_move = max(battle.available_moves, key=lambda move: move.base_power)
            return self.create_order(best_move)
        
        # 기술이 없으면 교체
        if battle.available_switches:
            return self.create_order(battle.available_switches[0])
        
        # 둘 다 없으면 랜덤
        return self.choose_random_move(battle)


class BattleRecorder(GreedyPlayer):
    """배틀 기록 및 분석용 플레이어 (Greedy 전략 사용)"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.turn_snapshots = []  # 각 턴의 스냅샷
        self.current_battle_tag = None
    
    def choose_move(self, battle):
        """기술 선택 + 턴 스냅샷 저장"""
        # 새 배틀이거나 턴이 증가했을 때만 저장
        if (self.current_battle_tag != battle.battle_tag or 
            not self.turn_snapshots or 
            self.turn_snapshots[-1]['turn'] < battle.turn):
            
            self.current_battle_tag = battle.battle_tag
            snapshot = self._create_snapshot(battle)
            self.turn_snapshots.append(snapshot)
        
        return super().choose_move(battle)
    
    def _create_snapshot(self, battle) -> Dict:
        """배틀 스냅샷 생성 - 턴 시작 시 한 번만 저장"""
        return {
            'turn': battle.turn,
            'battle_tag': battle.battle_tag,
            'player_team_alive': sum(1 for p in battle.team.values() if not p.fainted),
            'opponent_team_alive': sum(1 for p in battle.opponent_team.values() if not p.fainted),
        }


class SimulationAccuracyTester:
    """시뮬레이션 정확도 테스터"""
    
    def __init__(self):
        self.engine = SimplifiedBattleEngine()
        self.results = []
    
    def test_single_battle(self, snapshots: List[Dict], num_simulations: int = 10) -> Dict:
        """
        단일 배틀에 대한 시뮬레이션 정확도 테스트
        
        Args:
            snapshots: 배틀 턴별 스냅샷 리스트
            num_simulations: 각 턴에서 실행할 시뮬레이션 횟수
            
        Returns:
            턴별 오차 분석 결과 (각 턴에서 예측 vs 최종 배틀 결과)
        """
        # 최종 배틀 결과 (마지막 스냅샷)
        final_snapshot = snapshots[-1]
        actual_result = {
            'player_total_hp': final_snapshot['player_total_hp'],
            'player_total_max_hp': final_snapshot['player_total_max_hp'],
            'opponent_total_hp': final_snapshot['opponent_total_hp'],
            'opponent_total_max_hp': final_snapshot['opponent_total_max_hp'],
            'player_team_alive': final_snapshot['player_team_alive'],
            'opponent_team_alive': final_snapshot['opponent_team_alive'],
            'winner': 'player' if final_snapshot['player_team_alive'] > 0 else 'opponent'
        }
        
        # 디버깅: 첫 턴의 팀 정보 출력
        if snapshots:
            first_battle = snapshots[0]['simplified_battle']
            print(f"\n  === 초기 팀 정보 ===")
            print(f"  플레이어 팀:")
            for id, p in first_battle.team.items():
                move_count = len(p.moves) if p.moves else 0
                print(f"    {p.species}: HP={p.max_hp}, 기술={move_count}개")
            print(f"  상대 팀:")
            for id, p in first_battle.opponent_team.items():
                move_count = len(p.moves) if p.moves else 0
                stats_exist = p.stats is not None and len(p.stats) > 0
                print(f"    {p.species}: HP={p.max_hp}, 기술={move_count}개, 스탯={'있음' if stats_exist else '없음'}")
            print()
        
        turn_errors = []
        
        # 각 턴에서 시뮬레이션 실행하고 최종 결과와 비교
        for snapshot in snapshots[:-1]:  # 마지막 턴 제외
            current_turn = snapshot['turn']
            
            print(f"    턴 {current_turn} 시뮬레이션 중...", end='\r')
            
            # 시뮬레이션 실행 (N번)
            predictions = self._run_simulations(
                snapshot['simplified_battle'],
                num_simulations
            )
            
            # 오차 계산 (예측 vs 최종 결과)
            error = self._calculate_error(actual_result, predictions)
            
            turn_errors.append({
                'turn': current_turn,
                'error': error,
                'actual': actual_result,
                'predictions': predictions
            })
        
        return {
            'battle_tag': snapshots[0]['battle_tag'],
            'total_turns': len(snapshots),
            'actual_result': actual_result,
            'turn_errors': turn_errors
        }
    
    def _run_simulations(self, battle: SimplifiedBattle, num_simulations: int) -> Dict:
        """
        N번 전체 배틀 시뮬레이션 실행 후 통계 계산
        
        Returns:
            평균, 표준편차 등의 통계 (최종 결과 기준)
        """
        player_total_hps = []
        opponent_total_hps = []
        player_wins = 0  # 승리 예측 횟수
        opponent_wins = 0
        draws = 0  # 무승부 (최대 턴 도달)
        
        for _ in range(num_simulations):
            # 전체 배틀 시뮬레이션 (승패가 날 때까지)
            result = self.engine.simulate_full_battle(battle, max_turns=100, verbose=False)
            
            # 팀 전체 HP 합계 (SimplifiedBattle.team은 dict)
            player_total_hp = sum(p.current_hp for p in result.team.values())
            opponent_total_hp = sum(p.current_hp for p in result.opponent_team.values())
            
            player_total_hps.append(player_total_hp)
            opponent_total_hps.append(opponent_total_hp)
            
            # 승패 카운트
            player_alive = sum(1 for p in result.team.values() if p.current_hp > 0)
            opponent_alive = sum(1 for p in result.opponent_team.values() if p.current_hp > 0)
            
            if player_alive > 0 and opponent_alive == 0:
                player_wins += 1
            elif opponent_alive > 0 and player_alive == 0:
                opponent_wins += 1
            else:
                draws += 1
        
        return {
            'player_total_hp_mean': np.mean(player_total_hps),
            'player_total_hp_std': np.std(player_total_hps),
            'opponent_total_hp_mean': np.mean(opponent_total_hps),
            'opponent_total_hp_std': np.std(opponent_total_hps),
            'player_win_rate': player_wins / num_simulations,
            'opponent_win_rate': opponent_wins / num_simulations,
            'draw_rate': draws / num_simulations,
            'player_wins': player_wins,
            'opponent_wins': opponent_wins,
            'draws': draws,
        }
    
    def _calculate_error(self, actual: Dict, predictions: Dict) -> Dict:
        """
        실제 최종 결과와 예측의 오차 계산
        
        Metrics:
        - 승패 예측 정확도 (메인)
        - 팀 전체 HP 오차 (참고용)
        """
        # 실제 승패
        actual_winner = actual.get('winner', None)
        
        # 예측 승패 (더 높은 승률)
        predicted_winner = 'player' if predictions['player_win_rate'] > predictions['opponent_win_rate'] else 'opponent'
        
        # 무승부가 많으면 예측 불가
        if predictions.get('draw_rate', 0) > 0.5:
            predicted_winner = 'draw'
        
        # 승패 예측 정확도
        if predicted_winner == 'draw':
            win_prediction_correct = None  # 예측 불가
        else:
            win_prediction_correct = (actual_winner == predicted_winner) if actual_winner else None
        
        # HP 오차 (참고용)
        player_hp_error = abs(actual['player_total_hp'] - predictions['player_total_hp_mean'])
        opponent_hp_error = abs(actual['opponent_total_hp'] - predictions['opponent_total_hp_mean'])
        
        return {
            'win_prediction_correct': win_prediction_correct,
            'actual_winner': actual_winner,
            'predicted_winner': predicted_winner,
            'player_win_rate': predictions['player_win_rate'],
            'opponent_win_rate': predictions['opponent_win_rate'],
            'draw_rate': predictions.get('draw_rate', 0),
            'player_wins': predictions.get('player_wins', 0),
            'opponent_wins': predictions.get('opponent_wins', 0),
            'draws': predictions.get('draws', 0),
            'player_hp_mae': player_hp_error,
            'opponent_hp_mae': opponent_hp_error,
        }
    
    def analyze_results(self, results: List[Dict]):
        """
        전체 결과 분석
        
        - 턴별 평균 오차
        - 초기 턴 vs 후반 턴 오차 비교
        - 오차 추세 분석
        """
        all_turn_errors = []
        
        for battle_result in results:
            for turn_error in battle_result['turn_errors']:
                all_turn_errors.append(turn_error)
        
        if not all_turn_errors:
            print("분석할 데이터가 없습니다.")
            return
        
        print("\n" + "="*70)
        print("시뮬레이션 승패 예측 정확도 분석")
        print("="*70)
        
        print(f"\n총 배틀 수: {len(results)}")
        print(f"총 턴 수: {len(all_turn_errors)}")
        
        # 배틀별 실제 결과
        print("\n--- 배틀별 실제 결과 ---")
        for i, battle_result in enumerate(results, 1):
            actual = battle_result['actual_result']
            winner = actual['winner']
            print(f"배틀 {i}: {winner} 승리 ({battle_result['total_turns']}턴)")
        
        # 승패 예측 정확도
        win_predictions = [te['error']['win_prediction_correct'] 
                          for te in all_turn_errors 
                          if te['error']['win_prediction_correct'] is not None]
        
        if win_predictions:
            print("\n--- 전체 승패 예측 정확도 ---")
            accuracy = sum(win_predictions) / len(win_predictions) * 100
            correct = sum(win_predictions)
            total = len(win_predictions)
            print(f"정확도: {accuracy:.2f}% ({correct}/{total})")
            print(f"오답: {total - correct}개")
        
        # 턴별 그룹화
        turn_groups = {}
        for te in all_turn_errors:
            turn = te['turn']
            if turn not in turn_groups:
                turn_groups[turn] = []
            turn_groups[turn].append(te['error']['win_prediction_correct'])
        
        print("\n--- 턴별 승패 예측 정확도 ---")
        print(f"{'턴':<5} {'정확도':<12} {'정답/전체':<15} {'샘플 수':<10}")
        print("-" * 70)
        
        max_turn_display = min(15, max(turn_groups.keys()) if turn_groups else 0)
        for turn in sorted(turn_groups.keys())[:max_turn_display]:
            predictions = [p for p in turn_groups[turn] if p is not None]
            if predictions:
                accuracy = sum(predictions) / len(predictions) * 100
                correct = sum(predictions)
                total = len(predictions)
                print(f"{turn:<5} {accuracy:<12.1f}% {correct}/{total:<12} {len(predictions):<10}")
        
        # 초기 턴 vs 후반 턴
        early_preds = [te['error']['win_prediction_correct'] 
                      for te in all_turn_errors 
                      if te['turn'] <= 10 and te['error']['win_prediction_correct'] is not None]
        late_preds = [te['error']['win_prediction_correct'] 
                     for te in all_turn_errors 
                     if te['turn'] > 10 and te['error']['win_prediction_correct'] is not None]
        
        if early_preds and late_preds:
            print("\n--- 초기 턴 vs 후반 턴 비교 ---")
            early_acc = sum(early_preds) / len(early_preds) * 100
            late_acc = sum(late_preds) / len(late_preds) * 100
            print(f"초기 턴 (1~10턴) 정확도: {early_acc:.1f}% ({sum(early_preds)}/{len(early_preds)})")
            print(f"후반 턴 (11턴~) 정확도: {late_acc:.1f}% ({sum(late_preds)}/{len(late_preds)})")
            
            if late_acc > early_acc:
                print(f"\n✓ 후반 턴으로 갈수록 정확도가 {late_acc - early_acc:.1f}%p 증가합니다.")
            else:
                print(f"\n✗ 초기 턴과 후반 턴의 정확도 차이가 유의미하지 않습니다.")
        
        # 승률 분포
        print("\n--- 예측 승률 분포 ---")
        player_win_rates = [te['error']['player_win_rate'] for te in all_turn_errors]
        opponent_win_rates = [te['error']['opponent_win_rate'] for te in all_turn_errors]
        draw_rates = [te['error'].get('draw_rate', 0) for te in all_turn_errors]
        
        print(f"플레이어 평균 예측 승률: {np.mean(player_win_rates):.2f}")
        print(f"상대 평균 예측 승률: {np.mean(opponent_win_rates):.2f}")
        print(f"무승부 평균 비율: {np.mean(draw_rates):.2f}")
        
        # 무승부가 많은지 확인
        if draw_rates:
            high_draw_rate_count = sum(1 for rate in draw_rates if rate > 0.5)
            print(f"\n무승부 비율 > 50%인 턴: {high_draw_rate_count}/{len(draw_rates)}")
            
            if high_draw_rate_count > len(draw_rates) * 0.8:
                print("\n⚠️ 경고: 대부분의 시뮬레이션이 최대 턴 수에 도달하여 무승부로 끝났습니다.")
                print("   시뮬레이션 엔진의 데미지 계산이나 교체 로직을 확인이 필요합니다.")
        
        print("\n" + "="*70)


async def main():
    """메인 테스트 함수"""
    print("="*70)
    print("="*70)
    print("시뮬레이션 정확도 테스트 (승패 예측 정확도)")
    print("="*70)
    
    num_battles = 10
    
    print(f"\n{num_battles}개의 배틀 진행 중...\n")
    player1 = GreedyPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1
    )
    player2 = GreedyPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1
    )
    
    await player1.battle_against(player2, n_battles=num_battles)
    
    print(f"\n총 {num_battles}개의 배틀 완료\n")
    
    # 배틀별 결과
    print("="*70)
    print("배틀별 결과")
    print("="*70)
    
    player1_wins = 0
    for i, (battle_tag, battle) in enumerate(sorted(player1.battles.items()), 1):
        winner = "Player1" if battle.won else "Player2"
        if battle.won:
            player1_wins += 1
        
        # 배틀 정보
        player_team = ", ".join([p.species for p in battle.team.values()])[:50]
        opponent_team = ", ".join([p.species for p in battle.opponent_team.values()])[:50]
        
        print(f"배틀 {i}: {winner} 승리 ({battle.turn}턴)")
        print(f"  Player: {player_team}")
        print(f"  Opponent: {opponent_team}")
    
    print("\n" + "="*70)
    print("전체 요약")
    print("="*70)
    print(f"총 배틀: {num_battles}")
    print(f"Player1 승수: {player1_wins}승")
    print(f"Player2 승수: {num_battles - player1_wins}승")
    
    if player1_wins == num_battles:
        print("\n⚠️ Player1이 모든 배틀을 이겼습니다 (팀 운이 있거나 누군가 더 강함)")
    elif player1_wins == 0:
        print("\n⚠️ Player2가 모든 배틀을 이겼습니다 (팀 운이 있거나 누군가 더 강함)")
    else:
        fairness = (min(player1_wins, num_battles - player1_wins) / num_battles) * 100
        print(f"\n○ 합리적인 배분 ({fairness:.0f}% 공정함)")
    
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
