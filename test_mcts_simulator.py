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
    results = await cross_evaluate(
        [mcts_player, random_player],
        n_challenges=1
    )
    
    print("\n=== 결과 ===")
    print(f"MCTS 승률: {results[mcts_player.username][random_player.username]:.2%}")
    print(f"Random 승률: {results[random_player.username][mcts_player.username]:.2%}")


if __name__ == "__main__":
    asyncio.run(test_mcts_vs_random())
