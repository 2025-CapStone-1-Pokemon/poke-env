import time
import copy
import sys
import os
import asyncio
import tracemalloc
from pathlib import Path

# 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from poke_env.player import Player
from poke_env.battle import Battle
from sim.SimplifiedBattle import SimplifiedBattle


class BenchmarkPlayer(Player):
    """벤치마크용 플레이어"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.battle_count = 0
        self.simplified_times = []
        self.battle_times = []
        self.simplified_sizes = []
        self.battle_sizes = []
    
    def choose_move(self, battle):
        """배틀 선택 - 벤치마크 실행"""
        
        # SimplifiedBattle deepcopy 벤치마크
        if self.battle_count == 0:
            print("\n[SimplifiedBattle deepcopy test]")
            start = time.perf_counter()
            simplified_battle = SimplifiedBattle(battle)
            end = time.perf_counter()
            simplified_create_time = (end - start) * 1000
            print(f"  Creation time: {simplified_create_time:.4f} ms")
            
            # Memory size - deepcopy 포함 측정
            print("  Measuring memory (including deepcopy)...")
            tracemalloc.start()
            
            # 시작 상태
            snapshot_start = tracemalloc.take_snapshot()
            
            # 1회 deepcopy
            test_copy = copy.deepcopy(simplified_battle)
            
            # 종료 상태
            snapshot_end = tracemalloc.take_snapshot()
            
            top_stats = snapshot_end.compare_to(snapshot_start, 'lineno')
            simplified_size = abs(sum(stat.size_diff for stat in top_stats))
            tracemalloc.stop()
            
            print(f"  Memory usage (deepcopy): {simplified_size:,} bytes ({simplified_size/1024:.2f} KB, {simplified_size/1024/1024:.2f} MB)")
            self.simplified_sizes.append(simplified_size)
            
            # Deepcopy 100회 테스트
            print("  Running 100 deepcopy iterations...")
            times = []
            for i in range(100):
                start = time.perf_counter()
                copy_obj = copy.deepcopy(simplified_battle)
                end = time.perf_counter()
                times.append((end - start) * 1000)
                if (i + 1) % 20 == 0:
                    print(f"    Progress: {i+1}/100")
            
            avg_simplified = sum(times) / len(times)
            min_simplified = min(times)
            max_simplified = max(times)
            print(f"  Deepcopy average (100x): {avg_simplified:.4f} ms")
            print(f"  Min: {min_simplified:.4f} ms, Max: {max_simplified:.4f} ms")
            self.simplified_times.append(avg_simplified)
            
            # 일반 Battle deepcopy 벤치마크
            print("\n[Battle deepcopy test]")
            
            # Memory size - deepcopy 포함 측정
            print("  Measuring memory (including deepcopy)...")
            tracemalloc.start()
            
            # 시작 상태
            snapshot_start = tracemalloc.take_snapshot()
            
            # 1회 deepcopy
            test_copy = copy.deepcopy(battle)
            
            # 종료 상태
            snapshot_end = tracemalloc.take_snapshot()
            
            top_stats = snapshot_end.compare_to(snapshot_start, 'lineno')
            battle_size = abs(sum(stat.size_diff for stat in top_stats))
            tracemalloc.stop()
            
            print(f"  Memory usage (deepcopy): {battle_size:,} bytes ({battle_size/1024:.2f} KB, {battle_size/1024/1024:.2f} MB)")
            self.battle_sizes.append(battle_size)
            
            # Battle 100회 deepcopy 테스트
            print("  Running 100 deepcopy iterations...")
            times = []
            for i in range(100):
                start = time.perf_counter()
                copy_obj = copy.deepcopy(battle)
                end = time.perf_counter()
                times.append((end - start) * 1000)
                if (i + 1) % 20 == 0:
                    print(f"    Progress: {i+1}/100")
            
            avg_battle = sum(times) / len(times)
            min_battle = min(times)
            max_battle = max(times)
            print(f"  Deepcopy average (100x): {avg_battle:.4f} ms")
            print(f"  Min: {min_battle:.4f} ms, Max: {max_battle:.4f} ms")
            self.battle_times.append(avg_battle)
            
            # 비교
            print("\n[Comparison Results]")
            print(f"  SimplifiedBattle (time): {avg_simplified:.4f} ms")
            print(f"  Battle (time): {avg_battle:.4f} ms")
            print(f"  Speed improvement: {avg_battle/avg_simplified:.1f}x faster")
            print(f"\n  SimplifiedBattle (memory): {simplified_size/1024:.2f} KB")
            print(f"  Battle (memory): {battle_size/1024:.2f} KB")
            print(f"  Memory reduction: {battle_size/simplified_size:.1f}x smaller")
            
            self.battle_count += 1
        
        return self.choose_random_move(battle)


async def benchmark_deepcopy():
    """서버와 연결해서 Battle 객체 deepcopy 벤치마크"""
    print("="*70)
    print("[Actual Battle Object DeepCopy Performance Comparison]")
    print("="*70)
    
    try:
        # 벤치마크 플레이어 생성
        p1 = BenchmarkPlayer(
            battle_format="gen9randombattle",
            max_concurrent_battles=1
        )
        
        p2 = BenchmarkPlayer(
            battle_format="gen9randombattle",
            max_concurrent_battles=1
        )
        
        print("\nConnecting to server... (Starting 1 battle)")
        
        # 1판만 진행 (벤치마크)
        try:
            await p1.battle_against(p2, n_battles=1)
        except Exception as e:
            print(f"Battle error: {e}")
        
        print("\n" + "="*70)
        print("[Final Results]")
        print("="*70)
        
        if p1.simplified_times and p1.battle_times:
            print(f"\nDeepCopy Performance (100 iterations):")
            print(f"  SimplifiedBattle: {p1.simplified_times[0]:.4f} ms/iteration")
            print(f"  Battle: {p1.battle_times[0]:.4f} ms/iteration")
            ratio = p1.battle_times[0] / p1.simplified_times[0]
            print(f"  Speed improvement: {ratio:.1f}x faster")
            print(f"  Operations per second:")
            print(f"    SimplifiedBattle: {1000/p1.simplified_times[0]:.0f} deepcopy/sec")
            print(f"    Battle: {1000/p1.battle_times[0]:.0f} deepcopy/sec")
            
            print(f"\nMemory Usage:")
            print(f"  SimplifiedBattle: {p1.simplified_sizes[0]/1024:.2f} KB ({p1.simplified_sizes[0]/1024/1024:.2f} MB)")
            print(f"  Battle: {p1.battle_sizes[0]/1024:.2f} KB ({p1.battle_sizes[0]/1024/1024:.2f} MB)")
            if p1.simplified_sizes[0] > 0:
                mem_ratio = p1.battle_sizes[0] / p1.simplified_sizes[0]
                print(f"  Memory reduction: {mem_ratio:.1f}x smaller")
            else:
                print(f"  Memory reduction: Unable to calculate")
            
            print(f"\nConclusion:")
            print(f"  SimplifiedBattle is {ratio:.1f}x faster to deepcopy")
            print(f"  SimplifiedBattle uses {mem_ratio:.1f}x less memory")
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("Test completed")
    print("="*70)


if __name__ == "__main__":
    print("Benchmarking deepcopy performance...")
    print("(Requires Pokemon Showdown server running on localhost:8000)\n")
    
    asyncio.run(benchmark_deepcopy())
