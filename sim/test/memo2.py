"""
MCTS + SimplifiedBattle 통합 테스트 (고정 팀)
"""
import asyncio
import sys
import os

# 상위 디렉토리들을 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

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
            opp = battle.opponent_active_pokemon
            print(f"\n【 opponent_active_pokemon 모든 정보 】")
            print(f"  species: {opp.species}")
            print(f"  level: {opp.level}")
            print(f"  current_hp: {opp.current_hp}")
            print(f"  max_hp: {opp.max_hp}")
            print(f"  current_hp_fraction: {opp.current_hp_fraction}")
            print(f"  status: {opp.status}")
            print(f"  types: {opp.types}")
            print(f"  ability: {opp.ability}")
            print(f"  item: {opp.item}")
            print(f"  boosts: {opp.boosts}")
            print(f"  stats: {opp.stats}")
            print(f"  base_stats: {opp.base_stats}")
            print(f"  moves: {[m.id for m in opp.moves]}")
            print(f"  gender: {opp.gender}")
            print(f"  active: {opp.active}")
            print(f"  fainted: {opp.fainted}")
            print(f"  first_turn: {opp.first_turn}")
            print(f"  protect_counter: {opp.protect_counter}")
            print(f"  effects: {opp.effects}")
            print()
        
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