from poke_env.battle import Battle
from typing import Dict
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from SimplifiedPokemon import SimplifiedPokemon
from SimplifiedMove import SimplifiedMove
import random

# 기본 기술 개수
DEFAULT_MOVES = 4
DEFAULT_LEVEL = 80

class SimplifiedBattle:
    def __init__(self, poke_env_battle: Battle, fill_unknown_data: bool = True, gen : int = 9, team_num: int = 6):
        """
        Args:
            poke_env_battle: poke-env의 Battle 객체
            fill_unknown_data: 상대 팀의 부족한 정보를 랜덤으로 채울지 여부
        """

        # === 기본 정보 ===
        self.turn = poke_env_battle.turn
        self.gen = getattr(poke_env_battle, '_gen', 9)  # 기본값 9
        self.finished = poke_env_battle.finished
        self.won = poke_env_battle.won if hasattr(poke_env_battle, 'won') else False
        self.lost = poke_env_battle.lost if hasattr(poke_env_battle, 'lost') else False

        # === 팀 (SimplifiedPokemon으로 변환) ===
        self.team = {
            identifier: SimplifiedPokemon(pokemon)
            for identifier, pokemon in poke_env_battle.team.items()
        }
        self.opponent_team = {
            identifier: SimplifiedPokemon(pokemon)
            for identifier, pokemon in poke_env_battle.opponent_team.items()
        }
        
        # 상대 팀의 부족한 정보 채우기
        if fill_unknown_data:
            self._fill_opponent_team_data(team_num=team_num)

        # === 활성 포켓몬 ===
        # active_pokemon이 None이면 팀에서 첫 번째 살아있는 포켓몬 찾기
        if poke_env_battle.active_pokemon:
            self.active_pokemon = SimplifiedPokemon(poke_env_battle.active_pokemon)
        else:
            # 활성 포켓몬이 없으면 팀에서 첫 번째 살아있는 포켓몬 찾기
            self.active_pokemon = None
            for pokemon in self.team.values():
                if pokemon.current_hp > 0:
                    self.active_pokemon = pokemon
                    break
        
        # 상대 포켓몬의 hp는 백분율로 표시될 수 있으므로 is_percentage_hp=True로 설정
        if poke_env_battle.opponent_active_pokemon:
            self.opponent_active_pokemon = SimplifiedPokemon(poke_env_battle.opponent_active_pokemon, is_percentage_hp=True)
        else:
            # 활성 포켓몬이 없으면 팀에서 첫 번째 살아있는 포켓몬 찾기
            self.opponent_active_pokemon = None
            for pokemon in self.opponent_team.values():
                if pokemon.current_hp > 0:
                    self.opponent_active_pokemon = pokemon
                    break
        
        # opponent_active_pokemon의 기술도 채우기
        if self.opponent_active_pokemon and (not self.opponent_active_pokemon.moves or len(self.opponent_active_pokemon.moves) == 0):
            generated_moves = self._generate_random_moves(self.opponent_active_pokemon, DEFAULT_MOVES)
            if generated_moves and len(generated_moves) > 0:
                self.opponent_active_pokemon.moves = generated_moves

        # === 필드 효과 ===
        self.weather = poke_env_battle.weather.copy()
        self.fields = poke_env_battle.fields.copy()
        self.side_conditions = poke_env_battle.side_conditions.copy()
        self.opponent_side_conditions = poke_env_battle.opponent_side_conditions.copy()

        # === 턴 관련 ===
        # available_moves를 SimplifiedMove로 변환
        raw_moves = list(poke_env_battle.available_moves) if hasattr(poke_env_battle, 'available_moves') else []
        self.available_moves = [SimplifiedMove(move) for move in raw_moves if move is not None]
        
        # available_switches를 SimplifiedPokemon으로 변환
        raw_switches = list(poke_env_battle.available_switches) if hasattr(poke_env_battle, 'available_switches') else []
        self.available_switches = [SimplifiedPokemon(pokemon) for pokemon in raw_switches if pokemon is not None]
    
    def _fill_opponent_team_data(self, team_num: int = 6):
        """상대 팀의 부족한 정보를 pokedex 데이터 기반으로 채우기"""
        from poke_env.data import GenData
        
        data = GenData.from_gen(self.gen)
        
        # 0. 공개된 포켓몬들의 스탯 재계산 (HP + Atk/Def/...)
        for pokemon_id, pokemon in self.opponent_team.items():
            pokedex_data = data.pokedex.get(pokemon.species.lower(), {})
            if pokedex_data:
                base_stats = pokedex_data.get('baseStats', {})
                
                # --- A. HP 재계산 (비율 유지) ---
                base_hp = base_stats.get('hp', 100)
                # Random Battle 표준: IV 31, EV 84 (Gen 9 기준)
                recalculated_max_hp = int(((base_hp * 2 + 31 + (84 // 4)) * DEFAULT_LEVEL / 100) + DEFAULT_LEVEL + 10)
                
                # [중요] 현재 체력 비율 유지 로직
                if pokemon.max_hp > 0:
                    hp_ratio = pokemon.current_hp / pokemon.max_hp
                else:
                    hp_ratio = 1.0
                
                pokemon.max_hp = recalculated_max_hp
                pokemon.current_hp = int(recalculated_max_hp * hp_ratio) # 비율에 맞춰 재설정
                pokemon.level = DEFAULT_LEVEL

                # --- B. 나머지 스탯(Atk, Def...) 재계산 (누락된 부분 추가) ---
                # Random Battle은 보통 성격 보정을 알 수 없으므로 Neutral(1.0) 가정, EV 84
                new_stats = {}
                for stat_name in ['atk', 'def', 'spa', 'spd', 'spe']:
                    base_val = base_stats.get(stat_name, 100)
                    # 공식: ((base * 2 + IV + EV/4) * level / 100) + 5
                    # 소수점 버림(int) 처리 필수
                    val = int(((base_val * 2 + 31 + (84 // 4)) * DEFAULT_LEVEL / 100) + 5)
                    new_stats[stat_name] = val
                
                pokemon.stats = new_stats # 스탯 덮어쓰기
        
        # 1. 기존 공개된 포켓몬의 기술이 없으면 랜덤 기술 생성
        for pokemon_id, pokemon in self.opponent_team.items():
            if not pokemon.moves or len(pokemon.moves) == 0:
                # 부족한 기술 개수만큼 채우기
                generated_moves = self._generate_random_moves(pokemon, DEFAULT_MOVES - len(pokemon.moves))
                
                # 기술 생성 실패 체크
                if generated_moves and len(generated_moves) > 0:
                    pokemon.moves = generated_moves
                else:
                    # 기술 생성 실패 시 fallback (tackle만이라도 추가)
                    print(f"[경고] {pokemon_id}의 기술 생성 실패, fallback 사용")
                    default_move = self._create_default_move(pokemon)
                    pokemon.moves = [default_move] if default_move else []
        
        # 2. 상대 팀이 6마리 미만이면 미공개 포켓몬을 랜덤으로 추가
        if len(self.opponent_team) < team_num:
            # 이미 존재하는 포켓몬 종류 확인
            existing_species = {p.species.lower() for p in self.opponent_team.values()}
            
            # 추가할 포켓몬 개수
            num_to_add = team_num - len(self.opponent_team)
            
            # pokedex에서 랜덤으로 포켓몬 선택 (기존 포켓몬 제외)
            available_species = [s for s in data.pokedex.keys() if s not in existing_species]
            
            if not available_species:
                # 사용 가능한 포켓몬이 없으면 중단
                return
            
            for i in range(num_to_add):
                if not available_species:
                    break
                
                # 랜덤 포켓몬 선택
                species = random.choice(available_species)
                available_species.remove(species)
                
                # 더미 포켓몬 생성
                dummy_pokemon = self._create_dummy_pokemon(species)
                
                # 기술 생성 및 설정
                dummy_pokemon.moves = self._generate_random_moves(dummy_pokemon)
                
                # 팀에 추가
                dummy_id = f"p2: {species}_{i}"
                self.opponent_team[dummy_id] = dummy_pokemon
    
    def _create_dummy_pokemon_list(self, exisiting_species, num_to_add, gen):
        """랜덤 포켓몬 생성 리스트 (필터링 적용)"""
        from poke_env.data import GenData
        data = GenData.from_gen(self.gen)

        # TODO 베이즈추론 등 적용
        # 유효한 포켓몬 목록 필터링
        valid_species = []
        for name, entry in data.pokedex.items():
            # 1. 이미 있는 포켓몬 제외
            if name in exisiting_species:
                continue
                
            # 2. 비표준 포켓몬 제외 (Pokestar, CAP 등)
            # isNonstandard 속성이 있으면 거름 (Gigantamax 등 일부 예외는 허용 가능하지만 일단 엄격하게)
            if entry.get('isNonstandard'):
                continue
                
            # 3. 도감 번호가 0 이하인 더미 제외
            if entry.get('num', 0) <= 0:
                continue
                
            # 4. 진화체가 있는 미진화 포켓몬 제외 (Random Battle은 최종 진화체 위주)
            # (evos 키가 있으면 진화 가능하므로 제외)
            if 'evos' in entry:
                continue
            
            valid_species.append(name)

        # 개수만큼 생성
        pokemon_list = []
        for _ in range(num_to_add):
            if not valid_species:
                break
                
            random_species = random.choice(valid_species)
            # 중복 방지를 위해 선택 후 제거 (선택적)
            # valid_species.remove(random_species) 
            
            pokemon_list.append(self._create_dummy_pokemon(random_species))
        
        return pokemon_list
    
    def _create_dummy_pokemon(self, species: str = None):
        """pokedex 데이터를 기반으로 더미 포켓몬 생성"""
        from poke_env.data import GenData
        from poke_env.battle.pokemon_type import PokemonType
        
        # 데이터 로드
        data = GenData.from_gen(self.gen)
        
        # species 랜덤 선택 (없으면)
        if species is None:
            species = random.choice(list(data.pokedex.keys()))
        
        pokedex_data = data.pokedex.get(species.lower(), {})
        
        # SimplifiedPokemon 객체 생성
        dummy_pokemon = SimplifiedPokemon.__new__(SimplifiedPokemon)

        dummy_pokemon.volatiles = {}
        
        # 기본 정보
        dummy_pokemon.species = pokedex_data.get('baseSpecies', species).lower()
        dummy_pokemon.level = DEFAULT_LEVEL  # 레벨 100으로 통일
        dummy_pokemon.gender = None
        
        # 타입 설정
        types_list = pokedex_data.get('types', [])
        type_1_str = types_list[0].upper() if types_list else 'NORMAL'
        type_2_str = types_list[1].upper() if len(types_list) > 1 else None
        
        # PokemonType enum에 존재하는지 확인
        try:
            dummy_pokemon.type_1 = PokemonType[type_1_str] if type_1_str else PokemonType.NORMAL
        except KeyError:
            dummy_pokemon.type_1 = PokemonType.NORMAL
            
        try:
            dummy_pokemon.type_2 = PokemonType[type_2_str] if type_2_str else None
        except (KeyError, TypeError):
            dummy_pokemon.type_2 = None
            
        # types 리스트 설정
        types_converted = []
        for t in types_list:
            try:
                types_converted.append(PokemonType[t.upper()])
            except KeyError:
                types_converted.append(PokemonType.NORMAL)
        dummy_pokemon.types = types_converted if types_converted else [PokemonType.NORMAL]
        
        # ===== 스탯 계산 (포켓몬 공식 적용) =====
        # IV: 0~31 랜덤, EV: 0~255 랜덤 (편향되지 않도록)
        base_stats = pokedex_data.get('baseStats', {'hp': 100, 'atk': 100, 'def': 100, 'spa': 100, 'spd': 100, 'spe': 100})
        
        # IV와 EV 랜덤 생성
        iv = random.randint(0, 31)  # 0~31 균등 분포
        
        # EV는 너무 단조로우면 안 되므로:
        # - 75% 확률로 높은 EV (150~252)
        # - 25% 확률로 낮은 EV (0~100)
        if random.random() < 0.75:
            ev = random.randint(150, 252)
        else:
            ev = random.randint(0, 100)
        
        # HP 계산 (공식: ((base*2 + IV + EV/4) * level / 100) + level + 10)
        base_hp = base_stats.get('hp', 100)
        dummy_pokemon.max_hp = int(((base_hp * 2 + iv + ev // 4) * DEFAULT_LEVEL / 100) + DEFAULT_LEVEL + 10)
        dummy_pokemon.current_hp = dummy_pokemon.max_hp
        
        # 상태이상
        dummy_pokemon.status = None
        dummy_pokemon.status_counter = 0
        
        # 스탯 설정 (다른 스탯들도 동일 공식 적용)
        dummy_pokemon.base_stats = base_stats.copy()
        dummy_pokemon.stats = {}
        
        for stat_name, base in dummy_pokemon.base_stats.items():
            if stat_name == 'hp':
                # HP는 위에서 이미 계산
                dummy_pokemon.stats[stat_name] = dummy_pokemon.max_hp
            else:
                # 다른 스탯들: ((base*2 + IV + EV/4) * level / 100) + 5
                # 각 스탯마다 다른 IV/EV 생성
                stat_iv = random.randint(0, 31)
                if random.random() < 0.75:
                    stat_ev = random.randint(150, 252)
                else:
                    stat_ev = random.randint(0, 100)
                
                dummy_pokemon.stats[stat_name] = int(((base * 2 + stat_iv + stat_ev // 4) * DEFAULT_LEVEL / 100) + 5)
        
        # 부스트 설정
        dummy_pokemon.boosts = {stat: 0 for stat in ['atk', 'def', 'spa', 'spd', 'spe']}
        
        # 기술 설정 (나중에 _generate_random_moves에서 채워짐)
        dummy_pokemon.moves = []
        
        # 특성 및 아이템 설정
        abilities = pokedex_data.get('abilities', {})
        # 일반 특성 우선, 없으면 숨은 특성, 둘 다 없으면 'unknown'
        dummy_pokemon.ability = abilities.get('0', abilities.get('H', 'unknown'))
        dummy_pokemon.item = None
        
        # 효과 설정
        dummy_pokemon.effects = {}
        
        # 배틀 상태 설정
        dummy_pokemon.active = False
        dummy_pokemon.first_turn = True
        dummy_pokemon.must_recharge = False
        dummy_pokemon.protect_counter = 0
        
        return dummy_pokemon
    
    def _generate_random_moves(self, pokemon, num_to_add=4):
        """포켓몬의 기술 4개 생성"""
        
        # 일단 fallback 메서드로 기술 생성
        return self._generate_random_moves_fallback(pokemon, num_to_add)
    
    def _generate_random_moves_fallback(self, pokemon, num_to_add=4):
        """포켓몬에 맞는 랜덤 기술 생성 (learnset 데이터 사용)"""
        from poke_env.data import GenData
        from poke_env.battle.pokemon_type import PokemonType
        
        data = GenData.from_gen(self.gen)
        moves = []
        
        # 포켓몬이 배울 수 있는 기술들 가져오기
        pokedex_species = pokemon.species.lower()
        learnable_moves = []

        if pokedex_species in data.learnset and 'learnset' in data.learnset[pokedex_species]:
            learnable_moves = list(data.learnset[pokedex_species]['learnset'].keys())
        
        if not learnable_moves:
            # Learnset 데이터가 없으면 tackle 하나라도 반환
            print(f"[경고] {pokemon.species}의 learnset 데이터 없음")
            fallback_move = self._create_move_from_pokedex('tackle', data.moves.get('tackle', {'basePower': 40, 'type': 'Normal', 'category': 'Physical'}))
            return [fallback_move] if fallback_move else []
        
        # 포켓몬 타입과 일치하는 기술들 필터링
        type_moves = []      # 포켓몬 타입 기술 (위력 있음)
        strong_coverage = [] # 위력 80 이상 상성 극복
        medium_coverage = [] # 위력 60-79 상성 극복
        weak_coverage = []   # 위력 50-59 상성 극복
        status_moves = []    # 위력 0 기술 (스탯 변화, 상태이상 등)
        
        for move_id in learnable_moves:
            move_data = data.moves.get(move_id, {})
            move_type = move_data.get('type', 'Normal').upper()
            base_power = move_data.get('basePower', 0)
            
            pokemon_types = [t.name.upper() for t in pokemon.types]
            
            if base_power > 0:
                # 위력이 있는 기술
                if move_type in pokemon_types:
                    # 1. 포켓몬 타입과 일치하는 기술 (STAB)
                    type_moves.append((move_id, move_data))
                elif base_power >= 80:
                    # 2-1. 위력 80 이상 상성 극복 (우선)
                    strong_coverage.append((move_id, move_data))
                elif base_power >= 60:
                    # 2-2. 위력 60-79 상성 극복
                    medium_coverage.append((move_id, move_data))
                elif base_power >= 50:
                    # 2-3. 위력 50-59 상성 극복
                    weak_coverage.append((move_id, move_data))
            else:
                # 위력 0 기술은 마지막 수단
                status_moves.append((move_id, move_data))
        
        # 기술 선택 전략
        selected_moves = []

        # 1. STAB 기술 우선 (최소 2개, 가능하면 위력 높은것)
        if type_moves:
            strong_stab = sorted([m for m in type_moves if m[1].get('basePower', 0) >= 70], 
                                key=lambda x: x[1].get('basePower', 0), reverse=True)
            if strong_stab:
                # 최소 1개, 최대 2개의 강한 STAB 기술 (BP 70 이상)
                stab_count = min(2, len(strong_stab), num_to_add)
                selected_moves.extend(strong_stab[:stab_count])
            else:
                # BP 70 미만인 STAB 기술도 1개 추가
                stab_count = min(1, len(type_moves), num_to_add)
                selected_moves.extend(random.sample(type_moves, stab_count))
        
        # 2. 강한 상성 극복 기술 (순위 80+ > 60-79)
        if len(selected_moves) < num_to_add:
            remaining = num_to_add - len(selected_moves)
            
            # 먼저 강한 상성 극복 기술 추가
            if strong_coverage:
                strong_count = min(remaining, len(strong_coverage))
                selected_moves.extend(random.sample(strong_coverage, strong_count))
                remaining -= strong_count
            
            # 그 다음 중간 강도 상성 극복 기술
            if remaining > 0 and medium_coverage:
                medium_count = min(remaining, len(medium_coverage))
                selected_moves.extend(random.sample(medium_coverage, medium_count))
                remaining -= medium_count
            
            # 약한 상성 극복 기술
            if remaining > 0 and weak_coverage:
                weak_count = min(remaining, len(weak_coverage))
                selected_moves.extend(random.sample(weak_coverage, weak_count))
                remaining -= weak_count
            
            # 여전히 부족하면 상태 기술이라도 추가 (마지막 수단)
            if remaining > 0 and status_moves:
                status_count = min(remaining, len(status_moves))
                selected_moves.extend(random.sample(status_moves, status_count))
        
        # SimplifiedMove로 변환
        for move_id, move_data in selected_moves[:num_to_add]:
            move = self._create_move_from_pokedex(move_id, move_data)
            if move:
                moves.append(move)
        
        # 최종 확인: 기술이 4개보다 적으면 tackle 추가
        while len(moves) < num_to_add:
            tackle_data = data.moves.get('tackle', {'basePower': 40, 'type': 'Normal', 'category': 'Physical'})
            tackle_move = self._create_move_from_pokedex('tackle', tackle_data)
            if tackle_move:
                moves.append(tackle_move)
            else:
                break
        
        return moves
    
    def _create_move_from_pokedex(self, move_id: str, move_data: dict):
        """pokedex 데이터에서 기술 객체 생성"""
        from poke_env.battle.pokemon_type import PokemonType
        from poke_env.battle.move_category import MoveCategory
        
        # 기술 데이터 추출
        base_power = move_data.get('basePower', 0)
        accuracy = move_data.get('accuracy', 100)
        category = move_data.get('category', 'Physical')
        move_type = move_data.get('type', 'Normal')
        priority = move_data.get('priority', 0)
        
        # 타입 변환
        try:
            move_type_enum = PokemonType[move_type.upper()]
        except (KeyError, AttributeError):
            move_type_enum = PokemonType.NORMAL
        
        # 카테고리 변환
        try:
            category_enum = MoveCategory[category.upper()]
        except (KeyError, AttributeError):
            category_enum = MoveCategory.PHYSICAL
        
        class DummyMove:
            def __init__(self):
                self.id = move_id
                self.base_power = base_power if base_power else 0
                self.type = move_type_enum
                self.category = category_enum
                self.accuracy = accuracy if accuracy else 100
                self.priority = priority if priority else 0
                self.current_pp = 16
                self.max_pp = 16
                self.boosts = None
                self.self_boost = None
                self.status = None
                self.secondary = None
                self.crit_ratio = 0
                self.expected_hits = 1
                self.recoil = 0
                self.drain = 0
                self.flags = set()
                self.breaks_protect = False
                self.is_protect_move = False
        
        return SimplifiedMove(DummyMove())
        
    def _create_move_from_pokedex(self, move_id: str, move_data: dict):
        """pokedex 데이터에서 기술 객체 생성"""
        from poke_env.battle.pokemon_type import PokemonType
        from poke_env.battle.move_category import MoveCategory
        from poke_env.battle.status import Status  # 상태이상 Enum 필요
        
        # 1. 기술 데이터 추출
        base_power = move_data.get('basePower', 0)
        accuracy = move_data.get('accuracy', 100)
        category = move_data.get('category', 'Physical')
        move_type = move_data.get('type', 'Normal')
        priority = move_data.get('priority', 0)
        
        # 추가 데이터 추출
        recoil_data = move_data.get('recoil', None)      # 반동 [분자, 분모]
        drain_data = move_data.get('drain', None)        # 흡수 [분자, 분모]
        boosts_data = move_data.get('boosts', None)      # 상대 랭크 다운
        self_boost_data = move_data.get('selfBoost', None) # 자신 랭크 업
        status_str = move_data.get('status', None)       # 상태이상 (문자열)
        crit_ratio = move_data.get('critRatio', 0)       # 급소율
        flags_data = move_data.get('flags', {})          # 기술 플래그 (charge, recharge 등)
        secondary_data = move_data.get('secondary', None) # 부가 효과

        # 2. 타입 변환 (문자열 -> Enum)
        try:
            move_type_enum = PokemonType[move_type.upper()]
        except (KeyError, AttributeError):
            move_type_enum = PokemonType.NORMAL
        
        # 3. 카테고리 변환 (문자열 -> Enum)
        try:
            category_enum = MoveCategory[category.upper()]
        except (KeyError, AttributeError):
            category_enum = MoveCategory.PHYSICAL

        # 4. 상태이상 변환 (문자열 -> Enum)
        status_enum = None
        if status_str:
            try:
                status_enum = Status[status_str.upper()]
            except (KeyError, AttributeError):
                status_enum = None

        # 5. 더미 무브 클래스 정의
        class DummyMove:
            def __init__(self):
                self.id = move_id
                self.base_power = base_power if base_power else 0
                self.type = move_type_enum
                self.category = category_enum
                
                # Accuracy 정규화 (0~1.0)
                if accuracy is None or accuracy is True:
                    self.accuracy = 1.0
                elif isinstance(accuracy, int) or isinstance(accuracy, float):
                    if accuracy > 1: 
                        self.accuracy = accuracy / 100.0 
                    else: 
                        self.accuracy = accuracy
                else:
                    self.accuracy = 1.0

                self.priority = priority
                self.current_pp = 16
                self.max_pp = 16
                
                # [수정] 데이터 할당
                self.recoil = recoil_data
                self.drain = drain_data
                self.boosts = boosts_data
                self.self_boost = self_boost_data
                self.status = status_enum
                self.secondary = secondary_data
                self.crit_ratio = crit_ratio
                self.expected_hits = 1
                
                # [중요] Flags 처리 (dict_keys -> set)
                self.flags = set(flags_data.keys())
                
                self.breaks_protect = False
                self.is_protect_move = False
    
        return SimplifiedMove(DummyMove())

    def print_summary(self):
        print(f"=== SimplifiedBattle Summary ===")
        print(f"Turn: {self.turn}, Gen: {self.gen}, Finished: {self.finished}, Won: {self.won}")
        print(f"\n--- Team ---")
        for id, p in self.team.items():
            status = f"(기절)" if p.current_hp <= 0 else f"(HP: {p.current_hp}/{p.max_hp})"
            print(f"{id}: {p.species} {status}")
        print(f"\n--- Opponent Team ---")
        for id, p in self.opponent_team.items():
            status = f"(기절)" if p.current_hp <= 0 else f"(HP: {p.current_hp}/{p.max_hp})"
            print(f"{id}: {p.species} {status}")
        if self.active_pokemon:
            print(f"\nActive Pokemon: {self.active_pokemon.species} (HP: {self.active_pokemon.current_hp}/{self.active_pokemon.max_hp})")
            for move in self.active_pokemon.moves:
                print(f" - Move: {move.id} (Power: {move.base_power}, Type: {move.type.name})")
        if self.opponent_active_pokemon:
            print(f"Opponent Active Pokemon: {self.opponent_active_pokemon.species} (HP: {self.opponent_active_pokemon.current_hp}/{self.opponent_active_pokemon.max_hp})")
            for move in self.opponent_active_pokemon.moves:
                print(f" - Move: {move.id} (Power: {move.base_power}, Type: {move.type.name})")
        print(f"\n--- Field Effects ---")
        print(f"Weather: {self.weather}")
        print(f"Fields: {self.fields}")
        print(f"Side Conditions: {self.side_conditions}")
        print(f"Opponent Side Conditions: {self.opponent_side_conditions}")
        print(f"\n--- Available Actions ---")
        print(f"Available Moves: {[move.id for move in self.available_moves]}")
        print(f"Available Switches: {[poke.species for poke in self.available_switches]}")
    
    def get_alive_team(self):
        """살아있는 팀 포켓몬 반환 (Dict)"""
        return {id: p for id, p in self.team.items() if p.current_hp > 0}
    
    def get_alive_opponent_team(self):
        """살아있는 상대 팀 포켓몬 반환 (Dict)"""
        return {id: p for id, p in self.opponent_team.items() if p.current_hp > 0}
    
    def get_alive_count(self, is_player: bool = True):
        """살아있는 포켓몬 개수"""
        team = self.team if is_player else self.opponent_team
        return sum(1 for p in team.values() if p.current_hp > 0)
    
    def get_fainted_count(self, is_player: bool = True):
        """기절한 포켓몬 개수"""
        team = self.team if is_player else self.opponent_team
        return sum(1 for p in team.values() if p.current_hp <= 0)
    
    def clone(self):
        """
        [성능 최적화] Battle 객체 고속 복제
        deepcopy보다 5~10배 빠르며, 불필요한 poke-env 데이터 연동을 생략함.
        """
        # 1. 빈 객체 생성 (__init__ 건너뜀)
        new_battle = SimplifiedBattle.__new__(SimplifiedBattle)

        # 2. 기본 정보 복사
        new_battle.turn = self.turn
        new_battle.gen = self.gen
        new_battle.finished = self.finished
        new_battle.won = self.won
        new_battle.lost = self.lost

        # 3. 필드 효과 복사 (딕셔너리 얕은 복사)
        new_battle.weather = self.weather.copy()
        new_battle.fields = self.fields.copy()
        new_battle.side_conditions = self.side_conditions.copy()
        new_battle.opponent_side_conditions = self.opponent_side_conditions.copy()

        # 4. 팀 복제 (핵심: 내부 포켓몬들도 clone 수행)
        new_battle.team = {id: p.clone() for id, p in self.team.items()}
        new_battle.opponent_team = {id: p.clone() for id, p in self.opponent_team.items()}

        # 5. 활성 포켓몬(Active Pokemon) 연결
        # 단순히 clone()하면 team 딕셔너리에 있는 객체와 다른 객체가 되어버림.
        # 따라서 team 딕셔너리 안에 있는 '그 포켓몬'을 가리키도록 연결해줘야 함.
        
        # 5-1. 내 활성 포켓몬 연결
        new_battle.active_pokemon = None
        if self.active_pokemon:
            # 기존 팀에서 현재 활성 포켓몬의 ID(key)를 찾음
            active_id = None
            for id, p in self.team.items():
                # 객체 주소 비교(is)가 가장 확실하지만, 
                # 원본에서 객체가 분리되어 있을 수 있으므로 species로 2차 확인
                if p is self.active_pokemon or p.species == self.active_pokemon.species:
                    active_id = id
                    break
            
            if active_id and active_id in new_battle.team:
                new_battle.active_pokemon = new_battle.team[active_id]
            else:
                # 만약 못 찾으면 어쩔 수 없이 단독 복제 (Fallback)
                new_battle.active_pokemon = self.active_pokemon.clone()

        # 5-2. 상대 활성 포켓몬 연결
        new_battle.opponent_active_pokemon = None
        if self.opponent_active_pokemon:
            op_active_id = None
            for id, p in self.opponent_team.items():
                if p is self.opponent_active_pokemon or p.species == self.opponent_active_pokemon.species:
                    op_active_id = id
                    break
            
            if op_active_id and op_active_id in new_battle.opponent_team:
                new_battle.opponent_active_pokemon = new_battle.opponent_team[op_active_id]
            else:
                new_battle.opponent_active_pokemon = self.opponent_active_pokemon.clone()

        # 6. 사용 가능한 기술 복제 (Move는 불변에 가까우므로 리스트 컴프리헨션)
        new_battle.available_moves = [m.clone() for m in self.available_moves]

        # 7. 교체 가능 포켓몬 연결
        # 이것도 active_pokemon처럼 new_battle.team 안의 객체를 가리켜야 함
        new_battle.available_switches = []
        for switch_poke in self.available_switches:
            # 이름(species)이 같은 포켓몬을 새 팀에서 찾아서 추가
            for p in new_battle.team.values():
                if p.species == switch_poke.species:
                    new_battle.available_switches.append(p)
                    break
                    
        return new_battle