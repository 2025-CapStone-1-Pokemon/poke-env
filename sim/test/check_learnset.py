from poke_env.data import GenData

data = GenData.from_gen(9)

# Pikachu가 배울 수 있는 기술 확인
print('=== Pikachu learnable moves ===')
pikachu_learnset = data.learnset.get('pikachu', {}).get('learnset', {})
print(f'Total learnable: {len(pikachu_learnset)}')

# test_damage_debug에서 나온 기술들 확인
test_moves = ['thunder', 'lastresort', 'skullbash', 'dynamicpunch']
for move in test_moves:
    can_learn = move in pikachu_learnset
    move_data = data.moves.get(move, {})
    print(f'{move:20} - Can learn: {can_learn:5} BP={move_data.get("basePower", 0):3} Type={move_data.get("type")}')

# Blastoise가 배울 수 있는 기술 확인
print('\n=== Blastoise learnable moves ===')
blastoise_learnset = data.learnset.get('blastoise', {}).get('learnset', {})
print(f'Total learnable: {len(blastoise_learnset)}')

# test_damage_debug에서 나온 기술들 확인
test_moves_b = ['aquatail', 'hyperbeam', 'muddywater', 'hydropump']
for move in test_moves_b:
    can_learn = move in blastoise_learnset
    move_data = data.moves.get(move, {})
    print(f'{move:20} - Can learn: {can_learn:5} BP={move_data.get("basePower", 0):3} Type={move_data.get("type")}')
