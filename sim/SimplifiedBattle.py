from poke_env.battle import Battle
from typing import Dict
from SimplifiedPokemon import SimplifiedPokemon
from SimplifiedMove import SimplifiedMove
import random

# 기본 기술 개수
DEFAULT_MOVES = 4

class SimplifiedBattle:
    def __init__(self, poke_env_battle: Battle, fill_unknown_data: bool = True, gen : int = 9):
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
            self._fill_opponent_team_data()

        # === 활성 포켓몬 ===
        self.active_pokemon = (
            SimplifiedPokemon(poke_env_battle.active_pokemon)
            if poke_env_battle.active_pokemon else None
        )
        self.opponent_active_pokemon = (
            SimplifiedPokemon(poke_env_battle.opponent_active_pokemon)
            if poke_env_battle.opponent_active_pokemon else None
        )

        # === 필드 효과 ===
        self.weather = poke_env_battle.weather.copy()
        self.fields = poke_env_battle.fields.copy()
        self.side_conditions = poke_env_battle.side_conditions.copy()
        self.opponent_side_conditions = poke_env_battle.opponent_side_conditions.copy()

        # === 턴 관련 ===
        self.available_moves = list(poke_env_battle.available_moves) if hasattr(poke_env_battle, 'available_moves') else []
        self.available_switches = list(poke_env_battle.available_switches) if hasattr(poke_env_battle, 'available_switches') else []
    
    def _fill_opponent_team_data(self):
        """상대 팀의 부족한 정보를 pokedex 데이터 기반으로 채우기"""
        from poke_env.data import GenData
        
        data = GenData.from_gen(self.gen)
        
        # 1. 기존 공개된 포켓몬의 기술이 없으면 랜덤 기술 생성
        for pokemon_id, pokemon in self.opponent_team.items():
            if not pokemon.moves or len(pokemon.moves) == 0:
                # 부족한 기술 개수만큼 채우기
                pokemon.moves = self._generate_random_moves(pokemon, DEFAULT_MOVES - len(pokemon.moves))
        
        # 2. 상대 팀이 6마리 미만이면 미공개 포켓몬을 랜덤으로 추가
        if len(self.opponent_team) < 6:
            # 이미 존재하는 포켓몬 종류 확인
            existing_species = {p.species.lower() for p in self.opponent_team.values()}
            
            # 추가할 포켓몬 개수
            num_to_add = 6 - len(self.opponent_team)
            
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
        """랜덤 포켓몬 생성 리스트"""

        # Dict[str, Any] 의 형태임
        from poke_env.data import GenData
        data = GenData.from_gen(self.gen)

        # TODO 베이즈 추론등을 활용하여, 공개된 포켓몬으로 추정 가능한 포켓몬 생성하기

        # 개수 만큼 생성
        pokemon_list = []

        possible_species_name = [
                species for species in data.pokedex.keys()
                if species not in exisiting_species
            ]

        for _ in range(num_to_add):
            # 중복되지 않는 포켓몬 선택
            random_species = random.choice(possible_species_name)
            pokemon_list.append(self._create_dummy_pokemon(data.pokedex[random_species]))
        
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
        
        # 기본 정보
        dummy_pokemon.species = pokedex_data.get('baseSpecies', species).lower()
        dummy_pokemon.level = 50  # 기본 레벨 50
        dummy_pokemon.gender = None
        
        # 타입 설정
        types_list = pokedex_data.get('types', [])
        type_1_str = types_list[0].upper() if types_list else 'NORMAL'
        type_2_str = types_list[1].upper() if len(types_list) > 1 else None
        
        dummy_pokemon.type_1 = PokemonType[type_1_str] if type_1_str else PokemonType.NORMAL
        dummy_pokemon.type_2 = PokemonType[type_2_str] if type_2_str else None
        dummy_pokemon.types = [PokemonType[t.upper()] for t in types_list] if types_list else [PokemonType.NORMAL]
        
        # HP 설정
        base_stats = pokedex_data.get('baseStats', {'hp': 100, 'atk': 100, 'def': 100, 'spa': 100, 'spd': 100, 'spe': 100})
        base_hp = base_stats.get('hp', 100)
        dummy_pokemon.max_hp = int(((base_hp * 2 + 31 + 85) * 50) / 100) + 50 + 10
        dummy_pokemon.current_hp = dummy_pokemon.max_hp
        
        # 상태이상
        dummy_pokemon.status = None
        dummy_pokemon.status_counter = 0
        
        # 스탯 설정
        dummy_pokemon.base_stats = base_stats.copy()
        dummy_pokemon.stats = {}
        for stat_name, base in dummy_pokemon.base_stats.items():
            if stat_name == 'hp':
                dummy_pokemon.stats[stat_name] = int(((base * 2 + 31 + 85) * 50) / 100) + 50 + 10
            else:
                dummy_pokemon.stats[stat_name] = int(((base * 2 + 31 + 5) * 50) / 100) + 5
        
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
        """포켓몬에 맞는 랜덤 기술 생성 (실제 pokedex 데이터 사용)"""
        from poke_env.data import GenData
        from poke_env.battle.pokemon_type import PokemonType
        
        data = GenData.from_gen(self.gen)
        moves = []
        
        # 포켓몬 타입과 일치하는 기술들 필터링
        type_moves = []
        normal_moves = []
        
        for move_id, move_data in data.moves.items():
            move_type = move_data.get('type', 'Normal')
            base_power = move_data.get('basePower', 0)
            
            # 위력이 있는 기술만 선택 (상태 기술 제외)
            if base_power > 0:
                if move_type == pokemon.type_1.name.upper() or move_type == (pokemon.type_2.name.upper() if pokemon.type_2 else None):
                    type_moves.append((move_id, move_data))
                elif move_type == 'Normal':
                    normal_moves.append((move_id, move_data))
        
        # 기술 선택 우선순위
        selected_moves = []
        
        # 1. 타입 기술 우선
        if type_moves:
            selected_moves.extend(random.sample(type_moves, min(2, len(type_moves), num_to_add - len(selected_moves))))
        
        # 2. 일반 기술로 채우기
        if len(selected_moves) < num_to_add and normal_moves:
            remaining = num_to_add - len(selected_moves)
            selected_moves.extend(random.sample(normal_moves, min(remaining, len(normal_moves))))
        
        # 3. 여전히 부족하면 모든 기술에서 선택
        if len(selected_moves) < num_to_add:
            all_moves = list(data.moves.items())
            remaining = num_to_add - len(selected_moves)
            selected_moves.extend(random.sample(all_moves, min(remaining, len(all_moves))))
        
        # SimplifiedMove로 변환
        for move_id, move_data in selected_moves[:num_to_add]:
            move = self._create_move_from_pokedex(move_id, move_data)
            moves.append(move)
        
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
        except KeyError:
            move_type_enum = PokemonType.NORMAL
        
        # 카테고리 변환
        try:
            category_enum = MoveCategory[category.upper()]
        except KeyError:
            category_enum = MoveCategory.PHYSICAL
        
        class DummyMove:
            def __init__(self):
                self.id = move_id
                self.base_power = base_power if base_power else 0
                self.type = move_type_enum
                self.category = category_enum
                self.accuracy = accuracy if accuracy else 100
                self.priority = priority
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

    def print_summary(self):
        print(f"=== SimplifiedBattle Summary ===")
        print(f"Turn: {self.turn}, Gen: {self.gen}, Finished: {self.finished}, Won: {self.won}")
        print(f"\n--- Team ---")
        for id, p in self.team.items():
            print(f"{id}: {p.species} (HP: {p.current_hp}/{p.max_hp})")
        print(f"\n--- Opponent Team ---")
        for id, p in self.opponent_team.items():
            print(f"{id}: {p.species} (HP: {p.current_hp}/{p.max_hp})")
        if self.active_pokemon:
            print(f"\nActive Pokemon: {self.active_pokemon.species} (HP: {self.active_pokemon.current_hp}/{self.active_pokemon.max_hp})")
        if self.opponent_active_pokemon:
            print(f"Opponent Active Pokemon: {self.opponent_active_pokemon.species} (HP: {self.opponent_active_pokemon.current_hp}/{self.opponent_active_pokemon.max_hp})")
        print(f"\n--- Field Effects ---")
        print(f"Weather: {self.weather}")
        print(f"Fields: {self.fields}")
        print(f"Side Conditions: {self.side_conditions}")
        print(f"Opponent Side Conditions: {self.opponent_side_conditions}")
        print(f"\n--- Available Actions ---")
        print(f"Available Moves: {[move._id for move in self.available_moves]}")
        print(f"Available Switches: {[poke.species for poke in self.available_switches]}")