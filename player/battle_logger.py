# battle_logger.py
import re

class BattleLogMixin:
    """
    Player 클래스에 실시간 배틀 로그 출력 기능을 추가해 주는 믹스인 클래스.
    이 클래스를 다른 Player와 함께 상속하면 로그 기능이 자동으로 활성화됩니다.
    
    추가 기능:
    - opponent_action_store: 상대 행동 저장 {battle_tag: {turn: action_info}}
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.opponent_action_store = {}  # {battle_tag: {turn: action_info}}
        self.opponent_move_log = {}  # {battle_tag: [(turn, move_name), ...]} - 로그에서 수집한 정보
    
    def _format_pokemon_name(self, raw_name: str) -> str:
        """'p1a: Ribombee' 같은 형식에서 포켓몬 이름만 추출합니다."""
        clean_name = re.sub(r' \|.*', '', raw_name)
        if ': ' in clean_name:
            return clean_name.split(': ')[1].split(',')[0]
        return clean_name
    
    def _extract_move_idx(self, battle, move_name: str) -> int:
        """
        배틀 상태에서 기술 이름으로 move_idx 찾기
        상대 포켓몬의 가능한 기술 목록에서 인덱스 반환
        """
        if not battle or not battle.opponent_active_pokemon:
            return None
        
        active_poke = battle.opponent_active_pokemon
        if not active_poke or not active_poke.moves:
            return None
        
        for idx, move in enumerate(active_poke.moves):
            # move_name이 정확히 일치하는지 확인
            if move.id == move_name or move.id.lower() == move_name.lower():
                return idx
            # move.id가 하이픈 형식일 수도 있음
            if move.id.replace('-', '').lower() == move_name.replace('-', '').lower():
                return idx
        
        # 디버그: 일치하는 기술이 없을 때
        # print(f"  [DEBUG] move_idx 찾기 실패: move_name={move_name}, available_moves={[m.id for m in active_poke.moves]}")
        return None
    
    def _store_opponent_action(self, battle_tag: str, turn: int, action_info: dict) -> None:
        """상대 행동을 저장소에 기록 (중복 방지)"""
        if battle_tag not in self.opponent_action_store:
            self.opponent_action_store[battle_tag] = {}
        
        # 이미 해당 턴의 행동이 저장되어 있으면 스킵 (중복 방지)
        if turn in self.opponent_action_store[battle_tag]:
            return
        
        self.opponent_action_store[battle_tag][turn] = action_info
        
        # 로그 정보도 저장
        if battle_tag not in self.opponent_move_log:
            self.opponent_move_log[battle_tag] = []
        
        # move_name이 있으면 로그에 기록
        if action_info.get('move_name'):
            self.opponent_move_log[battle_tag].append((turn, action_info['move_name']))
        elif action_info.get('switch_to'):
            self.opponent_move_log[battle_tag].append((turn, f"switch:{action_info['switch_to']}"))
    
    def get_opponent_action(self, battle_tag: str, turn: int) -> dict:
        """특정 턴의 상대 행동 반환"""
        if battle_tag not in self.opponent_action_store:
            return None
        
        return self.opponent_action_store[battle_tag].get(turn)
    
    def get_opponent_move_log(self, battle_tag: str) -> list:
        """배틀의 모든 상대 행동 로그 반환: [(turn, move_name), ...]"""
        return self.opponent_move_log.get(battle_tag, [])
    
    def convert_move_name_to_idx(self, pokemon_species: str, move_name: str) -> int:
        """
        포켓몬 종과 기술 이름으로부터 move_idx 계산
        포켓몬의 learnset에서 이 기술이 있는지 확인하고 인덱스 반환
        """
        from poke_env.data import POKEDEX
        
        # 포켓몬 데이터 가져오기
        if pokemon_species not in POKEDEX:
            return None
        
        pokedex_entry = POKEDEX[pokemon_species]
        
        # learnset에서 해당 기술 찾기
        if not hasattr(pokedex_entry, 'learnset') or not pokedex_entry.learnset:
            return None
        
        # learnset은 {move_id: [methods]}로 구성
        # 예: {'tackle': ['1L'], 'ember': ['1L']}
        learnset = pokedex_entry.learnset
        
        # move_name을 정규화
        normalized_move = move_name.lower().replace(' ', '').replace('-', '')
        
        moves_list = []
        for move_id in learnset.keys():
            normalized_id = move_id.lower().replace(' ', '').replace('-', '')
            if normalized_id == normalized_move:
                moves_list.append(move_id)
        
        if moves_list:
            # 첫 번째 일치하는 기술의 인덱스 반환 (보통 하나만 있음)
            return 0  # 실제로는 배틀 상태에서 정확한 인덱스를 찾아야 함
        
        return None

    async def _handle_battle_message(self, split_message: list) -> None:
        """
        메시지를 가로채서 상대 행동을 저장합니다.
        """
        # 부모 클래스(Player)의 _handle_battle_message를 먼저 호출해야
        # 봇의 상태가 정상적으로 업데이트됩니다.
        await super()._handle_battle_message(split_message)
        
        # 현재 배틀 정보 추출
        battle_tag = None
        current_turn = None
        
        # split_message[0]의 첫 번째 요소에서 battle_tag 추출
        # 예: ['battle-gen9randombattle-12345', ['turn', '1'], ...]
        if split_message and isinstance(split_message[0], str):
            battle_tag = split_message[0]
        
        for sub_message in split_message:
            if not isinstance(sub_message, list) or len(sub_message) < 2:
                continue

            key = sub_message[1]
            try:
                # 턴 정보 추출
                if not current_turn and hasattr(self, '_current_battle') and self._current_battle:
                    current_turn = self._current_battle.turn
                
                if key == 'turn':
                    current_turn = int(sub_message[2])
                    # |turn| 메시지에서 battle_tag도 설정 (아직 없으면)
                    if not battle_tag and hasattr(self, '_current_battle_tag'):
                        battle_tag = self._current_battle_tag
                
                # 상대 기술 저장 (p2 = 상대)
                elif key == 'move':
                    pokemon_info = sub_message[2]  # 'p1a: toxicroak' 또는 'p2a: frosmoth'
                    move_name = sub_message[3]
                    
                    # 상대 행동 감지
                    if 'p2' in pokemon_info:
                        if not battle_tag:
                            # battle_tag 획득 시도
                            if hasattr(self, '_current_battle_tag'):
                                battle_tag = self._current_battle_tag
                            elif hasattr(self, '_current_battle') and self._current_battle:
                                battle_tag = self._current_battle.battle_tag
                        
                        if not current_turn and hasattr(self, '_current_battle_turn'):
                            current_turn = self._current_battle_turn
                        
                        if battle_tag and current_turn is not None:
                            # move_idx는 나중에 배틀 완료 후 일괄 처리
                            action_info = {
                                'order_type': 'move',
                                'move_idx': None,
                                'move_name': move_name,
                                'switch_to': None,
                            }
                            self._store_opponent_action(battle_tag, current_turn, action_info)
                
                # 상대 교체 저장 (p2 = 상대)
                elif key == 'switch':
                    pokemon_info = sub_message[2]  # 'p2a: frosmoth,82' 형식
                    species = pokemon_info.split(': ')[1].split(',')[0] if ': ' in pokemon_info else None
                    
                    # 상대 교체 감지
                    if 'p2' in pokemon_info:
                        if not battle_tag:
                            if hasattr(self, '_current_battle_tag'):
                                battle_tag = self._current_battle_tag
                            elif hasattr(self, '_current_battle') and self._current_battle:
                                battle_tag = self._current_battle.battle_tag
                        
                        if not current_turn and hasattr(self, '_current_battle_turn'):
                            current_turn = self._current_battle_turn
                        
                        if battle_tag and current_turn and species:
                            action_info = {
                                'order_type': 'switch',
                                'move_idx': None,
                                'move_name': None,
                                'switch_to': species,
                            }
                            self._store_opponent_action(battle_tag, current_turn, action_info)
            except (IndexError, ValueError):
                pass