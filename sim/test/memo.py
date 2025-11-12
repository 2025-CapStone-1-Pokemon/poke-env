"""
MCTS + SimplifiedBattle 통합 테스트 (고정 팀)
"""
import asyncio
import sys
import os

# 상위 디렉토리들을 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from player.MCTS_GEMINI import mcts_search
from poke_env.player import Player
from sim.SimplifiedBattle import SimplifiedBattle
from sim.battle.SimplifiedBattleEngine import SimplifiedBattleEngine


class RandomPlayer(Player):
    """간단한 랜덤 플레이어"""
    def choose_move(self, battle):
        return self.choose_random_move(battle)

class TestPlayer(Player):
    """객체 변환 테스트"""
    
    def choose_move(self, battle):

        if(battle.turn == 1):
            print("\n=============================================")
            print(">>> 1턴: SimplifiedBattleEngine 시뮬레이션 시작 (100번 반복)")
            # 시뮬레이션 100번 반복
            results = {"player_win": 0, "opponent_win": 0}
            
            for sim_num in range(500):
                simplified_battle = SimplifiedBattle(poke_env_battle=battle, team_num=3)
                simplified_battle_engine = SimplifiedBattleEngine()
                result = simplified_battle_engine.simulate_full_battle(battle=simplified_battle, verbose=False)
                
                # 결과 집계
                if result.won:
                    # 플레이어 팀 포켓몬 상세 정보 
                    results["player_win"] += 1
                else:
                    results["opponent_win"] += 1
                
                if (sim_num + 1) % 10 == 0:
                    print(f"  [{sim_num + 1}/100] 진행 중...")
            
            # 통계 출력
            total = results["player_win"] + results["opponent_win"]
            player_rate = (results["player_win"] / total * 100) if total > 0 else 0
            print(f"\n>>> 시뮬레이션 결과 (100번):")
            print(f"    플레이어 승리: {results['player_win']}승 ({player_rate:.1f}%)")
            print(f"    상대 승리: {results['opponent_win']}승 ({100-player_rate:.1f}%)")
            print("=============================================\n")
        
        return self.choose_random_move(battle)


async def test_mcts_vs_random():
    """MCTS vs Random 테스트"""
    print("=== MCTS vs Random Bot 테스트 (고정 팀) ===\n")
        
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

    # --- [수정] 2. 플레이어 생성 시 format 및 team 지정 ---



    
    # --- [수정] 2. 플레이어 생성 시 format 및 team 지정 ---
    mcts_player = TestPlayer(
        battle_format="gen9ou",  # gen9ou 포맷 사용
        team=TEAM_MCTS_PACKED,
        max_concurrent_battles=1
    )
    
    random_player = RandomPlayer(
        battle_format="gen9ou",  # gen9ou 포맷 사용
        team=TEAM_RANDOM_PACKED,  # 올바른 팀 사용
        max_concurrent_battles=1
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