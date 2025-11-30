import asyncio
import sys
import os
import time

# 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'player', 'mcts'))

# MCTS 모듈
try:
    from player.mcts.MCTS_temp_parallel import mcts_search
except ImportError:
    print("❌ MCTS 모듈을 찾을 수 없습니다.")
    sys.exit(1)

from poke_env.player import Player, SimpleHeuristicsPlayer
from poke_env.battle import Battle

# ==========================================
# MCTS Player (로그 끄고 속도 위주)
# ==========================================
class MCTSPlayer(Player):
    def _convert_simplified_action_to_battle_action(self, battle: Battle, simplified_action):
        if simplified_action is None: return None
        action_class_name = simplified_action.__class__.__name__
        if action_class_name == "SimplifiedMove":
            move_id = simplified_action.id
            for move in battle.available_moves:
                if move.id == move_id: return move
        elif action_class_name == "SimplifiedPokemon":
            pokemon_species = simplified_action.species
            for pokemon in battle.available_switches:
                if pokemon.species == pokemon_species: return pokemon
        return None

    async def choose_move(self, battle: Battle):
        if len(battle.available_moves) == 0:
            return self.choose_random_move(battle)
        
        loop = asyncio.get_running_loop()
        try:
            # [수정됨] 튜플 언패킹 제거 ( , _ 삭제)
            # mcts_search는 이제 action 객체 하나만 반환합니다.
            simplified_action = await loop.run_in_executor(
                None, mcts_search, battle, 100, False, 1 
            )
        except Exception as e:
            # 에러 발생 시 로그 출력 (침묵 방지)
            print(f"!!! MCTS 실행 중 에러: {e}")
            return self.choose_random_move(battle)

        if simplified_action is None: return self.choose_random_move(battle)
        
        try:
            original_action = self._convert_simplified_action_to_battle_action(battle, simplified_action)
            if original_action is None: return self.choose_random_move(battle)
            return self.create_order(original_action)
        except Exception:
            return self.choose_random_move(battle)

# ==========================================
# MaxDamagePlayer (무조건 센 거 때림)
# ==========================================
class MaxDamagePlayer(Player):
    def choose_move(self, battle):
        if battle.available_moves:
            best_move = max(battle.available_moves, key=lambda move: move.base_power)
            return self.create_order(best_move)
        return self.choose_random_move(battle)

# ==========================================
# 메인 실행
# ==========================================
async def main():
    # 1. 봇 생성
    mcts_bot = MCTSPlayer(battle_format="gen9randombattle", max_concurrent_battles=5)
    
    max_damage_bot = MaxDamagePlayer(battle_format="gen9randombattle", max_concurrent_battles=5)
    heuristic_bot = SimpleHeuristicsPlayer(battle_format="gen9randombattle", max_concurrent_battles=5)

    print("\n==========================================")
    print("🔥 ROUND 1: MCTS vs MaxDamagePlayer (깡딜봇)")
    print("==========================================")
    await mcts_bot.battle_against(max_damage_bot, n_battles=10)
    print(f"결과: {mcts_bot.n_won_battles}승 {mcts_bot.n_lost_battles}패 (승률: {mcts_bot.n_won_battles*10}%)")

    # 전적 초기화 안 되므로 새로 계산 필요 (누적됨)
    wins_r1 = mcts_bot.n_won_battles

    print("\n==========================================")
    print("🧠 ROUND 2: MCTS vs SimpleHeuristics (지능봇)")
    print("==========================================")
    await mcts_bot.battle_against(heuristic_bot, n_battles=100)
    
    wins_total = mcts_bot.n_won_battles
    wins_r2 = wins_total - wins_r1
    print(f"결과: {wins_r2}승 {100 - wins_r2}패 (승률: {wins_r2}%)")
if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())