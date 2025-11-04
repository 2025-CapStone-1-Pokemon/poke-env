# 지원 클래스 완전 분석

> **목적**: poke-env의 지원 클래스들 (Status, Weather, Field, Effect 등)을 완벽하게 이해

---

## 📌 목차

1. [개요](#개요)
2. [Status (상태이상)](#status-상태이상)
3. [Weather (날씨)](#weather-날씨)
4. [Field (필드 효과)](#field-필드-효과)
5. [SideCondition (사이드 조건)](#sidecondition-사이드-조건)
6. [Effect (효과)](#effect-효과)
7. [MoveCategory (기술 분류)](#movecategory-기술-분류)
8. [PokemonType (타입)](#pokemontype-타입)
9. [Target (대상 지정)](#target-대상-지정)
10. [SimplifiedBattle에서 사용법](#simplifiedbattle에서-사용법)

---

## 개요

### 지원 클래스란?

poke-env의 핵심 클래스들(Pokemon, Move, Battle)을 지원하는 **열거형(Enum) 클래스**들입니다.

**특징**:

- 모두 Python `Enum` 사용
- 불변 객체 (복사 불필요)
- 타입 안전성 보장
- Showdown 메시지 파싱 지원

```python
from poke_env.battle import Status, Weather, Field, Effect

# Enum 사용
if pokemon.status == Status.BRN:
    print("화상 상태!")

if Weather.RAINDANCE in battle.weather:
    print("비가 오는 중!")

if Field.ELECTRIC_TERRAIN in battle.fields:
    print("일렉트릭필드!")
```

---

## Status (상태이상)

### 개요

**Status**는 포켓몬이 걸릴 수 있는 **상태이상**을 나타냅니다.

**위치**: `poke_env/battle/status.py` (21줄)

### 열거형 값 (7개)

```python
class Status(Enum):
    BRN = auto()    # 화상
    FNT = auto()    # 기절
    FRZ = auto()    # 얼음
    PAR = auto()    # 마비
    PSN = auto()    # 독
    SLP = auto()    # 잠듦
    TOX = auto()    # 맹독
```

### 상세 설명

#### BRN (화상)

```python
Status.BRN
```

**효과**:

- 물리 공격력 **절반**
- 매 턴 **최대 HP의 1/16** 데미지
- 불꽃 타입은 화상 면역

**걸리는 기술**:

- 도깨비불 (명중 85%, 100% 화상)
- 불꽃펀치 (10% 화상)
- 화염방사 (10% 화상)
- 오버히트 (10% 화상)

**SimplifiedBattle에서**:

```python
if pokemon.status == Status.BRN:
    # 물리 공격력 절반
    physical_attack *= 0.5

    # 턴 종료 시 데미지
    burn_damage = pokemon.max_hp // 16
    pokemon.damage(burn_damage)
```

---

#### FNT (기절)

```python
Status.FNT
```

**효과**:

- HP 0
- 행동 불가
- 교체만 가능

**SimplifiedBattle에서**:

```python
if pokemon.status == Status.FNT or pokemon.current_hp == 0:
    pokemon.fainted = True
    # 강제 교체
```

---

#### FRZ (얼음)

```python
Status.FRZ
```

**효과**:

- **행동 불가** (매 턴 20% 확률로 해제)
- 불꽃 타입 기술을 맞으면 해제
- 얼음 타입은 얼음 면역

**걸리는 기술**:

- 냉동빔 (10% 얼음)
- 얼음엄니 (10% 얼음)
- 블리자드 (10% 얼음)

**SimplifiedBattle에서**:

```python
if pokemon.status == Status.FRZ:
    # 20% 확률 해제
    import random
    if random.random() < 0.2:
        pokemon.cure_status()
    else:
        return  # 행동 불가
```

---

#### PAR (마비)

```python
Status.PAR
```

**효과**:

- 스피드 **절반**
- 매 턴 **25% 확률로 행동 불가**
- 전기 타입은 마비 면역

**걸리는 기술**:

- 전기자석파 (명중 90%, 100% 마비)
- 10만볼트 (30% 마비)
- 방전 (30% 마비)

**SimplifiedBattle에서**:

```python
if pokemon.status == Status.PAR:
    # 스피드 절반
    speed *= 0.5

    # 25% 확률 행동 불가
    import random
    if random.random() < 0.25:
        return  # 행동 불가
```

---

#### PSN (독)

```python
Status.PSN
```

**효과**:

- 매 턴 **최대 HP의 1/8** 데미지
- 독/강철 타입은 독 면역

**걸리는 기술**:

- 독가루 (명중 75%, 100% 독)
- 독찌르기 (30% 독)
- 더스트슈트 (30% 독)

**SimplifiedBattle에서**:

```python
if pokemon.status == Status.PSN:
    poison_damage = pokemon.max_hp // 8
    pokemon.damage(poison_damage)
```

---

#### SLP (잠듦)

```python
Status.SLP
```

**효과**:

- **1~3턴 행동 불가**
- `status_counter`로 잠든 턴 수 추적

**걸리는 기술**:

- 최면술 (명중 60%, 100% 잠듦)
- 잠자기 (자신을 재우고 HP 100% 회복)
- 버섯포자 (명중 100%, 100% 잠듦, 풀 타입만)

**SimplifiedBattle에서**:

```python
if pokemon.status == Status.SLP:
    pokemon.status_counter += 1

    # 1~3턴 후 깨어남
    if pokemon.status_counter >= random.randint(1, 3):
        pokemon.cure_status()
        pokemon.status_counter = 0
    else:
        return  # 행동 불가
```

---

#### TOX (맹독)

```python
Status.TOX
```

**효과**:

- 매 턴 **증가하는 데미지** (1/16, 2/16, 3/16, ...)
- `status_counter`로 턴 수 추적
- 독/강철 타입은 면역

**걸리는 기술**:

- 독독 (명중 90%, 100% 맹독)
- 독압정 2겹 (교체 시 맹독)

**SimplifiedBattle에서**:

```python
if pokemon.status == Status.TOX:
    pokemon.status_counter += 1
    toxic_damage = (pokemon.max_hp * pokemon.status_counter) // 16
    pokemon.damage(toxic_damage)
```

---

### 사용 예시

```python
# 상태이상 확인
if pokemon.status == Status.BRN:
    print("화상으로 물리 공격력 절반!")

if pokemon.status == Status.PAR:
    print("마비로 스피드 절반, 25% 행동 불가!")

if pokemon.status in [Status.SLP, Status.FRZ]:
    print("행동 불가 상태!")

# 상태이상 치료
pokemon.cure_status()
pokemon.status  # None
```

---

## Weather (날씨)

### 개요

**Weather**는 배틀의 **날씨**를 나타냅니다.

**위치**: `poke_env/battle/weather.py` (50줄)

### 열거형 값 (9개)

```python
class Weather(Enum):
    UNKNOWN = auto()           # 알 수 없음
    RAINDANCE = auto()         # 비
    SUNNYDAY = auto()          # 맑음
    SANDSTORM = auto()         # 모래바람
    HAIL = auto()              # 싸라기눈
    SNOWSCAPE = SNOW = auto()  # 눈 (9세대)
    DESOLATELAND = auto()      # 끝의대지 (원시 그란돈)
    PRIMORDIALSEA = auto()     # 시초의바다 (원시 카이오가)
    DELTASTREAM = auto()       # 델타스트림 (메가 레쿠쟈)
```

### 상세 설명

#### RAINDANCE (비)

```python
Weather.RAINDANCE
```

**효과**:

- 물 타입 기술 **1.5배**
- 불꽃 타입 기술 **0.5배**
- 천둥 **필중**
- 솔라빔 위력 **절반**
- 달의불빛/아침햇살/광합성 회복량 **절반**
- 5턴 지속 (촉촉한바위: 8턴)

**시작 기술**: 비바라기

**SimplifiedBattle에서**:

```python
if Weather.RAINDANCE in battle.weather:
    if move.type == PokemonType.WATER:
        damage *= 1.5
    elif move.type == PokemonType.FIRE:
        damage *= 0.5
```

---

#### SUNNYDAY (맑음)

```python
Weather.SUNNYDAY
```

**효과**:

- 불꽃 타입 기술 **1.5배**
- 물 타입 기술 **0.5배**
- 솔라빔 **1턴 만에 사용**
- 달의불빛/아침햇살/광합성 회복량 **1.5배**
- 5턴 지속 (뜨거운바위: 8턴)

**시작 기술**: 쾌청

**SimplifiedBattle에서**:

```python
if Weather.SUNNYDAY in battle.weather:
    if move.type == PokemonType.FIRE:
        damage *= 1.5
    elif move.type == PokemonType.WATER:
        damage *= 0.5
```

---

#### SANDSTORM (모래바람)

```python
Weather.SANDSTORM
```

**효과**:

- 매 턴 **1/16 데미지** (바위/땅/강철 제외)
- 바위 타입 특방 **1.5배**
- 5턴 지속 (매끄러운바위: 8턴)

**시작 기술**: 모래바람

**SimplifiedBattle에서**:

```python
if Weather.SANDSTORM in battle.weather:
    # 턴 종료 시
    if pokemon.type_1 not in [PokemonType.ROCK, PokemonType.GROUND, PokemonType.STEEL]:
        sandstorm_damage = pokemon.max_hp // 16
        pokemon.damage(sandstorm_damage)
```

---

#### HAIL (싸라기눈)

```python
Weather.HAIL
```

**효과**:

- 매 턴 **1/16 데미지** (얼음 제외)
- 블리자드 **필중**
- 5턴 지속 (차가운바위: 8턴)

**시작 기술**: 싸라기눈

---

#### SNOWSCAPE (눈, 9세대)

```python
Weather.SNOWSCAPE
Weather.SNOW  # 동일
```

**효과**:

- 얼음 타입 방어 **1.5배**
- 블리자드 **필중**
- 오로라베일 사용 가능
- 5턴 지속

**시작 기술**: 눈 (9세대)

---

#### DESOLATELAND (끝의대지)

```python
Weather.DESOLATELAND
```

**효과**:

- 불꽃 타입 기술 **1.5배**
- **물 타입 기술 무효**
- 날씨 변경 불가
- 원시 그란돈 퇴장 시 종료

**SimplifiedBattle에서**:

```python
if Weather.DESOLATELAND in battle.weather:
    if move.type == PokemonType.WATER:
        return 0  # 무효
```

---

#### PRIMORDIALSEA (시초의바다)

```python
Weather.PRIMORDIALSEA
```

**효과**:

- 물 타입 기술 **1.5배**
- **불꽃 타입 기술 무효**
- 날씨 변경 불가
- 원시 카이오가 퇴장 시 종료

---

#### DELTASTREAM (델타스트림)

```python
Weather.DELTASTREAM
```

**효과**:

- 비행 타입 약점 **1배** (효과가 굉장 → 보통)
- 날씨 변경 불가
- 메가 레쿠쟈 퇴장 시 종료

---

### 사용 예시

```python
# 날씨 확인
if Weather.RAINDANCE in battle.weather:
    start_turn = battle.weather[Weather.RAINDANCE]
    print(f"비가 {start_turn}턴부터 내림")

# 날씨 효과 적용
for weather in battle.weather:
    if weather == Weather.RAINDANCE:
        if move.type == PokemonType.WATER:
            damage *= 1.5
```

---

## Field (필드 효과)

### 개요

**Field**는 배틀의 **필드 효과**를 나타냅니다.

**위치**: `poke_env/battle/field.py` (62줄)

### 열거형 값 (13개)

```python
class Field(Enum):
    UNKNOWN = auto()

    # 테레인 (5턴)
    ELECTRIC_TERRAIN = auto()   # 일렉트릭필드
    GRASSY_TERRAIN = auto()     # 그래스필드
    MISTY_TERRAIN = auto()      # 미스트필드
    PSYCHIC_TERRAIN = auto()    # 사이코필드

    # 룸 (5턴)
    TRICK_ROOM = auto()         # 트릭룸
    WONDER_ROOM = auto()        # 원더룸
    MAGIC_ROOM = auto()         # 매직룸

    # 기타
    GRAVITY = auto()            # 중력
    HEAL_BLOCK = auto()         # 힐블록
    MUD_SPORT = auto()          # 흙놀이
    MUD_SPOT = auto()           # 진흙물
    WATER_SPORT = auto()        # 물놀이
```

### 상세 설명

#### ELECTRIC_TERRAIN (일렉트릭필드)

```python
Field.ELECTRIC_TERRAIN
```

**효과**:

- 땅에 있는 포켓몬의 전기 타입 기술 **1.3배**
- 땅에 있는 포켓몬 **잠듦 방지**
- 5턴 지속 (일렉트릭시드: 8턴)

**시작 기술**: 일렉트릭필드

**SimplifiedBattle에서**:

```python
if Field.ELECTRIC_TERRAIN in battle.fields:
    if move.type == PokemonType.ELECTRIC and not pokemon.is_airborne:
        damage *= 1.3
```

---

#### GRASSY_TERRAIN (그래스필드)

```python
Field.GRASSY_TERRAIN
```

**효과**:

- 땅에 있는 포켓몬의 풀 타입 기술 **1.3배**
- 땅에 있는 포켓몬 매 턴 **1/16 회복**
- 지진/매그니튜드/불도저 위력 **절반**
- 5턴 지속

**시작 기술**: 그래스필드

**SimplifiedBattle에서**:

```python
if Field.GRASSY_TERRAIN in battle.fields:
    if move.type == PokemonType.GRASS and not pokemon.is_airborne:
        damage *= 1.3

    # 턴 종료 시
    if not pokemon.is_airborne:
        heal = pokemon.max_hp // 16
        pokemon.heal(heal)
```

---

#### MISTY_TERRAIN (미스트필드)

```python
Field.MISTY_TERRAIN
```

**효과**:

- 땅에 있는 포켓몬에게 **드래곤 타입 기술 0.5배**
- 땅에 있는 포켓몬 **상태이상 방지**
- 5턴 지속

**시작 기술**: 미스트필드

---

#### PSYCHIC_TERRAIN (사이코필드)

```python
Field.PSYCHIC_TERRAIN
```

**효과**:

- 땅에 있는 포켓몬의 에스퍼 타입 기술 **1.3배**
- 땅에 있는 포켓몬에게 **선공기 무효**
- 5턴 지속

**시작 기술**: 사이코필드

**SimplifiedBattle에서**:

```python
if Field.PSYCHIC_TERRAIN in battle.fields:
    if move.priority > 0 and not defender.is_airborne:
        return  # 선공기 무효
```

---

#### TRICK_ROOM (트릭룸)

```python
Field.TRICK_ROOM
```

**효과**:

- **느린 포켓몬이 먼저 행동**
- 5턴 지속

**시작 기술**: 트릭룸

**SimplifiedBattle에서**:

```python
if Field.TRICK_ROOM in battle.fields:
    # 스피드 순서 반전
    if speed1 > speed2:
        return action2, action1  # 느린 쪽 선공
    else:
        return action1, action2
```

---

#### WONDER_ROOM (원더룸)

```python
Field.WONDER_ROOM
```

**효과**:

- 모든 포켓몬의 **방어와 특방 교체**
- 5턴 지속

**시작 기술**: 원더룸

---

#### MAGIC_ROOM (매직룸)

```python
Field.MAGIC_ROOM
```

**효과**:

- 모든 포켓몬의 **아이템 효과 무효**
- 5턴 지속

**시작 기술**: 매직룸

---

#### GRAVITY (중력)

```python
Field.GRAVITY
```

**효과**:

- 부유 특성/**비행 타입** 무효
- 모든 기술 **명중률 +20%**
- 5턴 지속

**시작 기술**: 중력

---

### 속성

#### `is_terrain` 프로퍼티

테레인인지 확인합니다.

```python
field = Field.ELECTRIC_TERRAIN
field.is_terrain  # True

field = Field.TRICK_ROOM
field.is_terrain  # False
```

---

### 사용 예시

```python
# 필드 확인
if Field.ELECTRIC_TERRAIN in battle.fields:
    print("일렉트릭필드!")

# 테레인 확인
for field in battle.fields:
    if field.is_terrain:
        print(f"테레인: {field.name}")
```

---

## SideCondition (사이드 조건)

### 개요

**SideCondition**은 한 쪽 진영에만 적용되는 **사이드 조건**을 나타냅니다.

**위치**: `poke_env/battle/side_condition.py` (123줄)

### 열거형 값 (주요 15개)

```python
class SideCondition(Enum):
    UNKNOWN = auto()

    # 장판 기술
    STEALTH_ROCK = auto()      # 스텔스록
    SPIKES = auto()            # 압정뿌리기 (최대 3겹)
    TOXIC_SPIKES = auto()      # 독압정 (최대 2겹)
    STICKY_WEB = auto()        # 끈적끈적네트

    # 방어막
    REFLECT = auto()           # 리플렉터 (5턴)
    LIGHT_SCREEN = auto()      # 빛의장막 (5턴)
    AURORA_VEIL = auto()       # 오로라베일 (5턴, 싸라기눈/눈 필요)

    # 버프
    TAILWIND = auto()          # 순풍 (4턴)

    # 기타
    SAFEGUARD = auto()         # 신비의부적 (5턴)
    MIST = auto()              # 흰안개 (5턴)
    LUCKY_CHANT = auto()       # 행운의부적 (5턴)

    # 방어 기술
    QUICK_GUARD = auto()       # 패스트가드 (1턴)
    WIDE_GUARD = auto()        # 와이드가드 (1턴)
    MATBLOCK = auto()          # 따라가때리기 (1턴)

    # 거다이맥스
    G_MAX_STEELSURGE = auto()  # 거다이강타
    G_MAX_WILDFIRE = auto()    # 거다이화염
    # ... 등등
```

### 상세 설명

#### STEALTH_ROCK (스텔스록)

```python
SideCondition.STEALTH_ROCK
```

**효과**:

- 교체 시 **타입 상성 데미지**
- 제거 전까지 계속 유지

**데미지 계산**:

- 타입 상성 4배: 최대 HP의 **1/2**
- 타입 상성 2배: 최대 HP의 **1/4**
- 타입 상성 1배: 최대 HP의 **1/8**
- 타입 상성 0.5배: 최대 HP의 **1/16**
- 타입 상성 0.25배: 최대 HP의 **1/32**

**SimplifiedBattle에서**:

```python
if SideCondition.STEALTH_ROCK in battle.side_conditions:
    # 교체 시
    effectiveness = pokemon.damage_multiplier(PokemonType.ROCK)
    if effectiveness == 4.0:
        damage = pokemon.max_hp // 2
    elif effectiveness == 2.0:
        damage = pokemon.max_hp // 4
    elif effectiveness == 1.0:
        damage = pokemon.max_hp // 8
    elif effectiveness == 0.5:
        damage = pokemon.max_hp // 16
    else:  # 0.25
        damage = pokemon.max_hp // 32

    pokemon.damage(damage)
```

---

#### SPIKES (압정뿌리기)

```python
SideCondition.SPIKES
```

**효과**:

- 교체 시 데미지 (비행 타입/부유 제외)
- **최대 3겹** 중첩 가능
- 1겹: 최대 HP의 **1/8**
- 2겹: 최대 HP의 **1/6**
- 3겹: 최대 HP의 **1/4**

**SimplifiedBattle에서**:

```python
if SideCondition.SPIKES in battle.side_conditions:
    layers = battle.side_conditions[SideCondition.SPIKES]

    if not pokemon.is_airborne:  # 비행/부유 아니면
        if layers == 1:
            damage = pokemon.max_hp // 8
        elif layers == 2:
            damage = pokemon.max_hp // 6
        else:  # 3겹
            damage = pokemon.max_hp // 4

        pokemon.damage(damage)
```

---

#### TOXIC_SPIKES (독압정)

```python
SideCondition.TOXIC_SPIKES
```

**효과**:

- 교체 시 독 상태 부여 (비행 타입/부유 제외)
- **최대 2겹** 중첩 가능
- 1겹: **독** (PSN)
- 2겹: **맹독** (TOX)
- 독 타입이 흡수 (제거)

**SimplifiedBattle에서**:

```python
if SideCondition.TOXIC_SPIKES in battle.side_conditions:
    layers = battle.side_conditions[SideCondition.TOXIC_SPIKES]

    if PokemonType.POISON in pokemon.types:
        # 독 타입이 흡수
        del battle.side_conditions[SideCondition.TOXIC_SPIKES]
    elif not pokemon.is_airborne:
        if layers == 1:
            pokemon.status = Status.PSN
        else:  # 2겹
            pokemon.status = Status.TOX
```

---

#### STICKY_WEB (끈적끈적네트)

```python
SideCondition.STICKY_WEB
```

**효과**:

- 교체 시 **스피드 -1** (비행 타입/부유 제외)

**SimplifiedBattle에서**:

```python
if SideCondition.STICKY_WEB in battle.side_conditions:
    if not pokemon.is_airborne:
        pokemon.boost('spe', -1)
```

---

#### REFLECT (리플렉터)

```python
SideCondition.REFLECT
```

**효과**:

- **물리 데미지 절반**
- 5턴 지속 (빛의점토: 8턴)

**SimplifiedBattle에서**:

```python
if SideCondition.REFLECT in battle.opponent_side_conditions:
    if move.category == MoveCategory.PHYSICAL:
        damage *= 0.5
```

---

#### LIGHT_SCREEN (빛의장막)

```python
SideCondition.LIGHT_SCREEN
```

**효과**:

- **특수 데미지 절반**
- 5턴 지속 (빛의점토: 8턴)

**SimplifiedBattle에서**:

```python
if SideCondition.LIGHT_SCREEN in battle.opponent_side_conditions:
    if move.category == MoveCategory.SPECIAL:
        damage *= 0.5
```

---

#### AURORA_VEIL (오로라베일)

```python
SideCondition.AURORA_VEIL
```

**효과**:

- **물리/특수 데미지 둘 다 절반**
- 5턴 지속 (빛의점토: 8턴)
- **싸라기눈 또는 눈 날씨 필요**

**SimplifiedBattle에서**:

```python
if SideCondition.AURORA_VEIL in battle.opponent_side_conditions:
    if move.category in [MoveCategory.PHYSICAL, MoveCategory.SPECIAL]:
        damage *= 0.5
```

---

#### TAILWIND (순풍)

```python
SideCondition.TAILWIND
```

**효과**:

- **스피드 2배**
- 4턴 지속

**SimplifiedBattle에서**:

```python
if SideCondition.TAILWIND in battle.side_conditions:
    speed *= 2
```

---

### 겹수 확인

```python
# STACKABLE_CONDITIONS: 겹칠 수 있는 사이드 조건
from poke_env.battle.side_condition import STACKABLE_CONDITIONS

# {SideCondition.SPIKES: 3, SideCondition.TOXIC_SPIKES: 2}

if SideCondition.SPIKES in battle.side_conditions:
    layers = battle.side_conditions[SideCondition.SPIKES]
    print(f"압정뿌리기 {layers}겹")  # 1, 2, 또는 3
```

---

### 사용 예시

```python
# 사이드 조건 확인
if SideCondition.STEALTH_ROCK in battle.opponent_side_conditions:
    print("상대 쪽에 스텔스록!")

if SideCondition.REFLECT in battle.side_conditions:
    print("리플렉터 발동 중!")

# 겹수 확인
if SideCondition.SPIKES in battle.opponent_side_conditions:
    layers = battle.opponent_side_conditions[SideCondition.SPIKES]
    print(f"상대 쪽 압정뿌리기 {layers}겹")
```

---

## Effect (효과)

### 개요

**Effect**는 포켓몬에게 적용되는 **휘발성 상태** 및 **효과**를 나타냅니다.

**위치**: `poke_env/battle/effect.py` (1004줄, **200+ 효과**)

### 주요 효과들

#### 혼란 및 매력

```python
Effect.CONFUSION      # 혼란 (1~4턴, 33% 자해)
Effect.ATTRACT        # 헤롱헤롱 (50% 행동 불가)
Effect.INFATUATION    # 매혹 (ATTRACT와 유사)
```

#### 행동 제약

```python
Effect.TAUNT          # 도발 (변화기 사용 불가)
Effect.ENCORE         # 앵콜 (같은 기술만 사용)
Effect.TORMENT        # 트집 (같은 기술 연속 사용 불가)
Effect.DISABLE        # 사용금지 (특정 기술 사용 불가)
Effect.HEALBLOCK      # 힐블록 (회복 불가)
```

#### 방어 및 보호

```python
Effect.PROTECT        # 방어
Effect.ENDURE         # 버티기
Effect.SUBSTITUTE     # 대타 인형
```

#### 지속 데미지/회복

```python
Effect.LEECH_SEED     # 씨뿌리기 (매 턴 1/8 흡수)
Effect.AQUA_RING      # 아쿠아링 (매 턴 1/16 회복)
Effect.INGRAIN        # 뿌리박기 (매 턴 1/16 회복)
```

#### 능력치 관련

```python
Effect.FOCUS_ENERGY   # 기합 (급소율 +2)
Effect.MINIMIZE       # 작아지기 (회피율 +2)
Effect.LASER_FOCUS    # 레이저포커스 (다음 기술 급소)
```

#### 타입 변경

```python
Effect.TYPECHANGE     # 타입 변경 (물기먹기, 할로윈 등)
Effect.TYPEADD        # 타입 추가 (할로윈)
```

#### 특수 상태

```python
Effect.DYNAMAX        # 다이맥스
Effect.TRANSFORM      # 변신
Effect.STOCKPILE1     # 비축 1단계
Effect.STOCKPILE2     # 비축 2단계
Effect.STOCKPILE3     # 비축 3단계
```

#### 멸망의노래

```python
Effect.PERISH3        # 멸망의노래 3턴
Effect.PERISH2        # 멸망의노래 2턴
Effect.PERISH1        # 멸망의노래 1턴
Effect.PERISH0        # 멸망의노래 0턴 (기절)
```

---

### SimplifiedBattle에서 사용

```python
# 효과 확인
if Effect.CONFUSION in pokemon.effects:
    # 혼란 - 33% 자해
    import random
    if random.random() < 0.33:
        self_damage = pokemon.max_hp // 8
        pokemon.damage(self_damage)
        return  # 행동 불가

if Effect.LEECH_SEED in pokemon.effects:
    # 씨뿌리기 - 매 턴 1/8 흡수
    drain = pokemon.max_hp // 8
    pokemon.damage(drain)
    opponent.heal(drain)

if Effect.SUBSTITUTE in pokemon.effects:
    # 대타 - 데미지 대신 받음
    # (구현 복잡)
    pass
```

---

## MoveCategory (기술 분류)

### 개요

**MoveCategory**는 기술의 **분류**를 나타냅니다.

**위치**: `poke_env/battle/move_category.py` (15줄)

### 열거형 값 (3개)

```python
class MoveCategory(Enum):
    PHYSICAL = auto()   # 물리 기술
    SPECIAL = auto()    # 특수 기술
    STATUS = auto()     # 변화 기술
```

### 설명

#### PHYSICAL (물리 기술)

```python
MoveCategory.PHYSICAL
```

**특징**:

- **공격** 스탯 사용
- 상대 **방어** 스탯으로 계산
- 접촉 기술 多 (철가시, 까칠한피부 발동)
- 화상 시 위력 **절반**

**예시**: 지진, 암석봉인, 아쿠아브레이크

---

#### SPECIAL (특수 기술)

```python
MoveCategory.SPECIAL
```

**특징**:

- **특공** 스탯 사용
- 상대 **특방** 스탯으로 계산
- 접촉 없음 (대부분)

**예시**: 10만볼트, 화염방사, 냉동빔

---

#### STATUS (변화 기술)

```python
MoveCategory.STATUS
```

**특징**:

- **데미지 없음**
- 능력치 변화, 상태이상, 날씨 변경 등
- 도발에 막힘

**예시**: 칼춤, 방어, 전기자석파, 비바라기

---

### SimplifiedBattle에서 사용

```python
if move.category == MoveCategory.PHYSICAL:
    atk = attacker.get_effective_stat('atk')
    defense = defender.get_effective_stat('def')

    # 화상 보정
    if attacker.status == Status.BRN:
        atk *= 0.5

elif move.category == MoveCategory.SPECIAL:
    atk = attacker.get_effective_stat('spa')
    defense = defender.get_effective_stat('spd')

else:  # STATUS
    return 0  # 데미지 없음
```

---

## PokemonType (타입)

### 개요

**PokemonType**은 포켓몬 및 기술의 **타입**을 나타냅니다.

**위치**: `poke_env/battle/pokemon_type.py`

### 열거형 값 (19개)

```python
class PokemonType(Enum):
    BUG = auto()        # 벌레
    DARK = auto()       # 악
    DRAGON = auto()     # 드래곤
    ELECTRIC = auto()   # 전기
    FAIRY = auto()      # 페어리
    FIGHTING = auto()   # 격투
    FIRE = auto()       # 불꽃
    FLYING = auto()     # 비행
    GHOST = auto()      # 고스트
    GRASS = auto()      # 풀
    GROUND = auto()     # 땅
    ICE = auto()        # 얼음
    NORMAL = auto()     # 노말
    POISON = auto()     # 독
    PSYCHIC = auto()    # 에스퍼
    ROCK = auto()       # 바위
    STEEL = auto()      # 강철
    WATER = auto()      # 물
    STELLAR = auto()    # 스텔라 (9세대 테라스탈)
```

### 주요 메서드

#### `damage_multiplier(defender_type1, defender_type2, type_chart) -> float`

타입 상성 배율을 계산합니다.

```python
# 전기 → 물
effectiveness = PokemonType.ELECTRIC.damage_multiplier(
    PokemonType.WATER,
    None,
    type_chart=battle._data.type_chart
)
# → 2.0 (효과가 굉장!)

# 전기 → 물/땅
effectiveness = PokemonType.ELECTRIC.damage_multiplier(
    PokemonType.WATER,
    PokemonType.GROUND,
    type_chart=battle._data.type_chart
)
# → 0.0 (효과가 없다)
```

---

## Target (대상 지정)

### 개요

**Target**은 기술의 **대상 지정 방식**을 나타냅니다.

**위치**: `poke_env/battle/target.py`

### 주요 값

```python
class Target(Enum):
    NORMAL = auto()               # 앞의 적 1마리
    ALL_ADJACENT_FOES = auto()    # 인접한 모든 적
    ALL_ADJACENT = auto()         # 인접한 모든 포켓몬
    ALL = auto()                  # 모든 포켓몬
    SELF = auto()                 # 자신
    RANDOM_NORMAL = auto()        # 무작위 적 1마리
    # ... 등등
```

---

## SimplifiedBattle에서 사용법

### 전체 통합 예시

```python
class SimplifiedBattle:
    def _execute_move(self, attacker, defender, move):
        """기술 실행"""
        # 1. 명중 판정
        if not self._check_accuracy(attacker, defender, move):
            return

        # 2. 데미지 계산
        if move.category != MoveCategory.STATUS:
            damage = self._calculate_damage(attacker, defender, move)
            defender.damage(damage)

        # 3. 추가 효과
        if move.status:
            defender.status = move.status

        if move.boosts:
            for stat, amount in move.boosts.items():
                defender.boost(stat, amount)

    def _end_of_turn(self):
        """턴 종료 처리"""
        # 날씨 데미지
        if Weather.SANDSTORM in self.weather:
            for pokemon in [self.active_pokemon, self.opponent_active_pokemon]:
                if pokemon.type_1 not in [PokemonType.ROCK, PokemonType.GROUND, PokemonType.STEEL]:
                    damage = pokemon.max_hp // 16
                    pokemon.damage(damage)

        # 상태이상 데미지
        for pokemon in [self.active_pokemon, self.opponent_active_pokemon]:
            if pokemon.status == Status.BRN:
                damage = pokemon.max_hp // 16
                pokemon.damage(damage)
            elif pokemon.status == Status.PSN:
                damage = pokemon.max_hp // 8
                pokemon.damage(damage)
            elif pokemon.status == Status.TOX:
                pokemon.status_counter += 1
                damage = (pokemon.max_hp * pokemon.status_counter) // 16
                pokemon.damage(damage)

        # 효과
        for pokemon in [self.active_pokemon, self.opponent_active_pokemon]:
            if Effect.LEECH_SEED in pokemon.effects:
                drain = pokemon.max_hp // 8
                pokemon.damage(drain)
                # 상대 회복
```

---

## 다음 문서

- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - SimplifiedBattle 구현 완전 가이드

---

**끝!** 🎮
