# Python Enum 타입 완벽 가이드

Poke-env에서 사용되는 Enum 타입들(`PokemonType`, `PokemonGender`, `Status` 등)을 이해하고 활용하는 방법을 설명합니다.

---

## 📚 목차

1. [Enum이란?](#enum이란)
2. [PokemonType 구조 분석](#pokemontype-구조-분석)
3. [Enum 출력 형태 이해하기](#enum-출력-형태-이해하기)
4. [Enum 활용 방법](#enum-활용-방법)
5. [SimplifiedPokemon에서 사용하기](#simplifiedpokemon에서-사용하기)
6. [실전 예제](#실전-예제)

---

## Enum이란?

**Enum (Enumeration, 열거형)**은 관련된 상수들을 그룹으로 묶어서 관리하는 데이터 타입입니다.

### C/Java와 비교

**Java:**

```java
public enum PokemonType {
    FIRE,
    WATER,
    GRASS
}

PokemonType type = PokemonType.FIRE;
```

**Python:**

```python
from enum import Enum, auto

class PokemonType(Enum):
    FIRE = auto()    # 자동으로 1
    WATER = auto()   # 자동으로 2
    GRASS = auto()   # 자동으로 3

type = PokemonType.FIRE
```

---

## PokemonType 구조 분석

### 기본 구조

```python
from enum import Enum, auto, unique

@unique  # 중복된 값 방지
class PokemonType(Enum):
    """포켓몬 타입을 나타내는 열거형"""

    # auto()는 자동으로 1, 2, 3... 값 할당
    BUG = auto()       # 1
    DARK = auto()      # 2
    DRAGON = auto()    # 3
    ELECTRIC = auto()  # 4
    FAIRY = auto()     # 5
    FIGHTING = auto()  # 6
    FIRE = auto()      # 7
    FLYING = auto()    # 8
    GHOST = auto()     # 9
    GRASS = auto()     # 10
    GROUND = auto()    # 11
    ICE = auto()       # 12
    NORMAL = auto()    # 13
    POISON = auto()    # 14
    PSYCHIC = auto()   # 15
    ROCK = auto()      # 16
    STEEL = auto()     # 17
    WATER = auto()     # 18
```

### 주요 속성

```python
pokemon_type = PokemonType.STEEL

# 속성 접근
print(pokemon_type.name)   # "STEEL" (문자열)
print(pokemon_type.value)  # 17 (정수)
```

---

## Enum 출력 형태 이해하기

### 기본 출력

```python
from poke_env.battle.pokemon_type import PokemonType

type1 = PokemonType.STEEL
type2 = PokemonType.DRAGON

print(type1)              # PokemonType.STEEL
print(repr(type1))        # <PokemonType.STEEL: 17>
print([type1, type2])     # [<PokemonType.STEEL: 17>, <PokemonType.DRAGON: 3>]
```

### 출력 형태 분석

```
[<PokemonType.STEEL: 17>, <PokemonType.DRAGON: 3>]
  └────────┬─────────┘     └────────┬──────────┘
      첫 번째 타입              두 번째 타입

<PokemonType.STEEL: 17>
 └────┬─────┘ └──┬─┘ └┬┘
  클래스명    이름  값
```

| 구성 요소     | 의미        | 접근 방법   |
| ------------- | ----------- | ----------- |
| `PokemonType` | 클래스 이름 | `type(obj)` |
| `STEEL`       | Enum 이름   | `.name`     |
| `17`          | Enum 값     | `.value`    |

---

## Enum 활용 방법

### 1️⃣ 비교 연산

```python
# ✅ Enum 객체 비교 (권장)
if pokemon.type_1 == PokemonType.FIRE:
    print("불꽃 타입!")

# ✅ 여러 타입 체크
if pokemon.type_1 in [PokemonType.FIRE, PokemonType.WATER]:
    print("불 또는 물 타입")

# ✅ 타입 포함 여부
if PokemonType.DRAGON in pokemon.types:
    print("드래곤 타입 포함")

# ❌ 문자열 비교 (비권장)
if pokemon.type_1.name == "FIRE":  # 동작하지만 타입 안전하지 않음
    print("불꽃 타입")
```

### 2️⃣ 예쁜 출력

```python
types = [PokemonType.STEEL, PokemonType.DRAGON]

# ❌ 기본 출력 (읽기 어려움)
print(f"타입: {types}")
# 타입: [<PokemonType.STEEL: 17>, <PokemonType.DRAGON: 3>]

# ✅ 이름만 출력
print(f"타입: {[t.name for t in types]}")
# 타입: ['STEEL', 'DRAGON']

# ✅ 쉼표로 연결
print(f"타입: {', '.join(t.name for t in types)}")
# 타입: STEEL, DRAGON

# ✅ 슬래시로 연결 (포켓몬 표기법)
print(f"타입: {'/'.join(t.name for t in types)}")
# 타입: STEEL/DRAGON
```

### 3️⃣ 이름 ↔ Enum 변환

```python
# 문자열 → Enum
type_name = "FIRE"
pokemon_type = PokemonType[type_name]  # PokemonType.FIRE

# Enum → 문자열
pokemon_type = PokemonType.FIRE
type_name = pokemon_type.name  # "FIRE"

# 안전한 변환 (KeyError 방지)
try:
    pokemon_type = PokemonType[type_name]
except KeyError:
    pokemon_type = None
    print(f"유효하지 않은 타입: {type_name}")
```

### 4️⃣ 모든 Enum 순회

```python
# 모든 타입 출력
for pokemon_type in PokemonType:
    print(f"{pokemon_type.name}: {pokemon_type.value}")

# 출력:
# BUG: 1
# DARK: 2
# DRAGON: 3
# ...
```

---

## SimplifiedPokemon에서 사용하기

### ✅ 권장 방법: Enum 객체 그대로 저장

```python
from typing import Optional, Tuple
from poke_env.battle.pokemon import Pokemon
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.pokemon_gender import PokemonGender
from poke_env.battle.status import Status

class SimplifiedPokemon:
    def __init__(self, poke_env_pokemon: Pokemon):
        # ✅ Enum 객체 그대로 저장 (복사 불필요)
        self.gender: Optional[PokemonGender] = poke_env_pokemon.gender
        self.status: Optional[Status] = poke_env_pokemon.status
        self.types: Tuple[PokemonType, ...] = poke_env_pokemon.types

    def __str__(self) -> str:
        """예쁜 출력"""
        type_str = '/'.join(t.name for t in self.types)
        status_str = self.status.name if self.status else "정상"
        return f"{self.species} ({type_str}) - {status_str}"

    def is_fire_type(self) -> bool:
        """불꽃 타입인지 확인"""
        return PokemonType.FIRE in self.types

    def is_burned(self) -> bool:
        """화상 상태인지 확인"""
        return self.status == Status.BRN

    @property
    def type_names(self) -> list[str]:
        """타입 이름 리스트"""
        return [t.name for t in self.types]
```

### 왜 Enum 그대로 저장하나?

#### 장점 ✅

1. **타입 안전**: IDE가 자동완성 제공
2. **메모리 효율**: Enum은 싱글톤 (같은 객체 재사용)
3. **간결한 코드**: 변환 로직 불필요
4. **빠른 비교**: 객체 비교가 문자열 비교보다 빠름

#### 단점 ❌

1. JSON 직렬화 시 추가 처리 필요
2. 데이터베이스 저장 시 변환 필요

---

## 실전 예제

### 예제 1: 타입 상성 체크

```python
def get_type_effectiveness(move_type: PokemonType, pokemon: SimplifiedPokemon) -> str:
    """기술 타입에 따른 효과 판정"""

    # 예시: 불꽃 기술 vs 풀 타입
    if move_type == PokemonType.FIRE and PokemonType.GRASS in pokemon.types:
        return "효과가 굉장했다!"

    # 예시: 물 기술 vs 불꽃 타입
    elif move_type == PokemonType.WATER and PokemonType.FIRE in pokemon.types:
        return "효과가 굉장했다!"

    # 예시: 전기 기술 vs 땅 타입
    elif move_type == PokemonType.ELECTRIC and PokemonType.GROUND in pokemon.types:
        return "효과가 없는 것 같다..."

    else:
        return "보통이다"

# 사용
charizard = SimplifiedPokemon(...)  # types = [FIRE, FLYING]
result = get_type_effectiveness(PokemonType.WATER, charizard)
print(result)  # "효과가 굉장했다!"
```

### 예제 2: 팀 구성 분석

```python
def analyze_team_types(team: list[SimplifiedPokemon]) -> dict:
    """팀의 타입 분포 분석"""
    type_count = {}

    for pokemon in team:
        for ptype in pokemon.types:
            type_count[ptype.name] = type_count.get(ptype.name, 0) + 1

    return type_count

# 사용
team = [pokemon1, pokemon2, pokemon3, pokemon4, pokemon5, pokemon6]
distribution = analyze_team_types(team)
print(distribution)
# {'FIRE': 2, 'WATER': 1, 'GRASS': 1, 'ELECTRIC': 1, 'DRAGON': 2}
```

### 예제 3: 상태이상 체크

```python
def count_status_conditions(team: list[SimplifiedPokemon]) -> dict:
    """팀의 상태이상 현황"""
    status_count = {
        "정상": 0,
        "화상": 0,
        "마비": 0,
        "독": 0,
        "맹독": 0,
        "잠듦": 0,
        "얼음": 0,
    }

    for pokemon in team:
        if pokemon.status is None:
            status_count["정상"] += 1
        elif pokemon.status == Status.BRN:
            status_count["화상"] += 1
        elif pokemon.status == Status.PAR:
            status_count["마비"] += 1
        elif pokemon.status == Status.PSN:
            status_count["독"] += 1
        elif pokemon.status == Status.TOX:
            status_count["맹독"] += 1
        elif pokemon.status == Status.SLP:
            status_count["잠듦"] += 1
        elif pokemon.status == Status.FRZ:
            status_count["얼음"] += 1

    return status_count
```

### 예제 4: 디버깅용 출력

```python
def print_pokemon_info(pokemon: SimplifiedPokemon):
    """포켓몬 정보 상세 출력"""
    print("=" * 50)
    print(f"종류: {pokemon.species}")
    print(f"레벨: {pokemon.level}")

    # ✅ Enum을 예쁘게 출력
    print(f"타입: {', '.join(t.name for t in pokemon.types)}")
    print(f"성별: {pokemon.gender.name if pokemon.gender else 'N/A'}")
    print(f"상태: {pokemon.status.name if pokemon.status else '정상'}")

    print(f"HP: {pokemon.current_hp}/{pokemon.max_hp} ({pokemon.current_hp_fraction:.1%})")
    print(f"특성: {pokemon.ability}")
    print(f"아이템: {pokemon.item or '없음'}")
    print("=" * 50)

# 출력 예시:
# ==================================================
# 종류: charizard
# 레벨: 50
# 타입: FIRE, FLYING
# 성별: MALE
# 상태: 정상
# HP: 153/153 (100.0%)
# 특성: blaze
# 아이템: leftovers
# ==================================================
```

---

## 📊 Enum vs 문자열 비교

| 항목          | Enum 객체           | 문자열                |
| ------------- | ------------------- | --------------------- |
| **타입 안전** | ✅ IDE 자동완성     | ❌ 오타 위험          |
| **메모리**    | ✅ 싱글톤 (효율적)  | ⚠️ 매번 새로 생성     |
| **비교 속도** | ✅ 빠름 (객체 비교) | ⚠️ 느림 (문자열 비교) |
| **가독성**    | ✅ 명확함           | ⚠️ 매직 스트링        |
| **JSON 저장** | ⚠️ 변환 필요        | ✅ 바로 저장 가능     |
| **DB 저장**   | ⚠️ 변환 필요        | ✅ 바로 저장 가능     |

---

## 🎯 Best Practices

### ✅ 권장 사항

```python
# 1. Enum 객체 그대로 저장
self.types = pokemon.types  # ✅

# 2. 비교 시 Enum 객체 사용
if pokemon.type_1 == PokemonType.FIRE:  # ✅

# 3. 출력 시에만 .name 사용
print(f"타입: {', '.join(t.name for t in pokemon.types)}")  # ✅

# 4. JSON 저장 시에만 변환
def to_dict(self):
    return {
        "types": [t.name for t in self.types],  # ✅
    }
```

### ❌ 비권장 사항

```python
# 1. 불필요한 문자열 변환
self.types = [t.name for t in pokemon.types]  # ❌

# 2. 문자열 비교
if pokemon.type_1.name == "FIRE":  # ❌ (동작은 하지만 비권장)

# 3. 매직 스트링 사용
if type_str == "FIRE":  # ❌ 오타 위험
```

---

## 🔧 자주 하는 실수

### 실수 1: Enum과 문자열 혼동

```python
# ❌ 잘못된 코드
if pokemon.type_1 == "FIRE":  # TypeError!

# ✅ 올바른 코드
if pokemon.type_1 == PokemonType.FIRE:
# 또는
if pokemon.type_1.name == "FIRE":
```

### 실수 2: None 체크 누락

```python
# ❌ AttributeError 위험
print(pokemon.status.name)  # status가 None이면 에러!

# ✅ 안전한 코드
print(pokemon.status.name if pokemon.status else "정상")
```

### 실수 3: 타입 변환 실수

```python
# ❌ 잘못된 변환
type_name = str(PokemonType.FIRE)  # "PokemonType.FIRE" (원하는 결과 아님)

# ✅ 올바른 변환
type_name = PokemonType.FIRE.name  # "FIRE"
```

---

## 📚 요약

### Enum의 핵심

1. **정의**: 관련된 상수들의 그룹
2. **장점**: 타입 안전, 메모리 효율, 가독성
3. **속성**: `.name` (문자열), `.value` (숫자)

### 사용 원칙

1. **저장**: Enum 객체 그대로 (변환 ❌)
2. **비교**: Enum 객체로 직접 비교
3. **출력**: `.name` 사용
4. **직렬화**: 필요할 때만 `.name`으로 변환

### SimplifiedPokemon 적용

```python
# ✅ 이렇게 쓰세요
self.types = poke_env_pokemon.types  # Enum 그대로
self.gender = poke_env_pokemon.gender  # Enum 그대로
self.status = poke_env_pokemon.status  # Enum 그대로

# 출력할 때만
print(f"타입: {', '.join(t.name for t in self.types)}")
```

---

## 🔗 관련 문서

- [Python 공식 Enum 문서](https://docs.python.org/3/library/enum.html)
- [PYTHON_ESSENTIALS.md](./PYTHON_ESSENTIALS.md) - Python 기본 개념
- poke-env 공식 문서: [PokemonType](https://poke-env.readthedocs.io/en/latest/battle.html#pokemon-types)

---

**이 문서로 Enum 타입을 완벽하게 이해하고 SimplifiedPokemon에 효율적으로 적용할 수 있습니다!** 🎯🐍
