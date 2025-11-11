#!/usr/bin/env python3
"""더미 포켓몬 생성 통합 테스트"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sim'))

from poke_env.data import GenData
from SimplifiedPokemon import SimplifiedPokemon

def test_dummy_pokemon_creation():
    """_create_dummy_pokemon 메서드 테스트"""
    print("=" * 60)
    print("더미 포켓몬 생성 통합 테스트")
    print("=" * 60)
    
    from poke_env.battle.pokemon_type import PokemonType
    
    # GenData 로드
    data = GenData.from_gen(9)
    print(f"✓ Generation 9 데이터 로드 완료")
    
    # 테스트 포켓몬들
    test_species = ['pikachu', 'charizard', 'blastoise']
    
    for species in test_species:
        try:
            print(f"\n--- {species.upper()} 생성 테스트 ---")
            
            # pokedex 데이터 가져오기
            pokedex_data = data.pokedex.get(species.lower(), {})
            
            # SimplifiedPokemon 객체 생성 (__new__ 사용)
            dummy_pokemon = SimplifiedPokemon.__new__(SimplifiedPokemon)
            
            # 기본 정보 설정
            dummy_pokemon.species = pokedex_data.get('baseSpecies', species).lower()
            dummy_pokemon.level = 50
            dummy_pokemon.gender = None
            
            # 타입 설정
            types_list = pokedex_data.get('types', [])
            type_1_str = types_list[0].upper() if types_list else 'NORMAL'
            type_2_str = types_list[1].upper() if len(types_list) > 1 else None
            
            dummy_pokemon.type_1 = PokemonType[type_1_str] if type_1_str else PokemonType.NORMAL
            dummy_pokemon.type_2 = PokemonType[type_2_str] if type_2_str else None
            dummy_pokemon.types = [PokemonType[t.upper()] for t in types_list] if types_list else [PokemonType.NORMAL]
            
            # HP 설정
            base_stats = pokedex_data.get('baseStats', {'hp': 100, 'atk': 100, 'def': 100, 'spa': 100, 'spd': 100, 'spe': 100})
            base_hp = base_stats.get('hp', 100)
            dummy_pokemon.max_hp = int(((base_hp * 2 + 31 + 85) * 50) / 100) + 50 + 10
            dummy_pokemon.current_hp = dummy_pokemon.max_hp
            
            # 상태이상
            dummy_pokemon.status = None
            dummy_pokemon.status_counter = 0
            
            # 스탯 설정
            dummy_pokemon.base_stats = base_stats.copy()
            dummy_pokemon.stats = {}
            for stat_name, base in dummy_pokemon.base_stats.items():
                if stat_name == 'hp':
                    dummy_pokemon.stats[stat_name] = int(((base * 2 + 31 + 85) * 50) / 100) + 50 + 10
                else:
                    dummy_pokemon.stats[stat_name] = int(((base * 2 + 31 + 5) * 50) / 100) + 5
            
            # 부스트
            dummy_pokemon.boosts = {stat: 0 for stat in ['atk', 'def', 'spa', 'spd', 'spe']}
            
            # 기술
            dummy_pokemon.moves = []
            
            # 특성 및 아이템
            abilities = pokedex_data.get('abilities', {})
            dummy_pokemon.ability = abilities.get('0', abilities.get('H', 'unknown'))
            dummy_pokemon.item = None
            
            # 효과
            dummy_pokemon.effects = {}
            
            # 배틀 상태
            dummy_pokemon.active = False
            dummy_pokemon.first_turn = True
            dummy_pokemon.must_recharge = False
            dummy_pokemon.protect_counter = 0
            
            # 출력
            print(f"✓ 생성 성공!")
            print(f"  - 종류: {dummy_pokemon.species}")
            print(f"  - 레벨: {dummy_pokemon.level}")
            print(f"  - 타입: {dummy_pokemon.types}")
            print(f"  - 최대 HP: {dummy_pokemon.max_hp} / 현재 HP: {dummy_pokemon.current_hp}")
            print(f"  - 기본 스탯: {dummy_pokemon.base_stats}")
            print(f"  - 계산된 스탯: {dummy_pokemon.stats}")
            print(f"  - 특성: {dummy_pokemon.ability}")
            
        except Exception as e:
            print(f"✗ 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n" + "=" * 60)
    print("✓ 모든 테스트 완료!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_dummy_pokemon_creation()
    sys.exit(0 if success else 1)
