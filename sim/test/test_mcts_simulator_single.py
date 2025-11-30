import asyncio
import sys
import os
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'player', 'mcts'))

from player.mcts.MCTS_temp_parallel import mcts_search
from poke_env.player import Player, SimpleHeuristicsPlayer
from poke_env.battle import Battle
import time

# 고정 팀
TEAM_MCTS_PACKED = (
    "|Garchomp|Rocky Helmet|Rough Skin|Dragon Claw,Earthquake,Stone Edge,Swords Dance|Jolly|0,252,0,0,4,252||||100|]"
    "|Gengar|Black Sludge|Cursed Body|Shadow Ball,Sludge Bomb,Focus Blast,Trick|Timid|0,0,0,252,4,252||||100|]"
    "|Scizor|Choice Band|Technician|Bullet Punch,U-turn,Close Combat,Knock Off|Adamant|248,252,0,0,8,0||||100|"
)

TEAM_RANDOM_PACKED = (
    "|Tyranitar|Leftovers|Sand Stream|Stone Edge,Crunch,Earthquake,Dragon Dance|Adamant|252,252,0,0,4,0||||100|]"
    "|Corviknight|Leftovers|Pressure|Brave Bird,Iron Head,Roost,Defog|Impish|252,0,252,0,4,0||||100|]"
    "|Rotom-Wash|Leftovers|Levitate|Hydro Pump,Volt Switch,Will-O-Wisp,Pain Split|Bold|252,0,0,0,212,44||||100|"
)

class GreedyPlayer(Player):
    """ 위력이 가장 높은 기술을 선택하는 플레이어 """
    def choose_move(self, battle: Battle):
        if not battle.available_moves:
            return self.choose_random_move(battle)
        
        # 가장 높은 위력의 기술 선택
        best_move = max(battle.available_moves, key=lambda move: move.base_power)
        return self.create_order(best_move)
    
class RandomPlayer(Player):
    """Tyranitar, Corviknight, Rotom-Wash 팀"""
    def choose_move(self, battle : Battle):
        return self.choose_random_move(battle)

class RandomPlayer(Player):
    """Tyranitar, Corviknight, Rotom-Wash 팀"""
    def choose_move(self, battle : Battle):
        return self.choose_random_move(battle)

class MCTSPlayer(Player):
    """Garchomp, Gengar, Scizor 팀"""
    
    def _convert_simplified_action_to_battle_action(self, battle : Battle, simplified_action):
        """
        SimplifiedAction을 원본 Battle 객체의 action으로 변환
        
        Args:
            battle: 원본 Battle 객체
            simplified_action: SimplifiedMove 또는 SimplifiedPokemon
            
        Returns:
            원본 Battle 객체의 Move 또는 Pokemon
        """
        if simplified_action is None:
            return None
        
        action_class_name = simplified_action.__class__.__name__
        
        # 기술인 경우
        if action_class_name == "SimplifiedMove":
            move_id = simplified_action.id
            for move in battle.available_moves:
                if move.id == move_id:
                    return move
        
        # 포켓몬인 경우
        elif action_class_name == "SimplifiedPokemon":
            pokemon_species = simplified_action.species
            for pokemon in battle.available_switches:
                if pokemon.species == pokemon_species:
                    return pokemon
        
        return None
    
    def choose_move(self, battle: Battle):
        """MCTS로 최적 행동 선택"""
        # 기술이 없으면 교체 강제
        if len(battle.available_moves) == 0:
            return self.choose_random_move(battle)
        
        # print(f"\n[MCTSPlayer] 턴: {battle.turn}")
        
        # MCTS 검색 - SimplifiedAction 반환
        simplified_action = mcts_search(battle, iterations=100, verbose=False, n_workers=5)

        if simplified_action is None:
            return self.choose_random_move(battle)
        
        try:
            # SimplifiedAction을 원본 Battle action으로 변환
            original_action = self._convert_simplified_action_to_battle_action(battle, simplified_action)
            
            if original_action is None:
                return self.choose_random_move(battle)
            
            order = self.create_order(original_action)
            return order
        except Exception as e:
            print(f"[MCTSPlayer] Error: {e}")
            import traceback
            traceback.print_exc()
            return self.choose_random_move(battle)


async def test_mcts_vs_opponent():
    """MCTS vs Random 테스트"""
    print("=== MCTS vs Random Bot 테스트 ===\n")

    random_player = RandomPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=5,  # ✅ 5로 변경
    )
    
    mcts_player = MCTSPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=5,  # ✅ 5로 변경 (동시 배틀 5개)
    )
    
    greedy_player = GreedyPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=5,  # ✅ 5로 변경
    )

    smart_player = SimpleHeuristicsPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=5,  # ✅ 5로 변경
    )
    
    # 1판만 대결 (빠른 테스트)
    print("배틀 시작...\n")
    
    try:
        # ==========================================
        # 1. vs Smart Player (40판)
        # ==========================================
        print("\n🔥 [Round 1] MCTS vs Smart Player (50 battles)")
        await mcts_player.battle_against(smart_player, n_battles=1)
        
        # Round 1 결과 출력 (현재까지의 전적)
        wins_r1 = mcts_player.n_won_battles
        lost_r1 = mcts_player.n_lost_battles
        print(f"👉 Round 1 결과: {wins_r1}승 {lost_r1}패 (승률: {wins_r1/50*100:.1f}%)")


        # ==========================================
        # 2. vs Greedy Player (50판)
        # ==========================================
        # print("\n🔥 [Round 2] MCTS vs Greedy Player (100 battles)")
        # # 여기서 전적이 누적되므로, 시작 전 승수를 저장해둠
        # start_wins = mcts_player.n_won_battles
        # start_lost = mcts_player.n_lost_battles
        
        # await mcts_player.battle_against(greedy_player, n_battles=100)
        
        # # Round 2 결과 계산 (현재 전적 - 시작 전 전적)
        # wins_r2 = mcts_player.n_won_battles - start_wins
        # lost_r2 = mcts_player.n_lost_battles - start_lost
        # print(f"👉 Round 2 결과: {wins_r2}승 {lost_r2}패 (승률: {wins_r2/50*100:.1f}%)")

    except Exception as e:
        print(f"배틀 중 에러: {e}")
        import traceback
        traceback.print_exc()
    
    # 최종 합계 (선택 사항)
    print("\n=== 종합 결과 ===")
    print(f"MCTSPlayer 총 전적: {mcts_player.n_won_battles}승 {mcts_player.n_lost_battles}패")

if __name__ == "__main__":

    start_time = time.time()

    asyncio.run(test_mcts_vs_opponent())

    end_time = time.time()
    print(f"소요 시간: {end_time - start_time:.2f}초")