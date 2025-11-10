"""
SimplifiedBattleEngine 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from poke_env.player import RandomPlayer
from SimplifiedBattle import SimplifiedBattle
from SimplifiedBattleEngine import SimplifiedBattleEngine


class TestPlayer(RandomPlayer):
    """테스트용 플레이어"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.battle_history = []
    
    async def _battle_finished_callback(self, battle):
        """배틀 종료 시 호출"""
        # SimplifiedBattle로 변환
        simplified = SimplifiedBattle(battle)
        self.battle_history.append(simplified)
        
        print("\n" + "="*60)
        print("배틀 종료 - 시뮬레이션 테스트 시작")
        print("="*60)
        
        # 엔진 초기화
        engine = SimplifiedBattleEngine()
        
        # === 테스트 1: 3턴 시뮬레이션 ===
        print("\n[테스트 1] 3턴 시뮬레이션")
        print("-" * 60)
        current_battle = simplified
        
        for i in range(3):
            if current_battle.finished:
                print(f"턴 {i+1}: 배틀이 이미 종료되었습니다.")
                break
            
            # 랜덤으로 시뮬레이션
            next_battle = engine.simulate_turn(current_battle)
            
            # 결과 출력
            print(f"\n턴 {i+1} 결과:")
            if next_battle.active_pokemon:
                print(f"  플레이어: {next_battle.active_pokemon.species} "
                      f"(HP: {next_battle.active_pokemon.current_hp}/{next_battle.active_pokemon.max_hp})")
            
            if next_battle.opponent_active_pokemon:
                print(f"  상대: {next_battle.opponent_active_pokemon.species} "
                      f"(HP: {next_battle.opponent_active_pokemon.current_hp}/{next_battle.opponent_active_pokemon.max_hp})")
            
            current_battle = next_battle
        
        # === 테스트 2: 전체 배틀 시뮬레이션 ===
        print("\n" + "="*60)
        print("[테스트 2] 전체 배틀 시뮬레이션 (승패 결정까지)")
        print("="*60)
        
        final_battle = engine.simulate_full_battle(
            simplified,
            max_turns=50,
            verbose=True
        )
        
        # 최종 결과
        print("\n" + "="*60)
        print("최종 결과")
        print("="*60)
        print(f"배틀 종료: {final_battle.finished}")
        if final_battle.finished:
            winner = "플레이어" if final_battle.won else "상대"
            print(f"승자: {winner}")
        else:
            print("무승부 (최대 턴 수 도달)")
        
        # 팀 상태
        print("\n플레이어 팀:")
        for identifier, pokemon in final_battle.team.items():
            status = "생존" if pokemon.current_hp > 0 else "기절"
            print(f"  {pokemon.species}: {pokemon.current_hp}/{pokemon.max_hp} ({status})")
        
        print("\n상대 팀:")
        for identifier, pokemon in final_battle.opponent_team.items():
            status = "생존" if pokemon.current_hp > 0 else "기절"
            print(f"  {pokemon.species}: {pokemon.current_hp}/{pokemon.max_hp} ({status})")
        
        print("\n" + "="*60)
        print("시뮬레이션 테스트 종료")
        print("="*60 + "\n")


async def main():
    """메인 함수"""
    # 플레이어 생성
    player1 = TestPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1
    )
    player2 = RandomPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1
    )
    
    # 1배틀 진행
    await player1.battle_against(player2, n_battles=1)
    
    print(f"\n총 {len(player1.battle_history)}개의 배틀 기록")


if __name__ == "__main__":
    asyncio.run(main())
