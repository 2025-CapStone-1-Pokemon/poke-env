"""
배틀 데이터 저장 및 표시 관련 함수 모음
SimplifiedBattle과 SimplifiedPokemon을 JSON으로 직렬화하고,
턴별 결과를 저장하는 기능 제공
"""
import json
from pathlib import Path
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sim.BattleClass.SimplifiedMove import SimplifiedMove
from sim.BattleClass.SimplifiedBattle import SimplifiedBattle
from sim.BattleClass.SimplifiedPokemon import SimplifiedPokemon

def simplified_move_to_dict(move : SimplifiedMove):
    """SimplifiedMove의 모든 정보를 딕셔너리로 변환"""
    if not move:
        return None
    
    return {
        'id': move.id,
        'base_power': move.base_power,
        'type': move.type.name if hasattr(move.type, 'name') else str(move.type),
        'category': move.category.name if hasattr(move.category, 'name') else str(move.category),
        'accuracy': move.accuracy,
        'priority': move.priority if hasattr(move, 'priority') else 0,
        'current_pp': move.current_pp,
        'max_pp': move.max_pp,
        'boosts': move.boosts if hasattr(move, 'boosts') else None,
        'self_boost': move.self_boost if hasattr(move, 'self_boost') else None,
        'status': move.status.name if move.status and hasattr(move.status, 'name') else (str(move.status) if hasattr(move, 'status') else None),
        'crit_ratio': move.crit_ratio if hasattr(move, 'crit_ratio') else 0,
        'recoil': move.recoil if hasattr(move, 'recoil') else 0,
        'drain': move.drain if hasattr(move, 'drain') else 0,
    }


def simplified_pokemon_to_dict(pokemon : SimplifiedPokemon):
    """SimplifiedPokemon을 딕셔너리로 변환"""
    if not pokemon:
        return None
    
    return {
        'species': pokemon.species,
        'level': pokemon.level,
        'gender': pokemon.gender.name if hasattr(pokemon, 'gender') and pokemon.gender else None,
        'type_1': pokemon.type_1.name if pokemon.type_1 else None,
        'type_2': pokemon.type_2.name if pokemon.type_2 else None,
        'types': [t.name for t in pokemon.types] if hasattr(pokemon, 'types') and pokemon.types else [],
        'current_hp': pokemon.current_hp,
        'max_hp': pokemon.max_hp,
        'status': pokemon.status.name if pokemon.status else None,
        'status_counter': pokemon.status_counter,
        'toxic_counter': pokemon.toxic_counter if hasattr(pokemon, 'toxic_counter') else 0,
        'base_stats': pokemon.base_stats.copy() if pokemon.base_stats else {},
        'stats': pokemon.stats.copy() if pokemon.stats else {},
        'boosts': pokemon.boosts.copy() if pokemon.boosts else {},
        'boost_timers': pokemon.boost_timers.copy() if hasattr(pokemon, 'boost_timers') and pokemon.boost_timers else {},
        'moves': [simplified_move_to_dict(m) for m in pokemon.moves] if pokemon.moves else [],
        'ability': pokemon.ability,
        'item': pokemon.item,
        'effects': {
            (k.name if hasattr(k, 'name') else str(k)): v
            for k, v in pokemon.effects.items()
        } if pokemon.effects else {},
        'active': pokemon.active,
        'first_turn': pokemon.first_turn,
        'must_recharge': pokemon.must_recharge,
        'protect_counter': pokemon.protect_counter,
        'nature': pokemon.nature if hasattr(pokemon, 'nature') else None,
    }


def simplified_battle_to_dict(battle_state : SimplifiedBattle):
    """SimplifiedBattle을 딕셔너리로 변환"""
    if not battle_state:
        return None
    
    return {
        'turn': battle_state.turn,
        'gen': battle_state.gen,
        'finished': battle_state.finished,
        'won': battle_state.won,
        'lost': battle_state.lost,
        'active_pokemon': simplified_pokemon_to_dict(battle_state.active_pokemon),
        'opponent_active_pokemon': simplified_pokemon_to_dict(battle_state.opponent_active_pokemon),
        'team': {
            name: simplified_pokemon_to_dict(poke)
            for name, poke in battle_state.team.items()
        },
        'opponent_team': {
            name: simplified_pokemon_to_dict(poke)
            for name, poke in battle_state.opponent_team.items()
        },
        'weather': {k.name if hasattr(k, 'name') else str(k): v.name if hasattr(v, 'name') else str(v) for k, v in battle_state.weather.items()} if battle_state.weather else {},
        'fields': {k.name if hasattr(k, 'name') else str(k): v.name if hasattr(v, 'name') else str(v) for k, v in battle_state.fields.items()} if battle_state.fields else {},
        'side_conditions': {k.name if hasattr(k, 'name') else str(k): v.name if hasattr(v, 'name') else str(v) for k, v in battle_state.side_conditions.items()} if battle_state.side_conditions else {},
        'opponent_side_conditions': {k.name if hasattr(k, 'name') else str(k): v.name if hasattr(v, 'name') else str(v) for k, v in battle_state.opponent_side_conditions.items()} if battle_state.opponent_side_conditions else {},
        'available_moves': [m.id for m in battle_state.available_moves] if battle_state.available_moves else [],
        'available_switches': [p.species for p in battle_state.available_switches] if battle_state.available_switches else [],
    }


# === 턴별 시뮬레이션 데이터 저장 ===

def save_turn_simulation_data(battle_id, turn, current_battle_state, player_action_info, opponent_action_info,
                              actual_result_state, sim_result_state, error_metrics):
    """턴의 입력값과 결과값을 저장. Returns: (입력+결과 데이터, 결과 데이터) 튜플"""
    input_turn_data = {
        'turn': turn,
        'current_battle_state': simplified_battle_to_dict(current_battle_state),
        'player_action_info': {
            'order_type': player_action_info.get('order_type'),
            'move_idx': player_action_info.get('move_idx'),
            'move_name': player_action_info.get('move_name'),
            'switch_to': player_action_info.get('switch_to').species if hasattr(player_action_info.get('switch_to'), 'species') else player_action_info.get('switch_to'),
        },
        'opponent_action_info': {
            'order_type': opponent_action_info.get('order_type'),
            'move_idx': opponent_action_info.get('move_idx'),
            'move_name': opponent_action_info.get('move_name'), 
            'switch_to': opponent_action_info.get('switch_to').species if hasattr(opponent_action_info.get('switch_to'), 'species') else opponent_action_info.get('switch_to'),
        },
        'result': {
            'actual': simplified_battle_to_dict(actual_result_state),
            'simulated': simplified_battle_to_dict(sim_result_state),
        },
        'error_metrics': error_metrics
    }
    
    result_turn_data = {
        'turn': turn,
        'action': player_action_info.get('order_type'),
        'player_action_info': {
            'order_type': player_action_info.get('order_type'),
            'move_idx': player_action_info.get('move_idx'),
            'move_name': player_action_info.get('move_name'),
            'switch_to': player_action_info.get('switch_to').species if hasattr(player_action_info.get('switch_to'), 'species') else player_action_info.get('switch_to'),
        },
        'opponent_action_info': {
            'order_type': opponent_action_info.get('order_type'),
            'move_idx': opponent_action_info.get('move_idx'),
            'move_name': opponent_action_info.get('move_name'),
            'switch_to': opponent_action_info.get('switch_to').species if hasattr(opponent_action_info.get('switch_to'), 'species') else opponent_action_info.get('switch_to'),
        },
        'current_state': simplified_battle_to_dict(current_battle_state),
        'result': {
            'actual': simplified_battle_to_dict(actual_result_state),
            'simulated': simplified_battle_to_dict(sim_result_state),
        },
        'error_metrics': error_metrics
    }
    
    return (input_turn_data, result_turn_data)


def save_battle_turn_inputs(battle_id, turn_inputs_list):
    """배틀의 모든 턴 입력값을 저장. Returns: 저장된 파일 경로"""
    if not turn_inputs_list:
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    inputs_data = {
        'battle_id': battle_id,
        'timestamp': timestamp,
        'total_turns': len(turn_inputs_list),
        'turns': turn_inputs_list
    }
    
    output_dir = Path(__file__).parent / "battle_data" / battle_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / "inputs.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(inputs_data, f, indent=2, ensure_ascii=False)
    
    return str(filepath)


def save_battle_turn_results(battle_id, turn_results_list):
    """배틀의 모든 턴 결과값을 텍스트로 저장. Returns: 저장된 파일 경로"""
    if not turn_results_list:
        return None
    
    output_dir = Path(__file__).parent / "battle_data" / battle_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / "results.txt"
    with open(filepath, 'w', encoding='utf-8') as f:
        for turn_result in turn_results_list:
            turn = turn_result['turn']
            player_action_info = turn_result.get('player_action_info', {})
            opponent_action_info = turn_result.get('opponent_action_info', {})
            current = turn_result['current_state']
            result = turn_result['result']
            error = turn_result['error_metrics']
            
            f.write(f"【 Turn {turn} 】\n")
            
            player_action_str = f"{player_action_info.get('order_type', 'unknown')}"
            if player_action_info.get('order_type') == 'move':
                if player_action_info.get('move_name'):
                    player_action_str += f" ({player_action_info.get('move_name')})"
                elif player_action_info.get('move_idx') is not None:
                    player_action_str += f" (move_idx: {player_action_info.get('move_idx')})"
            elif player_action_info.get('order_type') == 'switch' and player_action_info.get('switch_to'):
                player_action_str += f" ({player_action_info.get('switch_to')})"
            f.write(f"  플레이어 행동: {player_action_str}\n")
            
            opponent_action_str = f"{opponent_action_info.get('order_type', 'unknown')}"
            if opponent_action_info.get('order_type') == 'move':
                if opponent_action_info.get('move_name'):
                    opponent_action_str += f" ({opponent_action_info.get('move_name')})"
                elif opponent_action_info.get('move_idx') is not None:
                    opponent_action_str += f" (move_idx: {opponent_action_info.get('move_idx')})"
            elif opponent_action_info.get('order_type') == 'switch' and opponent_action_info.get('switch_to'):
                opponent_action_str += f" ({opponent_action_info.get('switch_to')})"
            f.write(f"  상대의 행동: {opponent_action_str}\n")
            
            f.write(f"\n  【 현재 상태 】\n")
            f.write(f"    플레이어: {current['active_pokemon']['species']} | HP: {current['active_pokemon']['current_hp']}/{current['active_pokemon']['max_hp']} | 상태: {current['active_pokemon']['status']}\n")
            f.write(f"    상대: {current['opponent_active_pokemon']['species']} | HP: {current['opponent_active_pokemon']['current_hp']}/{current['opponent_active_pokemon']['max_hp']} | 상태: {current['opponent_active_pokemon']['status']}\n")
            
            actual = result['actual']
            f.write(f"\n  【 실제 결과 】\n")
            f.write(f"    플레이어: {actual['active_pokemon']['species']} | HP: {actual['active_pokemon']['current_hp']}/{actual['active_pokemon']['max_hp']} | 상태: {actual['active_pokemon']['status']}\n")
            f.write(f"    상대: {actual['opponent_active_pokemon']['species']} | HP: {actual['opponent_active_pokemon']['current_hp']}/{actual['opponent_active_pokemon']['max_hp']} | 상태: {actual['opponent_active_pokemon']['status']}\n")
            
            sim = result['simulated']
            f.write(f"\n  【 시뮬 결과 (1회) 】\n")
            f.write(f"    플레이어: {sim['active_pokemon']['species']} | HP: {sim['active_pokemon']['current_hp']}/{sim['active_pokemon']['max_hp']} | 상태: {sim['active_pokemon']['status']}\n")
            f.write(f"    상대: {sim['opponent_active_pokemon']['species']} | HP: {sim['opponent_active_pokemon']['current_hp']}/{sim['opponent_active_pokemon']['max_hp']} | 상태: {sim['opponent_active_pokemon']['status']}\n")
            
            f.write(f"\n  【 차이 】\n")
            f.write(f"    플레이어 HP 오차: {error.get('player_hp_error', 0):.1f}%\n")
            f.write(f"    상대 HP 오차: {error.get('opponent_hp_error', 0):.1f}%\n")
            f.write(f"    플레이어 포켓몬: {actual['active_pokemon']['species']} → {sim['active_pokemon']['species']} (일치: {error.get('player_pokemon_match', False)})\n")
            f.write(f"    상대 포켓몬: {actual['opponent_active_pokemon']['species']} → {sim['opponent_active_pokemon']['species']} (일치: {error.get('opponent_pokemon_match', False)})\n")
            f.write(f"    플레이어 상태 일치: {error.get('player_status_match', False)}\n")
            f.write(f"    상대 상태 일치: {error.get('opponent_status_match', False)}\n")
            f.write("-" * 70 + "\n\n")
    
    return str(filepath)


def print_turn_result(turn_data):
    """턴 결과를 콘솔에 출력"""
    result = turn_data['result']
    error = turn_data['error_metrics']
    
    actual = result['actual']
    simulated = result['simulated']
    
    turn = turn_data['turn']
    action = turn_data['action']
    
    # 현재 상태
    current = turn_data['current_state']
    
    print(f"\n{'='*70}")
    print(f"【 Turn {turn} 】 - 플레이어 행동: {action.upper()}")
    print(f"{'='*70}")
    
    print(f"\n  【 현재 상태 】")
    print(f"    플레이어: {current['active_pokemon']['species']:12} | HP: {current['active_pokemon']['current_hp']:3}/{current['active_pokemon']['max_hp']:3} | 상태: {str(current['active_pokemon']['status']):8}")
    print(f"    상대:     {current['opponent_active_pokemon']['species']:12} | HP: {current['opponent_active_pokemon']['current_hp']:3}/{current['opponent_active_pokemon']['max_hp']:3} | 상태: {str(current['opponent_active_pokemon']['status']):8}")
    
    print(f"\n  【 실제 결과 】")
    print(f"    플레이어: {actual['active_pokemon']['species']:12} | HP: {actual['active_pokemon']['current_hp']:3}/{actual['active_pokemon']['max_hp']:3} | 상태: {str(actual['active_pokemon']['status']):8}")
    print(f"    상대:     {actual['opponent_active_pokemon']['species']:12} | HP: {actual['opponent_active_pokemon']['current_hp']:3}/{actual['opponent_active_pokemon']['max_hp']:3} | 상태: {str(actual['opponent_active_pokemon']['status']):8}")
    
    print(f"\n  【 시뮬레이션 결과 (1회) 】")
    print(f"    플레이어: {simulated['active_pokemon']['species']:12} | HP: {simulated['active_pokemon']['current_hp']:3}/{simulated['active_pokemon']['max_hp']:3} | 상태: {str(simulated['active_pokemon']['status']):8}")
    print(f"    상대:     {simulated['opponent_active_pokemon']['species']:12} | HP: {simulated['opponent_active_pokemon']['current_hp']:3}/{simulated['opponent_active_pokemon']['max_hp']:3} | 상태: {str(simulated['opponent_active_pokemon']['status']):8}")
    
    print(f"\n  【 오차 비교 】")
    print(f"    플레이어 HP 오차율: {error.get('player_hp_error', 0):6.2f}%")
    print(f"    상대 HP 오차율:     {error.get('opponent_hp_error', 0):6.2f}%")
    print(f"    플레이어 포켓몬 일치: {error.get('player_pokemon_match', False)}")
    print(f"    상대 포켓몬 일치:     {error.get('opponent_pokemon_match', False)}")
    print(f"    플레이어 상태 일치:   {error.get('player_status_match', False)}")
    print(f"    상대 상태 일치:       {error.get('opponent_status_match', False)}")
