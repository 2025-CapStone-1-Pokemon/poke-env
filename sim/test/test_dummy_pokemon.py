#!/usr/bin/env python3
"""더미 포켓몬 생성 테스트"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sim'))

from poke_env.data import GenData
from SimplifiedPokemon import SimplifiedPokemon
from SimplifiedBattle import SimplifiedBattle

def test_create_dummy_pokemon():
    """_create_dummy_pokemon 메서드 테스트"""
    print("=" * 50)
    print("더미 포켓몬 생성 테스트")
    print("=" * 50)
    
    # GenData 로드
    data = GenData.from_gen(9)
    print(f"✓ Generation 9 데이터 로드 완료")
    
    # 테스트용 더미 Battle 객체 생성 (SimplifiedBattle은 Battle이 필요하므로)
    # 대신 SimplifiedBattle의 _create_dummy_pokemon 메서드를 직접 사용
    
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
    
    # SimplifiedBattle 인스턴스 생성 (fill_unknown_data=False로 _fill_opponent_team_data 스킵)
    try:
        dummy_battle = DummyBattle()
        sb = SimplifiedBattle(dummy_battle, fill_unknown_data=False)
        print(f"✓ SimplifiedBattle 인스턴스 생성 완료")
    except Exception as e:
        print(f"✗ SimplifiedBattle 생성 실패: {e}")
        return False
    
    # 테스트 포켓몬들
    test_species = ['pikachu', 'charizard', 'blastoise', 'gengar', 'alakazam']
    
    for species in test_species:
        try:
            dummy_pokemon = sb._create_dummy_pokemon(species)
            print(f"\n✓ {species} 더미 포켓몬 생성 성공")
            print(f"  - 종류: {dummy_pokemon.species}")
            print(f"  - 타입: {dummy_pokemon.types}")
            print(f"  - 기본 스탯: {dummy_pokemon.base_stats}")
            print(f"  - 최대 HP: {dummy_pokemon.max_hp}")
            print(f"  - 특성: {dummy_pokemon.ability}")
            
            # 기술 생성 테스트
            moves = sb._generate_random_moves(dummy_pokemon)
            print(f"  - 기술 개수: {len(moves)}")
            for move in moves:
                print(f"    • {move._id}")
        except Exception as e:
            print(f"\n✗ {species} 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "=" * 50)
    print("모든 테스트 완료! ✓")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = test_create_dummy_pokemon()
    sys.exit(0 if success else 1)
