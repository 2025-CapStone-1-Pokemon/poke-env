#!/usr/bin/env python3

from poke_env.data import GenData
from poke_env.battle.pokemon_type import PokemonType

# 직접적으로 시뮬레이션
data = GenData.from_gen(9)

# Pikachu pokedex 데이터
pikachu_data = data.pokedex['pikachu']
types_list = pikachu_data.get('types', [])

# SimplifiedPokemon에서 하는 것과 동일하게
types_enum_list = [PokemonType[t.upper()] for t in types_list] if types_list else [PokemonType.NORMAL]

print(f'=== Pikachu types ===')
print(f'types_list: {types_list}')
print(f'types_enum_list: {types_enum_list}')

# 포켓몬 타입 비교
pokemon_types = [t.name.upper() for t in types_enum_list]
print(f'pokemon_types: {pokemon_types}')

# Thunder 기술 확인
move_type = data.moves['thunder'].get('type')
print(f'\nThunder type: {move_type}')
print(f'Is Thunder in pokemon_types? {move_type in pokemon_types}')
