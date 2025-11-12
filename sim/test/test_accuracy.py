"""
SimplifiedBattle 엔진 정확도 테스트 (memo.py와 동일한 고정 포켓몬)

목적:
- Garchomp, Gengar, Scizor vs Tyranitar, Corviknight, Rotom-Wash 배틀
- 시뮬레이션 정확도 측정
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import copy
import numpy as np
from typing import Dict
from SimplifiedBattle import SimplifiedBattle
from SimplifiedPokemon import SimplifiedPokemon
from SimplifiedMove import SimplifiedMove
from battle.SimplifiedBattleEngine import SimplifiedBattleEngine
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.move_category import MoveCategory


def create_pokemon(species: str, hp: int, moves_list: list, base_power: int = 100) -> SimplifiedPokemon:
    """고정 포켓몬 생성"""
    poke = SimplifiedPokemon.__new__(SimplifiedPokemon)
    poke.species = species.lower()
    poke.level = 100
    poke.max_hp = hp
    poke.current_hp = hp
    poke.gender = None
    poke.type_1 = PokemonType.NORMAL
    poke.type_2 = None
    poke.types = [PokemonType.NORMAL]
    poke.base_stats = {'hp': hp, 'atk': 120, 'def': 100, 'spa': 120, 'spd': 100, 'spe': 100}
    poke.stats = {'hp': hp, 'atk': 120, 'def': 100, 'spa': 120, 'spd': 100, 'spe': 100}
    poke.ability = 'static'
    poke.item = None
    poke.status = None
    poke.effects = {}
    poke.boosts = {stat: 0 for stat in ['atk', 'def', 'spa', 'spd', 'spe']}
    poke.active = True
    poke.first_turn = True
    poke.must_recharge = False
    poke.protect_counter = 0
    
    # 기술 생성
    poke.moves = []
    for move_id in moves_list:
        move = SimplifiedMove.__new__(SimplifiedMove)
        move.id = move_id
        move.base_power = base_power
        move.type = PokemonType.NORMAL
        move.category = MoveCategory.PHYSICAL
        move.accuracy = 1.0
        move.priority = 0
        move.current_pp = 16
        move.max_pp = 16
        move.boosts = None
        move.self_boost = None
        move.status = None
        move.secondary = None
        move.crit_ratio = 0
        move.expected_hits = 1
        move.recoil = 0
        move.drain = 0
        move.flags = set()
        poke.moves.append(move)
    
    return poke


def create_test_battle() -> SimplifiedBattle:
    """memo.py와 동일한 팀으로 배틀 생성"""
    battle = SimplifiedBattle.__new__(SimplifiedBattle)
    battle.turn = 1
    battle.gen = 9
    battle.finished = False
    battle.won = False
    battle.lost = False
    
    # memo.py의 TEAM_MCTS_PACKED와 동일
    # "|Garchomp|...|Dragon Claw,Earthquake,Stone Edge,Swords Dance|...
    # "|Gengar|...|Shadow Ball,Sludge Bomb,Focus Blast,Trick|...
    # "|Scizor|...|Bullet Punch,U-turn,Close Combat,Knock Off|...
    
    battle.team = {
        'p1: garchomp': create_pokemon('Garchomp', hp=130, moves_list=['dragon-claw', 'earthquake', 'stone-edge', 'swords-dance']),
        'p1: gengar': create_pokemon('Gengar', hp=105, moves_list=['shadow-ball', 'sludge-bomb', 'focus-blast', 'trick']),
        'p1: scizor': create_pokemon('Scizor', hp=125, moves_list=['bullet-punch', 'u-turn', 'close-combat', 'knock-off']),
    }
    
    # memo.py의 TEAM_RANDOM_PACKED와 동일
    # "|Tyranitar|...|Stone Edge,Crunch,Earthquake,Dragon Dance|...
    # "|Corviknight|...|Brave Bird,Iron Head,Roost,Defog|...
    # "|Rotom-Wash|...|Hydro Pump,Volt Switch,Will-O-Wisp,Pain Split|...
    
    battle.opponent_team = {
        'p2: tyranitar': create_pokemon('Tyranitar', hp=135, moves_list=['stone-edge', 'crunch', 'earthquake', 'dragon-dance']),
        'p2: corviknight': create_pokemon('Corviknight', hp=125, moves_list=['brave-bird', 'iron-head', 'roost', 'defog']),
        'p2: rotom-wash': create_pokemon('Rotom-Wash', hp=115, moves_list=['hydro-pump', 'volt-switch', 'will-o-wisp', 'pain-split']),
    }
    
    # 활성 포켓몬
    battle.active_pokemon = battle.team['p1: garchomp']
    battle.opponent_active_pokemon = battle.opponent_team['p2: tyranitar']
    
    # 필드
    battle.weather = {}
    battle.fields = {}
    battle.side_conditions = {}
    battle.opponent_side_conditions = {}
    battle.available_moves = []
    battle.available_switches = []
    
    return battle


class SimulationAccuracyTester:
    """시뮬레이션 정확도 테스터"""
    
    def __init__(self):
        self.engine = SimplifiedBattleEngine()
    
    def run_simulations(self, battle: SimplifiedBattle, num_simulations: int = 500) -> Dict:
        """N번 배틀 시뮬레이션 실행"""
        player_wins = 0
        opponent_wins = 0
        draws = 0
        turn_counts = []
        
        for i in range(num_simulations):
            # 배틀 복사
            test_battle = copy.deepcopy(battle)
            
            # 시뮬레이션 실행
            result = self.engine.simulate_full_battle(test_battle, max_turns=100, verbose=False)
            
            # 결과 판정
            player_alive = sum(1 for p in result.team.values() if p.current_hp > 0)
            opponent_alive = sum(1 for p in result.opponent_team.values() if p.current_hp > 0)
            turn_counts.append(result.turn)
            
            if player_alive > 0 and opponent_alive == 0:
                player_wins += 1
            elif opponent_alive > 0 and player_alive == 0:
                opponent_wins += 1
            else:
                draws += 1
            
            if (i + 1) % 50 == 0:
                print(f"  진행: [{i + 1}/{num_simulations}]", end='\r')
        
        return {
            'player_wins': player_wins,
            'opponent_wins': opponent_wins,
            'draws': draws,
            'player_win_rate': player_wins / num_simulations,
            'opponent_win_rate': opponent_wins / num_simulations,
            'draw_rate': draws / num_simulations,
            'avg_turns': np.mean(turn_counts) if turn_counts else 0,
            'max_turns': max(turn_counts) if turn_counts else 0,
            'min_turns': min(turn_counts) if turn_counts else 0,
        }
    
    def analyze_results(self, results: Dict, num_simulations: int):
        """결과 분석"""
        print("\n" + "="*70)
        print("시뮬레이션 정확도 분석")
        print("="*70)
        
        print(f"\n총 시뮬레이션 횟수: {num_simulations}")
        print(f"\n--- 결과 분포 ---")
        print(f"플레이어 승리: {results['player_wins']}회 ({results['player_win_rate']*100:.1f}%)")
        print(f"상대 승리:    {results['opponent_wins']}회 ({results['opponent_win_rate']*100:.1f}%)")
        print(f"무승부:      {results['draws']}회 ({results['draw_rate']*100:.1f}%)")
        
        print(f"\n--- 턴 분석 ---")
        print(f"평균 턴:  {results['avg_turns']:.1f}")
        print(f"최대 턴:  {results['max_turns']}")
        print(f"최소 턴:  {results['min_turns']}")
        
        # 문제 진단
        print(f"\n--- 진단 ---")
        if results['draw_rate'] > 0.5:
            print(f"⚠️  경고: 무승부가 {results['draw_rate']*100:.1f}%로 매우 많습니다!")
            print(f"   → 데미지 계산 체계 검토 필요")
            
            if results['avg_turns'] >= 100:
                print(f"   → 최대 턴(100)에 도달해서 무승부로 처리됨")
        else:
            print(f"✓ 시뮬레이션이 정상적으로 완료됨")
            
            if abs(results['player_win_rate'] - results['opponent_win_rate']) < 0.1:
                print(f"✓ 양 팀의 승률이 균형있음 ({results['player_win_rate']*100:.1f}% vs {results['opponent_win_rate']*100:.1f}%)")
            else:
                winner = "플레이어" if results['player_win_rate'] > results['opponent_win_rate'] else "상대"
                diff = abs(results['player_win_rate'] - results['opponent_win_rate']) * 100
                print(f"⚠️  {winner}이 {diff:.1f}%p 더 유리함")
        
        print("="*70)


def main():
    """메인 테스트"""
    print("="*70)
    print("SimplifiedBattle 엔진 정확도 테스트")
    print("(memo.py의 팀 구성 사용)")
    print("="*70)
    
    # 테스트 배틀 생성
    test_battle = create_test_battle()
    
    print(f"\n배틀 초기 설정:")
    print(f"플레이어 팀 (MCTS):")
    for id, p in test_battle.team.items():
        print(f"  {p.species.upper()}: HP={p.current_hp}/{p.max_hp}, 기술={len(p.moves)}개")
    
    print(f"\n상대 팀 (Random):")
    for id, p in test_battle.opponent_team.items():
        print(f"  {p.species.upper()}: HP={p.current_hp}/{p.max_hp}, 기술={len(p.moves)}개")
    
    # 시뮬레이션 실행
    print(f"\n시뮬레이션 500회 실행 중...")
    tester = SimulationAccuracyTester()
    results = tester.run_simulations(test_battle, num_simulations=500)
    
    # 결과 분석
    tester.analyze_results(results, num_simulations=500)


if __name__ == "__main__":
    main()
