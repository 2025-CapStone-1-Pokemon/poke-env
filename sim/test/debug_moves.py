from poke_env.data import GenData

data = GenData.from_gen(9)

# Pikachu 필터링 - 더 자세한 디버그
pokedex_species = 'pikachu'
learnable_moves = []

if pokedex_species in data.learnset and 'learnset' in data.learnset[pokedex_species]:
    learnable_moves = list(data.learnset[pokedex_species]['learnset'].keys())

print(f'Total learnable moves: {len(learnable_moves)}')

# Thunder 체크
if 'thunder' in learnable_moves:
    print(f'Thunder is in learnable_moves: YES')
    thunder_data = data.moves.get('thunder', {})
    print(f'Thunder type: {thunder_data.get("type")}')
    print(f'Thunder BP: {thunder_data.get("basePower")}')

# 실제 필터링
pokemon_types_str = ['ELECTRIC']
type_moves = []
for move_id in learnable_moves:
    move_data = data.moves.get(move_id, {})
    move_type = move_data.get('type', 'Normal')
    base_power = move_data.get('basePower', 0)
    
    if base_power > 0 and move_type in pokemon_types_str:
        type_moves.append((move_id, move_data))
        if len(type_moves) <= 10:
            print(f'  Found: {move_id} ({move_type}, BP={base_power})')

print(f'\nTotal STAB moves: {len(type_moves)}')

# 체크: moves 딕셔너리에 thunder가 있는가?
if 'thunder' in data.moves:
    print(f'\nThunder in data.moves: YES')
    print(f'data.moves["thunder"] = {data.moves["thunder"]}')
else:
    print(f'\nThunder in data.moves: NO')
    print(f'Available moves sample: {list(data.moves.keys())[:20]}')





