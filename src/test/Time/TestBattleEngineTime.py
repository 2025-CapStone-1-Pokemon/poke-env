# 랜덤으로 포켓몬을 추정했을 때, 해당 포켓몬의 추정이 약하게 되는지를 확인하는 코드

"""
MCTS + SimplifiedBattle 통합 테스트
"""
import time  # ← time 모듈 자체를 import
import asyncio
from asyncio.log import logger
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# 상위 디렉토리들을 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from poke_env.player import Player, SimpleHeuristicsPlayer
from sim.SimplifiedBattle import SimplifiedBattle
from sim.battle.SimplifiedBattleEngine import SimplifiedBattleEngine


class TestPlayer(Player):
    """MCTS 플레이어 (테스트용)"""

    def choose_move(self, battle):

        if battle.turn == 1:
            simple_battle = SimplifiedBattle(battle)
            simple_battle_engine = SimplifiedBattleEngine(gen=9)

            # 100번 실행하는데 걸리는 시간 계산
            start_time = time.time()
            for _ in range(100):
                simple_battle_engine.simulate_full_battle(battle=simple_battle, verbose=False)
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"100번 실행하는데 걸리는 시간: {elapsed_time:.2f}초") 
        # ✅ 항상 유효한 선택지 반환
        return self.choose_random_move(battle)


class GreedyPlayer(Player):
    """간단한 랜덤 플레이어"""
    
    def choose_move(self, battle):
        """가용한 기술 중 가장 높은 위력을 가진 기술 선택"""
        if battle.available_moves:
            best_move = max(battle.available_moves, key=lambda move: move.base_power or 0)
            return self.create_order(best_move)
        return self.choose_random_move(battle)


async def test_mcts_vs_random():
    """MCTS vs Random 테스트"""
    # 플레이어 생성
    heuristic_player = SimpleHeuristicsPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1
    )
    
    greedy_player = GreedyPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1
    )

    try:
        await heuristic_player.battle_against(greedy_player, n_battles=50)
    except Exception as e:
        print(f"배틀 중 오류: {e}")
        import traceback
        traceback.print_exc()

    print("테스트 완료.")
    print("결과 : player 1 승리 수 =", heuristic_player.n_won_battles
          , ", player 2 승리 수 =", greedy_player.n_won_battles)

if __name__ == "__main__":
    asyncio.run(test_mcts_vs_random())
