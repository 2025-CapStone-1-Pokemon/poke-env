import asyncio
from poke_env.player import Player, RandomPlayer

# Player 클래스를 상속받아 나만의 플레이어를 만듭니다.
class MaxDamagePlayer(Player):
    # AI의 모든 로직은 choose_move 메소드 안에 구현됩니다.
    def choose_move(self, battle):
        # battle.available_moves는 현재 턴에서 사용할 수 있는 기술 목록입니다.
        # 이 목록이 비어있지 않다면, 즉 쓸 수 있는 기술이 있다면,
        if battle.available_moves:
            print(battle.available_moves)
            # key=lambda move: move.base_power를 사용해
            # 기술 목록에서 base_power가 가장 높은 기술을 찾습니다.
            best_move = max(battle.available_moves, key=lambda move: move.base_power)
            
            # 찾은 기술을 사용하라는 명령을 반환합니다.
            return self.create_order(best_move)
        
        # 만약 쓸 수 있는 기술이 없다면 (ex: 도발에 걸렸을 때)
        # 랜덤으로 가능한 행동(주로 교체)을 선택합니다.
        else:
            return self.choose_random_move(battle)

async def main():
    # 위에서 만든 MaxDamagePlayer와 기본 RandomPlayer를 생성합니다.
    max_damage_player = MaxDamagePlayer(
        battle_format="gen8randombattle"
    )
    random_player = RandomPlayer(
        battle_format="gen8randombattle"
    )

    # 두 플레이어를 100번 배틀시킵니다.
    await max_damage_player.battle_against(random_player, n_battles=100)

    # 배틀 결과를 출력합니다.
    print(
        f"MaxDamagePlayer won {max_damage_player.n_won_battles} / 100 battles"
    )

if __name__ == "__main__":
    asyncio.run(main())