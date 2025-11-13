"""
MCTS + SimplifiedBattle 통합 테스트 (병렬 처리)
"""
import asyncio
import random
import sys
import os
from concurrent.futures import ThreadPoolExecutor

# 상위 디렉토리들을 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'player', 'mcts'))

from player.mcts.MCTS_temp_parallel import mcts_search
from poke_env.player import Player
from poke_env.battle import Battle
from sim.SimplifiedBattle import SimplifiedBattle
from sim.battle.SimplifiedBattleEngine import SimplifiedBattleEngine

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


class RandomPlayer(Player):
    """Tyranitar, Corviknight, Rotom-Wash 팀"""
    def choose_move(self, battle : Battle):
        return self.choose_random_move(battle)

class TestPlayer(RandomPlayer):
    """Garchomp, Gengar, Scizor 팀"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # SimplifiedBattleEngine 한 번만 생성
        self.simple_engine = SimplifiedBattleEngine(gen=9)
    
    def choose_move(self, battle: Battle):

        if battle.turn == 1:
            simple_battle = SimplifiedBattle(battle)
        
            # 전투 시뮬레이션
            self.simple_engine.simulate_full_battle(battle=simple_battle, verbose=True)

        # available_moves가 비어있으면 교체
        if not battle.available_moves:
            if battle.available_switches:
                return self.create_order(battle.available_switches[0])
            return self.choose_random_move(battle)
        
        
        # 실제 배틀에서 선택
        return self.create_order(random.choice(battle.available_moves))


async def test_mcts_vs_random():
    """MCTS vs Random 테스트"""
    print("=== MCTS vs Random Bot 테스트 ===\n")
    
    # 플레이어 생성 (고정 팀)
    mcts_player = TestPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1,
        #team=TEAM_MCTS_PACKED
    )
    
    random_player = RandomPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1,
        #team=TEAM_MCTS_PACKED
    )
    
    # 1판만 대결 (빠른 테스트)
    print("배틀 시작...\n")
    
    try:
        await mcts_player.battle_against(random_player, n_battles=1)
    except Exception as e:
        print(f"배틀 중 에러: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 결과 ===")
    print(f"MCTS 전적: {mcts_player.n_won_battles}승 {mcts_player.n_lost_battles}패")
    print(f"Random 전적: {random_player.n_won_battles}승 {random_player.n_lost_battles}패")


if __name__ == "__main__":
    asyncio.run(test_mcts_vs_random())
