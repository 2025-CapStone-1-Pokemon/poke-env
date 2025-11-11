#!/usr/bin/env python3
"""SimplifiedBattle._create_dummy_pokemon 메서드 테스트"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sim'))

from poke_env.data import GenData
from SimplifiedBattle import SimplifiedBattle

def test_simplified_battle_methods():
    """SimplifiedBattle의 _create_dummy_pokemon 및 관련 메서드 테스트"""
    print("=" * 60)
    print("SimplifiedBattle._create_dummy_pokemon 테스트")
    print("=" * 60)
    
    # 더미 Battle 객체 생성
    class DummyBattle:
        def __init__(self):
            self.turn = 1
            self._gen = 9
            self.finished = False
            self.won = False
            self.lost = False
            self.team = {}
            self.opponent_team = {}
            self.active_pokemon = None
            self.opponent_active_pokemon = None
            self.weather = {}
            self.fields = {}
            self.side_conditions = {}
            self.opponent_side_conditions = {}
    
    # SimplifiedBattle 인스턴스 생성
    try:
        dummy_battle = DummyBattle()
        sb = SimplifiedBattle(dummy_battle, fill_unknown_data=False)
        print(f"✓ SimplifiedBattle 인스턴스 생성 완료\n")
    except Exception as e:
        print(f"✗ SimplifiedBattle 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 테스트 포켓몬들
    test_species = ['pikachu', 'charizard', 'blastoise']
    
    for species in test_species:
        try:
            print(f"--- {species.upper()} 생성 테스트 ---")
            
            # _create_dummy_pokemon 호출
            dummy_pokemon = sb._create_dummy_pokemon(species)
            print(f"✓ 포켓몬 생성 성공")
            
            # 기술 생성 테스트
            moves = sb._generate_random_moves(dummy_pokemon)
            print(f"✓ 기술 생성 성공 ({len(moves)}개)")
            
            # 출력
            print(f"  - 종류: {dummy_pokemon.species}")
            print(f"  - 타입: {dummy_pokemon.types}")
            print(f"  - 최대 HP: {dummy_pokemon.max_hp}")
            print(f"  - 특성: {dummy_pokemon.ability}")
            print(f"  - 기술: {[m.id for m in moves]}")
            print()
            
        except Exception as e:
            print(f"✗ 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("=" * 60)
    print("✓ 모든 테스트 완료!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_simplified_battle_methods()
    sys.exit(0 if success else 1)
