"""
배틀 데이터 저장 및 표시 관련 함수 모음
SimplifiedBattle과 SimplifiedPokemon을 JSON으로 직렬화하고,
턴별 결과를 저장하는 기능 제공
"""
import json
from pathlib import Path
from datetime import datetime


# === SimplifiedBattle을 JSON-직렬화 가능한 딕셔너리로 변환 ===

def simplified_pokemon_to_dict(pokemon):
    """SimplifiedPokemon의 모든 정보를 딕셔너리로 변환"""
    if not pokemon:
        return None
    
    return {
        # 기본 정보
        'species': pokemon.species,
        'level': pokemon.level,
        'gender': pokemon.gender.name if hasattr(pokemon, 'gender') and pokemon.gender else None,
        
        # 타입
        'type_1': pokemon.type_1.name if pokemon.type_1 else None,
        'type_2': pokemon.type_2.name if pokemon.type_2 else None,
        'types': [t.name for t in pokemon.types] if hasattr(pokemon, 'types') and pokemon.types else [],
        
        # HP
        'current_hp': pokemon.current_hp,
        'max_hp': pokemon.max_hp,
        
        # 상태이상
        'status': pokemon.status.name if pokemon.status else None,
        'status_counter': pokemon.status_counter,
        'toxic_counter': pokemon.toxic_counter if hasattr(pokemon, 'toxic_counter') else 0,
        
        # 스탯
        'base_stats': pokemon.base_stats.copy() if pokemon.base_stats else {},
        'stats': pokemon.stats.copy() if pokemon.stats else {},
        'boosts': pokemon.boosts.copy() if pokemon.boosts else {},
        'boost_timers': pokemon.boost_timers.copy() if hasattr(pokemon, 'boost_timers') and pokemon.boost_timers else {},
        
        # 기술
        'moves': [m.id for m in pokemon.moves] if pokemon.moves else [],
        
        # 특성 및 아이템
        'ability': pokemon.ability,
        'item': pokemon.item,
        
        # 효과 (enum 키를 문자열로 변환)
        'effects': {
            (k.name if hasattr(k, 'name') else str(k)): v
            for k, v in pokemon.effects.items()
        } if pokemon.effects else {},
        
        # 배틀 상태
        'active': pokemon.active,
        'first_turn': pokemon.first_turn,
        'must_recharge': pokemon.must_recharge,
        'protect_counter': pokemon.protect_counter,
        
        # 성질 및 캐시 (성질은 복원에 필요하지만 저장)
        'nature': pokemon.nature if hasattr(pokemon, 'nature') else None,
    }


def simplified_battle_to_dict(battle_state):
    """SimplifiedBattle의 모든 정보를 딕셔너리로 변환"""
    if not battle_state:
        return None
    
    return {
        # 기본 정보
        'turn': battle_state.turn,
        'gen': battle_state.gen,
        'finished': battle_state.finished,
        'won': battle_state.won,
        'lost': battle_state.lost,
        
        # 활성 포켓몬
        'active_pokemon': simplified_pokemon_to_dict(battle_state.active_pokemon),
        'opponent_active_pokemon': simplified_pokemon_to_dict(battle_state.opponent_active_pokemon),
        
        # 팀
        'team': {
            name: simplified_pokemon_to_dict(poke)
            for name, poke in battle_state.team.items()
        },
        'opponent_team': {
            name: simplified_pokemon_to_dict(poke)
            for name, poke in battle_state.opponent_team.items()
        },
        
        # 필드 효과 (enum을 name으로 변환)
        'weather': {k.name if hasattr(k, 'name') else str(k): v.name if hasattr(v, 'name') else str(v) for k, v in battle_state.weather.items()} if battle_state.weather else {},
        'fields': {k.name if hasattr(k, 'name') else str(k): v.name if hasattr(v, 'name') else str(v) for k, v in battle_state.fields.items()} if battle_state.fields else {},
        'side_conditions': {k.name if hasattr(k, 'name') else str(k): v.name if hasattr(v, 'name') else str(v) for k, v in battle_state.side_conditions.items()} if battle_state.side_conditions else {},
        'opponent_side_conditions': {k.name if hasattr(k, 'name') else str(k): v.name if hasattr(v, 'name') else str(v) for k, v in battle_state.opponent_side_conditions.items()} if battle_state.opponent_side_conditions else {},
        
        # 사용 가능한 선택지
        'available_moves': [m.id for m in battle_state.available_moves] if battle_state.available_moves else [],
        'available_switches': [p.species for p in battle_state.available_switches] if battle_state.available_switches else [],
    }


# === 턴별 시뮬레이션 데이터 저장 ===

def save_turn_simulation_data(battle_id, turn, current_battle_state, player_action_info, opponent_action_info,
                              actual_result_state, sim_result_state, error_metrics):
    """
    특정 턴의 입력값과 결과값을 함께 저장
    
    Args:
        battle_id: 배틀 ID
        turn: 턴 번호
        current_battle_state: SimplifiedBattle (턴 시작 시점)
        player_action_info: 플레이어 행동 정보
        opponent_action_info: 상대 행동 정보
        actual_result_state: SimplifiedBattle (실제 결과)
        sim_result_state: SimplifiedBattle (시뮬 결과)
        error_metrics: 오차 정보 딕셔너리
    
    Returns:
        (입력+결과 턴 데이터, 결과 턴 데이터) 튜플
    """
    # 입력값 + 결과값 함께 저장
    input_turn_data = {
        'turn': turn,
        'current_battle_state': simplified_battle_to_dict(current_battle_state),
        'player_action_info': {
            'order_type': player_action_info.get('order_type'),
            'move_idx': player_action_info.get('move_idx'),
            'switch_to': player_action_info.get('switch_to').species if hasattr(player_action_info.get('switch_to'), 'species') else player_action_info.get('switch_to'),
        },
        'opponent_action_info': {
            'order_type': opponent_action_info.get('order_type'),
            'move_idx': opponent_action_info.get('move_idx'),
            'switch_to': opponent_action_info.get('switch_to').species if hasattr(opponent_action_info.get('switch_to'), 'species') else opponent_action_info.get('switch_to'),
        },
        # 결과값도 포함
        'result': {
            'actual': simplified_battle_to_dict(actual_result_state),
            'simulated': simplified_battle_to_dict(sim_result_state),
        },
        'error_metrics': error_metrics
    }
    
    # 결과값만 (현재 상태도 포함)
    result_turn_data = {
        'turn': turn,
        'action': player_action_info.get('order_type'),
        'current_state': simplified_battle_to_dict(current_battle_state),
        'result': {
            'actual': simplified_battle_to_dict(actual_result_state),
            'simulated': simplified_battle_to_dict(sim_result_state),
        },
        'error_metrics': error_metrics
    }
    
    return (input_turn_data, result_turn_data)


def save_battle_turn_inputs(battle_id, turn_inputs_list):
    """
    배틀의 모든 턴 입력값을 저장
    
    Args:
        battle_id: 배틀 ID
        turn_inputs_list: 턴별 입력값 데이터 리스트
    
    Returns:
        저장된 파일 경로
    """
    if not turn_inputs_list:
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 저장할 데이터 구조
    inputs_data = {
        'battle_id': battle_id,
        'timestamp': timestamp,
        'total_turns': len(turn_inputs_list),
        'turns': turn_inputs_list
    }
    
    # 파일로 저장
    output_dir = Path(__file__).parent / "battle_data" / battle_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / "inputs.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(inputs_data, f, indent=2, ensure_ascii=False)
    
    return str(filepath)


def save_battle_turn_results(battle_id, turn_results_list):
    """
    배틀의 모든 턴 결과값을 텍스트 형식으로 저장
    
    Args:
        battle_id: 배틀 ID
        turn_results_list: 턴별 결과값 데이터 리스트
    
    Returns:
        저장된 파일 경로
    """
    if not turn_results_list:
        return None
    
    # 파일로 저장
    output_dir = Path(__file__).parent / "battle_data" / battle_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / "results.txt"
    with open(filepath, 'w', encoding='utf-8') as f:
        for turn_result in turn_results_list:
            turn = turn_result['turn']
            action = turn_result['action']
            current = turn_result['current_state']
            result = turn_result['result']
            error = turn_result['error_metrics']
            
            # 턴 헤더
            f.write(f"【 Turn {turn} 】\n")
            
            # 플레이어 행동
            f.write(f"  플레이어 행동: {action}\n")
            
            # 상대 행동 (서버 fog of war 때문에 실시간 정보 불가)
            f.write(f"  상대 행동: (서버에서 숨김)\n")
            
            # 현재 상태
            f.write(f"\n  【 현재 상태 】\n")
            f.write(f"    플레이어: {current['active_pokemon']['species']} | HP: {current['active_pokemon']['current_hp']}/{current['active_pokemon']['max_hp']} | 상태: {current['active_pokemon']['status']}\n")
            f.write(f"    상대: {current['opponent_active_pokemon']['species']} | HP: {current['opponent_active_pokemon']['current_hp']}/{current['opponent_active_pokemon']['max_hp']} | 상태: {current['opponent_active_pokemon']['status']}\n")
            
            # 실제 결과
            actual = result['actual']
            f.write(f"\n  【 실제 결과 】\n")
            f.write(f"    플레이어: {actual['active_pokemon']['species']} | HP: {actual['active_pokemon']['current_hp']}/{actual['active_pokemon']['max_hp']} | 상태: {actual['active_pokemon']['status']}\n")
            f.write(f"    상대: {actual['opponent_active_pokemon']['species']} | HP: {actual['opponent_active_pokemon']['current_hp']}/{actual['opponent_active_pokemon']['max_hp']} | 상태: {actual['opponent_active_pokemon']['status']}\n")
            
            # 시뮬 결과
            sim = result['simulated']
            f.write(f"\n  【 시뮬 결과 (1회) 】\n")
            f.write(f"    플레이어: {sim['active_pokemon']['species']} | HP: {sim['active_pokemon']['current_hp']}/{sim['active_pokemon']['max_hp']} | 상태: {sim['active_pokemon']['status']}\n")
            f.write(f"    상대: {sim['opponent_active_pokemon']['species']} | HP: {sim['opponent_active_pokemon']['current_hp']}/{sim['opponent_active_pokemon']['max_hp']} | 상태: {sim['opponent_active_pokemon']['status']}\n")
            
            # 오차
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
    """
    턴 결과를 콘솔에 출력
    
    Args:
        turn_data: 턴 결과 딕셔너리
    """
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
