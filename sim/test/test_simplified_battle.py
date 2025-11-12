# 랜덤으로 포켓몬을 추정했을 때, 해당 포켓몬의 추정이 약하게 되는지를 확인하는 코드

"""
MCTS + SimplifiedBattle 통합 테스트
"""
import asyncio
import sys
import os

# 상위 디렉토리들을 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from player.MCTS_GEMINI import mcts_search
from poke_env.player import Player
from sim.SimplifiedBattle import SimplifiedBattle


class RandomPlayer(Player):
    """간단한 랜덤 플레이어"""
    def choose_move(self, battle):
        return self.choose_random_move(battle)

class TestPlayer(Player):
    """객체 변환 테스트"""
    
    def choose_move(self, battle):

        if(battle.turn == 1):
            # MCTS로 선택
            simplified_battle = SimplifiedBattle(battle)
            simplified_battle.print_summary()
        
        return self.choose_random_move(battle)


async def test_mcts_vs_random():
    """MCTS vs Random 테스트"""
    print("=== MCTS vs Random Bot 테스트 ===\n")
    
    # 플레이어 생성
    mcts_player = TestPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1  # 1배틀 동시 진행
    )
    
    random_player = RandomPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1  # 1배틀 동시 진행
    )
    
    # 1판만 대결 (빠른 테스트)
    print("배틀 시작...\n")
    
    try:
        await mcts_player.battle_against(random_player, n_battles=1)
    except Exception as e:
        print(f"배틀 중 에러: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 결과 ===")
    print(f"MCTS 전적: {mcts_player.n_won_battles}승 {mcts_player.n_lost_battles}패")
    print(f"Random 전적: {random_player.n_won_battles}승 {random_player.n_lost_battles}패")


if __name__ == "__main__":
    asyncio.run(test_mcts_vs_random())
