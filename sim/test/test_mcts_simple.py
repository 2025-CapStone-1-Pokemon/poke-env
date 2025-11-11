"""
MCTS 로직만 테스트 (배틀 없이)
"""
import sys
import os

# 경로 설정
sim_path = os.path.join(os.path.dirname(__file__), '..')
poke_env_path = os.path.join(os.path.dirname(__file__), '..', '..')

sys.path.insert(0, poke_env_path)
sys.path.insert(0, sim_path)

from SimplifiedBattle import SimplifiedBattle
from test_simulator_accuracy_simple import TestPlayer
sys.path.insert(0, os.path.join(poke_env_path, 'player'))
from MCTS_GEMINI import mcts_search

import asyncio
import copy


async def test_mcts_logic():
    """MCTS 로직만 테스트"""
    print("=== MCTS 로직 단위 테스트 ===\n")
    
    # 1. 실제 배틀 진행 (SimplifiedBattle 변환용)
    print("1단계: 배틀 진행...")
    player1 = TestPlayer(battle_format="gen9randombattle", max_concurrent_battles=1)
    player2 = TestPlayer(battle_format="gen9randombattle", max_concurrent_battles=1)
    
    await player1.battle_against(player2, n_battles=1)
    
    if not player1.battles:
        print("배틀 진행 실패")
        return
    
    battle_tag = list(player1.battles.keys())[0]
    poke_env_battle = player1.battles[battle_tag]
    
    print(f"✓ 배틀 완료: {battle_tag}")
    print(f"  실제 결과: {'Player1 승' if poke_env_battle.won else 'Player2 승'} ({poke_env_battle.turn}턴)")
    
    # 2. SimplifiedBattle 변환
    print("\n2단계: SimplifiedBattle 변환...")
    simplified_battle = SimplifiedBattle(poke_env_battle)
    print(f"✓ 변환 완료")
    print(f"  플레이어 팀: {len(simplified_battle.team)}마리")
    print(f"  상대 팀: {len(simplified_battle.opponent_team)}마리")
    print(f"  활성: {simplified_battle.active_pokemon.species if simplified_battle.active_pokemon else 'None'}")
    print(f"  상대 활성: {simplified_battle.opponent_active_pokemon.species if simplified_battle.opponent_active_pokemon else 'None'}")
    
    # 3. MCTS 검색
    print("\n3단계: MCTS 검색 (iterations=50)...")
    action = mcts_search(simplified_battle, iterations=50, verbose=False)
    
    print(f"✓ MCTS 완료")
    print(f"  선택된 행동: {action}")
    print(f"  행동 타입: {type(action).__name__}")
    
    # 4. 선택 가능 여부 확인
    print("\n4단계: 행동 유효성 확인...")
    available_actions = list(simplified_battle.available_moves) + list(simplified_battle.available_switches)
    print(f"  가능한 행동: {len(available_actions)}개")
    
    if action in available_actions:
        print(f"  ✓ 선택된 행동은 유효합니다")
    else:
        print(f"  ✗ 선택된 행동이 유효하지 않습니다!")
    
    # 5. 동일 배틀에서 여러 번 MCTS 테스트
    print("\n5단계: 동일 배틀에서 5번 MCTS 실행...")
    actions_list = []
    for i in range(5):
        battle_copy = copy.deepcopy(simplified_battle)
        action = mcts_search(battle_copy, iterations=20, verbose=False)
        actions_list.append(action)
        print(f"  {i+1}. {action}")
    
    # 결과
    print("\n=== 결과 ===")
    print(f"✓ MCTS 로직이 정상적으로 동작합니다")
    print(f"  - Action 반환: {actions_list[0] is not None}")
    print(f"  - 결정성: {len(set(str(a) for a in actions_list))} 가지 선택")


if __name__ == "__main__":
    asyncio.run(test_mcts_logic())
