import asyncio
import sys
import os
import time
import logging

# 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from player.mcts.MCTS_temp_parallel import mcts_search
from sim.SimplifiedBattle import SimplifiedBattle  # SimplifiedAction 클래스 확인용
from poke_env.player import Player, RandomPlayer
from poke_env.battle import Battle

# 로깅 설정 (에러 확인용)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("MCTS_Test")

class MCTSPlayer(Player):
    def _convert_simplified_action_to_battle_action(self, battle: Battle, simplified_action):
        """MCTS 결과를 실제 배틀 액션으로 변환"""
        if simplified_action is None:
            return None
        
        # 클래스 이름으로 타입 확인
        action_type = simplified_action.__class__.__name__
        
        # 1. 기술(Move)인 경우
        if action_type == "SimplifiedMove":
            for move in battle.available_moves:
                if move.id == simplified_action.id:
                    return move
            logger.warning(f"⚠ 기술 매칭 실패: {simplified_action.id}")

        # 2. 교체(Pokemon)인 경우
        elif action_type == "SimplifiedPokemon":
            for pokemon in battle.available_switches:
                if pokemon.species == simplified_action.species:
                    return pokemon
            logger.warning(f"⚠ 교체 매칭 실패: {simplified_action.species}")
            
        return None

    def choose_move(self, battle: Battle):
        logger.info(f"[{battle.turn}턴] 행동 선택 시작... (Active: {battle.active_pokemon.species if battle.active_pokemon else 'None'})")
        
        # 1. 강제 교체 상황 (기술 사용 불가) 처리
        if not battle.available_moves:
            logger.info("👉 강제 교체 상황 (Force Switch) -> 랜덤 교체 수행")
            return self.choose_random_move(battle)

        # 2. MCTS 실행
        try:
            start_time = time.time()
            
            # MCTS 반복 횟수 30회로 조정 (속도 확보)
            simplified_action = mcts_search(battle, iterations=30, verbose=True, n_workers=1)
            
            elapsed = time.time() - start_time
            logger.info(f"⏱ MCTS 수행 시간: {elapsed:.2f}초")

            if simplified_action is None:
                logger.warning("❌ MCTS가 행동을 결정하지 못함 -> 랜덤 행동")
                return self.choose_random_move(battle)

            # 3. 행동 변환 및 실행
            final_action = self._convert_simplified_action_to_battle_action(battle, simplified_action)
            
            if final_action:
                logger.info(f"✅ MCTS 결정: {final_action}")
                return self.create_order(final_action)
            else:
                logger.error("❌ 행동 변환 실패 (Simplified -> Real) -> 랜덤 행동")
                return self.choose_random_move(battle)

        except Exception as e:
            logger.error(f"🔥 MCTS 에러 발생: {e}")
            import traceback
            traceback.print_exc()
            return self.choose_random_move(battle)

async def test_mcts_vs_random():
    print("\n" + "="*60)
    print("🥊 MCTS (Gen 9) vs Random Bot 대결 시작")
    print("="*60 + "\n")
    
    # 동시 배틀 수를 1로 줄여서 로그 꼬임 방지
    mcts_player = MCTSPlayer(battle_format="gen9randombattle", max_concurrent_battles=1)
    random_player = RandomPlayer(battle_format="gen9randombattle", max_concurrent_battles=1)
    
    # 1판 실행
    await mcts_player.battle_against(random_player, n_battles=1)

    print("\n" + "="*60)
    print(f"🏆 결과: MCTS {mcts_player.n_won_battles}승 vs Random {random_player.n_won_battles}승")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_mcts_vs_random())