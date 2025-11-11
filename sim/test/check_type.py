from poke_env.data import GenData
from poke_env.battle.pokemon_type import PokemonType

data = GenData.from_gen(9)

# Pikachu의 타입 정보 확인
pikachu_data = data.pokedex['pikachu']
types_list = pikachu_data.get('types', [])
print(f'=== Pikachu types (from pokedex) ===')
print(f'Types list: {types_list}')

# PokemonType enum으로 변환 확인
for t in types_list:
    try:
        ptype = PokemonType[t.upper()]
        print(f'{t} -> PokemonType.{ptype.name}')
    except Exception as e:
        print(f'{t} -> ERROR: {e}')

# 검증
print(f'\nPokemonType.ELECTRIC: {PokemonType.ELECTRIC}')
print(f'PokemonType.ELECTRIC.name: {PokemonType.ELECTRIC.name}')
print(f'PokemonType.ELECTRIC.name.upper(): {PokemonType.ELECTRIC.name.upper()}')

# Blastoise도 확인
blastoise_data = data.pokedex['blastoise']
blastoise_types = blastoise_data.get('types', [])
print(f'\n=== Blastoise types (from pokedex) ===')
print(f'Types list: {blastoise_types}')

