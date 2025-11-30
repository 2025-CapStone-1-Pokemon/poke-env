import asyncio
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor

# 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'player', 'mcts'))

# MCTS 모듈 임포트
try:
    from player.mcts.MCTS_temp_parallel import mcts_search
except ImportError:
    print("오류: 'player.mcts.MCTS_temp_parallel' 모듈을 찾을 수 없습니다.")
    sys.exit(1)

from poke_env.player import Player
from poke_env.battle import Battle


class RandomPlayer(Player):
    def choose_move(self, battle: Battle):
        return self.choose_random_move(battle)


class MCTSPlayer(Player):
    def _convert_simplified_action_to_battle_action(self, battle: Battle, simplified_action):
        """SimplifiedAction을 원본 Battle 객체의 action으로 변환"""
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

    async def choose_move(self, battle: Battle):
        """MCTS로 최적 행동 선택 (비동기 병렬 처리)"""
        # 기술이 없으면 랜덤
        if len(battle.available_moves) == 0:
            return self.choose_random_move(battle)
        
        # MCTS 연산을 별도 스레드풀에서 실행하여 이벤트 루프 차단 방지
        loop = asyncio.get_running_loop()
        
        try:
            simplified_action = await loop.run_in_executor(
                None,  # 기본 Executor 사용
                mcts_search,
                battle,
                300,    # iterations (탐색 횟수)
                False,  # verbose (로그 끔)
                1       # n_workers (내부 병렬 처리 수)
            )
        except Exception as e:
            print(f"[MCTS Error] {e}")
            return self.choose_random_move(battle)

        if simplified_action is None:
            return self.choose_random_move(battle)
        
        try:
            original_action = self._convert_simplified_action_to_battle_action(battle, simplified_action)
            
            if original_action is None:
                return self.choose_random_move(battle)
            
            return self.create_order(original_action)
        except Exception as e:
            print(f"[Action Conversion Error] {e}")
            return self.choose_random_move(battle)


async def test_mcts_vs_random():
    """MCTS vs Random Bot 다중 배틀 테스트"""
    
    # === 설정값 ===
    N_BATTLES = 10           # 총 배틀 수
    CONCURRENT_BATTLES = 5   # 동시에 진행할 배틀 수 (너무 높으면 타임아웃 위험)
    
    print(f"=== MCTS vs Random Bot 테스트 ===")
    print(f"총 배틀: {N_BATTLES}판 | 동시 진행: {CONCURRENT_BATTLES}판")
    print("배틀 시작...\n")
    
    start_time = time.time()

    # team 파라미터를 제거하여 서버가 주는 랜덤 팀 사용
    mcts_player = MCTSPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=CONCURRENT_BATTLES,
    )
    
    random_player = RandomPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=CONCURRENT_BATTLES,
    )
    
    try:
        await mcts_player.battle_against(random_player, n_battles=N_BATTLES)
    except Exception as e:
        print(f"배틀 실행 중 에러: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*30)
    print("       최종 결과       ")
    print("="*30)
    print(f"소요 시간: {duration:.2f}초")
    print(f"MCTS 승리: {mcts_player.n_won_battles}")
    print(f"MCTS 패배: {mcts_player.n_lost_battles}")
    if N_BATTLES > 0:
        print(f"승률: {mcts_player.n_won_battles / N_BATTLES * 100:.1f}%")
    print("="*30)


if __name__ == "__main__":
    # Windows 환경 이슈 대응
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(test_mcts_vs_random())