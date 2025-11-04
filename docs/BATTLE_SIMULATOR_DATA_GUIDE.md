# 배틀 시뮬레이터 구현 필수 데이터 가이드

## 📌 목차

1. [데이터 개요](#데이터-개요)
2. [Pokemon Showdown 데이터 위치](#pokemon-showdown-데이터-위치)
3. [필수 데이터 상세 설명](#필수-데이터-상세-설명)
4. [poke-env에서 데이터 접근하기](#poke-env에서-데이터-접근하기)
5. [SimplifiedBattle 구현 체크리스트](#simplifiedbattle-구현-체크리스트)

---

## 데이터 개요

배틀 시뮬레이터를 구현하려면 **Pokemon Showdown**의 데이터를 활용해야 합니다.

### ⚠️ 중요 개념

**poke-env는 라이브러리입니다!**

```python
from poke_env.player import Player
from poke_env.battle import Battle
from poke_env.data import GenData  # 데이터 접근용
```

- `poke-env`는 `pip install poke_env`으로 설치한 **외부 패키지**
- 여러분의 프로젝트 폴더가 아닌 **Python site-packages** 폴더에 설치됨
- Windows 기준 위치 예시: `C:\Users\[사용자]\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\poke_env\`

**Pokemon Showdown은 서버입니다!**

- 여러분의 `pokemon/pokemon-showdown/` 폴더에 있는 것은 Pokemon Showdown **서버 소스코드**
- TypeScript로 작성되어 있음
- 모든 게임 데이터가 여기에 있음

---

## Pokemon Showdown 데이터 위치

### 📂 핵심 데이터 파일들

| 데이터 유형       | 파일 경로            | 라인 수  | 설명                      |
| ----------------- | -------------------- | -------- | ------------------------- |
| **포켓몬 도감**   | `data/pokedex.ts`    | 20,121줄 | 모든 포켓몬의 기본 정보   |
| **기술 정보**     | `data/moves.ts`      | 22,114줄 | 모든 기술의 상세 정보     |
| **타입 상성**     | `data/typechart.ts`  | 485줄    | 타입별 데미지 배율        |
| **특성 정보**     | `data/abilities.ts`  | 5,632줄  | 모든 특성의 효과          |
| **아이템 정보**   | `data/items.ts`      | 7,700줄  | 모든 아이템의 효과        |
| **성격 정보**     | `data/natures.ts`    | 118줄    | 25가지 성격의 스탯 보정   |
| **상태이상/날씨** | `data/conditions.ts` | 896줄    | 상태이상, 날씨, 필드 효과 |

---

## 필수 데이터 상세 설명

### 1. 포켓몬 기본 정보 (Pokedex)

**파일**: `pokemon-showdown/data/pokedex.ts` (20,121줄)

**포함 데이터**:

```typescript
bulbasaur: {
    num: 1,                          // 도감 번호
    name: "Bulbasaur",               // 이름
    types: ["Grass", "Poison"],      // 타입 (최대 2개)
    baseStats: {                     // 종족값
        hp: 45,
        atk: 49,
        def: 49,
        spa: 65,
        spd: 65,
        spe: 45
    },
    abilities: {                     // 특성
        0: "Overgrow",              // 일반 특성
        H: "Chlorophyll"            // 숨겨진 특성
    },
    weightkg: 6.9,                  // 몸무게 (kg)
    evos: ["Ivysaur"],              // 진화 후 포켓몬
    eggGroups: ["Monster", "Grass"] // 알 그룹
}
```

**SimplifiedBattle에서 필요한 이유**:

- ✅ `baseStats`: 데미지 계산에 필수 (공격, 방어, 특공, 특방)
- ✅ `types`: 타입 상성 계산
- ✅ `abilities`: 특성 효과 적용
- ✅ `weightkg`: 풀베기(Grass Knot), 집어던지기(Heavy Slam) 등의 기술에 필요

---

### 2. 기술 정보 (Moves)

**파일**: `pokemon-showdown/data/moves.ts` (22,114줄)

**포함 데이터**:

```typescript
thunderbolt: {
    num: 85,                        // 기술 번호
    accuracy: 100,                  // 명중률
    basePower: 90,                  // 위력
    category: "Special",            // 물리/특수/변화
    name: "Thunderbolt",
    pp: 15,                         // PP
    priority: 0,                    // 우선도
    flags: {protect: 1, mirror: 1}, // 기술 플래그
    secondary: {                    // 추가 효과
        chance: 10,                 // 발동 확률 10%
        status: 'par'               // 마비
    },
    target: "normal",               // 대상 (단일, 전체 등)
    type: "Electric"                // 타입
}
```

**SimplifiedBattle에서 필요한 이유**:

- ✅ `basePower`, `category`: 데미지 계산
- ✅ `type`: 타입 상성 적용
- ✅ `accuracy`: 명중 판정
- ✅ `priority`: 행동 순서 결정
- ✅ `secondary`: 추가 효과 (화상, 마비 등)
- ✅ `flags`: 방어/판별/신비의부적 등의 상호작용

---

### 3. 타입 상성표 (TypeChart)

**파일**: `pokemon-showdown/data/typechart.ts` (485줄)

**포함 데이터**:

```typescript
electric: {
    damageTaken: {
        Bug: 0,        // 보통 (1배)
        Dark: 0,       // 보통 (1배)
        Dragon: 0,     // 보통 (1배)
        Electric: 2,   // 별로 (0.5배)
        Fighting: 0,   // 보통 (1배)
        Fire: 0,       // 보통 (1배)
        Flying: 2,     // 별로 (0.5배)
        Grass: 0,      // 보통 (1배)
        Ground: 1,     // 효과가 굉장 (2배)
        Ice: 0,        // 보통 (1배)
        Poison: 0,     // 보통 (1배)
        Psychic: 0,    // 보통 (1배)
        Rock: 0,       // 보통 (1배)
        Steel: 2,      // 별로 (0.5배)
        Water: 0,      // 보통 (1배)
        Fairy: 0,      // 보통 (1배)
        Ghost: 0,      // 보통 (1배)
        par: 3         // 전기 타입은 마비 무효
    }
}
```

**코드값 의미**:

- `0`: 보통 효과 (×1.0)
- `1`: 효과가 굉장 (×2.0)
- `2`: 효과가 별로 (×0.5)
- `3`: 무효 (×0)

**SimplifiedBattle에서 필요한 이유**:

- ✅ **데미지 계산의 핵심!**
- ✅ 전기 기술 → 땅 타입 = 무효
- ✅ 물 기술 → 불꽃 타입 = 2배
- ✅ 불꽃 기술 → 물 타입 = 0.5배

---

### 4. 특성 정보 (Abilities)

**파일**: `pokemon-showdown/data/abilities.ts` (5,632줄)

**포함 데이터**:

```typescript
intimidate: {
    name: "Intimidate",
    // 등장 시 상대 공격 1랭크 다운
    onStart(pokemon) {
        let activated = false;
        for (const target of pokemon.adjacentFoes()) {
            if (!activated) {
                this.add('-ability', pokemon, 'Intimidate', 'boost');
                activated = true;
            }
            if (target.volatiles['substitute']) {
                this.add('-immune', target);
            } else {
                this.boost({atk: -1}, target, pokemon, null, true);
            }
        }
    },
    flags: {},
    rating: 3.5,
    num: 22
}
```

**SimplifiedBattle에서 필요한 이유**:

- ✅ 특성은 **배틀 로직을 완전히 바꿈**
- ✅ 예시:
  - **위협(Intimidate)**: 등장 시 상대 공격 ↓
  - **부유(Levitate)**: 땅 타입 기술 무효
  - **특성변경(Mold Breaker)**: 상대 특성 무시
  - **타입 변경(Refrigerate)**: 노말 타입 기술 → 얼음 타입으로 변경 & 위력 1.2배

---

### 5. 아이템 정보 (Items)

**파일**: `pokemon-showdown/data/items.ts` (7,700줄)

**포함 데이터**:

```typescript
choicescarf: {
    name: "Choice Scarf",
    spritenum: 78,
    fling: {
        basePower: 10
    },
    // 스피드 1.5배
    onModifySpe(spe, pokemon) {
        return this.chainModify(1.5);
    },
    // 같은 기술만 사용 가능
    onStart(pokemon) {
        if (pokemon.volatiles['choicelock']) {
            this.debug('removing choicelock: ' + pokemon.volatiles['choicelock']);
        }
        pokemon.removeVolatile('choicelock');
    },
    onModifyMove(move, pokemon) {
        pokemon.addVolatile('choicelock');
    },
    num: 287,
    gen: 4
}
```

**SimplifiedBattle에서 필요한 이유**:

- ✅ **게임 균형의 핵심 요소**
- ✅ 예시:
  - **구애스카프(Choice Scarf)**: 스피드 1.5배, 같은 기술만 사용 가능
  - **생명의구슬(Life Orb)**: 위력 1.3배, 사용 시 HP 10% 감소
  - **자뭉열매(Sitrus Berry)**: HP 50% 이하 시 HP 25% 회복
  - **진화의휘석(Eviolite)**: 미진화 포켓몬의 방어/특방 1.5배

---

### 6. 성격 정보 (Natures)

**파일**: `pokemon-showdown/data/natures.ts` (118줄)

**포함 데이터**:

```typescript
// 성격은 총 25가지
adamant: {
    name: "Adamant",  // 고집
    plus: 'atk',      // 공격 ↑ (×1.1)
    minus: 'spa'      // 특공 ↓ (×0.9)
},
modest: {
    name: "Modest",   // 조심
    plus: 'spa',      // 특공 ↑
    minus: 'atk'      // 공격 ↓
},
timid: {
    name: "Timid",    // 겁쟁이
    plus: 'spe',      // 스피드 ↑
    minus: 'atk'      // 공격 ↓
},
hardy: {
    name: "Hardy"     // 노력 (보정 없음)
    // plus, minus 없음
}
```

**SimplifiedBattle에서 필요한 이유**:

- ✅ **실전 스탯 계산에 필수**
- ✅ 공격 ↑ / 특공 ↓ 성격 = 물리 어택커에 유리
- ✅ 특공 ↑ / 공격 ↓ 성격 = 특수 어택커에 유리
- ✅ 스피드 ↑ 성격 = 선공 확보

**스탯 계산 공식** (레벨 100 기준):

```python
# HP를 제외한 스탯
stat = ((2 * base_stat + IV + EV/4) * level / 100 + 5) * nature_multiplier

# 성격 보정
nature_multiplier = 1.1  # plus 스탯
nature_multiplier = 0.9  # minus 스탯
nature_multiplier = 1.0  # 보정 없음
```

---

### 7. 상태이상 및 필드 효과 (Conditions)

**파일**: `pokemon-showdown/data/conditions.ts` (896줄)

**포함 데이터**:

#### 7-1. 상태이상 (Status)

```typescript
// 화상 (brn)
brn: {
    name: 'brn',
    effectType: 'Status',
    onStart(target, source, sourceEffect) {
        this.add('-status', target, 'brn');
    },
    // 매 턴 최대 HP의 1/16 데미지
    onResidualOrder: 10,
    onResidual(pokemon) {
        this.damage(pokemon.baseMaxhp / 16);
    }
    // 물리 공격력 절반 (코드는 damage 함수에서 직접 처리)
}

// 마비 (par)
par: {
    name: 'par',
    effectType: 'Status',
    // 스피드 50% 감소
    onModifySpe(spe, pokemon) {
        if (!pokemon.hasAbility('quickfeet')) {
            spe = Math.floor(spe * 50 / 100);
        }
        return spe;
    },
    // 25% 확률로 행동 불가
    onBeforeMove(pokemon) {
        if (this.randomChance(1, 4)) {
            this.add('cant', pokemon, 'par');
            return false;
        }
    }
}

// 잠듦 (slp)
slp: {
    name: 'slp',
    effectType: 'Status',
    onStart(target, source, sourceEffect) {
        // 1~3턴 지속
        this.effectState.startTime = this.random(2, 5);
        this.effectState.time = this.effectState.startTime;
    },
    // 잠든 동안 행동 불가
    onBeforeMove(pokemon, target, move) {
        pokemon.statusState.time--;
        if (pokemon.statusState.time <= 0) {
            pokemon.cureStatus();
            return;
        }
        this.add('cant', pokemon, 'slp');
        return false;  // 행동 불가
    }
}

// 얼음 (frz)
frz: {
    name: 'frz',
    effectType: 'Status',
    // 20% 확률로 해제, 아니면 행동 불가
    onBeforeMove(pokemon, target, move) {
        if (this.randomChance(1, 5)) {
            pokemon.cureStatus();
            return;
        }
        this.add('cant', pokemon, 'frz');
        return false;
    }
}

// 독 (psn)
psn: {
    name: 'psn',
    effectType: 'Status',
    // 매 턴 최대 HP의 1/8 데미지
    onResidual(pokemon) {
        this.damage(pokemon.baseMaxhp / 8);
    }
}

// 맹독 (tox)
tox: {
    name: 'tox',
    effectType: 'Status',
    // 턴이 지날수록 데미지 증가 (1/16, 2/16, 3/16, ...)
    onStart(target, source, sourceEffect) {
        this.effectState.stage = 0;
    },
    onResidual(pokemon) {
        if (this.effectState.stage < 15) {
            this.effectState.stage++;
        }
        this.damage(this.clampIntRange(pokemon.baseMaxhp / 16, 1) * this.effectState.stage);
    }
}
```

#### 7-2. 날씨 (Weather)

```typescript
// 비 (RainDance)
raindance: {
    name: 'RainDance',
    effectType: 'Weather',
    duration: 5,  // 5턴 지속
    // 물 타입 기술 1.5배, 불꽃 타입 기술 0.5배
    onWeatherModifyDamage(damage, attacker, defender, move) {
        if (move.type === 'Water') {
            this.debug('rain water boost');
            return this.chainModify(1.5);
        }
        if (move.type === 'Fire') {
            this.debug('rain fire suppress');
            return this.chainModify(0.5);
        }
    }
}

// 맑음 (SunnyDay)
sunnyday: {
    name: 'SunnyDay',
    effectType: 'Weather',
    duration: 5,
    // 불꽃 타입 기술 1.5배, 물 타입 기술 0.5배
    onWeatherModifyDamage(damage, attacker, defender, move) {
        if (move.type === 'Fire') {
            return this.chainModify(1.5);
        }
        if (move.type === 'Water') {
            return this.chainModify(0.5);
        }
    }
}

// 모래바람 (Sandstorm)
sandstorm: {
    name: 'Sandstorm',
    effectType: 'Weather',
    duration: 5,
    // 바위/땅/강철 타입 제외 매 턴 1/16 데미지
    onResidual(pokemon) {
        this.damage(pokemon.baseMaxhp / 16);
    },
    // 바위 타입의 특방 1.5배
    onModifySpD(spd, pokemon) {
        if (pokemon.hasType('Rock')) {
            return this.chainModify(1.5);
        }
    }
}

// 싸라기눈 (Hail / Snow)
hail: {
    name: 'Hail',
    effectType: 'Weather',
    duration: 5,
    // 얼음 타입 제외 매 턴 1/16 데미지
    onResidual(pokemon) {
        this.damage(pokemon.baseMaxhp / 16);
    }
}
```

#### 7-3. 필드 효과 (Terrain)

```typescript
// 일렉트릭필드 (Electric Terrain)
electricterrain: {
    duration: 5,
    // 땅에 있는 포켓몬의 전기 기술 1.3배
    onBasePower(basePower, attacker, defender, move) {
        if (move.type === 'Electric' && attacker.isGrounded()) {
            return this.chainModify([5325, 4096]);  // 1.3배
        }
    },
    // 잠듦 상태 방지
    onSetStatus(status, target, source, effect) {
        if (status.id === 'slp' && target.isGrounded()) {
            return false;
        }
    }
}

// 그래스필드 (Grassy Terrain)
grassyterrain: {
    duration: 5,
    // 풀 기술 1.3배
    onBasePower(basePower, attacker, defender, move) {
        if (move.type === 'Grass' && attacker.isGrounded()) {
            return this.chainModify([5325, 4096]);
        }
    },
    // 매 턴 HP 1/16 회복
    onResidual(pokemon) {
        if (pokemon.isGrounded()) {
            this.heal(pokemon.baseMaxhp / 16);
        }
    }
}
```

#### 7-4. 장판 기술 (Entry Hazards)

```typescript
// 스텔스록 (Stealth Rock)
stealthrock: {
    // 교체 시 타입 상성에 따라 데미지
    onSwitchIn(pokemon) {
        const typeMod = this.clampIntRange(pokemon.runEffectiveness(this.dex.getActiveMove('stealthrock')), -6, 6);
        this.damage(pokemon.maxhp * Math.pow(2, typeMod) / 8);
    }
}

// 압정뿌리기 (Spikes)
spikes: {
    // 최대 3겹 (1겹: 1/8, 2겹: 1/6, 3겹: 1/4)
    onSwitchIn(pokemon) {
        if (!pokemon.isGrounded()) return;
        const damageAmounts = [0, 3, 4, 6];  // [0겹, 1겹, 2겹, 3겹]
        this.damage(damageAmounts[this.effectState.layers] * pokemon.maxhp / 24);
    }
}

// 독압정 (Toxic Spikes)
toxicspikes: {
    // 1겹: 독, 2겹: 맹독
    onSwitchIn(pokemon) {
        if (!pokemon.isGrounded()) return;
        if (this.effectState.layers >= 2) {
            pokemon.trySetStatus('tox', pokemon.side.foe.active[0]);
        } else {
            pokemon.trySetStatus('psn', pokemon.side.foe.active[0]);
        }
    }
}

// 끈적끈적네트 (Sticky Web)
stickyweb: {
    // 교체 시 스피드 1랭크 다운
    onSwitchIn(pokemon) {
        if (pokemon.isGrounded()) {
            this.add('-activate', pokemon, 'move: Sticky Web');
            this.boost({spe: -1}, pokemon, this.effectState.source, this.dex.getActiveMove('stickyweb'));
        }
    }
}
```

#### 7-5. 사이드 효과 (Side Conditions)

```typescript
// 리플렉터 (Reflect) - 물리 데미지 절반
reflect: {
    duration: 5,
    onSideStart(side) {
        this.add('-sidestart', side, 'Reflect');
    },
    onAnyModifyDamage(damage, source, target, move) {
        if (target !== source && target.side === this.effectState.target && move.category === 'Physical') {
            return this.chainModify(0.5);  // 더블배틀에서는 2/3
        }
    }
}

// 빛의장막 (Light Screen) - 특수 데미지 절반
lightscreen: {
    duration: 5,
    onSideStart(side) {
        this.add('-sidestart', side, 'Light Screen');
    },
    onAnyModifyDamage(damage, source, target, move) {
        if (target !== source && target.side === this.effectState.target && move.category === 'Special') {
            return this.chainModify(0.5);
        }
    }
}

// 오로라베일 (Aurora Veil) - 물리/특수 둘 다 절반 (싸라기눈 날씨 필요)
auroraveil: {
    duration: 5,
    onAnyModifyDamage(damage, source, target, move) {
        if (target !== source && target.side === this.effectState.target) {
            if ((move.category === 'Physical' || move.category === 'Special')) {
                return this.chainModify(0.5);
            }
        }
    }
}
```

**SimplifiedBattle에서 필요한 이유**:

- ✅ **상태이상**: 화상 = 물리 공격력 절반, 마비 = 스피드 절반
- ✅ **날씨**: 비 = 물 기술 1.5배, 맑음 = 불꽃 기술 1.5배
- ✅ **필드**: 일렉트릭필드 = 전기 기술 1.3배
- ✅ **장판 기술**: 스텔스록, 압정뿌리기, 독압정
- ✅ **사이드 효과**: 리플렉터, 빛의장막

---

## poke-env에서 데이터 접근하기

### 방법 1: poke-env 라이브러리 사용

poke-env는 Pokemon Showdown의 데이터를 **이미 파싱해서 제공**합니다.

```python
from poke_env.battle import Battle
from poke_env.data import GenData

# 8세대 데이터 로드
gen_data = GenData.from_gen(8)

# 포켓몬 정보 접근
bulbasaur = gen_data.pokedex['bulbasaur']
print(bulbasaur['baseStats'])  # {'hp': 45, 'atk': 49, 'def': 49, ...}
print(bulbasaur['types'])      # ['Grass', 'Poison']

# 기술 정보 접근
thunderbolt = gen_data.moves['thunderbolt']
print(thunderbolt['basePower'])  # 90
print(thunderbolt['type'])       # 'Electric'

# 타입 상성 접근
type_chart = gen_data.type_chart
effectiveness = type_chart.get_effectiveness('Electric', 'Water')
print(effectiveness)  # 2.0 (효과가 굉장!)
```

### 방법 2: Battle 객체에서 접근

```python
from poke_env.player import Player

class MyPlayer(Player):
    def choose_move(self, battle: Battle):
        # 현재 배틀의 활성 포켓몬
        my_pokemon = battle.active_pokemon

        # 포켓몬 정보
        print(my_pokemon.species)      # "Pikachu"
        print(my_pokemon.base_stats)   # {'hp': 35, 'atk': 55, ...}
        print(my_pokemon.types)        # (PokemonType.ELECTRIC,)

        # 기술 정보
        for move_id, move in my_pokemon.moves.items():
            print(f"{move.id}: {move.base_power}")
            print(f"타입: {move.type}")
            print(f"명중률: {move.accuracy}")

        # 상대 포켓몬
        opponent = battle.opponent_active_pokemon
        print(opponent.types)

        return self.choose_random_move(battle)
```

### 방법 3: type_chart.json 직접 사용

여러분의 프로젝트에 이미 있습니다!

```python
import json

# type_chart.json 로드
with open('poke-env/type_chart.json', 'r') as f:
    type_chart = json.load(f)

# 타입 상성 확인
# type_chart[공격 타입][방어 타입] = 배율
print(type_chart['ELECTRIC']['WATER'])   # 2 (효과가 굉장!)
print(type_chart['ELECTRIC']['GROUND'])  # 0 (효과가 없다...)
print(type_chart['WATER']['FIRE'])      # 2 (효과가 굉장!)
```

**type_chart.json 구조**:

```json
{
  "BUG": {
    "BUG": 1,
    "DARK": 2,
    "DRAGON": 1,
    "ELECTRIC": 1,
    "FAIRY": 0.5,
    "FIGHTING": 0.5,
    "FIRE": 0.5,
    "FLYING": 0.5,
    "GHOST": 0.5,
    "GRASS": 2,
    "GROUND": 1,
    "ICE": 1,
    "NORMAL": 1,
    "POISON": 0.5,
    "PSYCHIC": 2,
    "ROCK": 1,
    "STEEL": 0.5,
    "WATER": 1
  },
  ...
}
```

---

## SimplifiedBattle 구현 체크리스트

배틀 시뮬레이터를 만들 때 **반드시 구현해야 할 데이터**:

### ✅ Tier 1: 필수 (데미지 계산)

| 데이터             | 파일           | 사용처         | 우선순위 |
| ------------------ | -------------- | -------------- | -------- |
| **포켓몬 종족값**  | `pokedex.ts`   | 데미지 계산    | 🔴 필수  |
| **기술 위력/타입** | `moves.ts`     | 데미지 계산    | 🔴 필수  |
| **타입 상성표**    | `typechart.ts` | 데미지 배율    | 🔴 필수  |
| **성격 보정**      | `natures.ts`   | 실전 스탯 계산 | 🔴 필수  |

### ✅ Tier 2: 중요 (게임 시스템)

| 데이터       | 파일            | 사용처           | 우선순위 |
| ------------ | --------------- | ---------------- | -------- |
| **특성**     | `abilities.ts`  | 데미지/스탯 보정 | 🟠 중요  |
| **아이템**   | `items.ts`      | 데미지/스탯 보정 | 🟠 중요  |
| **상태이상** | `conditions.ts` | 화상/마비 등     | 🟠 중요  |
| **날씨**     | `conditions.ts` | 비/맑음 등       | 🟠 중요  |

### ✅ Tier 3: 선택 (고급 기능)

| 데이터          | 파일            | 사용처          | 우선순위 |
| --------------- | --------------- | --------------- | -------- |
| **필드 효과**   | `conditions.ts` | 일렉트릭필드 등 | 🟡 선택  |
| **장판 기술**   | `conditions.ts` | 스텔스록 등     | 🟡 선택  |
| **사이드 효과** | `conditions.ts` | 리플렉터 등     | 🟡 선택  |

---

## 구현 순서 추천

### 1단계: 기본 데미지 계산 ✅

```python
class SimplifiedBattle:
    def calculate_damage(self, attacker, defender, move):
        # 1. 종족값 가져오기 (pokedex.ts)
        base_attack = attacker.base_stats['atk']  # or 'spa'
        base_defense = defender.base_stats['def']  # or 'spd'

        # 2. 기술 정보 가져오기 (moves.ts)
        base_power = move.base_power
        move_type = move.type

        # 3. 타입 상성 계산 (typechart.ts)
        effectiveness = self.get_type_effectiveness(move_type, defender.types)

        # 4. 데미지 계산
        damage = calculate_damage_formula(
            level=100,
            attack=base_attack,
            defense=base_defense,
            base_power=base_power,
            effectiveness=effectiveness
        )
        return damage
```

### 2단계: 성격 및 능력치 보정 ✅

```python
def apply_nature(base_stat, nature, stat_name):
    # natures.ts 참조
    if nature.plus == stat_name:
        return base_stat * 1.1
    elif nature.minus == stat_name:
        return base_stat * 0.9
    return base_stat

def apply_boosts(stat, boost_level):
    # 능력치 변화: -6 ~ +6
    multiplier = max(2, 2 + boost_level) / max(2, 2 - boost_level)
    return stat * multiplier
```

### 3단계: 특성 및 아이템 ✅

```python
def apply_ability_effects(damage, attacker, defender, move):
    # abilities.ts 참조
    if attacker.ability == 'Adaptability':
        if move.type in attacker.types:
            damage *= 2.0  # STAB 1.5배 → 2배로 증가

    if defender.ability == 'Levitate' and move.type == 'Ground':
        damage = 0  # 땅 타입 무효

    return damage

def apply_item_effects(damage, pokemon):
    # items.ts 참조
    if pokemon.item == 'Life Orb':
        damage *= 1.3
    elif pokemon.item == 'Choice Band' and move.category == 'Physical':
        damage *= 1.5

    return damage
```

### 4단계: 상태이상 및 날씨 ✅

```python
def apply_status_effects(damage, attacker, move):
    # conditions.ts 참조
    if attacker.status == 'brn' and move.category == 'Physical':
        damage *= 0.5  # 화상: 물리 공격력 절반

    return damage

def apply_weather_effects(damage, move, weather):
    # conditions.ts 참조
    if weather == 'RainDance':
        if move.type == 'Water':
            damage *= 1.5
        elif move.type == 'Fire':
            damage *= 0.5
    elif weather == 'SunnyDay':
        if move.type == 'Fire':
            damage *= 1.5
        elif move.type == 'Water':
            damage *= 0.5

    return damage
```

---

## 데이터 파싱 예제

### TypeScript → Python 변환

**Pokemon Showdown (TypeScript)**:

```typescript
thunderbolt: {
    num: 85,
    accuracy: 100,
    basePower: 90,
    category: "Special",
    name: "Thunderbolt",
    pp: 15,
    priority: 0,
    type: "Electric"
}
```

**Python Dictionary**:

```python
moves_data = {
    'thunderbolt': {
        'num': 85,
        'accuracy': 100,
        'base_power': 90,
        'category': 'Special',
        'name': 'Thunderbolt',
        'pp': 15,
        'priority': 0,
        'type': 'Electric'
    }
}
```

---

## 최종 정리

### 🎯 SimplifiedBattle에 필요한 최소 데이터

1. **포켓몬 종족값** (`baseStats`)
2. **기술 위력/타입** (`basePower`, `type`)
3. **타입 상성표** (`typechart.ts` 또는 `type_chart.json`)
4. **성격 보정** (`natures.ts`)

### 🎯 고급 기능에 필요한 추가 데이터

5. **특성** (`abilities.ts`)
6. **아이템** (`items.ts`)
7. **상태이상** (`conditions.ts` - brn, par, slp 등)
8. **날씨** (`conditions.ts` - RainDance, SunnyDay 등)
9. **필드 효과** (`conditions.ts` - ElectricTerrain 등)
10. **장판 기술** (`conditions.ts` - StealthRock, Spikes 등)

### 🎯 어디서 가져올까?

**옵션 1**: `poke-env` 라이브러리 사용 (권장)

```python
from poke_env.data import GenData
gen_data = GenData.from_gen(8)
```

**옵션 2**: `type_chart.json` 직접 로드

```python
import json
with open('poke-env/type_chart.json', 'r') as f:
    type_chart = json.load(f)
```

**옵션 3**: Pokemon Showdown TypeScript 파일 파싱

- 복잡하므로 비추천
- `poke-env`가 이미 파싱해놓음

---

## 참고: 데미지 계산 공식 (완전판)

```python
def calculate_damage(level, attack, defense, base_power,
                     type_effectiveness, stab, burn, weather,
                     ability_multiplier, item_multiplier):
    """
    Pokemon Showdown의 데미지 계산 공식

    Args:
        level: 레벨 (보통 50 또는 100)
        attack: 공격력 (물리) 또는 특공 (특수)
        defense: 방어력 (물리) 또는 특방 (특수)
        base_power: 기술 위력
        type_effectiveness: 타입 상성 (0, 0.25, 0.5, 1, 2, 4)
        stab: 자속 보정 (같은 타입: 1.5, 다른 타입: 1.0)
        burn: 화상 보정 (화상 시 물리: 0.5, 아니면: 1.0)
        weather: 날씨 보정 (비: 물 1.5/불꽃 0.5, 맑음: 불꽃 1.5/물 0.5)
        ability_multiplier: 특성 보정
        item_multiplier: 아이템 보정

    Returns:
        int: 최종 데미지
    """
    # 1단계: 기본 데미지
    base_damage = ((2 * level / 5 + 2) * base_power * attack / defense) / 50 + 2

    # 2단계: 보정 적용
    damage = base_damage
    damage *= type_effectiveness  # 타입 상성
    damage *= stab               # 자속 보정
    damage *= burn               # 화상 보정
    damage *= weather            # 날씨 보정
    damage *= ability_multiplier # 특성 보정
    damage *= item_multiplier    # 아이템 보정

    # 3단계: 랜덤 보정 (85% ~ 100%)
    random_factor = random.uniform(0.85, 1.0)
    damage *= random_factor

    return int(damage)
```

---

**이제 SimplifiedBattle 구현을 시작하세요!** 🚀
