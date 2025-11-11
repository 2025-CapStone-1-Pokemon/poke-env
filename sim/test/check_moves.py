from poke_env.data import GenData

data = GenData.from_gen(9)

# Pikachu 확인
print('=== Pikachu ===')
pikachu = data.pokedex['pikachu']
print(f'Type: {pikachu.get("type")}')
print(f'Learnset sample: {list(pikachu.get("learnset", {}).keys())[:10]}')

# 몇 가지 전기 기술 확인
print('\n=== Electric moves in pokedex ===')
electric_moves = []
for move_id, move_data in list(data.moves.items())[:50]:
    if move_data.get('type') == 'Electric' and move_data.get('basePower', 0) > 0:
        electric_moves.append((move_id, move_data.get('basePower')))
        print(f'{move_id}: {move_data.get("basePower")} BP, type: {move_data.get("type")}')

# Blastoise 확인
print('\n=== Blastoise ===')
blastoise = data.pokedex['blastoise']
print(f'Type: {blastoise.get("type")}')
print(f'Learnset sample: {list(blastoise.get("learnset", {}).keys())[:10]}')

# 몇 가지 워터 기술 확인
print('\n=== Water moves in pokedex ===')
water_moves = []
for move_id, move_data in list(data.moves.items())[:50]:
    if move_data.get('type') == 'Water' and move_data.get('basePower', 0) > 0:
        water_moves.append((move_id, move_data.get('basePower')))
        print(f'{move_id}: {move_data.get("basePower")} BP, type: {move_data.get("type")}')

# Pikachu가 배울 수 있는 전기 기술 확인
print('\n=== Electric moves Pikachu can learn ===')
pikachu_learnset = pikachu.get('learnset', {})
electric_pikachu = []
for move_id in pikachu_learnset.keys():
    move_data = data.moves.get(move_id, {})
    if move_data.get('type') == 'Electric' and move_data.get('basePower', 0) > 0:
        electric_pikachu.append((move_id, move_data.get('basePower')))
        print(f'{move_id}: {move_data.get("basePower")} BP')

print(f'Total: {len(electric_pikachu)} electric moves for Pikachu')
