from poke_env.data import GenData

data = GenData.from_gen(9)  # 9세대 데이터 로드
pikachu_data = data.pokedex['pikachu']

print("Pikachu의 속성들:")
for key, value in pikachu_data.items():
    print(f"{key}: {value}")