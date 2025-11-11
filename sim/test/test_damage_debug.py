#!/usr/bin/env python3
"""데미지 계산 디버깅 테스트"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from SimplifiedBattle import SimplifiedBattle
from poke_env.battle.pokemon_type import PokemonType
from poke_env.data import GenData

# 더미 Battle 객체
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

def test_damage_calculation():
    """데미지 계산 테스트"""
    print("=" * 70)
    print("데미지 계산 디버깅 테스트")
    print("=" * 70)
    
    dummy_battle = DummyBattle()
    sb = SimplifiedBattle(dummy_battle, fill_unknown_data=False)
    
    # 더미 포켓몬 2개 생성
    poke1 = sb._create_dummy_pokemon('pikachu')
    poke2 = sb._create_dummy_pokemon('blastoise')
    
    # 기술 설정
    poke1.moves = sb._generate_random_moves(poke1, 4)
    poke2.moves = sb._generate_random_moves(poke2, 4)
    
    print("\n[포켓몬 1 - Pikachu]")
    print(f"  종류: {poke1.species}")
    print(f"  타입: {[t.name for t in poke1.types]}")
    print(f"  레벨: {poke1.level}")
    print(f"  HP: {poke1.current_hp}/{poke1.max_hp}")
    print(f"  스탯: ATK={poke1.stats.get('atk', 100)}, DEF={poke1.stats.get('def', 100)}, SPA={poke1.stats.get('spa', 100)}, SPD={poke1.stats.get('spd', 100)}, SPE={poke1.stats.get('spe', 100)}")
    print(f"  기술:")
    for i, move in enumerate(poke1.moves):
        print(f"    {i+1}. {move.id:<20} BP={move.base_power:>3} ({move.category.name})")
    
    print("\n[포켓몬 2 - Blastoise]")
    print(f"  종류: {poke2.species}")
    print(f"  타입: {[t.name for t in poke2.types]}")
    print(f"  레벨: {poke2.level}")
    print(f"  HP: {poke2.current_hp}/{poke2.max_hp}")
    print(f"  스탯: ATK={poke2.stats.get('atk', 100)}, DEF={poke2.stats.get('def', 100)}, SPA={poke2.stats.get('spa', 100)}, SPD={poke2.stats.get('spd', 100)}, SPE={poke2.stats.get('spe', 100)}")
    print(f"  기술:")
    for i, move in enumerate(poke2.moves):
        print(f"    {i+1}. {move.id:<20} BP={move.base_power:>3} ({move.category.name})")
    
    # 시뮬레이션 엔진
    from battle.SimplifiedBattleEngine import SimplifiedBattleEngine
    
    engine = SimplifiedBattleEngine(gen=9)
    
    # 기술 선택
    move1 = poke1.moves[0] if poke1.moves else None
    move2 = poke2.moves[0] if poke2.moves else None
    
    if not move1 or not move2:
        print("기술이 없습니다!")
        return
    
    print("\n" + "=" * 70)
    print("데미지 계산 테스트")
    print("=" * 70)
    
    print(f"\n[Pikachu의 {move1.id}로 Blastoise를 공격]")
    print(f"  기술: {move1.id}")
    print(f"  위력: {move1.base_power}")
    print(f"  타입: {move1.type.name}")
    print(f"  카테고리: {move1.category.name}")
    
    if move1.category.name == "PHYSICAL":
        print(f"  공격스탯: {poke1.get_effective_stat('atk')}")
        print(f"  방어스탯: {poke2.get_effective_stat('def')}")
    else:
        print(f"  특공스탯: {poke1.get_effective_stat('spa')}")
        print(f"  특방스탯: {poke2.get_effective_stat('spd')}")
    
    # 데미지 계산
    damage = engine._calculate_damage(
        SimplifiedBattle(dummy_battle, fill_unknown_data=False),
        poke1, poke2, move1, crit=False
    )
    
    print(f"\n  계산된 데미지: {damage}")
    print(f"  Blastoise HP: {poke2.current_hp} → {max(0, poke2.current_hp - damage)}")
    print(f"  데미지율: {(damage / poke2.max_hp) * 100:.1f}%")
    
    print(f"\n[Blastoise의 {move2.id}로 Pikachu를 공격]")
    print(f"  기술: {move2.id}")
    print(f"  위력: {move2.base_power}")
    print(f"  타입: {move2.type.name}")
    print(f"  카테고리: {move2.category.name}")
    
    if move2.category.name == "PHYSICAL":
        print(f"  공격스탯: {poke2.get_effective_stat('atk')}")
        print(f"  방어스탯: {poke1.get_effective_stat('def')}")
    else:
        print(f"  특공스탯: {poke2.get_effective_stat('spa')}")
        print(f"  특방스탯: {poke1.get_effective_stat('spd')}")
    
    # 데미지 계산
    damage2 = engine._calculate_damage(
        SimplifiedBattle(dummy_battle, fill_unknown_data=False),
        poke2, poke1, move2, crit=False
    )
    
    print(f"\n  계산된 데미지: {damage2}")
    print(f"  Pikachu HP: {poke1.current_hp} → {max(0, poke1.current_hp - damage2)}")
    print(f"  데미지율: {(damage2 / poke1.max_hp) * 100:.1f}%")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        test_damage_calculation()
    except Exception as e:
        print(f"에러: {e}")
        import traceback
        traceback.print_exc()
