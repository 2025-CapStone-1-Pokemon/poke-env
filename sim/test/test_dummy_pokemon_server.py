import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from poke_env.player import Player, RandomPlayer
from SimplifiedBattle import SimplifiedBattle
from battle.SimplifiedBattleEngine import SimplifiedBattleEngine

# Player 클래스를 상속받아 나만의 플레이어를 만듭니다.
class TestPlayer(Player):
    def choose_move(self, battle):

        if(battle.turn == 1):

            simplified_battle = SimplifiedBattle(battle)
            simplified_battle.print_summary()

            engine = SimplifiedBattleEngine()
            engine.simulate_full_battle(battle = simplified_battle, verbose = True)

        return self.choose_random_move(battle)

async def main():
    # 위에서 만든 MCTSPlayer와 기본 RandomPlayer를 생성합니다.
    test_player = TestPlayer(
        battle_format="gen8randombattle"
    )
    
    random_player = RandomPlayer(
        battle_format="gen8randombattle"
    )

    await test_player.battle_against(random_player, n_battles=1)

if __name__ == "__main__":
    asyncio.run(main())