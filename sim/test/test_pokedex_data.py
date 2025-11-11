#!/usr/bin/env python3
"""간단한 더미 포켓몬 생성 테스트"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sim'))

from poke_env.data import GenData

def test_pokedex():
    """pokedex 데이터 로드 및 포켓몬 생성 테스트"""
    print("포켓몬 데이터 로드 테스트...")
    
    # GenData 로드
    data = GenData.from_gen(9)
    print(f"✓ Generation 9 데이터 로드 완료")
    print(f"✓ 총 포켓몬 수: {len(data.pokedex)}")
    
    # Pikachu 확인
    pikachu = data.pokedex['pikachu']
    print(f"\n✓ Pikachu 데이터:")
    print(f"  - 기본 종류: {pikachu.get('baseSpecies')}")
    print(f"  - 타입: {pikachu.get('types')}")
    print(f"  - 기본 스탯: {pikachu.get('baseStats')}")
    print(f"  - 특성: {pikachu.get('abilities')}")
    print(f"  - 이름: {pikachu.get('name')}")
    
    # Charizard 확인
    charizard = data.pokedex['charizard']
    print(f"\n✓ Charizard 데이터:")
    print(f"  - 기본 종류: {charizard.get('baseSpecies')}")
    print(f"  - 타입: {charizard.get('types')}")
    print(f"  - 기본 스탯: {charizard.get('baseStats')}")
    
    print(f"\n✓ 모든 테스트 완료!")

if __name__ == "__main__":
    try:
        test_pokedex()
    except Exception as e:
        print(f"✗ 에러: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
