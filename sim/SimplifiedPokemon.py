import copy
from typing import Optional, Tuple, Dict
from poke_env.battle.pokemon import Pokemon
# 포켓몬 타입 객체
from poke_env.battle.pokemon_type import PokemonType
# 포켓몬 기술 객체
from poke_env.battle.move import SPECIAL_MOVES, Move
# 포켓몬 성별 객체
from poke_env.battle.pokemon_gender import PokemonGender

# 포켓몬 객체
class SimplifiedPokemon:

    # poke_env에 있는 Pokemon 객체를 통해서 만듬
    def __init__(self, poke_env_pokemon: Pokemon):
        # 기본 정보
        self.species = poke_env_pokemon.species
        self.level = poke_env_pokemon.level
        self.gender: PokemonGender = poke_env_pokemon.gender

        # HP 관련
        self.current_hp: int = poke_env_pokemon.current_hp or 0
        self.max_hp: int = poke_env_pokemon.max_hp or 0
        self.current_hp_fraction: float = poke_env_pokemon.current_hp_fraction
        self.fainted: bool = poke_env_pokemon.fainted

        # 상태
        self.status: Optional[str] = poke_env_pokemon.status.name if poke_env_pokemon.status else None
        self.active: bool = poke_env_pokemon.active

        # 특성 및 아이템
        self.ability: Optional[str] = poke_env_pokemon.ability
        self.item: Optional[str] = poke_env_pokemon.item

        # 타입
        self.types: Tuple[PokemonType, ...] = poke_env_pokemon.types

        # 스탯
        self.stats: Dict[str, int] = poke_env_pokemon.stats.copy() if poke_env_pokemon.stats else {}
        self.base_stats: Dict[str, int] = poke_env_pokemon.base_stats.copy() if poke_env_pokemon.base_stats else {}

        # 능력치 변화
        self.boosts: Dict[str, int] = poke_env_pokemon.boosts.copy()

        # 기술
        self.moves: Dict[str, Move] = copy.deepcopy(poke_env_pokemon.moves)

        # 효과
        self.effects: Dict = poke_env_pokemon.effects.copy()

    # 메서드
    def switch_in(self, details: str) -> None:       # 교체 들어올 때
        pass

    def switch_out(self) -> None:                     # 교체 나갈 때
        pass

    def set_hp_status(self, hp_status: str) -> None: # HP 상태 설정
        pass

    def clear_boosts(self) -> None:                   # 능력치 변화 초기화
        pass

    def available_moves_from_request(self, request) -> None:  # 요청에서 사용 가능한 기술 파싱
        pass