import timeit
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SimplifiedPokemon import SimplifiedPokemon

# 현재 구현
def current_implementation():
    
    simplified_pokemon = SimplifiedPokemon()
    simplified_pokemon.get_effective_stat(stat_name=)

# 기준: 1회 = ?ms
time_per_call = timeit.timeit(current_implementation, number=1000) / 1000
print(f"호출당 {time_per_call * 1000:.3f}ms")

# 800회 호출 시간
total_time = time_per_call * 800
print(f"800회 호출 총 시간: {total_time * 1000:.1f}ms")