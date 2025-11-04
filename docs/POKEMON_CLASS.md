# Pokemon 클래스 완전 분석

> **목적**: poke-env의 Pokemon 클래스를 완벽하게 이해하고 SimplifiedPokemon 구현에 활용

---

## 📌 목차

1. [개요](#개요)
2. [클래스 구조](#클래스-구조)
3. [속성 완전 목록](#속성-완전-목록)
4. [메서드 완전 목록](#메서드-완전-목록)
5. [주요 사용 패턴](#주요-사용-패턴)
6. [SimplifiedPokemon 구현 가이드](#simplifiedpokemon-구현-가이드)

---

## 개요

### Pokemon 클래스란?

**Pokemon**은 배틀에 참여하는 **개별 포켓몬**의 모든 정보를 담는 핵심 클래스입니다.

```python
from poke_env.battle import Pokemon

# Battle 객체에서 Pokemon 가져오기
my_pokemon = battle.active_pokemon          # 내 활성 포켓몬
opp_pokemon = battle.opponent_active_pokemon # 상대 활성 포켓몬

# Pokemon 정보 접근
print(f"종족: {my_pokemon.species}")        # 'pikachu'
print(f"HP: {my_pokemon.current_hp}/{my_pokemon.max_hp}")  # 85/100
print(f"타입: {my_pokemon.types}")          # [PokemonType.ELECTRIC]
print(f"레벨: {my_pokemon.level}")          # 50
print(f"특성: {my_pokemon.ability}")        # 'static'
```

### 파일 정보

- **위치**: `poke_env/battle/pokemon.py`
- **라인 수**: 1114줄
- ****slots** 개수**: 55개 (메모리 최적화)
- **주요 의존성**: `Move`, `PokemonType`, `Status`, `Effect`, `PokemonGender`

---

## 클래스 구조

### **slots** 정의 (55개)

Pokemon 클래스는 **메모리 효율**을 위해 `__slots__`를 사용합니다.

```python
class Pokemon:
    __slots__ = (
        # 기본 정보
        "_species",           # 종족 (예: "pikachu")
        "_name",              # 닉네임
        "_level",             # 레벨
        "_gender",            # 성별
        "_shiny",             # 색이 다른 포켓몬 여부

        # 타입
        "_type_1",            # 첫 번째 타입
        "_type_2",            # 두 번째 타입 (없으면 None)
        "_temporary_types",   # 임시 타입 (물기먹기, 할로윈 등)
        "_terastallized",     # 테라스탈 여부
        "_terastallized_type",# 테라 타입

        # HP 및 상태
        "_current_hp",        # 현재 HP
        "_max_hp",            # 최대 HP
        "_fainted",           # 기절 여부
        "_status",            # 상태이상 (BRN, PAR, SLP 등)
        "_status_counter",    # 상태이상 카운터

        # 스탯
        "_base_stats",        # 종족값
        "_stats",             # 실제 스탯
        "_boosts",            # 능력치 랭크 변화 (-6~+6)

        # 기술 및 특성
        "_moves",             # 보유 기술들 (Dict[str, Move])
        "_ability",           # 특성
        "_possible_abilities",# 가능한 특성 목록
        "_item",              # 소지 아이템

        # 효과
        "_effects",           # 현재 효과들 (혼란, 도발 등)

        # 배틀 상태
        "_active",            # 필드에 나와있는지
        "_active",            # ⚠️ 중복! (버그)
        "_first_turn",        # 교체 후 첫 턴 여부
        "_must_recharge",     # 반동 필요 (파괴광선)
        "_preparing_move",    # 준비 중인 기술 (솔라빔, 하늘을날다)
        "_preparing_target",  # 준비 기술의 대상
        "_protect_counter",   # 연속 방어 카운터
        "_revealed",          # 배틀에 등장했는지

        # 물리적 특성
        "_heightm",           # 키 (미터)
        "_weightkg",          # 무게 (킬로그램)

        # 메가진화 / Z기술 / 다이맥스
        "_was_mega",          # 메가진화 했었는지
        "_was_gmax",          # 거다이맥스 했었는지

        # 기타
        "_data",              # GenData (게임 데이터)
        "_last_request",      # 마지막 서버 요청
        "_last_details",      # 마지막 상세 정보
        # ... 등등 (총 55개)
    )
```

⚠️ **버그 발견**: `_active`가 두 번 선언되어 있습니다 (23번째와 24번째 줄).

---

## 속성 완전 목록

### 1. 기본 정보 (7개)

| 속성      | 타입            | 설명                   | 예시                        |
| --------- | --------------- | ---------------------- | --------------------------- |
| `species` | `str`           | 종족 이름              | `'pikachu'`                 |
| `name`    | `str`           | 닉네임 (없으면 종족명) | `'찌리리'` 또는 `'Pikachu'` |
| `level`   | `int`           | 레벨                   | `50`, `100`                 |
| `gender`  | `PokemonGender` | 성별                   | `PokemonGender.MALE`        |
| `shiny`   | `bool`          | 색이 다른 포켓몬       | `True`, `False`             |
| `height`  | `float`         | 키 (미터)              | `0.4`                       |
| `weight`  | `float`         | 무게 (킬로그램)        | `6.0`                       |

```python
# 사용 예
print(f"{pokemon.name} (Lv.{pokemon.level})")  # "찌리리 (Lv.50)"
print(f"종족: {pokemon.species}")               # "종족: pikachu"
print(f"성별: {pokemon.gender}")                # "성별: PokemonGender.MALE"
```

---

### 2. 타입 시스템 (7개)

| 속성               | 타입                    | 설명                    | 예시                                |
| ------------------ | ----------------------- | ----------------------- | ----------------------------------- |
| `type_1`           | `PokemonType`           | 첫 번째 타입            | `PokemonType.ELECTRIC`              |
| `type_2`           | `Optional[PokemonType]` | 두 번째 타입            | `None` 또는 `PokemonType.FLYING`    |
| `types`            | `List[PokemonType]`     | 타입 리스트 (1~2개)     | `[ELECTRIC]` 또는 `[WATER, GROUND]` |
| `original_types`   | `List[PokemonType]`     | 원래 타입 (변경 전)     | `[ELECTRIC]`                        |
| `tera_type`        | `Optional[PokemonType]` | 테라 타입               | `PokemonType.WATER`                 |
| `is_terastallized` | `bool`                  | 테라스탈 상태           | `True`, `False`                     |
| `_temporary_types` | `List[PokemonType]`     | 임시 타입 (물기먹기 등) | `[GRASS]`                           |

```python
# 타입 확인
if pokemon.type_1 == PokemonType.ELECTRIC:
    print("전기 타입!")

# 복합 타입
if pokemon.type_2 is not None:
    print(f"복합 타입: {pokemon.type_1.name}/{pokemon.type_2.name}")

# 테라스탈
if pokemon.is_terastallized:
    print(f"테라 타입: {pokemon.tera_type}")
```

**타입 변경 우선순위**:

1. **테라스탈** (최우선) → `type_1 = tera_type`, `type_2 = None`
2. **임시 타입** (물기먹기, 할로윈 등) → `types = _temporary_types`
3. **원래 타입** → `type_1`, `type_2`

---

### 3. HP 및 상태이상 (6개)

| 속성                  | 타입               | 설명        | 예시             |
| --------------------- | ------------------ | ----------- | ---------------- |
| `current_hp`          | `int`              | 현재 HP     | `85`             |
| `max_hp`              | `int`              | 최대 HP     | `100`            |
| `current_hp_fraction` | `float`            | HP 비율     | `0.85` (85%)     |
| `fainted`             | `bool`             | 기절 여부   | `False`          |
| `status`              | `Optional[Status]` | 상태이상    | `Status.BRN`     |
| `status_counter`      | `int`              | 상태 카운터 | `2` (잠듦 2턴째) |

```python
# HP 확인
if pokemon.current_hp_fraction < 0.3:
    print("HP가 위험!")

# 상태이상 확인
if pokemon.status == Status.BRN:
    print("화상 상태! 물리 공격력 절반")
elif pokemon.status == Status.PAR:
    print("마비 상태! 스피드 절반, 25% 행동 불가")
elif pokemon.status == Status.SLP:
    print(f"잠듦 {pokemon.status_counter}턴째")

# 기절 확인
if pokemon.fainted:
    print("기절!")
```

**Status 종류**:

- `BRN` (화상): 물리 공격력 절반, 매 턴 1/16 데미지
- `PAR` (마비): 스피드 절반, 25% 행동 불가
- `PSN` (독): 매 턴 1/8 데미지
- `TOX` (맹독): 턴마다 증가 (1/16, 2/16, 3/16, ...)
- `SLP` (잠듦): 1~3턴 행동 불가
- `FRZ` (얼음): 행동 불가 (20% 해제)
- `FNT` (기절)

---

### 4. 종족값 및 스탯 (3개)

| 속성         | 타입                       | 설명               | 예시                          |
| ------------ | -------------------------- | ------------------ | ----------------------------- |
| `base_stats` | `Dict[str, int]`           | 종족값 (고정)      | `{'hp': 35, 'atk': 55, ...}`  |
| `stats`      | `Dict[str, Optional[int]]` | 실제 스탯 (계산됨) | `{'hp': 115, 'atk': 90, ...}` |
| `boosts`     | `Dict[str, int]`           | 능력치 랭크 변화   | `{'atk': 2, 'def': -1}`       |

```python
# 종족값 (Species Base Stats) - 포켓몬 종족마다 고정
print(pokemon.base_stats)
# {'hp': 35, 'atk': 55, 'def': 40, 'spa': 50, 'spd': 50, 'spe': 90}

# 실제 스탯 (레벨, 노력치, 개체값 반영)
print(pokemon.stats)
# {'hp': 115, 'atk': 90, 'def': 75, 'spa': 85, 'spd': 85, 'spe': 145}

# 능력치 랭크 변화 (-6 ~ +6)
print(pokemon.boosts)
# {'atk': 2, 'def': 0, 'spa': 0, 'spd': 0, 'spe': -1, 'accuracy': 0, 'evasion': 0}
```

**능력치 랭크 변화 (Boosts)**:

- 범위: **-6 ~ +6**
- 배율:
  - +1 = 1.5배, +2 = 2배, +3 = 2.5배, +4 = 3배, +5 = 3.5배, +6 = 4배
  - -1 = 0.67배, -2 = 0.5배, -3 = 0.4배, -4 = 0.33배, -5 = 0.29배, -6 = 0.25배

```python
# 능력치 변화 예시
if pokemon.boosts['atk'] >= 2:
    print("공격이 크게 올랐다!")
if pokemon.boosts['spe'] <= -2:
    print("스피드가 크게 떨어졌다!")
```

---

### 5. 기술 및 특성 (4개)

| 속성                 | 타입              | 설명             | 예시                         |
| -------------------- | ----------------- | ---------------- | ---------------------------- |
| `moves`              | `Dict[str, Move]` | 보유 기술들      | `{'thunderbolt': Move, ...}` |
| `ability`            | `Optional[str]`   | 특성             | `'static'`                   |
| `possible_abilities` | `List[str]`       | 가능한 특성 목록 | `['static', 'lightningrod']` |
| `item`               | `Optional[str]`   | 소지 아이템      | `'leftovers'`                |

```python
# 기술 확인
for move_id, move in pokemon.moves.items():
    print(f"{move_id}: 위력 {move.base_power}, PP {move.current_pp}/{move.max_pp}")

# 특성 확인
if pokemon.ability == 'levitate':
    print("부유 특성 - 땅 타입 무효!")

# 아이템 확인
if pokemon.item == 'choicescarf':
    print("스카프 착용 - 스피드 1.5배, 기술 고정")
elif pokemon.item == 'leftovers':
    print("먹다 남은 음식 - 매 턴 1/16 회복")
```

**기술 (Moves) 구조**:

```python
pokemon.moves = {
    'thunderbolt': Move(id='thunderbolt', base_power=90, ...),
    'quickattack': Move(id='quickattack', base_power=40, ...),
    'irontail': Move(id='irontail', base_power=100, ...),
    'surf': Move(id='surf', base_power=90, ...)
}
```

---

### 6. 효과 및 휘발성 상태 (1개)

| 속성      | 타입                | 설명        | 예시                    |
| --------- | ------------------- | ----------- | ----------------------- |
| `effects` | `Dict[Effect, int]` | 현재 효과들 | `{Effect.CONFUSION: 2}` |

```python
# 효과 확인
if Effect.CONFUSION in pokemon.effects:
    turns = pokemon.effects[Effect.CONFUSION]
    print(f"혼란 {turns}턴 남음")

if Effect.LEECH_SEED in pokemon.effects:
    print("씨뿌리기 상태!")

if Effect.SUBSTITUTE in pokemon.effects:
    print("대타 인형 존재!")

if Effect.ATTRACT in pokemon.effects:
    print("헤롱헤롱 상태 - 50% 행동 불가")
```

**주요 효과들**:

- `CONFUSION` - 혼란 (1~4턴, 33% 자해)
- `LEECH_SEED` - 씨뿌리기 (매 턴 1/8 흡수)
- `SUBSTITUTE` - 대타 인형
- `ATTRACT` - 헤롱헤롱 (50% 행동 불가)
- `TAUNT` - 도발 (변화기 사용 불가)
- `ENCORE` - 앵콜 (같은 기술만 사용)
- `PROTECT` - 방어
- `DYNAMAX` - 다이맥스
- ... 200+ 효과

---

### 7. 배틀 상태 (8개)

| 속성               | 타입                | 설명              | 예시                  |
| ------------------ | ------------------- | ----------------- | --------------------- |
| `active`           | `bool`              | 필드에 나와있는지 | `True`                |
| `first_turn`       | `bool`              | 교체 후 첫 턴     | `True`                |
| `must_recharge`    | `bool`              | 반동 필요         | `True` (파괴광선)     |
| `preparing`        | `bool`              | 기술 준비 중      | `True` (솔라빔 1턴째) |
| `preparing_move`   | `Optional[Move]`    | 준비 중인 기술    | `Move('solarbeam')`   |
| `preparing_target` | `Optional[Pokemon]` | 준비 기술 대상    | `opponent_pokemon`    |
| `protect_counter`  | `int`               | 연속 방어 카운터  | `1`                   |
| `revealed`         | `bool`              | 배틀 등장 여부    | `True`                |

```python
# 활성 상태
if pokemon.active:
    print("필드에 나와있음!")

# 첫 턴
if pokemon.first_turn:
    print("이번 턴에 교체됨!")

# 반동
if pokemon.must_recharge:
    print("다음 턴 반동으로 행동 불가!")

# 준비 중
if pokemon.preparing:
    print(f"{pokemon.preparing_move.id} 준비 중...")

# 연속 방어
if pokemon.protect_counter > 0:
    print(f"방어 {pokemon.protect_counter}번째 - 실패율 상승")
```

---

### 8. 메가진화 / 다이맥스 / 테라스탈 (4개)

| 속성               | 타입   | 설명                | 예시   |
| ------------------ | ------ | ------------------- | ------ |
| `is_dynamaxed`     | `bool` | 다이맥스 중         | `True` |
| `is_terastallized` | `bool` | 테라스탈 중         | `True` |
| `_was_mega`        | `bool` | 메가진화 했었는지   | `True` |
| `_was_gmax`        | `bool` | 거다이맥스 했었는지 | `True` |

```python
# 다이맥스
if pokemon.is_dynamaxed:
    print("다이맥스 중! HP 2배, 기술이 다이맥스기로 변경")

# 테라스탈
if pokemon.is_terastallized:
    print(f"테라스탈! 타입이 {pokemon.tera_type}로 변경")

# 메가진화 (이미 했는지 확인)
if pokemon._was_mega:
    print("이미 메가진화함 (배틀당 1회)")
```

---

### 9. 기타 (4개)

| 속성              | 타입             | 설명             | 예시             |
| ----------------- | ---------------- | ---------------- | ---------------- |
| `pokeball`        | `Optional[str]`  | 몬스터볼 종류    | `'pokeball'`     |
| `stab_multiplier` | `float`          | STAB 배율        | `1.5` 또는 `2.0` |
| `_data`           | `GenData`        | 게임 데이터      | GenData 객체     |
| `_last_request`   | `Optional[Dict]` | 마지막 서버 요청 | `{...}`          |

```python
# STAB (Same Type Attack Bonus)
# - 일반: 1.5배
# - 테라스탈 (같은 타입): 2.0배
# - Adaptability 특성: 2.0배
# - 테라스탈 + Adaptability: 2.25배
stab = pokemon.stab_multiplier
if stab == 2.0:
    print("테라스탈 STAB 2배!")
elif stab == 1.5:
    print("일반 STAB 1.5배")
```

---

## 메서드 완전 목록

### 1. HP 관리 메서드 (5개)

#### `damage(hp_status: str)`

데미지를 받아 HP를 감소시킵니다.

```python
# 서버 메시지: "50/100" (현재HP/최대HP)
pokemon.damage("50/100")

# 결과
pokemon.current_hp  # 50
pokemon.max_hp      # 100
```

#### `heal(hp_status: str)`

HP를 회복합니다.

```python
pokemon.heal("75/100")
pokemon.current_hp  # 75
```

#### `set_hp(hp_status: str)`

HP를 직접 설정합니다.

```python
pokemon.set_hp("100/100")  # 완전 회복
```

#### `faint()`

포켓몬을 기절시킵니다.

```python
pokemon.faint()
pokemon.fainted  # True
pokemon.status   # Status.FNT
```

#### `set_hp_status(hp_status: str)`

HP와 상태이상을 동시에 설정합니다.

```python
# "50/100 brn" - HP 50/100, 화상 상태
pokemon.set_hp_status("50/100 brn")
pokemon.current_hp  # 50
pokemon.status      # Status.BRN
```

---

### 2. 능력치 변화 메서드 (4개)

#### `boost(stat: str, amount: int)`

능력치 랭크를 변화시킵니다.

```python
# 공격 +2
pokemon.boost('atk', 2)
pokemon.boosts['atk']  # 2

# 방어 -1
pokemon.boost('def', -1)
pokemon.boosts['def']  # -1

# 최대/최소 제한 (-6 ~ +6)
pokemon.boost('atk', 10)  # +6으로 제한됨
```

#### `set_boost(stat: str, amount: int)`

능력치 랭크를 직접 설정합니다.

```python
pokemon.set_boost('spe', -2)
pokemon.boosts['spe']  # -2
```

#### `clear_boosts()`

모든 능력치 변화를 초기화합니다.

```python
pokemon.clear_boosts()
pokemon.boosts  # {'atk': 0, 'def': 0, ...}
```

#### `clear_negative_boosts()`

음수 능력치 변화만 초기화합니다.

```python
pokemon.boosts = {'atk': 2, 'def': -2, 'spe': -1}
pokemon.clear_negative_boosts()
pokemon.boosts  # {'atk': 2, 'def': 0, 'spe': 0}
```

---

### 3. 상태이상 메서드 (2개)

#### `cure_status(status: Optional[str] = None)`

상태이상을 치료합니다.

```python
# 특정 상태 치료
pokemon.cure_status('brn')
pokemon.status  # None

# 모든 상태 치료
pokemon.cure_status()
```

#### `set_status(status: Status)`

상태이상을 설정합니다.

```python
pokemon.status = Status.BRN
# 또는
pokemon.status = 'brn'  # 문자열도 가능
```

---

### 4. 효과 관리 메서드 (2개)

#### `start_effect(effect_str: str)`

효과를 시작합니다.

```python
# 혼란 시작
pokemon.start_effect('confusion')
Effect.CONFUSION in pokemon.effects  # True

# 씨뿌리기
pokemon.start_effect('leechseed')
```

#### `end_effect(effect_str: str)`

효과를 종료합니다.

```python
pokemon.end_effect('confusion')
Effect.CONFUSION in pokemon.effects  # False
```

---

### 5. 교체 메서드 (2개)

#### `switch_in(details: str = "")`

포켓몬을 교체해서 필드에 내보냅니다.

```python
# details: "Pikachu, L50, M" (종족, 레벨, 성별)
pokemon.switch_in("Pikachu, L50, M")

pokemon.active      # True
pokemon.first_turn  # True
```

#### `switch_out()`

포켓몬을 필드에서 회수합니다.

```python
pokemon.switch_out()

pokemon.active       # False
pokemon.first_turn   # False
pokemon.effects      # {} (대부분 효과 제거)
pokemon.boosts       # {'atk': 0, ...} (랭크 초기화)
```

---

### 6. 기술 사용 메서드 (3개)

#### `moved(move_id: str, failed: bool = False, use: bool = True)`

기술을 사용합니다.

```python
# 10만볼트 사용
pokemon.moved('thunderbolt')

# PP 소모됨
pokemon.moves['thunderbolt'].current_pp  # 14 (15 → 14)

# 기술 실패
pokemon.moved('thunderbolt', failed=True)
```

#### `prepare(move_id: str, target: Pokemon)`

2턴 기술을 준비합니다 (솔라빔, 하늘을날다 등).

```python
# 솔라빔 1턴째
pokemon.prepare('solarbeam', opponent_pokemon)

pokemon.preparing        # True
pokemon.preparing_move   # Move('solarbeam')
pokemon.preparing_target # opponent_pokemon
```

#### `used_z_move()`

Z기술을 사용했음을 기록합니다.

```python
pokemon.used_z_move()
# (배틀당 1회 제한 처리)
```

---

### 7. 타입 상성 메서드 (1개)

#### `damage_multiplier(type_or_move: Union[PokemonType, Move]) -> float`

타입 상성 배율을 계산합니다.

```python
# 타입으로 계산
multiplier = pokemon.damage_multiplier(PokemonType.ELECTRIC)
# pokemon이 물 타입이면 → 2.0 (효과가 굉장)
# pokemon이 풀 타입이면 → 0.5 (효과가 별로)
# pokemon이 땅 타입이면 → 0.0 (효과가 없다)

# Move 객체로 계산
move = Move('thunderbolt')
multiplier = pokemon.damage_multiplier(move)
```

**반환값**:

- `4.0` - 4배 (복합 타입 양쪽 모두 약점)
- `2.0` - 효과가 굉장
- `1.0` - 보통
- `0.5` - 효과가 별로
- `0.25` - 1/4배
- `0.0` - 효과가 없다

---

### 8. 폼 체인지 / 진화 메서드 (4개)

#### `forme_change(species: str)`

폼을 변경합니다 (로토무, 데오키시스 등).

```python
# 히트 로토무 → 워시 로토무
pokemon.forme_change('rotomwash')
pokemon.species  # 'rotomwash'
pokemon.types    # [PokemonType.WATER, PokemonType.ELECTRIC]
```

#### `mega_evolve(mega_species: str)`

메가진화합니다.

```python
pokemon.mega_evolve('charizardmegax')
pokemon.species    # 'charizardmegax'
pokemon._was_mega  # True
```

#### `primal_revert(species: str)`

원시회귀합니다 (그란돈, 카이오가).

```python
pokemon.primal_revert('kyogreprimal')
```

#### `terastallize(tera_type: PokemonType)`

테라스탈합니다.

```python
pokemon.terastallize(PokemonType.WATER)
pokemon.is_terastallized  # True
pokemon.tera_type         # PokemonType.WATER
pokemon.type_1            # PokemonType.WATER
pokemon.type_2            # None
```

---

### 9. 기타 메서드 (3개)

#### `transform(into: Pokemon)`

변신합니다.

```python
ditto.transform(pikachu)
ditto.species  # 'pikachu'
ditto.types    # pikachu와 동일
ditto.moves    # pikachu와 동일
ditto.stats    # pikachu와 동일
```

#### `identifier(player_role: str) -> str`

Showdown 로그용 식별자를 반환합니다.

```python
identifier = pokemon.identifier('p1')
# "p1: Pikachu"
```

#### `update_from_request(request: Dict)`

서버 요청 데이터로 포켓몬을 업데이트합니다.

```python
# 서버에서 온 요청 데이터
request = {
    'species': 'Pikachu',
    'level': 50,
    'moves': ['thunderbolt', 'quickattack', 'irontail'],
    'ability': 'static',
    'item': 'lightball',
    'stats': {'hp': 115, 'atk': 90, ...},
    # ...
}

pokemon.update_from_request(request)
```

---

## 주요 사용 패턴

### 1. 포켓몬 정보 출력

```python
def print_pokemon_info(pokemon: Pokemon):
    print(f"=== {pokemon.name} (Lv.{pokemon.level}) ===")
    print(f"종족: {pokemon.species}")
    print(f"타입: {'/'.join(t.name for t in pokemon.types)}")
    print(f"HP: {pokemon.current_hp}/{pokemon.max_hp} ({pokemon.current_hp_fraction:.1%})")
    print(f"특성: {pokemon.ability}")
    print(f"아이템: {pokemon.item}")

    if pokemon.status:
        print(f"상태이상: {pokemon.status.name}")

    print(f"능력치 변화:")
    for stat, boost in pokemon.boosts.items():
        if boost != 0:
            print(f"  {stat}: {boost:+d}")

    print(f"기술:")
    for move_id, move in pokemon.moves.items():
        print(f"  - {move.id}: {move.base_power} / {move.current_pp}/{move.max_pp} PP")
```

---

### 2. 타입 상성 체크

```python
def check_effectiveness(attacker: Pokemon, defender: Pokemon, move: Move) -> str:
    """타입 상성을 체크하고 메시지를 반환"""
    effectiveness = defender.damage_multiplier(move)

    if effectiveness == 0:
        return "효과가 없다..."
    elif effectiveness >= 4.0:
        return "효과가 굉장! (4배)"
    elif effectiveness >= 2.0:
        return "효과가 굉장!"
    elif effectiveness <= 0.25:
        return "효과가 별로... (1/4배)"
    elif effectiveness <= 0.5:
        return "효과가 별로..."
    else:
        return "보통"

# 사용
msg = check_effectiveness(pikachu, gyarados, thunderbolt)
print(msg)  # "효과가 굉장! (4배)" - 물/비행 타입에 전기
```

---

### 3. 교체 가능 여부 확인

```python
def can_switch(pokemon: Pokemon, battle: Battle) -> bool:
    """교체 가능한지 확인"""
    # 기절했으면 불가
    if pokemon.fainted:
        return False

    # 이미 활성이면 불가
    if pokemon.active:
        return False

    # 배틀에서 교체 가능한 리스트에 있는지 확인
    return pokemon in battle.available_switches

# 사용
for poke in battle.team.values():
    if can_switch(poke, battle):
        print(f"{poke.name} 교체 가능!")
```

---

### 4. 최적 기술 선택 (타입 상성 기반)

```python
def choose_best_move(battle: Battle) -> str:
    """타입 상성이 가장 좋은 기술 선택"""
    my_pokemon = battle.active_pokemon
    opp_pokemon = battle.opponent_active_pokemon

    best_move = None
    best_effectiveness = 0.0

    for move in battle.available_moves:
        # 타입 상성 계산
        effectiveness = opp_pokemon.damage_multiplier(move)

        # 위력 고려
        effective_power = move.base_power * effectiveness

        if effective_power > best_effectiveness:
            best_effectiveness = effective_power
            best_move = move

    if best_move:
        return f"/choose move {best_move.id}"
    else:
        return battle.choose_random_move()
```

---

### 5. 능력치 변화 추적

```python
def get_effective_stat(pokemon: Pokemon, stat_name: str) -> float:
    """능력치 변화를 반영한 실제 스탯 계산"""
    base_stat = pokemon.stats.get(stat_name, 0)
    boost = pokemon.boosts.get(stat_name, 0)

    # 능력치 변화 배율
    if boost >= 0:
        multiplier = (2 + boost) / 2
    else:
        multiplier = 2 / (2 - boost)

    # 상태이상 보정
    if stat_name == 'atk' and pokemon.status == Status.BRN:
        multiplier *= 0.5  # 화상은 물리 공격력 절반

    if stat_name == 'spe' and pokemon.status == Status.PAR:
        multiplier *= 0.5  # 마비는 스피드 절반

    return base_stat * multiplier

# 사용
effective_atk = get_effective_stat(pokemon, 'atk')
print(f"실제 공격력: {effective_atk:.0f}")
```

---

## SimplifiedPokemon 구현 가이드

### 1. 복사해야 할 속성

```python
class SimplifiedPokemon:
    def __init__(self, poke_env_pokemon: Pokemon):
        # === 기본 정보 (불변) ===
        self.species = poke_env_pokemon.species
        self.level = poke_env_pokemon.level
        self.gender = poke_env_pokemon.gender

        # === 타입 (변경 가능) ===
        self.type_1 = poke_env_pokemon.type_1
        self.type_2 = poke_env_pokemon.type_2
        self.types = poke_env_pokemon.types.copy()  # List

        # === HP (시뮬레이션마다 변경) ===
        self.current_hp = poke_env_pokemon.current_hp
        self.max_hp = poke_env_pokemon.max_hp

        # === 상태이상 (변경 가능) ===
        self.status = poke_env_pokemon.status
        self.status_counter = poke_env_pokemon.status_counter

        # === 스탯 ===
        self.base_stats = poke_env_pokemon.base_stats.copy()
        self.stats = poke_env_pokemon.stats.copy()
        self.boosts = poke_env_pokemon.boosts.copy()

        # === 기술 (deepcopy 필요!) ===
        import copy
        self.moves = copy.deepcopy(poke_env_pokemon.moves)

        # === 특성 및 아이템 ===
        self.ability = poke_env_pokemon.ability
        self.item = poke_env_pokemon.item

        # === 효과 ===
        self.effects = poke_env_pokemon.effects.copy()

        # === 배틀 상태 ===
        self.active = poke_env_pokemon.active
        self.first_turn = poke_env_pokemon.first_turn
        self.must_recharge = poke_env_pokemon.must_recharge
        self.protect_counter = poke_env_pokemon.protect_counter
```

### 2. 필요한 메서드

```python
class SimplifiedPokemon:
    # ... __init__ ...

    def damage(self, amount: int):
        """데미지 받기"""
        self.current_hp = max(0, self.current_hp - amount)
        if self.current_hp == 0:
            self.faint()

    def heal(self, amount: int):
        """회복"""
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    def faint(self):
        """기절"""
        self.current_hp = 0
        self.status = Status.FNT

    def boost(self, stat: str, amount: int):
        """능력치 변화"""
        current = self.boosts.get(stat, 0)
        self.boosts[stat] = max(-6, min(6, current + amount))

    def damage_multiplier(self, move_type: PokemonType) -> float:
        """타입 상성 계산"""
        from poke_env.data import GenData

        data = GenData.from_gen(9)  # 9세대 데이터

        multiplier = 1.0
        for poke_type in self.types:
            multiplier *= poke_type.damage_multiplier(
                move_type,
                type_chart=data.type_chart
            )

        return multiplier

    def get_effective_stat(self, stat_name: str) -> float:
        """능력치 변화 반영한 실제 스탯"""
        base = self.stats.get(stat_name, 0)
        boost = self.boosts.get(stat_name, 0)

        if boost >= 0:
            multiplier = (2 + boost) / 2
        else:
            multiplier = 2 / (2 - boost)

        # 상태이상 보정
        if stat_name == 'atk' and self.status == Status.BRN:
            multiplier *= 0.5
        if stat_name == 'spe' and self.status == Status.PAR:
            multiplier *= 0.5

        return base * multiplier
```

### 3. 복사 시 주의사항

| 속성                            | 복사 방법         | 이유                         |
| ------------------------------- | ----------------- | ---------------------------- |
| `species`, `level`, `gender`    | 직접 할당         | 불변 값                      |
| `types`                         | `.copy()`         | List이지만 Enum 원소 (안전)  |
| `base_stats`, `stats`, `boosts` | `.copy()`         | Dict, 얕은 복사 OK           |
| `moves`                         | `copy.deepcopy()` | **Move 객체 내부 상태 있음** |
| `effects`                       | `.copy()`         | Dict, 얕은 복사 OK           |
| `status`                        | 직접 할당         | Enum (불변)                  |
| `ability`, `item`               | 직접 할당         | 문자열 (불변)                |

**중요**: `moves`는 **deepcopy 필수**입니다!

```python
# ❌ 잘못된 방법
self.moves = poke_env_pokemon.moves  # 원본과 공유됨!

# ❌ 얕은 복사도 불충분
self.moves = poke_env_pokemon.moves.copy()  # Move 객체는 여전히 공유

# ✅ 올바른 방법
import copy
self.moves = copy.deepcopy(poke_env_pokemon.moves)
```

---

## 다음 문서

- **[MOVE_CLASS.md](MOVE_CLASS.md)** - Move 클래스 완전 분석
- **[BATTLE_CLASS.md](BATTLE_CLASS.md)** - Battle 클래스 완전 분석
- **[SUPPORTING_CLASSES.md](SUPPORTING_CLASSES.md)** - 지원 클래스들
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - SimplifiedBattle 구현 가이드

---

**끝!** ⚡
