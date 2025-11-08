# PokemonWeather.py
# 필드에서 날씨를 나타내는 열거형 정의


from enum import Enum, auto

class Weather(Enum):
    """Enumeration, represent a non null weather in a battle."""

    UNKNOWN = auto()
    DESOLATELAND = auto()
    DELTASTREAM = auto()
    HAIL = auto()
    PRIMORDIALSEA = auto()
    RAINDANCE = auto()
    SANDSTORM = auto()
    SNOWSCAPE = SNOW = auto()
    SUNNYDAY = auto()

    def __str__(self) -> str:
        return f"{self.name} (weather) object"