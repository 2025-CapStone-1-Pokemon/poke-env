# Battle 클래스 완전 분석

> **목적**: poke-env의 Battle 및 AbstractBattle 클래스를 완벽하게 이해하고 SimplifiedBattle 구현에 활용

---

## 📌 목차

1. [개요](#개요)
2. [클래스 계층 구조](#클래스-계층-구조)
3. [AbstractBattle 분석](#abstractbattle-분석)
4. [Battle 분석](#battle-분석)
5. [주요 사용 패턴](#주요-사용-패턴)
6. [SimplifiedBattle 구현 가이드](#simplifiedbattle-구현-가이드)

---

## 개요

### Battle 시스템이란?

**Battle**은 포켓몬 배틀의 **전체 상태**를 관리하는 최상위 클래스입니다.

```python
from poke_env.player import Player

class MyPlayer(Player):
    def choose_move(self, battle: Battle):
        # battle 객체에 모든 정보 포함
        print(f"턴: {battle.turn}")
        print(f"내 포켓몬: {battle.active_pokemon.species}")
        print(f"상대: {battle.opponent_active_pokemon.species}")
        print(f"날씨: {battle.weather}")

        return self.choose_random_move(battle)
```

### 파일 정보

| 클래스             | 위치                 | 라인 수 | **slots** | 역할      |
| ------------------ | -------------------- | ------- | --------- | --------- |
| **AbstractBattle** | `abstract_battle.py` | 1532줄  | **113개** | 공통 기능 |
| **Battle**         | `battle.py`          | 264줄   | 상속      | 싱글 배틀 |
| **DoubleBattle**   | `double_battle.py`   | -       | 상속      | 더블 배틀 |

---

## 클래스 계층 구조

### 상속 다이어그램

```
AbstractBattle (ABC - 추상 클래스)
    │
    ├── 공통 기능 (113개 __slots__)
    │   ├── 팀 관리 (team, opponent_team)
    │   ├── 메시지 파싱 (parse_message)
    │   ├── 날씨/필드 (weather, fields)
    │   ├── 사이드 조건 (side_conditions)
    │   └── 배틀 상태 (turn, finished, won)
    │
    ├─→ Battle (싱글 배틀)
    │     ├── 활성 포켓몬 1마리
    │     ├── parse_request() 구현
    │     └── available_moves, available_switches
    │
    └─→ DoubleBattle (더블 배틀)
          ├── 활성 포켓몬 2마리
          ├── parse_request() 구현
          └── 대상 지정 필요
```

---

## AbstractBattle 분석

### 개요

**AbstractBattle**은 모든 배틀 타입의 **추상 기본 클래스**입니다.

```python
from abc import ABC, abstractmethod

class AbstractBattle(ABC):
    """모든 배틀의 공통 기능"""

    __slots__ = (
        # 총 113개!
        "_battle_tag",
        "_team",
        "_opponent_team",
        "_weather",
        "_fields",
        "_turn",
        # ... 등등
    )

    @abstractmethod
    def parse_request(self, request: Dict) -> None:
        """하위 클래스가 반드시 구현"""
        pass
```

### **slots** 전체 목록 (113개)

#### 1. 기본 정보 (9개)

```python
"_battle_tag",           # 배틀 태그 ('battle-gen9randombattle-12345')
"_gen",                  # 세대 (8, 9 등)
"_format",               # 포맷 ('gen9randombattle')
"_player_username",      # 플레이어 이름
"_opponent_username",    # 상대 이름
"_player_role",          # 플레이어 역할 ('p1' 또는 'p2')
"_players",              # 플레이어 목록
"_max_team_size",        # 최대 팀 크기
"_team_size",            # 팀 크기 Dict
```

#### 2. 팀 관리 (4개)

```python
"_team",                      # 내 팀 Dict[str, Pokemon]
"_opponent_team",             # 상대 팀 Dict[str, Pokemon]
"_teampreview_team",          # 팀프리뷰 내 팀 Set[Pokemon]
"_teampreview_opponent_team", # 팀프리뷰 상대 팀 Set[Pokemon]
```

#### 3. 배틀 상태 (11개)

```python
"_turn",                 # 현재 턴
"_finished",             # 배틀 종료 여부
"_won",                  # 승리 여부 (True/False/None)
"_rating",               # 내 레이팅
"_opponent_rating",      # 상대 레이팅
"_teampreview",          # 팀프리뷰 중인지
"in_team_preview",       # 팀프리뷰 대기 중
"_wait",                 # 대기 중
"_reconnected",          # 재접속 여부
"_anybody_inactive",     # 누군가 비활성
"_last_request",         # 마지막 요청 Dict
```

#### 4. 필드 효과 (4개)

```python
"_weather",                      # 날씨 Dict[Weather, int]
"_fields",                       # 필드 효과 Dict[Field, int]
"_side_conditions",              # 내 쪽 사이드 조건 Dict[SideCondition, int]
"_opponent_side_conditions",     # 상대 쪽 사이드 조건 Dict[SideCondition, int]
```

#### 5. 특수 행동 (8개)

```python
"_used_mega_evolve",         # 메가진화 사용 여부
"_used_z_move",              # Z기술 사용 여부
"_used_dynamax",             # 다이맥스 사용 여부
"_used_tera",                # 테라스탈 사용 여부
"_opponent_used_mega_evolve",# 상대 메가진화
"_opponent_used_z_move",     # 상대 Z기술
"_opponent_used_dynamax",    # 상대 다이맥스
"_opponent_used_tera",       # 상대 테라스탈
```

#### 6. 턴 선택 (7개)

```python
"_available_moves",      # 사용 가능한 기술들
"_available_switches",   # 교체 가능한 포켓몬들
"_can_mega_evolve",      # 메가진화 가능
"_can_z_move",           # Z기술 가능
"_can_dynamax",          # 다이맥스 가능
"_can_tera",             # 테라스탈 가능
"_force_switch",         # 강제 교체
```

#### 7. 기타 (70개)

```python
"_data",                 # GenData 객체
"_dynamax_turn",         # 다이맥스 시작 턴
"_opponent_dynamax_turn",# 상대 다이맥스 시작 턴
"_maybe_trapped",        # 트랩 가능성
"_trapped",              # 트랩됨
"_reviving",             # 부활 중 (위시패스 등)
"_observations",         # 턴별 관찰 데이터
"_current_observation",  # 현재 관찰
"_replay_data",          # 리플레이 데이터
"_save_replays",         # 리플레이 저장 여부
"rules",                 # 배틀 룰
"logger",                # 로거
```

---

### 주요 속성 (AbstractBattle)

#### 팀 정보

```python
# 내 팀
battle.team: Dict[str, Pokemon]
# {'p1: Pikachu': Pokemon(...), 'p1: Charizard': Pokemon(...), ...}

# 상대 팀
battle.opponent_team: Dict[str, Pokemon]
# {'p2: Venusaur': Pokemon(...), 'p2: Blastoise': Pokemon(...), ...}

# 팀 크기
battle.team_size: int  # 6 (보통)
```

#### 배틀 상태

```python
# 턴
battle.turn: int  # 1, 2, 3, ...

# 종료 여부
battle.finished: bool  # True/False

# 승패
battle.won: Optional[bool]  # True (승리), False (패배), None (진행중)

# 레이팅
battle.rating: Optional[int]  # 1500
battle.opponent_rating: Optional[int]  # 1480
```

#### 필드 효과

```python
# 날씨
battle.weather: Dict[Weather, int]
# {Weather.RAINDANCE: 5}  # 5턴에 시작

# 필드
battle.fields: Dict[Field, int]
# {Field.ELECTRIC_TERRAIN: 3}  # 3턴에 시작

# 사이드 조건
battle.side_conditions: Dict[SideCondition, int]
# {SideCondition.STEALTH_ROCK: 2, SideCondition.SPIKES: 3}

battle.opponent_side_conditions: Dict[SideCondition, int]
```

---

### 주요 메서드 (AbstractBattle)

#### `get_pokemon(identifier: str, ...) -> Pokemon`

식별자로 Pokemon 객체를 가져옵니다.

```python
# 식별자: "p1: Pikachu" 또는 "p2a: Charizard"
pokemon = battle.get_pokemon("p1: Pikachu")
```

#### `parse_message(split_message: List[str])`

서버 메시지를 파싱하여 배틀 상태를 업데이트합니다.

```python
# 서버 메시지 예시
messages = [
    ['switch', 'p2a: Pikachu', 'Pikachu, L50, M', '100/100'],
    ['move', 'p1a: Charizard', 'Flamethrower', 'p2a: Pikachu'],
    ['-damage', 'p2a: Pikachu', '50/100'],
]

for msg in messages:
    battle.parse_message(msg)
```

**주요 메시지 타입**:

- `switch` - 포켓몬 교체
- `move` - 기술 사용
- `-damage` - 데미지
- `-heal` - 회복
- `-boost` - 능력치 상승
- `-unboost` - 능력치 하락
- `-status` - 상태이상
- `-weather` - 날씨 변경
- `-fieldstart` - 필드 시작
- `-sidestart` - 사이드 조건 시작
- `faint` - 기절
- `win` - 승리

---

## Battle 분석

### 개요

**Battle**은 **1vs1 싱글 배틀** 전용 구현 클래스입니다.

```python
class Battle(AbstractBattle):
    """싱글 배틀 (1 vs 1)"""

    def __init__(self, battle_tag, username, logger, gen, save_replays):
        super().__init__(...)  # AbstractBattle 초기화

        # 싱글 배틀 전용 속성
        self._available_moves: List[Move] = []
        self._available_switches: List[Pokemon] = []
        self._can_mega_evolve = False
        self._can_z_move = False
        self._can_dynamax = False
        self._can_tera = False
        self._force_switch = False
        self._trapped = False
```

---

### 주요 속성 (Battle)

#### 활성 포켓몬 (1마리)

```python
# 내 활성 포켓몬
battle.active_pokemon: Optional[Pokemon]

# 상대 활성 포켓몬
battle.opponent_active_pokemon: Optional[Pokemon]

# 모든 활성 포켓몬 (싱글은 2마리)
battle.all_active_pokemons: List[Optional[Pokemon]]
# [my_pokemon, opponent_pokemon]
```

#### 사용 가능한 행동

```python
# 사용 가능한 기술들
battle.available_moves: List[Move]
# [Move('thunderbolt'), Move('quickattack'), ...]

# 교체 가능한 포켓몬들
battle.available_switches: List[Pokemon]
# [Pokemon('charizard'), Pokemon('blastoise'), ...]
```

#### 특수 행동 가능 여부

```python
# 메가진화 가능
battle.can_mega_evolve: bool

# Z기술 가능
battle.can_z_move: bool

# 다이맥스 가능
battle.can_dynamax: bool

# 테라스탈 가능
battle.can_tera: bool

# 강제 교체 (드래곤테일 등)
battle.force_switch: bool

# 트랩됨 (교체 불가)
battle.trapped: bool

# 트랩 가능성
battle.maybe_trapped: bool
```

---

### 주요 메서드 (Battle)

#### `parse_request(request: Dict)`

서버 요청을 파싱하여 사용 가능한 행동들을 업데이트합니다.

```python
# 서버 요청 예시
request = {
    'active': [{
        'moves': [
            {'move': 'Thunderbolt', 'id': 'thunderbolt', 'pp': 24, 'maxpp': 24, ...},
            {'move': 'Quick Attack', 'id': 'quickattack', 'pp': 30, 'maxpp': 30, ...},
        ],
        'canMegaEvo': True,
        'canZMove': False,
        'canDynamax': False,
        'canTerastallize': False,
    }],
    'side': {
        'pokemon': [
            {'ident': 'p1: Pikachu', 'condition': '100/100', 'active': True, ...},
            {'ident': 'p1: Charizard', 'condition': '85/100', 'active': False, ...},
            # ... 나머지 팀
        ]
    }
}

battle.parse_request(request)

# 결과
battle.available_moves  # [Move('thunderbolt'), Move('quickattack')]
battle.available_switches  # [Pokemon('charizard'), ...]
battle.can_mega_evolve  # True
```

#### `switch(pokemon_str: str, details: str, hp_status: str)`

포켓몬 교체를 처리합니다.

```python
# 서버 메시지: |switch|p1a: Charizard|Charizard, L50, M|100/100
battle.switch('p1a: Charizard', 'Charizard, L50, M', '100/100')

# 이전 활성 포켓몬은 switch_out() 호출됨
# 새 포켓몬은 switch_in() 호출됨
```

#### `clear_all_boosts()`

모든 활성 포켓몬의 능력치 변화를 초기화합니다.

```python
# 흑무 사용 시
battle.clear_all_boosts()

# 결과
battle.active_pokemon.boosts  # {'atk': 0, 'def': 0, ...}
battle.opponent_active_pokemon.boosts  # {'atk': 0, 'def': 0, ...}
```

---

## 주요 사용 패턴

### 1. 배틀 정보 출력

```python
def print_battle_info(battle: Battle):
    print(f"=== 턴 {battle.turn} ===")
    print(f"포맷: {battle.format}")
    print(f"플레이어: {battle.player_username} vs {battle.opponent_username}")

    # 내 포켓몬
    my_poke = battle.active_pokemon
    if my_poke:
        print(f"\n내 포켓몬: {my_poke.species}")
        print(f"  HP: {my_poke.current_hp}/{my_poke.max_hp}")
        print(f"  상태: {my_poke.status}")

    # 상대 포켓몬
    opp_poke = battle.opponent_active_pokemon
    if opp_poke:
        print(f"\n상대: {opp_poke.species}")
        print(f"  HP: {opp_poke.current_hp}/{opp_poke.max_hp}")
        print(f"  상태: {opp_poke.status}")

    # 날씨
    if battle.weather:
        for weather, turn in battle.weather.items():
            print(f"\n날씨: {weather.name} (시작: {turn}턴)")

    # 필드
    if battle.fields:
        for field, turn in battle.fields.items():
            print(f"필드: {field.name} (시작: {turn}턴)")

    # 사이드 조건
    if battle.side_conditions:
        print(f"\n내 쪽 사이드 조건:")
        for sc, value in battle.side_conditions.items():
            print(f"  {sc.name}: {value}")

    if battle.opponent_side_conditions:
        print(f"\n상대 쪽 사이드 조건:")
        for sc, value in battle.opponent_side_conditions.items():
            print(f"  {sc.name}: {value}")
```

---

### 2. 행동 선택 로직

```python
def choose_move(self, battle: Battle) -> str:
    """기술 또는 교체 선택"""

    # 강제 교체
    if battle.force_switch:
        if battle.available_switches:
            return f"/choose switch {battle.available_switches[0].species}"
        else:
            return "/choose pass"

    # 사용 가능한 기술이 없으면 교체
    if not battle.available_moves:
        if battle.available_switches:
            return f"/choose switch {battle.available_switches[0].species}"
        else:
            return "/choose pass"

    # 최적 기술 선택
    best_move = None
    best_score = 0

    for move in battle.available_moves:
        score = move.base_power

        # 타입 상성
        if battle.opponent_active_pokemon:
            effectiveness = battle.opponent_active_pokemon.damage_multiplier(move)
            score *= effectiveness

        if score > best_score:
            best_score = score
            best_move = move

    # 메가진화 가능하면 사용
    if battle.can_mega_evolve and best_move:
        return f"/choose move {best_move.id} mega"

    # 다이맥스 가능하면 사용
    if battle.can_dynamax and best_move:
        return f"/choose move {best_move.id} dynamax"

    if best_move:
        return f"/choose move {best_move.id}"

    return "/choose pass"
```

---

### 3. 팀 분석

```python
def analyze_team(battle: Battle):
    """팀 상태 분석"""
    print(f"=== 팀 분석 ===")

    alive_count = 0
    total_hp = 0

    for pokemon in battle.team.values():
        if not pokemon.fainted:
            alive_count += 1
            total_hp += pokemon.current_hp_fraction

    print(f"살아있는 포켓몬: {alive_count}/{len(battle.team)}")
    print(f"평균 HP: {total_hp / max(alive_count, 1):.1%}")

    # 타입 분포
    types = {}
    for pokemon in battle.team.values():
        for poke_type in pokemon.types:
            types[poke_type] = types.get(poke_type, 0) + 1

    print(f"\n타입 분포:")
    for poke_type, count in types.items():
        print(f"  {poke_type.name}: {count}")
```

---

### 4. 상대 분석

```python
def analyze_opponent(battle: Battle):
    """상대 팀 분석"""
    print(f"=== 상대 분석 ===")

    revealed_count = 0
    for pokemon in battle.opponent_team.values():
        if pokemon.revealed:
            revealed_count += 1
            print(f"\n{pokemon.species}:")
            print(f"  타입: {'/'.join(t.name for t in pokemon.types)}")
            print(f"  특성: {pokemon.ability or '?'}")
            print(f"  아이템: {pokemon.item or '?'}")
            print(f"  알려진 기술: {len(pokemon.moves)}/4")
            for move_id in pokemon.moves:
                print(f"    - {move_id}")

    print(f"\n공개된 포켓몬: {revealed_count}/{len(battle.opponent_team)}")
```

---

### 5. 배틀 기록

```python
class BattleRecorder:
    def __init__(self):
        self.turns = []

    def record_turn(self, battle: Battle):
        """매 턴 기록"""
        turn_data = {
            'turn': battle.turn,
            'my_pokemon': battle.active_pokemon.species if battle.active_pokemon else None,
            'my_hp': battle.active_pokemon.current_hp_fraction if battle.active_pokemon else 0,
            'opp_pokemon': battle.opponent_active_pokemon.species if battle.opponent_active_pokemon else None,
            'opp_hp': battle.opponent_active_pokemon.current_hp_fraction if battle.opponent_active_pokemon else 0,
            'weather': list(battle.weather.keys()),
            'fields': list(battle.fields.keys()),
        }
        self.turns.append(turn_data)

    def print_summary(self):
        """배틀 요약"""
        print(f"총 {len(self.turns)}턴 진행")

        # 날씨 사용 횟수
        weather_count = {}
        for turn in self.turns:
            for weather in turn['weather']:
                weather_count[weather] = weather_count.get(weather, 0) + 1

        if weather_count:
            print("\n날씨 사용:")
            for weather, count in weather_count.items():
                print(f"  {weather.name}: {count}턴")
```

---

## SimplifiedBattle 구현 가이드

### 1. 복사해야 할 속성

```python
class SimplifiedBattle:
    def __init__(self, poke_env_battle: Battle):
        # === 기본 정보 ===
        self.turn = poke_env_battle.turn
        self.gen = poke_env_battle._gen

        # === 팀 (SimplifiedPokemon으로 변환) ===
        self.team = {
            identifier: SimplifiedPokemon(pokemon)
            for identifier, pokemon in poke_env_battle.team.items()
        }
        self.opponent_team = {
            identifier: SimplifiedPokemon(pokemon)
            for identifier, pokemon in poke_env_battle.opponent_team.items()
        }

        # === 활성 포켓몬 ===
        self.active_pokemon = (
            SimplifiedPokemon(poke_env_battle.active_pokemon)
            if poke_env_battle.active_pokemon else None
        )
        self.opponent_active_pokemon = (
            SimplifiedPokemon(poke_env_battle.opponent_active_pokemon)
            if poke_env_battle.opponent_active_pokemon else None
        )

        # === 필드 효과 ===
        self.weather = poke_env_battle.weather.copy()
        self.fields = poke_env_battle.fields.copy()
        self.side_conditions = poke_env_battle.side_conditions.copy()
        self.opponent_side_conditions = poke_env_battle.opponent_side_conditions.copy()

        # === 특수 행동 사용 여부 ===
        self.used_mega_evolve = poke_env_battle.used_mega_evolve
        self.used_z_move = poke_env_battle.used_z_move
        self.used_dynamax = poke_env_battle.used_dynamax
        self.used_tera = poke_env_battle.used_tera

        self.opponent_used_mega_evolve = poke_env_battle.opponent_used_mega_evolve
        self.opponent_used_z_move = poke_env_battle.opponent_used_z_move
        self.opponent_used_dynamax = poke_env_battle.opponent_used_dynamax
        self.opponent_used_tera = poke_env_battle.opponent_used_tera
```

---

### 2. 필요한 메서드

```python
class SimplifiedBattle:
    # ... __init__ ...

    def simulate_turn(self, my_action: Action, opp_action: Action) -> 'SimplifiedBattle':
        """
        1턴 시뮬레이션

        Args:
            my_action: 내 행동 (기술 사용 or 교체)
            opp_action: 상대 행동

        Returns:
            새로운 SimplifiedBattle 객체 (원본 유지)
        """
        # 1. 배틀 상태 복사
        new_battle = copy.deepcopy(self)
        new_battle.turn += 1

        # 2. 교체 처리
        my_action, opp_action = self._handle_switches(new_battle, my_action, opp_action)

        # 3. 우선순위 및 스피드 계산
        first, second = self._determine_order(new_battle, my_action, opp_action)

        # 4. 선공 실행
        self._execute_action(new_battle, first)

        # 5. 후공 실행 (선공으로 기절하지 않았으면)
        if not self._check_fainted(new_battle):
            self._execute_action(new_battle, second)

        # 6. 턴 종료 처리
        self._end_of_turn(new_battle)

        return new_battle

    def _determine_order(self, battle, action1, action2):
        """행동 순서 결정"""
        # 1. 우선도 비교
        priority1 = action1.move.priority if action1.is_move else 0
        priority2 = action2.move.priority if action2.is_move else 0

        if priority1 > priority2:
            return action1, action2
        elif priority2 > priority1:
            return action2, action1

        # 2. 스피드 비교
        speed1 = battle.active_pokemon.get_effective_stat('spe')
        speed2 = battle.opponent_active_pokemon.get_effective_stat('spe')

        if speed1 > speed2:
            return action1, action2
        elif speed2 > speed1:
            return action2, action1
        else:
            # 동속: 랜덤
            import random
            return random.choice([(action1, action2), (action2, action1)])

    def _execute_action(self, battle, action):
        """행동 실행"""
        if action.is_move:
            self._execute_move(battle, action.user, action.target, action.move)
        else:  # switch
            self._execute_switch(battle, action.user, action.switch_pokemon)

    def _execute_move(self, battle, attacker, defender, move):
        """기술 실행"""
        # 1. PP 소모
        move.use()

        # 2. 명중 판정
        if not self._check_accuracy(attacker, defender, move):
            return  # 빗나감

        # 3. 데미지 계산 및 적용
        if move.category != MoveCategory.STATUS:
            damage = move.calculate_damage(attacker, defender, battle)
            defender.damage(damage)

        # 4. 추가 효과
        self._apply_secondary_effects(battle, attacker, defender, move)

    def _end_of_turn(self, battle):
        """턴 종료 처리"""
        # 1. 날씨 데미지
        self._apply_weather_damage(battle)

        # 2. 상태이상 데미지
        self._apply_status_damage(battle)

        # 3. 아이템 효과 (먹다 남은 음식 등)
        self._apply_item_effects(battle)

        # 4. 능력치 변화 리셋 (일부)
        # (protect_counter 등)
```

---

### 3. 복사 전략

| 항목                    | 복사 방법              | 이유                       |
| ----------------------- | ---------------------- | -------------------------- |
| `turn`, `gen`           | 직접 할당              | 정수 (불변)                |
| `team`, `opponent_team` | Dict 재구성            | SimplifiedPokemon으로 변환 |
| `active_pokemon`        | SimplifiedPokemon 생성 | 독립적인 객체 필요         |
| `weather`, `fields`     | `.copy()`              | Dict, 얕은 복사 OK         |
| `side_conditions`       | `.copy()`              | Dict, 얕은 복사 OK         |
| `used_mega_evolve` 등   | 직접 할당              | 불리언 (불변)              |

**중요**: 시뮬레이션마다 **deepcopy**로 완전히 독립적인 배틀 상태를 만들어야 합니다!

```python
import copy

# ✅ 올바른 방법
def simulate(battle: SimplifiedBattle, action1, action2):
    # 원본 유지, 새 객체 반환
    new_battle = copy.deepcopy(battle)
    new_battle.simulate_turn(action1, action2)
    return new_battle

# ❌ 잘못된 방법
def simulate(battle: SimplifiedBattle, action1, action2):
    # 원본 수정! MCTS에서 문제 발생
    battle.simulate_turn(action1, action2)
    return battle
```

---

## 다음 문서

- **[SUPPORTING_CLASSES.md](SUPPORTING_CLASSES.md)** - 지원 클래스들 (Status, Weather, Field, Effect 등)
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - SimplifiedBattle 구현 완전 가이드

---

**끝!** ⚔️
