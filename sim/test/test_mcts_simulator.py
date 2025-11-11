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


class RandomPlayer(Player):
    """간단한 랜덤 플레이어"""
    def choose_move(self, battle):
        return self.choose_random_move(battle)

class MCTSPlayer(Player):
    """MCTS를 사용하는 플레이어"""
    
    def choose_move(self, battle):
        """MCTS로 최적 행동 선택"""
        # 기술이 없으면 교체 강제
        if len(battle.available_moves) == 0:
            return self.choose_random_move(battle)
        
        # MCTS 검색 (100번 - 정확도와 속도 균형)
        action = mcts_search(battle, iterations=200, verbose=False)
        
        if action is None:
            return self.choose_random_move(battle)
        
        try:
            order = self.create_order(action)
            return order
        except Exception as e:
            return self.choose_random_move(battle)


async def test_mcts_vs_random():
    """MCTS vs Random 테스트"""
    print("=== MCTS vs Random Bot 테스트 ===\n")
    
    # 플레이어 생성
    mcts_player = MCTSPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=5  # 5배틀 동시 진행
    )
    
    random_player = RandomPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=5  # 5배틀 동시 진행
    )
    
    # 1판만 대결 (빠른 테스트)
    print("배틀 시작...\n")
    
    try:
        await mcts_player.battle_against(random_player, n_battles=5)
    except Exception as e:
        print(f"배틀 중 에러: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 결과 ===")
    print(f"MCTS 전적: {mcts_player.n_won_battles}승 {mcts_player.n_lost_battles}패")
    print(f"Random 전적: {random_player.n_won_battles}승 {random_player.n_lost_battles}패")


if __name__ == "__main__":
    asyncio.run(test_mcts_vs_random())
