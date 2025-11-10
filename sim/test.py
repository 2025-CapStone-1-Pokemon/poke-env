# 클래스 복사가 잘 되나 확인하는 코드

import asyncio
from poke_env.player import Player
from poke_env.battle import Battle
from SimplifiedPokemon import SimplifiedPokemon
from SimplifiedBattle import SimplifiedBattle

class CustomPlayer(Player):
    def choose_move(self, battle: Battle):
        # Pokemon 객체를 SimplifiedPokemon으로 변환
        my_pokemons = []
        for pokemon in battle.team.values():
            simplified = SimplifiedPokemon(pokemon)
            my_pokemons.append(simplified)
        
        opponent_pokemons = []
        for pokemon in battle.opponent_team.values():
            simplified = SimplifiedPokemon(pokemon)
            opponent_pokemons.append(simplified)
        
        # ✅ SimplifiedPokemon 속성 상세 확인
        print("\n" + "="*60)
        print("📋 SimplifiedPokemon 속성 확인")
        print("="*60)
        
        # 내 포켓몬 확인
        if my_pokemons:
            print("\n[내 팀 첫 번째 포켓몬]")
            p = my_pokemons[0]
            p.print_summary()
        
        # 랜덤으로 행동 선택
        return self.choose_random_move(battle)

class CustomPlayer2(Player):
    def choose_move(self, battle: Battle):
        
        simplified_battle = SimplifiedBattle(battle)
        simplified_battle.print_summary()

        # 랜덤으로 행동 선택
        return self.choose_random_move(battle)


async def main():
    player1 = CustomPlayer2(battle_format="gen8randombattle")
    player2 = CustomPlayer2(battle_format="gen8randombattle")

    # 5번 배틀 (디버깅용)
    await player1.battle_against(player2, n_battles=1)

    print(f"Player1 won {player1.n_won_battles} / 1 battles")

if __name__ == "__main__":
    asyncio.run(main())