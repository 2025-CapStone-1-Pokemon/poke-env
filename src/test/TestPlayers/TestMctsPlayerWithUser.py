import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from player.mcts.MctsPlayer import mcts_search
from poke_env.player import Player
from poke_env.ps_client.account_configuration import AccountConfiguration
from poke_env.ps_client.server_configuration import LocalhostServerConfiguration
from poke_env.battle import Battle

class MCTSPlayer(Player):
    def _convert_simplified_action_to_battle_action(self, battle: Battle, simplified_action):
        """MCTS 결과를 poke-env 행동 객체로 변환"""
        if simplified_action is None: return None
        
        action_class_name = simplified_action.__class__.__name__
        
        # 기술(Move)인 경우
        if action_class_name == "SimplifiedMove":
            move_id = simplified_action.id
            for move in battle.available_moves:
                if move.id == move_id: return move
        
        # 교체(Pokemon)인 경우
        elif action_class_name == "SimplifiedPokemon":
            pokemon_species = simplified_action.species
            for pokemon in battle.available_switches:
                if pokemon.species == pokemon_species: return pokemon
        
        return None

    async def choose_move(self, battle: Battle):
        """매 턴마다 호출되는 메인 함수"""
        
        if len(battle.available_moves) == 0:
            return self.choose_random_move(battle)
        
        print(f"\n [MCTS] {battle.player_username} 턴 {battle.turn} 계산 중...", end="", flush=True)
        
        loop = asyncio.get_running_loop()
        try:
            simplified_action = await loop.run_in_executor(
                None, 
                mcts_search, 
                battle, 
                100,    # iterations
                True,  # verbose
                1       # n_workers
            )
        except Exception as e:
            print(f"\n❌ [MCTS Error] {e}")
            import traceback
            traceback.print_exc()
            return self.choose_random_move(battle)

        print(" 완료!") 

        # 결과 변환 및 실행
        if simplified_action is None:
            return self.choose_random_move(battle)
        
        try:
            original_action = self._convert_simplified_action_to_battle_action(battle, simplified_action)
            
            if original_action is None:
                return self.choose_random_move(battle)
            
            return self.create_order(original_action)
        except Exception:
            return self.choose_random_move(battle)

async def main():
    bot_username = "MCTS_Bot"
    bot_account_config = AccountConfiguration(bot_username, None)

    mcts_bot = MCTSPlayer(
        account_configuration=bot_account_config,
        server_configuration=LocalhostServerConfiguration,
        battle_format="gen9randombattle", 
        max_concurrent_battles=10,        
    )

    print("\n==================================================")
    print(f"🚀 {bot_username} 가 로컬 서버에 접속했습니다!")
    print("==================================================")

    while True:
        try:
            await mcts_bot.accept_challenges(None, 1)
        except Exception as e:
            print(f"⚠️ 에러 발생 (재접속 시도): {e}")
            await asyncio.sleep(1)


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n 봇을 종료합니다.")