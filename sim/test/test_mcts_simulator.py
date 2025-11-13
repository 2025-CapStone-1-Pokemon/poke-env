"""
MCTS + SimplifiedBattle 통합 테스트 (병렬 처리)
"""
import asyncio
import sys
import os
from concurrent.futures import ThreadPoolExecutor

# 상위 디렉토리들을 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'player', 'mcts'))

from player.mcts.MCTS_temp_parallel import mcts_search
from poke_env.player import Player
from poke_env.battle import Battle

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
        
        # MCTS 검색 - SimplifiedAction 반환
        simplified_action = mcts_search(battle, iterations=1, verbose=False, n_workers=5)

        if simplified_action is None:
            return self.choose_random_move(battle)
        
        try:
            # SimplifiedAction을 원본 Battle action으로 변환
            original_action = self._convert_simplified_action_to_battle_action(battle, simplified_action)
            
            if original_action is None:
                return self.choose_random_move(battle)
            
            # 액션 타입 표시
            # action_class_name = simplified_action.__class__.__name__
            # if action_class_name == "SimplifiedMove":
            #     print(f"[MCTSPlayer] 선택: 기술 - {original_action.id}")
            # elif action_class_name == "SimplifiedPokemon":
            #     print(f"[MCTSPlayer] 선택: 포켓몬 교체 - {original_action.species}")
            
            order = self.create_order(original_action)
            return order
        except Exception as e:
            print(f"[MCTSPlayer] Error: {e}")
            import traceback
            traceback.print_exc()
            return self.choose_random_move(battle)


async def test_mcts_vs_random():
    """MCTS vs Random 테스트"""
    print("=== MCTS vs Random Bot 테스트 ===\n")
    
    # 플레이어 생성 (고정 팀)
    mcts_player = MCTSPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=10,
        #team=TEAM_MCTS_PACKED
    )
    
    random_player = RandomPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=10,
        #team=TEAM_MCTS_PACKED
    )
    
    # 1판만 대결 (빠른 테스트)
    print("배틀 시작...\n")
    
    try:
        await mcts_player.battle_against(random_player, n_battles=100)
    except Exception as e:
        print(f"배틀 중 에러: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 결과 ===")
    print(f"MCTS 전적: {mcts_player.n_won_battles}승 {mcts_player.n_lost_battles}패")
    print(f"Random 전적: {random_player.n_won_battles}승 {random_player.n_lost_battles}패")


if __name__ == "__main__":
    asyncio.run(test_mcts_vs_random())
