# Move 클래스 완전 분석

> **목적**: poke-env의 Move 클래스를 완벽하게 이해하고 SimplifiedBattle 구현에 활용

---

## 📌 목차

1. [개요](#개요)
2. [클래스 구조](#클래스-구조)
3. [속성 완전 목록](#속성-완전-목록)
4. [메서드 완전 목록](#메서드-완전-목록)
5. [특수 Move 클래스들](#특수-move-클래스들)
6. [주요 사용 패턴](#주요-사용-패턴)
7. [SimplifiedMove 구현 가이드](#simplifiedmove-구현-가이드)

---

## 개요

### Move 클래스란?

**Move**는 포켓몬이 사용할 수 있는 **기술(기술)**의 모든 정보를 담는 클래스입니다.

```python
from poke_env.battle import Move

# Pokemon 객체에서 Move 가져오기
for move_id, move in pokemon.moves.items():
    print(f"{move.id}: {move.base_power} / {move.type.name}")

# 예시 출력
# thunderbolt: 90 / ELECTRIC
# quickattack: 40 / NORMAL
# irontail: 100 / STEEL
# surf: 90 / WATER
```

### 파일 정보

- **위치**: `poke_env/battle/move.py`
- **라인 수**: 937줄
- \***\*slots** 개수\*\*: 7개 (메모리 최적화)
- **주요 의존성**: `PokemonType`, `MoveCategory`, `Effect`, `Status`, `Weather`, `Field`, `Target`

### Move 데이터 소스

Move는 **Pokemon Showdown 데이터**에서 정보를 가져옵니다:

```python
class Move:
    def __init__(self, move_id: str, gen: int):
        self._id = move_id
        self._gen = gen
        self._moves_dict = GenData.from_gen(gen).moves  # 데이터 로드

        # 데이터에서 정보 자동 로드
        # self.entry → self._moves_dict[move_id]
```

---

## 클래스 구조

### **slots** 정의 (7개)

```python
class Move:
    __slots__ = (
        "_id",                    # 기술 ID ('thunderbolt')
        "_base_power_override",   # 위력 오버라이드 (히든파워)
        "_current_pp",            # 현재 PP
        "_dynamaxed_move",        # 다이맥스 기술 캐시
        "_gen",                   # 세대 (8, 9 등)
        "_is_empty",              # 빈 기술 여부
        "_moves_dict",            # 기술 데이터 딕셔너리
        "_request_target",        # 서버 요청의 대상 정보
    )
```

Pokemon 클래스의 55개에 비하면 매우 적습니다! 대부분의 정보는 **데이터에서 동적으로 가져옵니다**.

---

## 속성 완전 목록

### 1. 기본 정보 (6개)

| 속성         | 타입           | 설명             | 예시                   |
| ------------ | -------------- | ---------------- | ---------------------- |
| `id`         | `str`          | 기술 ID          | `'thunderbolt'`        |
| `base_power` | `int`          | 위력             | `90`                   |
| `type`       | `PokemonType`  | 타입             | `PokemonType.ELECTRIC` |
| `category`   | `MoveCategory` | 분류             | `MoveCategory.SPECIAL` |
| `accuracy`   | `float`        | 명중률 (0.0~1.0) | `1.0` (100%)           |
| `priority`   | `int`          | 우선도 (-7~+5)   | `0`                    |

```python
# 기본 정보 확인
print(f"기술: {move.id}")
print(f"위력: {move.base_power}")
print(f"타입: {move.type.name}")
print(f"분류: {move.category.name}")  # PHYSICAL, SPECIAL, STATUS
print(f"명중률: {move.accuracy * 100}%")
print(f"우선도: {move.priority}")
```

**MoveCategory (분류)**:

- `PHYSICAL` - 물리 기술 (공격 vs 방어)
- `SPECIAL` - 특수 기술 (특공 vs 특방)
- `STATUS` - 변화 기술 (데미지 없음)

**Priority (우선도)**:

- `+5`: 페인트 (선제공격)
- `+4`: 신속 등
- `+3`: 얼음뭉치 등
- `+2`: 신속방어, 익스트림스피드
- `+1`: 아쿠아젯, 불릿펀치, 선제베기
- `0`: 대부분의 기술
- `-1`: 보복
- `-3`: 트릭룸
- `-7`: 드래곤테일

---

### 2. PP 관리 (2개)

| 속성         | 타입  | 설명    | 예시             |
| ------------ | ----- | ------- | ---------------- |
| `max_pp`     | `int` | 최대 PP | `24` (15 \* 8/5) |
| `current_pp` | `int` | 현재 PP | `23`             |

```python
# PP 확인
print(f"PP: {move.current_pp}/{move.max_pp}")

# PP 사용
move.use()
print(f"PP: {move.current_pp}/{move.max_pp}")  # 23/24 → 22/24
```

**max_pp 계산**:

- 기본 PP × 8/5 (PP증가 아이템 최대 사용 시)
- 예: 10만볼트 기본 PP 15 → 최대 24

---

### 3. 데미지 관련 (7개)

| 속성            | 타입              | 설명           | 예시                   |
| --------------- | ----------------- | -------------- | ---------------------- |
| `base_power`    | `int`             | 기본 위력      | `90`                   |
| `damage`        | `Union[int, str]` | 고정 데미지    | `0` 또는 `'level'`     |
| `crit_ratio`    | `int`             | 급소율 (0~6)   | `0` (보통), `1` (높음) |
| `expected_hits` | `float`           | 예상 타격 횟수 | `2.5` (2~5회)          |
| `n_hit`         | `Tuple[int, int]` | 타격 횟수 범위 | `(2, 5)`               |
| `recoil`        | `float`           | 반동 비율      | `0.33` (1/3)           |
| `drain`         | `float`           | 흡수 비율      | `0.5` (1/2)            |

```python
# 위력
if move.base_power > 0:
    print(f"위력: {move.base_power}")
else:
    print("위력 없음 (변화기)")

# 고정 데미지 (용의분노, 지구던지기 등)
if move.damage:
    print(f"고정 데미지: {move.damage}")  # 40 또는 'level'

# 다단히트 (연속베기, 미사일바늘 등)
min_hits, max_hits = move.n_hit
if max_hits > 1:
    print(f"{min_hits}~{max_hits}회 공격!")
    print(f"평균 {move.expected_hits:.1f}회")

# 반동 (와일드볼트, 브레이브버드)
if move.recoil > 0:
    print(f"반동: {move.recoil * 100}%")

# 흡수 (기가드레인, 메가드레인)
if move.drain > 0:
    print(f"흡수: {move.drain * 100}%")
```

**특수 케이스**:

- **고정 데미지**: 용의분노 (40), 지구던지기 (level), 분노의이빨 (50)
- **다단히트**: 연속베기 (2~5회), 미사일바늘 (2~5회), 트리플킥 (3회)
- **반동**: 와일드볼트 (1/3), 브레이브버드 (1/3), 아쿠아리오드 (1/3)
- **흡수**: 기가드레인 (1/2), 드레인펀치 (1/2)

---

### 4. 추가 효과 (12개)

| 속성              | 타입                       | 설명             | 예시                                |
| ----------------- | -------------------------- | ---------------- | ----------------------------------- |
| `boosts`          | `Optional[Dict[str, int]]` | 상대 능력치 변화 | `{'def': -1}`                       |
| `self_boost`      | `Optional[Dict[str, int]]` | 자신 능력치 변화 | `{'atk': 1}`                        |
| `status`          | `Optional[Status]`         | 상태이상 부여    | `Status.BRN`                        |
| `volatile_status` | `Optional[Effect]`         | 휘발성 상태      | `Effect.CONFUSION`                  |
| `side_condition`  | `Optional[SideCondition]`  | 사이드 조건      | `SideCondition.STEALTH_ROCK`        |
| `weather`         | `Optional[Weather]`        | 날씨 변경        | `Weather.RAINDANCE`                 |
| `terrain`         | `Optional[Field]`          | 필드 변경        | `Field.ELECTRIC_TERRAIN`            |
| `heal`            | `float`                    | 회복 비율        | `0.5` (1/2)                         |
| `secondary`       | `List[Dict]`               | 추가 효과들      | `[{'chance': 30, 'status': 'par'}]` |
| `force_switch`    | `bool`                     | 강제 교체        | `True`                              |
| `self_switch`     | `Union[str, bool]`         | 자가 교체        | `True` 또는 `'copyvolatile'`        |
| `self_destruct`   | `Optional[str]`            | 자폭             | `'always'`                          |

```python
# 상대 능력치 하락 (으름장, 매혹적인목소리)
if move.boosts:
    print(f"상대 능력치 변화: {move.boosts}")  # {'atk': -1}

# 자신 능력치 상승 (칼춤, 용의춤)
if move.self_boost:
    print(f"자신 능력치 변화: {move.self_boost}")  # {'atk': 2}

# 상태이상 부여 (도깨비불, 전기자석파)
if move.status:
    print(f"상태이상: {move.status.name}")  # BRN, PAR

# 혼란 등 휘발성 상태
if move.volatile_status:
    print(f"효과: {move.volatile_status.name}")  # CONFUSION

# 날씨 변경 (비바라기, 쾌청)
if move.weather:
    print(f"날씨: {move.weather.name}")

# 필드 변경 (일렉트릭필드, 그래스필드)
if move.terrain:
    print(f"필드: {move.terrain.name}")

# 회복 (잠자기, 달의불빛)
if move.heal > 0:
    print(f"회복: {move.heal * 100}%")

# 추가 효과 (30% 확률로 마비 등)
if move.secondary:
    for effect in move.secondary:
        if 'chance' in effect:
            print(f"{effect['chance']}% 확률로 추가 효과")
```

**예시**:

- **boosts**: 으름장 (`{'atk': -1}`), 매혹적인목소리 (`{'spa': -2}`)
- **self_boost**: 칼춤 (`{'atk': 2}`), 나비춤 (`{'spa': 1, 'spd': 1, 'spe': 1}`)
- **status**: 도깨비불 (`BRN`), 전기자석파 (`PAR`), 독독 (`TOX`)
- **volatile_status**: 이상한빛 (`CONFUSION`), 헤롱헤롱 (`ATTRACT`)
- **secondary**: 10만볼트 (30% 마비), 불꽃펀치 (10% 화상)

---

### 5. 명중 및 회피 (4개)

| 속성               | 타입                            | 설명           | 예시         |
| ------------------ | ------------------------------- | -------------- | ------------ |
| `accuracy`         | `float`                         | 명중률         | `1.0` (100%) |
| `ignore_ability`   | `bool`                          | 특성 무시      | `True`       |
| `ignore_defensive` | `bool`                          | 방어 랭크 무시 | `True`       |
| `ignore_evasion`   | `bool`                          | 회피율 무시    | `True`       |
| `ignore_immunity`  | `Union[bool, Set[PokemonType]]` | 타입 면역 무시 | `{GROUND}`   |

```python
# 명중률
print(f"명중률: {move.accuracy * 100}%")

# 특수 명중 처리
if move.ignore_evasion:
    print("회피율 무시!")

if move.ignore_ability:
    print("특성 무시!")

if move.ignore_defensive:
    print("상대 방어 랭크 무시!")

if move.ignore_immunity:
    if isinstance(move.ignore_immunity, bool):
        print("모든 면역 무시!")
    else:
        print(f"면역 무시 타입: {move.ignore_immunity}")
```

**예시**:

- **ignore_evasion**: 파동미사일, 오라스피어 등 (명중률 100%, 회피 무시)
- **ignore_ability**: 몰드브레이커 효과 기술
- **ignore_defensive**: 칩어웨이, 성스러운칼
- **ignore_immunity**: 천둥 (땅 타입에 맞음), 프리즈드라이 (물 타입에 효과가 굉장)

---

### 6. 플래그 및 특성 (10개)

| 속성                   | 타입       | 설명                | 예시                     |
| ---------------------- | ---------- | ------------------- | ------------------------ |
| `flags`                | `Set[str]` | 기술 플래그들       | `{'contact', 'protect'}` |
| `breaks_protect`       | `bool`     | 방어 관통           | `True`                   |
| `is_protect_move`      | `bool`     | 방어 기술           | `True`                   |
| `is_protect_counter`   | `bool`     | 방어 카운터 증가    | `True`                   |
| `is_side_protect_move` | `bool`     | 사이드 방어         | `True`                   |
| `stalling_move`        | `bool`     | 시간 끄는 기술      | `True`                   |
| `sleep_usable`         | `bool`     | 잠듦 시 사용 가능   | `True`                   |
| `thaws_target`         | `bool`     | 얼음 녹임           | `True`                   |
| `steals_boosts`        | `bool`     | 능력치 변화 훔침    | `True`                   |
| `use_target_offensive` | `bool`     | 상대 공격 스탯 사용 | `True`                   |

```python
# 플래그 확인
if 'contact' in move.flags:
    print("접촉 기술! (철가시, 까칠한피부 발동)")

if 'protect' in move.flags:
    print("방어 가능!")

if 'sound' in move.flags:
    print("소리 기술! (방음 무효)")

# 특수 속성
if move.breaks_protect:
    print("방어 관통!")

if move.is_protect_move:
    print("방어 기술!")

if move.sleep_usable:
    print("잠들어도 사용 가능! (코골기, 잠꼬대)")
```

**주요 플래그**:

- `contact` - 접촉 기술 (철가시, 까칠한피부 발동)
- `protect` - 방어로 막을 수 있는 기술
- `mirror` - 매직코트로 반사 가능
- `sound` - 소리 기술 (방음 무효)
- `punch` - 펀치 기술 (철주먹 특성 1.2배)
- `bite` - 깨물기 기술 (강철의턱 특성 1.5배)
- `powder` - 가루 기술 (풀 타입 무효)

---

### 7. 대상 지정 (3개)

| 속성             | 타입               | 설명           | 예시            |
| ---------------- | ------------------ | -------------- | --------------- |
| `target`         | `Optional[Target]` | 기본 대상      | `Target.NORMAL` |
| `request_target` | `Optional[Target]` | 서버 요청 대상 | `Target.NORMAL` |
| `deduced_target` | `Optional[Target]` | 추론된 대상    | `Target.NORMAL` |

```python
# 대상 확인
print(f"대상: {move.target}")

# Target 종류:
# - NORMAL: 앞의 적 1마리
# - ALL_ADJACENT_FOES: 인접한 모든 적
# - ALL_ADJACENT: 인접한 모든 포켓몬 (적+아군)
# - ALL: 모든 포켓몬
# - SELF: 자신
# - RANDOM_NORMAL: 무작위 적 1마리
```

---

### 8. Z기술 / 다이맥스 (5개)

| 속성            | 타입             | 설명              | 예시                   |
| --------------- | ---------------- | ----------------- | ---------------------- |
| `is_z`          | `bool`           | Z기술 여부        | `True`                 |
| `can_z_move`    | `bool`           | Z기술 가능        | `True`                 |
| `z_move_power`  | `int`            | Z기술 위력        | `175`                  |
| `z_move_boost`  | `Optional[Dict]` | Z기술 능력치 변화 | `{'atk': 1}`           |
| `z_move_effect` | `Optional[str]`  | Z기술 효과        | `'clearnegativeboost'` |
| `dynamaxed`     | `DynamaxMove`    | 다이맥스 버전     | DynamaxMove 객체       |

```python
# Z기술
if move.can_z_move:
    print(f"Z기술 위력: {move.z_move_power}")
    if move.z_move_boost:
        print(f"Z기술 추가 능력치 변화: {move.z_move_boost}")

# 다이맥스
dmax_move = move.dynamaxed
print(f"다이맥스 기술: {dmax_move.id}")
print(f"다이맥스 위력: {dmax_move.base_power}")
```

**Z기술 위력 계산**:
| 기본 위력 | Z기술 위력 |
|---------|----------|
| ~55 | 100 |
| 56~65 | 120 |
| 66~75 | 140 |
| 76~85 | 160 |
| 86~95 | 175 |
| 96~100 | 180 |
| 101~110 | 185 |
| 111~125 | 190 |
| 126~130 | 195 |
| 131+ | 200 |

---

### 9. 기타 (8개)

| 속성                 | 타입            | 설명          | 예시                    |
| -------------------- | --------------- | ------------- | ----------------------- |
| `defensive_category` | `MoveCategory`  | 방어 분류     | `MoveCategory.PHYSICAL` |
| `pseudo_weather`     | `Optional[str]` | 유사 날씨     | `'fairylock'`           |
| `slot_condition`     | `Optional[str]` | 슬롯 조건     | `'healingwish'`         |
| `non_ghost_target`   | `bool`          | 비고스트 대상 | `True` (저주)           |
| `no_pp_boosts`       | `bool`          | PP 증가 불가  | `True`                  |
| `is_empty`           | `bool`          | 빈 기술       | `False`                 |
| `entry`              | `Dict`          | 원본 데이터   | `{...}`                 |

---

## 메서드 완전 목록

### 1. PP 관리 (1개)

#### `use()`

PP를 1 소모합니다.

```python
print(f"사용 전: {move.current_pp}")  # 24
move.use()
print(f"사용 후: {move.current_pp}")  # 23
```

---

### 2. 정적 메서드 (4개)

#### `Move.should_be_stored(move_id: str, gen: int) -> bool`

기술을 저장해야 하는지 판단합니다.

```python
# 일반 기술
Move.should_be_stored('thunderbolt', 9)  # True

# 특수 기술 (저장 불필요)
Move.should_be_stored('struggle', 9)     # False (발버둥)
Move.should_be_stored('recharge', 9)     # False (반동)
Move.should_be_stored('zmove', 9)        # False (Z기술)
```

#### `Move.is_id_z(id_: str, gen: int) -> bool`

Z기술인지 확인합니다.

```python
Move.is_id_z('zbolt', 9)           # True
Move.is_id_z('thunderbolt', 9)     # False
```

#### `Move.is_max_move(id_: str, gen: int) -> bool`

다이맥스 기술인지 확인합니다.

```python
Move.is_max_move('maxlightning', 9)  # True
Move.is_max_move('thunderbolt', 9)   # False
```

#### `Move.retrieve_id(move_name: str) -> str`

기술 이름에서 ID를 추출합니다.

```python
Move.retrieve_id('Thunder Bolt')     # 'thunderbolt'
Move.retrieve_id('Hidden Power 70')  # 'hiddenpower'
```

---

## 특수 Move 클래스들

### 1. EmptyMove

**목적**: 정보가 없는 기술 (상대 포켓몬의 미공개 기술)

```python
class EmptyMove(Move):
    def __init__(self, move_id: str):
        self._id = move_id
        self._is_empty = True

    def __getattribute__(self, name: str):
        # 모든 속성 접근 시 0 또는 기본값 반환
        try:
            return super(Move, self).__getattribute__(name)
        except:
            return 0
```

**사용 예**:

```python
# 상대 포켓몬이 아직 사용하지 않은 기술
unknown_move = EmptyMove('unknown1')
print(unknown_move.base_power)  # 0
print(unknown_move.accuracy)    # 0
print(unknown_move.is_empty)    # True
```

---

### 2. DynamaxMove

**목적**: 다이맥스 기술 버전

```python
class DynamaxMove(Move):
    # 타입별 능력치 변화
    BOOSTS_MAP = {
        PokemonType.BUG: {'spa': -1},      # 다이워엄 - 특공 -1
        PokemonType.DARK: {'spd': -1},     # 다이악 - 특방 -1
        PokemonType.DRAGON: {'atk': -1},   # 다이드래군 - 공격 -1
        PokemonType.GHOST: {'def': -1},    # 다이호로우 - 방어 -1
        PokemonType.NORMAL: {'spe': -1},   # 다이어택 - 스피드 -1
    }

    SELF_BOOSTS_MAP = {
        PokemonType.FIGHTING: {'atk': +1}, # 다이너클 - 자신 공격 +1
        PokemonType.FLYING: {'spe': +1},   # 다이제트 - 자신 스피드 +1
        PokemonType.GROUND: {'spd': +1},   # 다이어스 - 자신 특방 +1
        PokemonType.POISON: {'spa': +1},   # 다이애시드 - 자신 특공 +1
    }
```

**사용 예**:

```python
# 일반 기술
move = Move('thunderbolt', gen=9)
print(move.base_power)  # 90

# 다이맥스 버전
dmax = move.dynamaxed
print(dmax.base_power)  # 130 (다이썬더)
print(dmax.terrain)     # Field.ELECTRIC_TERRAIN
```

**다이맥스 기술 위력**:
| 기본 위력 | 다이맥스 위력 |
|---------|------------|
| 0~40 | 90 |
| 41~50 | 100 |
| 51~60 | 110 |
| 61~70 | 120 |
| 71~100 | 130 |
| 101~140 | 140 |
| 141+ | 150 |

---

## 주요 사용 패턴

### 1. 기술 정보 출력

```python
def print_move_info(move: Move):
    print(f"=== {move.id.upper()} ===")
    print(f"타입: {move.type.name}")
    print(f"분류: {move.category.name}")
    print(f"위력: {move.base_power}")
    print(f"명중률: {move.accuracy * 100:.0f}%")
    print(f"PP: {move.current_pp}/{move.max_pp}")
    print(f"우선도: {move.priority}")

    if move.status:
        print(f"상태이상: {move.status.name}")

    if move.boosts:
        print(f"능력치 변화: {move.boosts}")

    if move.secondary:
        for effect in move.secondary:
            if 'chance' in effect:
                print(f"추가 효과 ({effect['chance']}%)")

    if 'contact' in move.flags:
        print("접촉 기술")

# 사용
thunderbolt = Move('thunderbolt', gen=9)
print_move_info(thunderbolt)

# 출력:
# === THUNDERBOLT ===
# 타입: ELECTRIC
# 분류: SPECIAL
# 위력: 90
# 명중률: 100%
# PP: 24/24
# 우선도: 0
# 추가 효과 (30%)  <- 30% 마비
```

---

### 2. 최적 기술 선택 (타입 상성 + 위력)

```python
def choose_best_move(battle: Battle) -> Move:
    """타입 상성과 위력을 고려한 최적 기술 선택"""
    opp = battle.opponent_active_pokemon
    best_move = None
    best_score = 0.0

    for move in battle.available_moves:
        # 타입 상성
        effectiveness = opp.damage_multiplier(move)

        # 위력 (변화기는 제외)
        power = move.base_power if move.base_power > 0 else 0

        # 종합 점수
        score = power * effectiveness

        # 추가 효과 고려
        if move.priority > 0:
            score *= 1.2  # 선공기 우대

        if move.secondary:
            score *= 1.1  # 추가 효과 있으면 약간 우대

        if score > best_score:
            best_score = score
            best_move = move

    return best_move
```

---

### 3. 기술 필터링

```python
def get_status_moves(pokemon: Pokemon) -> List[Move]:
    """변화 기술만 필터링"""
    return [
        move for move in pokemon.moves.values()
        if move.category == MoveCategory.STATUS
    ]

def get_priority_moves(pokemon: Pokemon) -> List[Move]:
    """선공 기술만 필터링"""
    return [
        move for move in pokemon.moves.values()
        if move.priority > 0
    ]

def get_setup_moves(pokemon: Pokemon) -> List[Move]:
    """랭업 기술만 필터링"""
    return [
        move for move in pokemon.moves.values()
        if move.self_boost is not None
    ]

# 사용
status_moves = get_status_moves(pokemon)
for move in status_moves:
    print(f"{move.id}: {move.self_boost or move.boosts}")
```

---

### 4. PP 체크 및 관리

```python
def has_usable_moves(pokemon: Pokemon) -> bool:
    """사용 가능한 기술이 있는지 확인"""
    return any(
        move.current_pp > 0
        for move in pokemon.moves.values()
        if not move.is_empty
    )

def get_low_pp_moves(pokemon: Pokemon, threshold: float = 0.25) -> List[Move]:
    """PP가 부족한 기술 찾기"""
    return [
        move for move in pokemon.moves.values()
        if move.current_pp / move.max_pp < threshold
    ]

# 사용
if not has_usable_moves(pokemon):
    print("PP가 모두 소진됨! 발버둥만 사용 가능")

low_pp = get_low_pp_moves(pokemon)
for move in low_pp:
    print(f"{move.id}: {move.current_pp}/{move.max_pp} PP 남음")
```

---

### 5. 다이맥스 기술 변환

```python
def show_dynamax_version(move: Move):
    """다이맥스 버전 정보 출력"""
    print(f"원본: {move.id} (위력 {move.base_power})")

    dmax = move.dynamaxed
    print(f"다이맥스: {dmax.id} (위력 {dmax.base_power})")

    if dmax.terrain:
        print(f"필드: {dmax.terrain.name}")

    if dmax.weather:
        print(f"날씨: {dmax.weather.name}")

    if dmax.boosts:
        print(f"상대 능력치 변화: {dmax.boosts}")

    if dmax.self_boost:
        print(f"자신 능력치 변화: {dmax.self_boost}")

# 사용
thunderbolt = Move('thunderbolt', gen=9)
show_dynamax_version(thunderbolt)

# 출력:
# 원본: thunderbolt (위력 90)
# 다이맥스: maxlightning (위력 130)
# 필드: ELECTRIC_TERRAIN
```

---

## SimplifiedMove 구현 가이드

### 1. 복사해야 할 속성

```python
class SimplifiedMove:
    def __init__(self, poke_env_move: Move):
        # === 기본 정보 (불변) ===
        self.id = poke_env_move.id
        self.base_power = poke_env_move.base_power
        self.type = poke_env_move.type
        self.category = poke_env_move.category
        self.accuracy = poke_env_move.accuracy
        self.priority = poke_env_move.priority

        # === PP (시뮬레이션마다 변경) ===
        self.current_pp = poke_env_move.current_pp
        self.max_pp = poke_env_move.max_pp

        # === 추가 효과 (불변) ===
        self.boosts = poke_env_move.boosts
        self.self_boost = poke_env_move.self_boost
        self.status = poke_env_move.status
        self.secondary = poke_env_move.secondary

        # === 데미지 관련 (불변) ===
        self.crit_ratio = poke_env_move.crit_ratio
        self.expected_hits = poke_env_move.expected_hits
        self.recoil = poke_env_move.recoil
        self.drain = poke_env_move.drain

        # === 플래그 (불변) ===
        self.flags = poke_env_move.flags.copy()
        self.breaks_protect = poke_env_move.breaks_protect
        self.is_protect_move = poke_env_move.is_protect_move
```

---

### 2. 필요한 메서드

```python
class SimplifiedMove:
    # ... __init__ ...

    def use(self):
        """PP 소모"""
        self.current_pp = max(0, self.current_pp - 1)

    def calculate_damage(self, attacker, defender, battle_state):
        """데미지 계산 (간소화 버전)"""
        if self.category == MoveCategory.STATUS:
            return 0

        # 1. 기본 위력
        power = self.base_power
        if power == 0:
            return 0

        # 2. 공격/방어 스탯
        if self.category == MoveCategory.PHYSICAL:
            atk = attacker.get_effective_stat('atk')
            defense = defender.get_effective_stat('def')
        else:
            atk = attacker.get_effective_stat('spa')
            defense = defender.get_effective_stat('spd')

        # 3. 기본 데미지
        level = attacker.level
        damage = ((2 * level / 5 + 2) * power * atk / defense / 50) + 2

        # 4. STAB (Same Type Attack Bonus)
        if self.type in attacker.types:
            damage *= attacker.stab_multiplier

        # 5. 타입 상성
        effectiveness = defender.damage_multiplier(self.type)
        damage *= effectiveness

        # 6. 난수 (85% ~ 100%)
        import random
        damage *= random.uniform(0.85, 1.0)

        return int(damage)
```

---

### 3. 복사 시 주의사항

| 속성                           | 복사 방법                | 이유                     |
| ------------------------------ | ------------------------ | ------------------------ |
| `id`, `base_power`, `priority` | 직접 할당                | 불변 값                  |
| `type`, `category`, `status`   | 직접 할당                | Enum (불변)              |
| `accuracy`, `recoil`, `drain`  | 직접 할당                | 숫자 (불변)              |
| `flags`                        | `.copy()`                | Set, 얕은 복사 OK        |
| `boosts`, `self_boost`         | 직접 할당 또는 `.copy()` | Dict 또는 None           |
| `secondary`                    | 직접 할당                | List, 읽기 전용으로 사용 |

**중요**: Move 객체는 **대부분 불변 데이터**입니다. `current_pp`만 변경되므로 **얕은 복사로 충분**합니다!

```python
# ✅ 올바른 방법 (얕은 복사)
import copy
simplified_moves = {}
for move_id, move in pokemon.moves.items():
    simplified_moves[move_id] = SimplifiedMove(move)

# 또는 더 간단하게
simplified_moves = {
    move_id: SimplifiedMove(move)
    for move_id, move in pokemon.moves.items()
}
```

---

## 다음 문서

- **[BATTLE_CLASS.md](BATTLE_CLASS.md)** - Battle 클래스 완전 분석
- **[SUPPORTING_CLASSES.md](SUPPORTING_CLASSES.md)** - 지원 클래스들
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - SimplifiedBattle 구현 가이드

---

**끝!** ⚡
