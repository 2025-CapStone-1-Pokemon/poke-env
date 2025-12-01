import asyncio
import sys
import os
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from player.mcts.MctsPlayer import mcts_search
from poke_env.player import Player, SimpleHeuristicsPlayer
from poke_env.battle import Battle
import time

class GreedyPlayer(Player):
    """ 위력이 가장 높은 기술을 선택하는 플레이어 """
    def choose_move(self, battle: Battle):
        if not battle.available_moves:
            return self.choose_random_move(battle)
        
        # 가장 높은 위력의 기술 선택
        best_move = max(battle.available_moves, key=lambda move: move.base_power)
        return self.create_order(best_move)

class RandomPlayer(Player):
    """ 무작위로 기술을 선택하는 플레이어 """
    def choose_move(self, battle : Battle):
        return self.choose_random_move(battle)

class MCTSPlayer(Player):
    """MCTS 기반 플레이어"""
    
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
        
        # MCTS 검색 - SimplifiedAction 반환
        simplified_action = mcts_search(battle, iterations=100, verbose=False)

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
    """MCTS vs 봇 테스트"""

    random_player = RandomPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=5, 
    )
    
    mcts_player = MCTSPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=5, 
    )
    
    greedy_player = GreedyPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=5, 
    )

    smart_player = SimpleHeuristicsPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=5,
    )
    
    print("배틀 시작...\n")
    
    try:
        print("\nMCTS vs Bot Players")
        await mcts_player.battle_against(random_player, n_battles=100)
        
        # Round 1 결과 출력
        wins_r1 = mcts_player.n_won_battles
        lost_r1 = mcts_player.n_lost_battles
        print(f"Round 1 결과: {wins_r1}승 {lost_r1}패 (승률: {wins_r1/100*100:.1f}%)")

        print("\nMCTS vs Greedy Player")
        await mcts_player.battle_against(greedy_player, n_battles=100)
        
        # Round 2 결과 출력
        wins_r2 = mcts_player.n_won_battles - wins_r1
        lost_r2 = mcts_player.n_lost_battles - lost_r1
        print(f"Round 2 결과: {wins_r2}승 {lost_r2}패 (승률: {wins_r2/100*100:.1f}%)")
        print("\nMCTS vs Simple Heuristics Player")
        await mcts_player.battle_against(smart_player, n_battles=100)

        # Round 3 결과 출력
        wins_r3 = mcts_player.n_won_battles - wins_r1 - wins_r2
        lost_r3 = mcts_player.n_lost_battles - lost_r1 - lost_r2
        print(f"Round 3 결과: {wins_r3}승 {lost_r3}패 (승률: {wins_r3/100*100:.1f}%)")

    except Exception as e:
        print(f"배틀 중 에러: {e}")
        import traceback
        traceback.print_exc()
    
    # 최종 합계 출력
    print("\n=== 종합 결과 ===")
    print(f"MCTSPlayer 총 전적: {mcts_player.n_won_battles}승 {mcts_player.n_lost_battles}패")

if __name__ == "__main__":

    start_time = time.time()

    asyncio.run(test_mcts_vs_opponent())

    end_time = time.time()
    print(f"소요 시간: {end_time - start_time:.2f}초")