# PokemonMoveCategory.py
# 포켓몬의 기술 분류를 나타내는 열거형입니다.

from enum import Enum, auto, unique

@unique
class MoveCategory(Enum):
    """Enumeration, represent a move category."""

    PHYSICAL = auto()
    SPECIAL = auto()
    STATUS = auto()

    def __str__(self) -> str:
        return f"{self.name} (move category) object"
