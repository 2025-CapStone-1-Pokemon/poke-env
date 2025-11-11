from poke_env.data import GenData
import json

data = GenData.from_gen(9)

# Pikachu 상세 분석
print('=== Pikachu full data ===')
pikachu = data.pokedex['pikachu']
print(f'Keys: {list(pikachu.keys())}')

print('\n=== Checking for learnset ===')
print(f'Has learnset: {"learnset" in pikachu}')

# poke-env의 move 데이터 구조 확인
print('\n=== Sample moves ===')
sample_moves = list(data.moves.items())[:5]
for move_id, move_data in sample_moves:
    print(f'{move_id}: {move_data}')

# Pikachu가 배우는 기술을 찾기 위해 다른 방법 시도
print('\n=== Trying to find Pikachu learnset ===')
# Check if there's a learnsets attribute
if hasattr(data, 'learnsets'):
    print('data has learnsets attribute')
    if 'pikachu' in data.learnsets:
        print(f'Pikachu learnset: {list(data.learnsets["pikachu"].keys())[:10]}')
else:
    print('No learnsets attribute in data')

# Check all attributes of data
print(f'\n=== data attributes ===')
print([attr for attr in dir(data) if not attr.startswith('_')])
