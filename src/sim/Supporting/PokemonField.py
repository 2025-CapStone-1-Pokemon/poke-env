# PokemonField.py
# 포켓몬 배틀에서의 필드를 나타내는 열거형 클래스입니다.

from enum import Enum, auto, unique

@unique
class Field(Enum):
    """Enumeration, represent a non null field in a battle."""

    UNKNOWN = auto()
    ELECTRIC_TERRAIN = auto()
    GRASSY_TERRAIN = auto()
    GRAVITY = auto()
    HEAL_BLOCK = auto()
    MAGIC_ROOM = auto()
    MISTY_TERRAIN = auto()
    MUD_SPORT = auto()
    MUD_SPOT = auto()
    PSYCHIC_TERRAIN = auto()
    TRICK_ROOM = auto()
    WATER_SPORT = auto()
    WONDER_ROOM = auto()

    def __str__(self) -> str:
        return f"{self.name} (field) object"