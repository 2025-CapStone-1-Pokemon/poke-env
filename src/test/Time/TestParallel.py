import time
import pickle
import copy
import sys
import os
import random
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

current_dir = os.path.dirname(os.path.abspath(__file__))
src_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if src_root not in sys.path:
    sys.path.insert(0, src_root)

from src.sim.BattleEngine.SimplifiedBattleEngine import SimplifiedBattleEngine
from src.sim.BattleClass.SimplifiedBattle import SimplifiedBattle
from src.sim.BattleClass.SimplifiedPokemon import SimplifiedPokemon
from src.sim.BattleClass.SimplifiedMove import SimplifiedMove
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.move_category import MoveCategory

def make_dummy_move(mid, bp=90, category=MoveCategory.PHYSICAL):
    m = SimplifiedMove.__new__(SimplifiedMove)
    m.id = mid
    m.base_power = bp
    m.type = PokemonType.NORMAL
    m.category = category
    m.accuracy = 1.0
    m.priority = 0
    m.current_pp = 50  # PP 넉넉하게
    m.max_pp = 50
    m.crit_ratio = 0
    m.expected_hits = 1
    m.recoil = 0
    m.drain = 0
    m.flags = {}
    m.breaks_protect = False
    m.is_protect_move = False
    m.boosts = None
    m.self_boost = None
    m.status = None
    m.secondary = None
    return m

def make_dummy_pokemon(species, hp=300):
    p = SimplifiedPokemon.__new__(SimplifiedPokemon)
    p.species = species
    p.level = 80
    p.type_1 = PokemonType.NORMAL
    p.type_2 = None
    p.types = [PokemonType.NORMAL]
    p.current_hp = hp
    p.max_hp = hp
    p.base_stats = {'hp': 100, 'atk': 100, 'def': 100, 'spa': 100, 'spd': 100, 'spe': 100}
    p.stats = p.base_stats.copy()
    p.boosts = {k: 0 for k in ['atk','def','spa','spd','spe', 'accuracy', 'evasion']}
    p.boost_timers = {}
    p.moves = [make_dummy_move('tackle', 40), make_dummy_move('quickattack', 40)]
    p.ability = None
    p.item = None
    p.active = True
    p.first_turn = True
    p.must_recharge = False
    p.protect_counter = 0
    p.status = None
    p.status_counter = 0
    p.toxic_counter = 0
    p.volatiles = {}
    p.effects = {}
    p._stat_cache = {}
    p.gender = 'M'
    return p

def make_dummy_battle():
    sb = SimplifiedBattle.__new__(SimplifiedBattle)
    sb.turn = 1
    sb.gen = 9
    sb.finished = False
    sb.won = False
    sb.lost = False
    p1 = make_dummy_pokemon('pikachu', 300)
    op1 = make_dummy_pokemon('eevee', 300)
    sb.team = {'p1': p1}
    sb.opponent_team = {'op1': op1}
    sb.active_pokemon = p1
    sb.opponent_active_pokemon = op1
    sb.weather = {}
    sb.fields = {}
    sb.side_conditions = {}
    sb.opponent_side_conditions = {}
    sb.available_moves = p1.moves
    sb.available_switches = []
    return sb

# Worker Functions

def _worker_cpu_task(battle, iterations):
    # 쓰레드풀용
    engine = SimplifiedBattleEngine()
    for _ in range(iterations):
        st = copy.deepcopy(battle)
        engine.simulate_turn(st, verbose=False)
    return iterations

def _worker_leaf_task(battle):
    #리프병렬화용
    engine = SimplifiedBattleEngine()
    st = copy.deepcopy(battle)
    engine.simulate_turn(st, verbose=False)
    return 1

def _worker_root_task(seed, battle, iterations):
    #루트 병렬화용
    random.seed(seed)
    engine = SimplifiedBattleEngine()
    
    for _ in range(iterations):
        st = copy.deepcopy(battle)
        engine.simulate_turn(st, verbose=False)
    return iterations

# 메인 함수 모음

# [실험 1] 쓰레드풀 벤치마크
def bench_thread(battle, iterations=1000):
    print(f"\n[1] ThreadPool Benchmark")
    print(f"\nIteration = {iterations}")

    # (A) Sequential
    print("\n -> Single (1 Thread)")
    _worker_cpu_task(battle, 10)  # Warm-up

    t0 = time.perf_counter()
    _worker_cpu_task(battle, iterations)
    t_seq = time.perf_counter() - t0
    print(f"    Time: {t_seq:.4f}s")

    # (B) Multi-Thread
    thread_counts = [2, 4, 8]
    batch_size = 10 
    
    for workers in thread_counts:
        print(f"\n -> ThreadPool ({workers} Threads)")
        
        num_batches = iterations // batch_size
        remainder = iterations % batch_size
        
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = []
            for _ in range(num_batches):
                futures.append(ex.submit(_worker_cpu_task, battle, batch_size))
            if remainder > 0:
                futures.append(ex.submit(_worker_cpu_task, battle, remainder))
            [f.result() for f in futures]
            
        t_par = time.perf_counter() - t0
        speedup = t_seq / t_par
        print(f"    Time: {t_par:.4f}s")
        print(f"    Speedup: {speedup:.2f}x")

# [실험 2] 리프 병렬화 벤치마크
def bench_leaf(battle, iterations=200):
    print(f"\n[2] Leaf Benchmark")
    print(f"\nIteration = {iterations}")

    # (A) Sequential
    print("\n -> Single")
    engine = SimplifiedBattleEngine()
    st_warm = copy.deepcopy(battle) # Warm-up
    engine.simulate_turn(st_warm, verbose=False)
    
    t0 = time.perf_counter()
    for _ in range(iterations):
        st = copy.deepcopy(battle)
        engine.simulate_turn(st, verbose=False)
    t_seq = time.perf_counter() - t0
    print(f"    Time: {t_seq:.4f}s")

    # (B) ProcessPool Scaling
    worker_counts = [2, 4, 8]
    for workers in worker_counts:
        print(f"\n -> Leaf Parallelism ({workers} Processes)")
        t0 = time.perf_counter()
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(_worker_leaf_task, battle) for _ in range(iterations)]
            [f.result() for f in futures]
        t_proc = time.perf_counter() - t0
        speedup = t_seq / t_proc if t_proc > 0 else 0
        print(f"    Time: {t_proc:.4f}s")
        print(f"    Speedup: {speedup:.4f}x")

# [실험 3] Pickle 비용 측정
def bench_pickle(battle, iterations=200):
    print(f"\n[3] Pickle Benchmark ")
    print(f"\nIteration = {iterations}")

    t0 = time.perf_counter()
    for _ in range(iterations):
        data = pickle.dumps(battle)
        _ = pickle.loads(data)
    t_pickle = time.perf_counter() - t0
    
    avg_pickle_sec = t_pickle / iterations

    print(f" \nTotal Pickle time: {t_pickle:.4f}s")
    print(f" \nOne Pickle time  : {avg_pickle_sec:.6f}s")


# [실험 4] 프로세스 생성 비용 측정
def _worker_empty_task(arg):
    # 아무 작업 X
    return arg

def bench_process(iterations=5):
    print(f"\n [4] Process time Benchmark ")

    worker_counts = [2, 4, 8]

    for workers in worker_counts:
        total_spawn_time = 0
        print(f"\n -> Testing with {workers} Workers")

        for i in range(iterations):
            t0 = time.perf_counter()
            
            # 프로세스 만들고 빈 작업을 하고 닫는 총 시간 
            with ProcessPoolExecutor(max_workers=workers) as ex:
                futures = [ex.submit(_worker_empty_task, j) for j in range(workers)]
                [f.result() for f in futures]
            
            t_end = time.perf_counter()
            duration = t_end - t0
            total_spawn_time += duration
            
        avg_spawn_time = total_spawn_time / iterations

        print(f"    Time: {avg_spawn_time:.4f}s")


# [실험 5] 루트 병렬화 벤치마크
def bench_root(battle, low_iters=200, high_iters=20000):
    print(f"\n [5] Root Benchmark ")
    
    # iteration = 200일 때 비교

    print(f" \n Iteration == 200")

    print(f" \n-> Single (1 Process)")
    
    engine_seq = SimplifiedBattleEngine()
    
    t0 = time.perf_counter()
    for _ in range(low_iters):
        st = copy.deepcopy(battle)
        engine_seq.simulate_turn(st, verbose=False)
    t_seq_low = time.perf_counter() - t0
    print(f"    Time: {t_seq_low:.4f}s")

    worker_counts = [4, 8]
    
    for workers in worker_counts:
        print(f" \n-> Root Parallelism ({workers} Processes)")
        
        iter_per_worker = max(1, low_iters // workers)
        
        t0 = time.perf_counter()
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(_worker_root_task, i, battle, iter_per_worker) for i in range(workers)]
            [f.result() for f in futures]
        t_par = time.perf_counter() - t0
        
        speedup = t_seq_low / t_par if t_par > 0 else 0
        print(f"    Time: {t_par:.4f}s")
        print(f"    Speedup: {speedup:.4f}x")
        
    # 워커 = 4, iteration = 20000 일때는?
    print(f" \n Iteration == 20000")

    print(f" \n-> Single (1 Process)")
    t0 = time.perf_counter()
    for _ in range(high_iters):
        st = copy.deepcopy(battle)
        engine_seq.simulate_turn(st, verbose=False)
    t_seq_high = time.perf_counter() - t0
    print(f"    Time: {t_seq_high:.4f}s")

    workers = 4
    print(f" \n-> Root Parallelism ({workers} Processes)")
    
    iter_per_worker = high_iters // workers
    
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_worker_root_task, i, battle, iter_per_worker) for i in range(workers)]
        [f.result() for f in futures]
    t_par_high = time.perf_counter() - t0
    
    speedup = t_seq_high / t_par_high if t_par_high > 0 else 0
    print(f"    Time: {t_par_high:.4f}s")
    print(f"    Speedup: {speedup:.4f}x")
    

if __name__ == "__main__":
    battle = make_dummy_battle()
    
    # 1. 쓰레드풀 실험 (200회)
    #bench_thread(battle, iterations=200)
    
    # 2. 리프 병렬화 실험 (200회) 
    #bench_leaf(battle, iterations=200)
    
    # 3. Pickle 비용 측정 
    #bench_pickle(battle, iterations=200)

    # 4. 프로세스 생성 비용 측정
    #bench_process(iterations=5)

    # 5. 루트 병렬화 실험 (200회 vs 20000회) 
    #bench_root(battle, low_iters=200, high_iters=20000)