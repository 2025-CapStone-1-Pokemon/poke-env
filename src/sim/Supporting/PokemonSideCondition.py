# PokemonSideCondition.py
# 포켓몬 배틀에서의 사이드 컨디션을 나타내는 열거형 클래스 정의

from enum import Enum, auto, unique

@unique
class SideCondition(Enum):
    """Enumeration, represent a in-battle side condition."""

    UNKNOWN = auto()
    AURORA_VEIL = auto()
    CRAFTY_SHIELD = auto()
    FIRE_PLEDGE = auto()
    G_MAX_CANNONADE = auto()
    G_MAX_STEELSURGE = auto()
    G_MAX_VINE_LASH = auto()
    G_MAX_VOLCALITH = auto()
    G_MAX_WILDFIRE = auto()
    GRASS_PLEDGE = auto()
    LIGHT_SCREEN = auto()
    LUCKY_CHANT = auto()
    MATBLOCK = auto()
    MIST = auto()
    QUICK_GUARD = auto()
    REFLECT = auto()
    SAFEGUARD = auto()
    SPIKES = auto()
    STEALTH_ROCK = auto()
    STICKY_WEB = auto()
    TAILWIND = auto()
    TOXIC_SPIKES = auto()
    WATER_PLEDGE = auto()
    WIDE_GUARD = auto()

    def __str__(self) -> str:
        return f"{self.name} (side condition) object"