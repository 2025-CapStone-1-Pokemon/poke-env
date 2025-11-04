# 클래스 복사가 잘 되나 확인하는 코드

import asyncio
from poke_env.player import Player
from poke_env.battle import Battle
from SimplifiedPokemon import SimplifiedPokemon

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
            print(f"  종류(species): {p.species}")
            print(f"  레벨(level): {p.level}")
            print(f"  성별(gender): {p.gender}")
            print(f"  HP: {p.current_hp}/{p.max_hp} ({p.current_hp_fraction:.2%})")
            print(f"  기절 여부(fainted): {p.fainted}")
            print(f"  상태이상(status): {p.status}")
            print(f"  활성 여부(active): {p.active}")
            print(f"  특성(ability): {p.ability}")
            print(f"  아이템(item): {p.item}")
            print(f"  타입(types): {p.types}")
            print(f"  능력치 변화(boosts): {p.boosts}")
            print(f"  스탯(stats): {p.stats}")
            print(f"  기본 스탯(base_stats): {p.base_stats}")
            print(f"  기술 수(moves): {len(p.moves)}개")
            if p.moves:
                print(f"  기술 목록: {list(p.moves.keys())}")
            print(f"  효과(effects): {p.effects}")
        
        # 상대 포켓몬 확인
        if opponent_pokemons:
            print("\n[상대 팀 첫 번째 포켓몬]")
            p = opponent_pokemons[0]
            print(f"  종류(species): {p.species}")
            print(f"  레벨(level): {p.level}")
            print(f"  성별(gender): {p.gender}")
            print(f"  HP: {p.current_hp}/{p.max_hp} ({p.current_hp_fraction:.2%})")
            print(f"  기절 여부(fainted): {p.fainted}")
            print(f"  상태이상(status): {p.status}")
            print(f"  활성 여부(active): {p.active}")
            print(f"  특성(ability): {p.ability}")
            print(f"  아이템(item): {p.item}")
            print(f"  타입(types): {p.types}")
            print(f"  능력치 변화(boosts): {p.boosts}")
            print(f"  스탯(stats): {p.stats}")
            print(f"  기본 스탯(base_stats): {p.base_stats}")
            print(f"  기술 수(moves): {len(p.moves)}개")
            if p.moves:
                print(f"  기술 목록: {list(p.moves.keys())}")
            print(f"  효과(effects): {p.effects}")
        
        print("\n" + "="*60 + "\n")
        
        # 랜덤으로 행동 선택
        return self.choose_random_move(battle)

async def main():
    player1 = CustomPlayer(battle_format="gen8randombattle")
    player2 = CustomPlayer(battle_format="gen8randombattle")

    # 5번 배틀 (디버깅용)
    await player1.battle_against(player2, n_battles=1)

    print(f"Player1 won {player1.n_won_battles} / 1 battles")

if __name__ == "__main__":
    asyncio.run(main())