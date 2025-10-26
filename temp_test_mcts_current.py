"""
현재 MCTS 성능 테스트
BattleState 통합 전 기존 휴리스틱 기반 MCTS 성능 측정
"""

import asyncio
from poke_env.player import Player, RandomPlayer
import temp_mcts_simulation as MCTS

class MCTSPlayerCurrent(Player):
    """기존 휴리스틱 기반 MCTS 플레이어"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iterations = 500  # iteration 수 증가
        self.move_count = 0
        self.debug = False  # 디버깅 비활성화
    
    def choose_move(self, battle):
        """MCTS로 최적의 행동 선택"""
        self.move_count += 1
        
        # 첫 3턴만 디버깅
        debug_mode = self.debug and self.move_count <= 3
        
        # 사용 가능한 액션 확인
        if battle.available_moves:
            try:
                # MCTS 검색 실행
                best_action = MCTS.mcts_search(battle, iterations=self.iterations, debug=debug_mode)
                
                if best_action:
                    if debug_mode:
                        print(f"Turn {self.move_count}: MCTS chose {best_action}\n")
                    return self.create_order(best_action)
                else:
                    # MCTS 실패시 첫 번째 기술 사용
                    return self.create_order(battle.available_moves[0])
            except Exception as e:
                print(f"MCTS Error: {e}")
                # 에러 발생시 랜덤 선택
                return self.choose_random_move(battle)
        else:
            # 교체만 가능한 경우
            return self.choose_random_move(battle)

async def test_current_mcts():
    """현재 MCTS 성능 테스트"""
    print("="*70)
    print("CURRENT MCTS PERFORMANCE TEST")
    print("="*70)
    print("\nTesting: MCTS (Heuristic) vs Random Player")
    print(f"Iterations per move: 100")
    print(f"Number of battles: 30")
    print("-"*70)
    
    # 플레이어 생성
    mcts_player = MCTSPlayerCurrent(battle_format="gen8randombattle")
    random_player = RandomPlayer(battle_format="gen8randombattle")
    
    # 배틀 시작
    print("\nStarting battles...")
    await mcts_player.battle_against(random_player, n_battles=10)
    
    # 결과 출력
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"MCTS Player:")
    print(f"  Wins: {mcts_player.n_won_battles}")
    print(f"  Losses: {mcts_player.n_lost_battles}")
    print(f"  Win Rate: {mcts_player.win_rate:.1%}")
    print(f"  Total Moves: {mcts_player.move_count}")
    print("-"*70)
    print(f"Random Player:")
    print(f"  Wins: {random_player.n_won_battles}")
    print(f"  Losses: {random_player.n_lost_battles}")
    print(f"  Win Rate: {random_player.win_rate:.1%}")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_current_mcts())
