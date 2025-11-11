"""
MCTS + SimplifiedBattle 통합 테스트
"""
import asyncio
from player.MCTS_GEMINI import mcts_search
from poke_env.player import RandomPlayer, cross_evaluate
from poke_env.player import Player


class MCTSPlayer(Player):
    """MCTS를 사용하는 플레이어"""
    
    def choose_move(self, battle):
        """MCTS로 최적 행동 선택"""
        print(f"[턴 {battle.turn}] MCTS 검색 시작...")
        
        # MCTS 검색 (10번만 반복 - 빠른 테스트용)
        action = mcts_search(battle, iterations=10)
        
        print(f"[턴 {battle.turn}] MCTS 검색 완료")
        
        if action is None:
            # MCTS가 실패하면 랜덤 선택
            return self.choose_random_move(battle)
        
        # action을 실제 선택으로 변환
        return self.create_order(action)


async def test_mcts_vs_random():
    """MCTS vs Random 테스트"""
    print("=== MCTS vs Random Bot 테스트 ===\n")
    
    # 플레이어 생성
    mcts_player = MCTSPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1
    )
    
    random_player = RandomPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1
    )
    
    # 1판만 대결 (빠른 테스트)
    print("배틀 시작...\n")
    
    try:
        await mcts_player.battle_against(random_player, n_battles=1)
    except Exception as e:
        print(f"배틀 중 에러: {e}")
    
    print("\n=== 결과 ===")
    print(f"MCTS 전적: {mcts_player.n_won_battles}승 {mcts_player.n_lost_battles}패")
    print(f"Random 전적: {random_player.n_won_battles}승 {random_player.n_lost_battles}패")


if __name__ == "__main__":
    asyncio.run(test_mcts_vs_random())
