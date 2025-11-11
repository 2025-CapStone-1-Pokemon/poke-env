from poke_env.data import GenData

data = GenData.from_gen(9)

# Pikachu의 learnset 확인
print('=== data.learnset structure ===')
print(f'Type: {type(data.learnset)}')
print(f'Has pikachu: {"pikachu" in data.learnset}')

if 'pikachu' in data.learnset:
    pikachu_full = data.learnset['pikachu']
    print(f'Pikachu full structure keys: {list(pikachu_full.keys())}')
    
    if 'learnset' in pikachu_full:
        pikachu_learnset = pikachu_full['learnset']
        print(f'Pikachu learnset type: {type(pikachu_learnset)}')
        print(f'Pikachu learnset keys (first 20): {list(pikachu_learnset.keys())[:20]}')

        # Electric 기술 확인
        print('\n=== Electric moves Pikachu can learn ===')
        electric_count = 0
        for move_id in pikachu_learnset.keys():
            move_data = data.moves.get(move_id, {})
            if move_data.get('type') == 'Electric' and move_data.get('basePower', 0) > 0:
                print(f'{move_id}: {move_data.get("basePower")} BP, pp={move_data.get("pp")}')
                electric_count += 1
                if electric_count >= 10:
                    break
        
        print(f'Total Electric moves found: {electric_count}+')
