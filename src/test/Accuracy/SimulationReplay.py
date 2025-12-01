"""
저장된 inputs.json을 로드해서 특정 턴의 배틀을 재현하는 클래스
"""
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sim.BattleClass.SimplifiedBattle import SimplifiedBattle
from sim.BattleClass.SimplifiedPokemon import SimplifiedPokemon
from sim.BattleClass.SimplifiedMove import SimplifiedMove
from sim.BattleEngine.SimplifiedBattleEngine import SimplifiedBattleEngine
from sim.Supporting.PokemonStatus import Status


class SimulationReplay:
    """저장된 입력값으로부터 특정 턴의 배틀을 재현"""
    
    def __init__(self, battle_data_dir: str):
        """
        Args:
            battle_data_dir: battle_data/{battle_id} 디렉토리 경로
        """
        self.battle_data_dir = Path(battle_data_dir)
        self.inputs_file = self.battle_data_dir / "inputs.json"
        self.results_file = self.battle_data_dir / "results.txt"
        
        if not self.inputs_file.exists():
            raise FileNotFoundError(f"입력값 파일을 찾을 수 없습니다: {self.inputs_file}")
        
        # 입력값 로드
        with open(self.inputs_file, 'r', encoding='utf-8') as f:
            self.inputs_data = json.load(f)
        
        self.battle_id = self.inputs_data.get('battle_id')
        self.total_turns = self.inputs_data.get('total_turns', 0)
        self.turns = self.inputs_data.get('turns', [])
    
    def load_turn_data(self, turn: int) -> Optional[Dict]:
        """
        특정 턴의 입력값 로드
        
        Args:
            turn: 턴 번호 (1부터 시작)
        
        Returns:
            턴 데이터 딕셔너리
        """
        for turn_data in self.turns:
            if turn_data.get('turn') == turn:
                return turn_data
        return None
    
    def dict_to_simplified_pokemon(self, pokemon_dict: Dict) -> SimplifiedPokemon:
        """
        저장된 SimplifiedPokemon 딕셔너리를 객체로 복원
        
        Args:
            pokemon_dict: 저장된 포켓몬 딕셔너리
        
        Returns:
            SimplifiedPokemon 객체
        """
        from poke_env.data import GenData
        from poke_env.battle.pokemon_type import PokemonType
        
        if not pokemon_dict:
            return None
        
        # SimplifiedPokemon 객체 생성 (직접 구성)
        pokemon = SimplifiedPokemon.__new__(SimplifiedPokemon)
        
        # 기본 정보
        pokemon.species = pokemon_dict.get('species')
        pokemon.level = pokemon_dict.get('level', 100)
        pokemon.gender = pokemon_dict.get('gender')  # enum.name으로 저장됨
        
        # 타입 정보 (저장된 데이터에서 직접 로드)
        type_1_name = pokemon_dict.get('type_1')
        type_2_name = pokemon_dict.get('type_2')
        types_names = pokemon_dict.get('types', [])
        
        # 저장된 타입 정보 사용
        if types_names:
            try:
                pokemon.types = [PokemonType[t] for t in types_names]
            except (KeyError, TypeError):
                pokemon.types = [PokemonType.NORMAL]
        else:
            pokemon.types = [PokemonType.NORMAL]
        
        # type_1, type_2 설정
        if type_1_name:
            try:
                pokemon.type_1 = PokemonType[type_1_name]
            except (KeyError, TypeError):
                pokemon.type_1 = pokemon.types[0] if pokemon.types else PokemonType.NORMAL
        else:
            pokemon.type_1 = pokemon.types[0] if pokemon.types else PokemonType.NORMAL
        
        if type_2_name:
            try:
                pokemon.type_2 = PokemonType[type_2_name]
            except (KeyError, TypeError):
                pokemon.type_2 = pokemon.types[1] if len(pokemon.types) > 1 else None
        else:
            pokemon.type_2 = pokemon.types[1] if len(pokemon.types) > 1 else None
        
        # HP
        pokemon.current_hp = pokemon_dict.get('current_hp', 0)
        pokemon.max_hp = pokemon_dict.get('max_hp', 100)
        
        # 상태이상
        status_str = pokemon_dict.get('status')
        if status_str:
            try:
                pokemon.status = Status[status_str]
            except (KeyError, TypeError):
                pokemon.status = None
        else:
            pokemon.status = None
        pokemon.status_counter = pokemon_dict.get('status_counter', 0)
        pokemon.toxic_counter = pokemon_dict.get('toxic_counter', 0)
        
        # 스탯 - 
        pokemon.base_stats = pokemon_dict.get('base_stats', {}).copy() if pokemon_dict.get('base_stats') else {}
        pokemon.stats = pokemon_dict.get('stats', {}).copy() if pokemon_dict.get('stats') else {}
        pokemon.boosts = pokemon_dict.get('boosts', {}).copy() if pokemon_dict.get('boosts') else {}
        pokemon.boost_timers = pokemon_dict.get('boost_timers', {}).copy() if pokemon_dict.get('boost_timers') else {}
        
        # 기술 - 저장된 move 딕셔너리에서 SimplifiedMove 복원
        moves_data = pokemon_dict.get('moves', [])
        pokemon.moves = []
        try:
            for move_data in moves_data:
                if isinstance(move_data, dict) and 'id' in move_data:
                    # SimplifiedMove 객체를 직접 생성 (저장된 데이터에서)
                    move = SimplifiedMove.__new__(SimplifiedMove)
                    move.id = move_data.get('id')
                    move.base_power = move_data.get('base_power')
                    
                    # Type 객체 복원
                    type_str = move_data.get('type')
                    if type_str:
                        try:
                            from poke_env.battle.pokemon_type import PokemonType
                            move.type = PokemonType[type_str] if isinstance(type_str, str) else type_str
                        except:
                            move.type = type_str
                    
                    # Category 객체 복원
                    category_str = move_data.get('category')
                    if category_str:
                        try:
                            from poke_env.battle.move_category import MoveCategory
                            move.category = MoveCategory[category_str] if isinstance(category_str, str) else category_str
                        except:
                            move.category = category_str
                    
                    move.accuracy = move_data.get('accuracy')
                    move.priority = move_data.get('priority', 0)
                    move.current_pp = move_data.get('current_pp', 0)
                    move.max_pp = move_data.get('max_pp', 0)
                    move.boosts = move_data.get('boosts')
                    move.self_boost = move_data.get('self_boost')
                    
                    # Status 객체 복원
                    status_str = move_data.get('status')
                    if status_str:
                        try:
                            move.status = Status[status_str] if isinstance(status_str, str) else status_str
                        except:
                            move.status = status_str
                    else:
                        move.status = None
                    
                    move.crit_ratio = move_data.get('crit_ratio', 0)
                    move.recoil = move_data.get('recoil', 0)
                    move.drain = move_data.get('drain', 0)
                    move.secondary = None
                    move.expected_hits = 1
                    move.flags = {}
                    move.breaks_protect = False
                    move.is_protect_move = False
                    
                    pokemon.moves.append(move)
                elif isinstance(move_data, str):
                    print(f"Legacy move format (string only): {move_data}")
        except Exception as e:
            print(f"Error loading moves for {pokemon_dict.get('species')}: {e}")
            import traceback
            traceback.print_exc()
        
        # 특성 및 아이템
        pokemon.ability = pokemon_dict.get('ability')
        pokemon.item = pokemon_dict.get('item')
        
        # 효과
        pokemon.effects = pokemon_dict.get('effects', {}).copy() if pokemon_dict.get('effects') else {}
        
        # 배틀 상태
        pokemon.active = pokemon_dict.get('active', False)
        pokemon.first_turn = pokemon_dict.get('first_turn', False)
        pokemon.must_recharge = pokemon_dict.get('must_recharge', False)
        pokemon.protect_counter = pokemon_dict.get('protect_counter', 0)
        
        # 성질
        pokemon.nature = pokemon_dict.get('nature')
        
        # 캐시
        pokemon._stat_cache = {}
        
        return pokemon
    
    def dict_to_simplified_battle(self, battle_dict: Dict) -> SimplifiedBattle:
        """
        저장된 SimplifiedBattle 딕셔너리를 객체로 복원
        
        Args:
            battle_dict: 저장된 배틀 상태 딕셔너리
        
        Returns:
            SimplifiedBattle 객체
        """
        # SimplifiedBattle 객체 생성 (직접 구성)
        battle = SimplifiedBattle.__new__(SimplifiedBattle)
        
        # 기본 정보
        battle.turn = battle_dict.get('turn', 1)
        battle.gen = battle_dict.get('gen', 9)
        battle.finished = battle_dict.get('finished', False)
        battle.won = battle_dict.get('won', False)
        battle.lost = battle_dict.get('lost', False)
        
        # 활성 포켓몬 복원
        active_pokemon_dict = battle_dict.get('active_pokemon')
        battle.active_pokemon = self.dict_to_simplified_pokemon(active_pokemon_dict) if active_pokemon_dict else None
        
        opponent_active_dict = battle_dict.get('opponent_active_pokemon')
        battle.opponent_active_pokemon = self.dict_to_simplified_pokemon(opponent_active_dict) if opponent_active_dict else None
        
        # 팀 복원
        battle.team = {}
        team_dict = battle_dict.get('team', {})
        for species, pokemon_dict in team_dict.items():
            battle.team[species] = self.dict_to_simplified_pokemon(pokemon_dict)
        
        battle.opponent_team = {}
        opponent_team_dict = battle_dict.get('opponent_team', {})
        for species, pokemon_dict in opponent_team_dict.items():
            battle.opponent_team[species] = self.dict_to_simplified_pokemon(pokemon_dict)
        
        # 필드 효과 복원 (enum.name으로 저장됨)
        from poke_env.battle.weather import Weather
        from poke_env.battle.field import Field
        from poke_env.battle.side_condition import SideCondition
        
        battle.weather = {}
        weather_dict = battle_dict.get('weather', {})
        for weather_name, turns in weather_dict.items():
            try:
                weather_enum = Weather[weather_name]
                battle.weather[weather_enum] = turns
            except (KeyError, TypeError):
                pass
        
        battle.fields = {}
        fields_dict = battle_dict.get('fields', {})
        for field_name, turns in fields_dict.items():
            try:
                field_enum = Field[field_name]
                battle.fields[field_enum] = turns
            except (KeyError, TypeError):
                pass
        
        battle.side_conditions = {}
        side_dict = battle_dict.get('side_conditions', {})
        for side_name, turns in side_dict.items():
            try:
                side_enum = SideCondition[side_name]
                battle.side_conditions[side_enum] = turns
            except (KeyError, TypeError):
                pass
        
        battle.opponent_side_conditions = {}
        opp_side_dict = battle_dict.get('opponent_side_conditions', {})
        for side_name, turns in opp_side_dict.items():
            try:
                side_enum = SideCondition[side_name]
                battle.opponent_side_conditions[side_enum] = turns
            except (KeyError, TypeError):
                pass
        
        # 사용 가능한 기술 복원
        from poke_env.data import GenData
        gen_data = GenData.from_gen(battle.gen)
        
        battle.available_moves = []
        moves_list = battle_dict.get('available_moves', [])
        for move_id in moves_list:
            try:
                move_obj = gen_data.moves.get(move_id)
                if move_obj:
                    battle.available_moves.append(SimplifiedMove(move_obj))
            except:
                pass
        
        # 사용 가능한 교체 포켓몬 복원
        battle.available_switches = []
        switches_list = battle_dict.get('available_switches', [])
        for species in switches_list:
            if species in battle.team:
                battle.available_switches.append(battle.team[species])
        
        return battle
    
    def replay_turn(self, turn: int) -> Tuple[SimplifiedBattle, Dict]:
        """
        특정 턴을 재현하고 결과 반환
        
        Args:
            turn: 턴 번호 (1부터 시작)
        
        Returns:
            (재현된 배틀 상태, 오차 메트릭) 튜플
        """
        # 입력값 로드
        turn_data = self.load_turn_data(turn)
        if not turn_data:
            raise ValueError(f"턴 {turn}의 입력값을 찾을 수 없습니다")
        
        # 배틀 상태 복원
        current_battle_state = self.dict_to_simplified_battle(
            turn_data.get('current_battle_state')
        )
        
        # 행동 정보 추출
        player_action_info = turn_data.get('player_action_info', {})
        opponent_action_info = turn_data.get('opponent_action_info', {})
        
        print(f"\n{'='*70}")
        print(f"【 Turn {turn} 재현 】")
        print(f"{'='*70}")
        print(f"\n플레이어 포켓몬: {current_battle_state.active_pokemon.species}")
        print(f"  - HP: {current_battle_state.active_pokemon.current_hp}/{current_battle_state.active_pokemon.max_hp}")
        print(f"  - 상태: {current_battle_state.active_pokemon.status}")
        
        print(f"\n상대 포켓몬: {current_battle_state.opponent_active_pokemon.species}")
        print(f"  - HP: {current_battle_state.opponent_active_pokemon.current_hp}/{current_battle_state.opponent_active_pokemon.max_hp}")
        print(f"  - 상태: {current_battle_state.opponent_active_pokemon.status}")
        
        print(f"\n플레이어 행동: {player_action_info.get('order_type')}")
        if player_action_info.get('order_type') == 'move':
            move_name = player_action_info.get('move_name')
            move_idx = player_action_info.get('move_idx')
            available_move_ids = turn_data.get('current_battle_state', {}).get('available_moves', [])
            if move_name:
                print(f"  - 기술: {move_name}")
            elif move_idx is not None and move_idx < len(available_move_ids):
                print(f"  - 기술: {available_move_ids[move_idx]}")
            else:
                print(f"  - 기술 인덱스: {move_idx}")
        elif player_action_info.get('order_type') == 'switch':
            print(f"  - 교체 대상: {player_action_info.get('switch_to')}")
        
        print(f"\n상대 행동: {opponent_action_info.get('order_type')}")
        if opponent_action_info.get('order_type') == 'move':
            move_name = opponent_action_info.get('move_name')
            move_idx = opponent_action_info.get('move_idx')
            opp_moves = turn_data.get('current_battle_state', {}).get('opponent_active_pokemon', {}).get('moves', [])
            if move_name:
                print(f"  - 기술: {move_name}")
            elif move_idx is not None and move_idx < len(opp_moves):
                print(f"  - 기술: {opp_moves[move_idx]}")
            elif move_idx is not None:
                print(f"  - 기술 인덱스: {move_idx}")
            else:
                print(f"  - 기술: (미확인)")
        elif opponent_action_info.get('order_type') == 'switch':
            print(f"  - 교체 대상: {opponent_action_info.get('switch_to')}")
        
        # 배틀 엔진 초기화 및 턴 실행
        engine = SimplifiedBattleEngine(gen=current_battle_state.gen)
        
        # 배틀 상태를 복사해서 시뮬레이션 (원본 유지)
        import copy
        battle_copy = copy.deepcopy(current_battle_state)
        
        # 행동에서 기술 인덱스 추출
        player_move_idx = None
        opponent_move_idx = None
        opponent_move_name = None
        
        # 교체인 경우
        player_switch_to = None
        opponent_switch_to = None
        if player_action_info.get('order_type') == 'switch':
            player_switch_to = player_action_info.get('switch_to')
            print(f"\n플레이어가 {player_switch_to}로 교체합니다.")
        if opponent_action_info.get('order_type') == 'switch':
            opponent_switch_to = opponent_action_info.get('switch_to')
            print(f"\n상대가 {opponent_switch_to}로 교체합니다.")

        # 기술인 경우
        if player_action_info.get('order_type') == 'move':
            player_move_idx = player_action_info.get('move_idx')
        
        if opponent_action_info.get('order_type') == 'move':
            opponent_move_idx = opponent_action_info.get('move_idx')
            opponent_move_name = opponent_action_info.get('move_name')  

        print(f"\n시뮬레이션을 시작합니다...")
        
        # 시뮬레이션 실행
        simulated_battle = engine.simulate_turn(
            new_battle=battle_copy,
            player_move_idx=player_move_idx,
            opponent_move_idx=opponent_move_idx,
            opponent_move_name=opponent_move_name, 
            player_switch_to=player_switch_to,
            opponent_switch_to=opponent_switch_to,
            verbose=True
        )
        
        print(f"\n【 시뮬레이션 결과 】")
        print(f"플레이어: {simulated_battle.active_pokemon.species}")
        print(f"  - HP: {simulated_battle.active_pokemon.current_hp}/{simulated_battle.active_pokemon.max_hp}")
        print(f"  - 상태: {simulated_battle.active_pokemon.status}")
        
        print(f"\n상대: {simulated_battle.opponent_active_pokemon.species}")
        print(f"  - HP: {simulated_battle.opponent_active_pokemon.current_hp}/{simulated_battle.opponent_active_pokemon.max_hp}")
        print(f"  - 상태: {simulated_battle.opponent_active_pokemon.status}")
        
        # 실제 결과와 비교
        actual_data = turn_data.get('result', {}).get('actual', {})
        
        if actual_data:
            actual_battle = self.dict_to_simplified_battle(actual_data)
            
            print(f"\n【 실제 결과 】")
            print(f"플레이어: {actual_battle.active_pokemon.species}")
            print(f"  - HP: {actual_battle.active_pokemon.current_hp}/{actual_battle.active_pokemon.max_hp}")
            print(f"  - 상태: {actual_battle.active_pokemon.status}")
            
            print(f"\n상대: {actual_battle.opponent_active_pokemon.species}")
            print(f"  - HP: {actual_battle.opponent_active_pokemon.current_hp}/{actual_battle.opponent_active_pokemon.max_hp}")
            print(f"  - 상태: {actual_battle.opponent_active_pokemon.status}")
            
            # 오차 계산
            player_hp_error = abs(
                (simulated_battle.active_pokemon.current_hp / max(1, simulated_battle.active_pokemon.max_hp)) -
                (actual_battle.active_pokemon.current_hp / max(1, actual_battle.active_pokemon.max_hp))
            ) * 100
            
            opponent_hp_error = abs(
                (simulated_battle.opponent_active_pokemon.current_hp / max(1, simulated_battle.opponent_active_pokemon.max_hp)) -
                (actual_battle.opponent_active_pokemon.current_hp / max(1, actual_battle.opponent_active_pokemon.max_hp))
            ) * 100
            
            print(f"\n【 오차 비교 】")
            print(f"플레이어 HP 오차: {player_hp_error:.1f}%")
            print(f"상대 HP 오차: {opponent_hp_error:.1f}%")
            print(f"플레이어 포켓몬 일치: {simulated_battle.active_pokemon.species == actual_battle.active_pokemon.species}")
            print(f"상대 포켓몬 일치: {simulated_battle.opponent_active_pokemon.species == actual_battle.opponent_active_pokemon.species}")
            
            error_metrics = {
                'player_hp_error': player_hp_error,
                'opponent_hp_error': opponent_hp_error,
                'player_pokemon_match': simulated_battle.active_pokemon.species == actual_battle.active_pokemon.species,
                'opponent_pokemon_match': simulated_battle.opponent_active_pokemon.species == actual_battle.opponent_active_pokemon.species,
            }
            
            return simulated_battle, error_metrics
        
        return simulated_battle, {}
    
    def list_available_turns(self) -> list:
        """저장된 모든 턴 번호 반환"""
        return [turn_data.get('turn') for turn_data in self.turns]
    
    def get_turn_summary(self, turn: int) -> Dict:
        """특정 턴의 요약 정보 반환"""
        turn_data = self.load_turn_data(turn)
        if not turn_data:
            return None
        
        current = self.dict_to_simplified_battle(turn_data.get('current_battle_state'))
        result = turn_data.get('result', {})
        actual = self.dict_to_simplified_battle(result.get('actual', {})) if result.get('actual') else None
        simulated = self.dict_to_simplified_battle(result.get('simulated', {})) if result.get('simulated') else None
        
        return {
            'turn': turn,
            'player_action': turn_data.get('player_action_info', {}).get('order_type'),
            'opponent_action': turn_data.get('opponent_action_info', {}).get('order_type'),
            'current_state': current,
            'actual_result': actual,
            'simulated_result': simulated,
            'error_metrics': turn_data.get('error_metrics', {})
        }


def select_battle_data():
    """배틀 데이터 디렉토리 선택 메뉴"""
    battle_data_dir = Path(__file__).parent / "battle_data"
    
    if not battle_data_dir.exists():
        print(f"battle_data 디렉토리를 찾을 수 없습니다: {battle_data_dir}")
        return None
    
    # 배틀 데이터 디렉토리 목록 (최신순)
    battle_dirs = sorted(
        [d for d in battle_data_dir.iterdir() if d.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    if not battle_dirs:
        print("저장된 배틀 데이터가 없습니다")
        return None
    
    print("\n" + "="*70)
    print("저장된 배틀 데이터")
    print("="*70)
    
    for idx, battle_dir in enumerate(battle_dirs, 1):
        # inputs.json에서 총 턴 수 확인
        inputs_file = battle_dir / "inputs.json"
        total_turns = "?"
        if inputs_file.exists():
            try:
                with open(inputs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total_turns = data.get('total_turns', 0)
            except:
                pass
        
        print(f"{idx}. {battle_dir.name} (총 {total_turns}턴)")
    
    print(f"{len(battle_dirs) + 1}. 종료")
    
    while True:
        try:
            choice = int(input("\n선택 (번호 입력): "))
            if choice == len(battle_dirs) + 1:
                return None
            if 1 <= choice <= len(battle_dirs):
                return str(battle_dirs[choice - 1])
            print("잘못된 선택입니다")
        except ValueError:
            print("숫자를 입력하세요")


def select_turn(replay: SimulationReplay):
    """턴 선택 메뉴"""
    available_turns = replay.list_available_turns()
    
    print("\n" + "="*70)
    print(f"사용 가능한 턴 (총 {len(available_turns)}개)")
    print("="*70)
    
    # 턴을 여러 줄에 나열 (한 줄에 10개)
    for i, turn in enumerate(available_turns, 1):
        if i % 10 == 1:
            print()
        print(f"{turn:3d}", end=" ")
    
    print(f"\n{len(available_turns) + 1}. 이전 메뉴")
    
    while True:
        try:
            choice = int(input("\n턴 번호 입력: "))
            if choice == len(available_turns) + 1:
                return None
            if choice in available_turns:
                return choice
            print("잘못된 턴 번호입니다")
        except ValueError:
            print("숫자를 입력하세요")


if __name__ == "__main__":
    # 명령줄 인자로 전달된 경우 그대로 사용
    import sys
    
    if len(sys.argv) >= 2:
        # 레거시 지원: python simulation_replay.py <battle_dir> [turn]
        battle_dir = sys.argv[1]
        turn_num = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        
        try:
            replay = SimulationReplay(battle_dir)
            print(f"배틀 ID: {replay.battle_id}")
            print(f"총 턴 수: {replay.total_turns}")
            print(f"사용 가능한 턴: {replay.list_available_turns()}\n")
            
            # 특정 턴 재현
            simulated_battle, error_metrics = replay.replay_turn(turn_num)
            print(f"\n✅ Turn {turn_num} 재현 완료")
            
        except Exception as e:
            print(f"오류: {e}")
            import traceback
            traceback.print_exc()
    else:
        # 메뉴 기반 모드
        print("\n" + "="*70)
        print("배틀 시뮬레이션 재현 도구")
        print("="*70)
        
        while True:
            battle_dir = select_battle_data()
            if battle_dir is None:
                print("\n종료합니다")
                break
            
            try:
                replay = SimulationReplay(battle_dir)
                
                while True:
                    turn_num = select_turn(replay)
                    if turn_num is None:
                        break
                    
                    try:
                        simulated_battle, error_metrics = replay.replay_turn(turn_num)
                        print(f"\nTurn {turn_num} 재현 완료")
                        
                        # 다시 실행 여부 확인
                        again = input("\n다른 턴을 보시겠습니까? (y/n): ").lower().strip()
                        if again != 'y':
                            break
                    except Exception as e:
                        print(f"❌ Turn {turn_num} 재현 오류: {e}")
                        import traceback
                        traceback.print_exc()
                
            except Exception as e:
                print(f"오류: {e}")
                import traceback
                traceback.print_exc()
