# PokemonStatus.py
# 포켓몬 상태 관련 클래스 정의

from enum import Enum, auto, unique

@unique
class Status(Enum):
    """Enumeration, represent a status a pokemon can be afflicted with."""

    BRN = auto()
    FNT = auto()
    FRZ = auto()
    PAR = auto()
    PSN = auto()
    SLP = auto()
    TOX = auto()

    def __str__(self) -> str:
        return f"{self.name} (status) object"