from poke_env.battle import Battle
from SimplifiedPokemon import SimplifiedPokemon
import random

# TODO 포켓몬 유추하기
class SimplifiedBattle:
    def __init__(self, poke_env_battle: Battle, fill_unknown_data: bool = True):
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
        """상대 팀의 부족한 정보를 랜덤으로 채우기"""
        from poke_env.battle.pokemon_type import PokemonType
        from poke_env.battle.move_category import MoveCategory
        from SimplifiedMove import SimplifiedMove
        
        # 1. 기존 공개된 포켓몬의 기술이 없으면 랜덤 기술 생성
        for pokemon_id, pokemon in self.opponent_team.items():
            if not pokemon.moves or len(pokemon.moves) == 0:
                pokemon.moves = self._generate_random_moves(pokemon)
            # 스탯이 없으면 기본값으로 설정
            if pokemon.stats is None or not pokemon.stats or any(v is None for v in pokemon.stats.values()):
                pokemon.stats = {
                    'hp': pokemon.max_hp,
                    'atk': 150,
                    'def': 150,
                    'spa': 150,
                    'spd': 150,
                    'spe': 150
                }
        
        # 2. 상대 팀이 6마리 미만이면 미공개 포켓몬을 랜덤으로 추가
        if len(self.opponent_team) < 6:
            # 일반적인 랜덤 배틀 포켓몬 풀 (간단한 예시)
            common_pokemon = [
                ('pikachu', PokemonType.ELECTRIC, 250),
                ('charizard', PokemonType.FIRE, 266),
                ('blastoise', PokemonType.WATER, 268),
                ('venusaur', PokemonType.GRASS, 270),
                ('gengar', PokemonType.GHOST, 230),
                ('machamp', PokemonType.FIGHTING, 280),
                ('alakazam', PokemonType.PSYCHIC, 220),
                ('dragonite', PokemonType.DRAGON, 281),
                ('gyarados', PokemonType.WATER, 291),
                ('snorlax', PokemonType.NORMAL, 380),
            ]
            
            # 이미 존재하는 포켓몬 이름 확인
            existing_species = {p.species.lower() for p in self.opponent_team.values()}
            
            # 중복되지 않는 포켓몬만 추가
            available_pokemon = [p for p in common_pokemon if p[0] not in existing_species]
            
            num_to_add = 6 - len(self.opponent_team)
            for i in range(num_to_add):
                if not available_pokemon:
                    # 더 이상 추가할 포켓몬이 없으면 중단
                    break
                species, ptype, hp = random.choice(available_pokemon)
                available_pokemon.remove((species, ptype, hp))  # 선택한 포켓몬 제거
                
                dummy_id = f"p2: {species}{i}"
                dummy_pokemon = self._create_dummy_pokemon(species, ptype, hp)
                # 더미 포켓몬에 기술 생성
                dummy_pokemon.moves = self._generate_random_moves(dummy_pokemon)
                self.opponent_team[dummy_id] = dummy_pokemon
    
    def _create_dummy_pokemon(self, species: str, ptype, max_hp: int):
        """더미 포켓몬 생성"""
        from poke_env.battle.move_category import MoveCategory
        
        class DummyPokemon:
            def __init__(self):
                self.species = species
                self.level = 50
                self.gender = None
                self.type_1 = ptype
                self.type_2 = None
                self.types = [ptype]
                self.current_hp = max_hp  # 풀 HP로 시작 (아직 등장하지 않았지만 살아있음)
                self.max_hp = max_hp
                self.status = None
                self.status_counter = 0
                self.base_stats = {'hp': 100, 'atk': 100, 'def': 100, 'spa': 100, 'spd': 100, 'spe': 100}
                self.stats = {'hp': max_hp, 'atk': 150, 'def': 150, 'spa': 150, 'spd': 150, 'spe': 150}
                self.boosts = {}
                self.moves = {}  # 빈 딕셔너리로 초기화
                self.ability = None
                self.item = None
                self.effects = set()
                self.active = False
                self.first_turn = False
                self.must_recharge = False
                self.protect_counter = 0
        
        return SimplifiedPokemon(DummyPokemon())
    
    def _generate_random_moves(self, pokemon):
        """포켓몬에 맞는 랜덤 기술 4개 생성"""
        from poke_env.battle.move_category import MoveCategory
        from SimplifiedMove import SimplifiedMove
        
        # 타입에 맞는 기본 기술들
        type_moves = {
            'NORMAL': [('tackle', 40, MoveCategory.PHYSICAL), ('body-slam', 85, MoveCategory.PHYSICAL)],
            'FIRE': [('flamethrower', 90, MoveCategory.SPECIAL), ('fire-blast', 110, MoveCategory.SPECIAL)],
            'WATER': [('surf', 90, MoveCategory.SPECIAL), ('hydro-pump', 110, MoveCategory.SPECIAL)],
            'ELECTRIC': [('thunderbolt', 90, MoveCategory.SPECIAL), ('thunder', 110, MoveCategory.SPECIAL)],
            'GRASS': [('energy-ball', 90, MoveCategory.SPECIAL), ('solar-beam', 120, MoveCategory.SPECIAL)],
            'ICE': [('ice-beam', 90, MoveCategory.SPECIAL), ('blizzard', 110, MoveCategory.SPECIAL)],
            'FIGHTING': [('close-combat', 120, MoveCategory.PHYSICAL), ('brick-break', 75, MoveCategory.PHYSICAL)],
            'POISON': [('sludge-bomb', 90, MoveCategory.SPECIAL), ('gunk-shot', 120, MoveCategory.PHYSICAL)],
            'GROUND': [('earthquake', 100, MoveCategory.PHYSICAL), ('earth-power', 90, MoveCategory.SPECIAL)],
            'FLYING': [('air-slash', 75, MoveCategory.SPECIAL), ('brave-bird', 120, MoveCategory.PHYSICAL)],
            'PSYCHIC': [('psychic', 90, MoveCategory.SPECIAL), ('psyshock', 80, MoveCategory.SPECIAL)],
            'BUG': [('bug-buzz', 90, MoveCategory.SPECIAL), ('x-scissor', 80, MoveCategory.PHYSICAL)],
            'ROCK': [('stone-edge', 100, MoveCategory.PHYSICAL), ('rock-slide', 75, MoveCategory.PHYSICAL)],
            'GHOST': [('shadow-ball', 80, MoveCategory.SPECIAL), ('phantom-force', 90, MoveCategory.PHYSICAL)],
            'DRAGON': [('draco-meteor', 130, MoveCategory.SPECIAL), ('outrage', 120, MoveCategory.PHYSICAL)],
            'DARK': [('dark-pulse', 80, MoveCategory.SPECIAL), ('knock-off', 65, MoveCategory.PHYSICAL)],
            'STEEL': [('flash-cannon', 80, MoveCategory.SPECIAL), ('iron-head', 80, MoveCategory.PHYSICAL)],
            'FAIRY': [('moonblast', 95, MoveCategory.SPECIAL), ('play-rough', 90, MoveCategory.PHYSICAL)],
        }
        
        moves = []
        ptype_name = pokemon.type_1.name if pokemon.type_1 else 'NORMAL'
        
        # 타입에 맞는 기술 2개 선택
        if ptype_name in type_moves:
            for move_data in random.sample(type_moves[ptype_name], min(2, len(type_moves[ptype_name]))):
                moves.append(self._create_move(move_data[0], move_data[1], pokemon.type_1, move_data[2]))
        
        # 나머지는 노말 타입 기술로 채우기
        while len(moves) < 4:
            from poke_env.battle.pokemon_type import PokemonType
            moves.append(self._create_move('tackle', 40, PokemonType.NORMAL, MoveCategory.PHYSICAL))
        
        return moves
    
    def _create_move(self, move_id: str, base_power: int, move_type, category):
        """기술 객체 생성"""
        from SimplifiedMove import SimplifiedMove
        
        class DummyMove:
            def __init__(self):
                self.id = move_id
                self.base_power = base_power
                self.type = move_type
                self.category = category
                self.accuracy = 100
                self.priority = 0
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