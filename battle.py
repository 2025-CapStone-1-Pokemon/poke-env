import asyncio
from poke_env.player import Player, RandomPlayer
import MCTS_GEMINI as MCTS

# Player 클래스를 상속받아 나만의 플레이어를 만듭니다.
class MCTSPlayer(Player):
    # AI의 모든 로직은 choose_move 메소드 안에 구현됩니다.
    def choose_move(self, battle):
        if battle.available_moves:
            best_move = MCTS.mcts_search(battle, iterations=100)
            print("Best Move: \n", best_move)
            return self.create_order(best_move)
        else:
            return self.choose_random_move(battle)

async def main():
    # 위에서 만든 MCTSPlayer와 기본 RandomPlayer를 생성합니다.
    mcts_player = MCTSPlayer(
        battle_format="gen8randombattle"
    )
    random_player = RandomPlayer(
        battle_format="gen8randombattle"
    )

    # 두 플레이어를 100번 배틀시킵니다.
    await mcts_player.battle_against(random_player, n_battles=100)

    # 배틀 결과를 출력합니다.
    print(
        f"MCTSPlayer won {mcts_player.n_won_battles} / 100 battles"
    )

if __name__ == "__main__":
    asyncio.run(main())