# SimplifiedBattle 구현 완전 가이드

> **목적**: poke-env 분석을 바탕으로 MCTS용 SimplifiedBattle/SimplifiedPokemon을 **실제로 구현**하는 방법

---

## 📌 목차

1. [시작하기 전에](#시작하기 전에)
2. [SimplifiedPokemon 구현](#simplifiedpokemon-구현)
3. [SimplifiedMove 구현](#simplifiedmove-구현)
4. [SimplifiedBattle 구현](#simplifiedbattle-구현)
5. [데미지 계산 엔진](#데미지-계산-엔진)
6. [턴 시뮬레이션](#턴-시뮬레이션)
7. [MCTS 통합](#mcts-통합)
8. [테스트 전략](#테스트-전략)
9. [최적화 팁](#최적화-팁)
10. [자주 하는 실수](#자주-하는-실수)

---

## 시작하기 전에

### 왜 SimplifiedBattle인가?

**poke-env의 한계**:

```python
# ❌ poke-env Battle 객체는 네트워크 통신 필요
battle = Battle(...)
battle.choose_move(...)  # → 서버에 메시지 전송 → 응답 대기

# MCTS는 초당 수천 번 시뮬레이션 필요
for _ in range(1000):
    # 네트워크 통신으로는 불가능!
    simulate_move(...)
```

**SimplifiedBattle의 목표**:

```python
# ✅ 로컬에서 즉시 시뮬레이션
simplified_battle = SimplifiedBattle.from_battle(real_battle)

# MCTS에서 빠른 시뮬레이션
for _ in range(10000):
    clone = simplified_battle.clone()
    result = clone.simulate_turn(move1, move2)
    # 네트워크 없이 즉시 결과!
```

---

### 구현 난이도

| 컴포넌트          | 난이도     | 필수 여부 | 이유             |
| ----------------- | ---------- | --------- | ---------------- |
| SimplifiedPokemon | ⭐⭐       | ✅ 필수   | 기본 상태만      |
| SimplifiedMove    | ⭐         | ✅ 필수   | 읽기 전용        |
| 기본 데미지 계산  | ⭐⭐⭐     | ✅ 필수   | 복잡한 공식      |
| 턴 시뮬레이션     | ⭐⭐⭐⭐   | ✅ 필수   | 순서 결정 복잡   |
| 상태이상 처리     | ⭐⭐⭐     | ⚠️ 중요   | 화상/마비는 필수 |
| 날씨 효과         | ⭐⭐       | ⚠️ 중요   | 자주 사용됨      |
| 필드 효과         | ⭐⭐       | 🔵 선택   | 테레인 정도만    |
| 사이드 조건       | ⭐⭐⭐⭐   | 🔵 선택   | 스텔스록만 구현  |
| 특성 효과         | ⭐⭐⭐⭐⭐ | 🔵 선택   | 너무 많음 (300+) |
| 아이템 효과       | ⭐⭐⭐⭐   | 🔵 선택   | 자주 쓰이는 것만 |

---

### 단계별 로드맵

**Phase 1: 기본 구조 (1주)**

- [ ] SimplifiedPokemon 클래스
- [ ] SimplifiedMove 클래스
- [ ] SimplifiedBattle 클래스 (빈 껍데기)

**Phase 2: 데미지 계산 (1주)**

- [ ] 기본 데미지 공식
- [ ] 타입 상성
- [ ] STAB 보너스
- [ ] 급소 데미지

**Phase 3: 턴 시뮬레이션 (2주)**

- [ ] 스피드 계산 및 행동 순서
- [ ] 기술 실행
- [ ] HP 관리
- [ ] 기절 처리

**Phase 4: 고급 기능 (2주)**

- [ ] 상태이상 (화상/마비/독)
- [ ] 날씨 효과 (비/맑음)
- [ ] 능력치 랭크 변화
- [ ] 교체 처리

**Phase 5: 최적화 & 테스트 (1주)**

- [ ] 성능 프로파일링
- [ ] 단위 테스트
- [ ] 실전 테스트

---

## SimplifiedPokemon 구현

### 기본 구조

```python
from dataclasses import dataclass
from typing import Optional, Dict, Set
from poke_env.battle import Status, Effect, PokemonType
import copy

@dataclass
class SimplifiedPokemon:
    """MCTS용 간소화된 포켓몬"""

    # 기본 정보 (불변)
    species: str
    level: int
    type_1: PokemonType
    type_2: Optional[PokemonType]

    # 스탯 (불변)
    max_hp: int
    base_stats: Dict[str, int]  # {'atk': 130, 'def': 100, ...}

    # 기술 (불변)
    moves: Dict[str, 'SimplifiedMove']  # {move_id: SimplifiedMove}

    # 현재 상태 (가변)
    current_hp: int
    status: Optional[Status]
    status_counter: int  # 잠듦/맹독 턴 추적

    # 능력치 변화 (가변)
    boosts: Dict[str, int]  # {'atk': 0, 'def': 0, ...}

    # 효과 (가변)
    effects: Set[Effect]

    # 기타 (가변)
    fainted: bool
    active: bool

    def __post_init__(self):
        """초기화"""
        if self.boosts is None:
            self.boosts = {
                'atk': 0, 'def': 0, 'spa': 0,
                'spd': 0, 'spe': 0, 'accuracy': 0,
                'evasion': 0
            }

        if self.effects is None:
            self.effects = set()

        if self.fainted is None:
            self.fainted = (self.current_hp == 0)

    @classmethod
    def from_pokemon(cls, pokemon: 'Pokemon') -> 'SimplifiedPokemon':
        """poke-env의 Pokemon 객체에서 생성"""
        return cls(
            species=pokemon.species,
            level=pokemon.level,
            type_1=pokemon.type_1,
            type_2=pokemon.type_2,
            max_hp=pokemon.max_hp,
            base_stats={
                'atk': pokemon.base_stats['atk'],
                'def': pokemon.base_stats['def'],
                'spa': pokemon.base_stats['spa'],
                'spd': pokemon.base_stats['spd'],
                'spe': pokemon.base_stats['spe'],
            },
            moves={
                move_id: SimplifiedMove.from_move(move)
                for move_id, move in pokemon.moves.items()
            },
            current_hp=pokemon.current_hp or pokemon.max_hp,
            status=pokemon.status,
            status_counter=pokemon.status_counter,
            boosts=pokemon.boosts.copy(),
            effects=pokemon.effects.copy(),
            fainted=pokemon.fainted,
            active=pokemon.active,
        )

    def clone(self) -> 'SimplifiedPokemon':
        """깊은 복사"""
        return SimplifiedPokemon(
            species=self.species,
            level=self.level,
            type_1=self.type_1,
            type_2=self.type_2,
            max_hp=self.max_hp,
            base_stats=self.base_stats.copy(),
            moves=self.moves.copy(),  # SimplifiedMove는 불변
            current_hp=self.current_hp,
            status=self.status,
            status_counter=self.status_counter,
            boosts=self.boosts.copy(),
            effects=self.effects.copy(),
            fainted=self.fainted,
            active=self.active,
        )

    def damage(self, amount: int) -> int:
        """데미지 받기 (실제 데미지 반환)"""
        amount = min(amount, self.current_hp)
        self.current_hp -= amount

        if self.current_hp <= 0:
            self.current_hp = 0
            self.fainted = True
            self.status = Status.FNT

        return amount

    def heal(self, amount: int) -> int:
        """회복 (실제 회복량 반환)"""
        if self.fainted:
            return 0

        amount = min(amount, self.max_hp - self.current_hp)
        self.current_hp += amount
        return amount

    def boost(self, stat: str, amount: int):
        """능력치 변화"""
        self.boosts[stat] = max(-6, min(6, self.boosts[stat] + amount))

    def get_boosted_stat(self, stat: str) -> int:
        """능력치 랭크 적용"""
        base = self.base_stats[stat]
        boost = self.boosts[stat]

        if boost >= 0:
            multiplier = (2 + boost) / 2
        else:
            multiplier = 2 / (2 - boost)

        return int(base * multiplier)

    def cure_status(self):
        """상태이상 치료"""
        self.status = None
        self.status_counter = 0

    def __repr__(self):
        return f"{self.species} ({self.current_hp}/{self.max_hp})"
```

---

### 핵심 메서드

#### `get_boosted_stat(stat)`

능력치 랭크 변화를 적용합니다.

```python
# 칼춤 (+2 공격)
pokemon.boost('atk', 2)

# 실제 공격력
attack = pokemon.get_boosted_stat('atk')
# boost = 2 → multiplier = (2+2)/2 = 2.0
# attack = base_atk * 2.0
```

**랭크 배율**:
| 랭크 | 배율 |
|------|------|
| +6 | 4.0x |
| +5 | 3.5x |
| +4 | 3.0x |
| +3 | 2.5x |
| +2 | 2.0x |
| +1 | 1.5x |
| 0 | 1.0x |
| -1 | 0.67x |
| -2 | 0.5x |
| -6 | 0.25x |

---

## SimplifiedMove 구현

### 기본 구조

```python
from dataclasses import dataclass
from typing import Optional, Dict
from poke_env.battle import MoveCategory, PokemonType

@dataclass(frozen=True)  # 불변 객체
class SimplifiedMove:
    """MCTS용 간소화된 기술"""

    # 기본 정보
    id: str
    name: str
    type: PokemonType
    category: MoveCategory

    # 위력 및 명중
    base_power: int
    accuracy: int  # 0~100, 필중은 100

    # 우선도
    priority: int

    # 추가 효과
    boosts: Optional[Dict[str, int]]  # 능력치 변화
    status: Optional[Status]  # 상태이상

    # 기타
    drain: Optional[float]  # 흡혈 비율 (0.5 = 50%)
    recoil: Optional[float]  # 반동 비율 (0.33 = 33%)

    @classmethod
    def from_move(cls, move: 'Move') -> 'SimplifiedMove':
        """poke-env의 Move 객체에서 생성"""
        return cls(
            id=move.id,
            name=move.name or move.id,
            type=move.type,
            category=move.category,
            base_power=move.base_power,
            accuracy=move.accuracy or 100,  # 필중은 100
            priority=move.priority,
            boosts=move.boosts,
            status=move.status,
            drain=move.drain,
            recoil=move.recoil,
        )
```

---

## SimplifiedBattle 구현

### 기본 구조

```python
from typing import Optional, Dict, List
from poke_env.battle import Weather, Field, SideCondition
import random

class SimplifiedBattle:
    """MCTS용 간소화된 배틀"""

    def __init__(
        self,
        player_team: List[SimplifiedPokemon],
        opponent_team: List[SimplifiedPokemon],
        player_active_idx: int = 0,
        opponent_active_idx: int = 0,
    ):
        # 팀 (6마리)
        self.player_team = player_team
        self.opponent_team = opponent_team

        # 현재 필드의 포켓몬
        self.player_active_idx = player_active_idx
        self.opponent_active_idx = opponent_active_idx

        # 환경
        self.weather: Dict[Weather, int] = {}  # {날씨: 시작_턴}
        self.fields: Dict[Field, int] = {}  # {필드: 시작_턴}
        self.player_side_conditions: Dict[SideCondition, int] = {}
        self.opponent_side_conditions: Dict[SideCondition, int] = {}

        # 턴 카운터
        self.turn: int = 0

        # 타입 차트 (poke-env에서 복사)
        from poke_env.data import GenData
        gen_data = GenData.from_gen(9)
        self.type_chart = gen_data.type_chart

    @property
    def player_active(self) -> SimplifiedPokemon:
        return self.player_team[self.player_active_idx]

    @property
    def opponent_active(self) -> SimplifiedPokemon:
        return self.opponent_team[self.opponent_active_idx]

    @classmethod
    def from_battle(cls, battle: 'Battle') -> 'SimplifiedBattle':
        """poke-env의 Battle 객체에서 생성"""
        # 플레이어 팀
        player_team = [
            SimplifiedPokemon.from_pokemon(p)
            for p in battle.team.values()
        ]

        # 상대 팀
        opponent_team = [
            SimplifiedPokemon.from_pokemon(p)
            for p in battle.opponent_team.values()
        ]

        # 현재 필드의 포켓몬 인덱스
        player_active_idx = next(
            (i for i, p in enumerate(player_team) if p.active),
            0
        )
        opponent_active_idx = next(
            (i for i, p in enumerate(opponent_team) if p.active),
            0
        )

        return cls(
            player_team=player_team,
            opponent_team=opponent_team,
            player_active_idx=player_active_idx,
            opponent_active_idx=opponent_active_idx,
        )

    def clone(self) -> 'SimplifiedBattle':
        """깊은 복사"""
        return SimplifiedBattle(
            player_team=[p.clone() for p in self.player_team],
            opponent_team=[p.clone() for p in self.opponent_team],
            player_active_idx=self.player_active_idx,
            opponent_active_idx=self.opponent_active_idx,
        )
```

---

## 데미지 계산 엔진

### 기본 데미지 공식

**포켓몬 쇼다운 공식**:

```
Damage = (((2 × Level / 5 + 2) × Power × A / D) / 50 + 2) × Modifiers
```

**Modifiers**:

- Targets (더블배틀: 0.75)
- Weather (비/맑음: 1.5 or 0.5)
- Critical Hit (1.5)
- Random (0.85 ~ 1.0)
- STAB (1.5)
- Type Effectiveness (0.25 ~ 4.0)
- Burn (0.5, 물리 공격만)

---

### 구현

```python
class SimplifiedBattle:
    def calculate_damage(
        self,
        attacker: SimplifiedPokemon,
        defender: SimplifiedPokemon,
        move: SimplifiedMove,
        crit: bool = False,
    ) -> int:
        """데미지 계산"""
        # 변화 기술은 데미지 없음
        if move.category == MoveCategory.STATUS:
            return 0

        # 1. 레벨
        level = attacker.level

        # 2. 위력
        power = move.base_power
        if power == 0:
            return 0

        # 3. 공격/방어
        if move.category == MoveCategory.PHYSICAL:
            A = attacker.get_boosted_stat('atk')
            D = defender.get_boosted_stat('def')

            # 화상 보정
            if attacker.status == Status.BRN and not crit:
                A = int(A * 0.5)
        else:  # SPECIAL
            A = attacker.get_boosted_stat('spa')
            D = defender.get_boosted_stat('spd')

        # 4. 기본 데미지
        base = ((2 * level / 5 + 2) * power * A / D) / 50 + 2

        # 5. Modifiers
        modifier = 1.0

        # 5-1. 날씨
        modifier *= self._weather_modifier(move)

        # 5-2. 급소
        if crit:
            modifier *= 1.5

        # 5-3. 랜덤 (0.85 ~ 1.0)
        modifier *= random.uniform(0.85, 1.0)

        # 5-4. STAB
        if move.type in [attacker.type_1, attacker.type_2]:
            modifier *= 1.5

        # 5-5. 타입 상성
        effectiveness = self._type_effectiveness(move.type, defender)
        modifier *= effectiveness

        # 최종 데미지
        damage = int(base * modifier)
        return max(1, damage)  # 최소 1

    def _weather_modifier(self, move: SimplifiedMove) -> float:
        """날씨 보정"""
        if Weather.RAINDANCE in self.weather:
            if move.type == PokemonType.WATER:
                return 1.5
            elif move.type == PokemonType.FIRE:
                return 0.5

        elif Weather.SUNNYDAY in self.weather:
            if move.type == PokemonType.FIRE:
                return 1.5
            elif move.type == PokemonType.WATER:
                return 0.5

        return 1.0

    def _type_effectiveness(
        self,
        move_type: PokemonType,
        defender: SimplifiedPokemon,
    ) -> float:
        """타입 상성"""
        return move_type.damage_multiplier(
            defender.type_1,
            defender.type_2,
            type_chart=self.type_chart,
        )
```

---

### 급소 판정

```python
def _check_critical_hit(
    self,
    attacker: SimplifiedPokemon,
    move: SimplifiedMove,
) -> bool:
    """급소 판정"""
    # 급소율 단계
    crit_stage = 0

    # 기합 효과
    if Effect.FOCUS_ENERGY in attacker.effects:
        crit_stage += 2

    # 급소에 맞기 쉬운 기술
    if move.id in ['stoneedge', 'crosschop']:
        crit_stage += 1

    # 급소율
    crit_ratios = [1/24, 1/8, 1/2, 1/1]
    crit_ratio = crit_ratios[min(crit_stage, 3)]

    return random.random() < crit_ratio
```

---

## 턴 시뮬레이션

### 핵심 로직

```python
class SimplifiedBattle:
    def simulate_turn(
        self,
        player_action: str,  # "move:earthquake" or "switch:1"
        opponent_action: str,
    ) -> Dict:
        """턴 시뮬레이션"""
        self.turn += 1

        # 1. 행동 파싱
        p_type, p_data = self._parse_action(player_action)
        o_type, o_data = self._parse_action(opponent_action)

        # 2. 교체는 먼저 실행
        if p_type == "switch":
            self._switch(self.player_team, int(p_data))
        if o_type == "switch":
            self._switch(self.opponent_team, int(o_data))

        # 3. 기술 사용 순서 결정
        if p_type == "move" and o_type == "move":
            p_move = self.player_active.moves[p_data]
            o_move = self.opponent_active.moves[o_data]

            # 우선도 확인
            if p_move.priority > o_move.priority:
                first, second = ("player", p_move), ("opponent", o_move)
            elif p_move.priority < o_move.priority:
                first, second = ("opponent", o_move), ("player", p_move)
            else:
                # 스피드 비교
                p_speed = self._effective_speed(self.player_active)
                o_speed = self._effective_speed(self.opponent_active)

                if p_speed > o_speed:
                    first, second = ("player", p_move), ("opponent", o_move)
                elif p_speed < o_speed:
                    first, second = ("opponent", o_move), ("player", p_move)
                else:
                    # 동속 (50:50)
                    if random.random() < 0.5:
                        first, second = ("player", p_move), ("opponent", o_move)
                    else:
                        first, second = ("opponent", o_move), ("player", p_move)

            # 기술 실행
            self._execute_move(first[0], first[1])

            # 기절 확인
            if not self._check_fainted():
                self._execute_move(second[0], second[1])

        # 4. 턴 종료 처리
        self._end_of_turn()

        # 5. 배틀 종료 확인
        winner = self._check_winner()

        return {
            "winner": winner,
            "player_hp": self.player_active.current_hp,
            "opponent_hp": self.opponent_active.current_hp,
        }

    def _parse_action(self, action: str) -> tuple:
        """행동 파싱"""
        if action.startswith("move:"):
            return "move", action[5:]
        elif action.startswith("switch:"):
            return "switch", action[7:]
        else:
            raise ValueError(f"Invalid action: {action}")

    def _effective_speed(self, pokemon: SimplifiedPokemon) -> int:
        """실제 스피드 계산"""
        speed = pokemon.get_boosted_stat('spe')

        # 마비
        if pokemon.status == Status.PAR:
            speed = int(speed * 0.5)

        # 순풍
        if SideCondition.TAILWIND in self.player_side_conditions:
            speed = int(speed * 2)

        # 트릭룸
        if Field.TRICK_ROOM in self.fields:
            speed = -speed  # 음수로 반전

        return speed

    def _switch(self, team: List[SimplifiedPokemon], idx: int):
        """포켓몬 교체"""
        for i, pokemon in enumerate(team):
            pokemon.active = (i == idx)

    def _execute_move(self, side: str, move: SimplifiedMove):
        """기술 실행"""
        if side == "player":
            attacker = self.player_active
            defender = self.opponent_active
        else:
            attacker = self.opponent_active
            defender = self.player_active

        # 기절 확인
        if attacker.fainted:
            return

        # 명중 판정
        if not self._check_accuracy(attacker, defender, move):
            return

        # 급소 판정
        crit = self._check_critical_hit(attacker, move)

        # 데미지 계산
        damage = self.calculate_damage(attacker, defender, move, crit)
        defender.damage(damage)

        # 추가 효과
        if move.status and defender.status is None:
            defender.status = move.status

        if move.boosts:
            for stat, amount in move.boosts.items():
                defender.boost(stat, amount)

        # 반동/흡혈
        if move.recoil:
            recoil_damage = int(damage * move.recoil)
            attacker.damage(recoil_damage)

        if move.drain:
            drain_heal = int(damage * move.drain)
            attacker.heal(drain_heal)

    def _check_accuracy(
        self,
        attacker: SimplifiedPokemon,
        defender: SimplifiedPokemon,
        move: SimplifiedMove,
    ) -> bool:
        """명중 판정"""
        # 필중
        if move.accuracy == 100:
            return True

        # 명중률 계산
        acc_boost = attacker.boosts.get('accuracy', 0)
        eva_boost = defender.boosts.get('evasion', 0)

        if acc_boost >= 0:
            acc_mult = (3 + acc_boost) / 3
        else:
            acc_mult = 3 / (3 - acc_boost)

        if eva_boost >= 0:
            eva_mult = 3 / (3 + eva_boost)
        else:
            eva_mult = (3 - eva_boost) / 3

        final_accuracy = move.accuracy * acc_mult * eva_mult

        return random.random() * 100 < final_accuracy

    def _check_fainted(self) -> bool:
        """기절 확인"""
        return self.player_active.fainted or self.opponent_active.fainted

    def _end_of_turn(self):
        """턴 종료 처리"""
        # 날씨 데미지
        if Weather.SANDSTORM in self.weather:
            for pokemon in [self.player_active, self.opponent_active]:
                if pokemon.type_1 not in [PokemonType.ROCK, PokemonType.GROUND, PokemonType.STEEL]:
                    damage = pokemon.max_hp // 16
                    pokemon.damage(damage)

        # 상태이상 데미지
        for pokemon in [self.player_active, self.opponent_active]:
            if pokemon.status == Status.BRN:
                pokemon.damage(pokemon.max_hp // 16)
            elif pokemon.status == Status.PSN:
                pokemon.damage(pokemon.max_hp // 8)
            elif pokemon.status == Status.TOX:
                pokemon.status_counter += 1
                damage = (pokemon.max_hp * pokemon.status_counter) // 16
                pokemon.damage(damage)

    def _check_winner(self) -> Optional[str]:
        """승자 확인"""
        player_alive = any(not p.fainted for p in self.player_team)
        opponent_alive = any(not p.fainted for p in self.opponent_team)

        if not player_alive:
            return "opponent"
        elif not opponent_alive:
            return "player"
        else:
            return None
```

---

## MCTS 통합

### MCTS 노드

```python
import math

class MCTSNode:
    def __init__(
        self,
        battle: SimplifiedBattle,
        parent: Optional['MCTSNode'] = None,
        action: Optional[str] = None,
    ):
        self.battle = battle
        self.parent = parent
        self.action = action  # 이 노드로 오게 한 행동

        self.children: List[MCTSNode] = []
        self.visits = 0
        self.wins = 0

    def is_fully_expanded(self) -> bool:
        """모든 행동 확장 완료?"""
        legal_actions = self._get_legal_actions()
        return len(self.children) == len(legal_actions)

    def best_child(self, c_param: float = 1.414) -> 'MCTSNode':
        """UCB1으로 최적 자식 선택"""
        choices_weights = [
            (child.wins / child.visits) +
            c_param * math.sqrt((2 * math.log(self.visits)) / child.visits)
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]

    def expand(self) -> 'MCTSNode':
        """새 자식 노드 추가"""
        legal_actions = self._get_legal_actions()
        tried_actions = [child.action for child in self.children]
        untried_actions = [a for a in legal_actions if a not in tried_actions]

        action = random.choice(untried_actions)

        # 시뮬레이션
        new_battle = self.battle.clone()
        opponent_action = self._opponent_policy(new_battle)
        new_battle.simulate_turn(action, opponent_action)

        child = MCTSNode(new_battle, parent=self, action=action)
        self.children.append(child)
        return child

    def rollout(self) -> str:
        """랜덤 플레이아웃"""
        battle = self.battle.clone()

        while True:
            winner = battle._check_winner()
            if winner:
                return winner

            # 랜덤 행동
            p_action = random.choice(self._get_legal_actions())
            o_action = self._opponent_policy(battle)

            battle.simulate_turn(p_action, o_action)

    def backpropagate(self, result: str):
        """결과 역전파"""
        self.visits += 1
        if result == "player":
            self.wins += 1

        if self.parent:
            self.parent.backpropagate(result)

    def _get_legal_actions(self) -> List[str]:
        """합법 행동 목록"""
        actions = []

        # 기술 사용
        for move_id in self.battle.player_active.moves:
            actions.append(f"move:{move_id}")

        # 교체
        for i, pokemon in enumerate(self.battle.player_team):
            if not pokemon.fainted and not pokemon.active:
                actions.append(f"switch:{i}")

        return actions

    def _opponent_policy(self, battle: SimplifiedBattle) -> str:
        """상대 정책 (간단한 휴리스틱)"""
        # 랜덤 (실제로는 더 복잡)
        actions = []
        for move_id in battle.opponent_active.moves:
            actions.append(f"move:{move_id}")
        return random.choice(actions)
```

---

### MCTS 알고리즘

```python
def mcts_search(
    battle: SimplifiedBattle,
    iterations: int = 1000,
) -> str:
    """MCTS로 최적 행동 찾기"""
    root = MCTSNode(battle)

    for _ in range(iterations):
        # 1. Selection
        node = root
        while node.is_fully_expanded() and node.children:
            node = node.best_child()

        # 2. Expansion
        if not node.is_fully_expanded():
            node = node.expand()

        # 3. Simulation
        result = node.rollout()

        # 4. Backpropagation
        node.backpropagate(result)

    # 최다 방문 자식 선택
    best = max(root.children, key=lambda c: c.visits)
    return best.action
```

---

## 테스트 전략

### 단위 테스트

```python
import pytest

def test_simplified_pokemon_clone():
    """SimplifiedPokemon 복사 테스트"""
    from poke_env.battle import PokemonType, Status

    pokemon = SimplifiedPokemon(
        species="pikachu",
        level=50,
        type_1=PokemonType.ELECTRIC,
        type_2=None,
        max_hp=100,
        base_stats={'atk': 55, 'def': 40, 'spa': 50, 'spd': 50, 'spe': 90},
        moves={},
        current_hp=100,
        status=None,
        status_counter=0,
        boosts={'atk': 0},
        effects=set(),
        fainted=False,
        active=True,
    )

    # 복사
    clone = pokemon.clone()

    # 독립성 확인
    clone.damage(50)
    assert pokemon.current_hp == 100
    assert clone.current_hp == 50

def test_damage_calculation():
    """데미지 계산 테스트"""
    # 레벨 50 피카츄의 10만볼트 vs 레벨 50 갸라도스
    # 예상: ~90 데미지 (타입 상성 2배)
    pass

def test_turn_simulation():
    """턴 시뮬레이션 테스트"""
    # 선공 테스트
    # 후공 테스트
    # 기절 테스트
    pass
```

---

### 통합 테스트

```python
def test_full_battle():
    """전체 배틀 테스트"""
    # 실제 poke-env Battle 객체 생성
    from poke_env.player import RandomPlayer

    player = RandomPlayer()
    # ... 배틀 진행

    # SimplifiedBattle로 변환
    simplified = SimplifiedBattle.from_battle(player.current_battle)

    # 시뮬레이션
    result = simplified.simulate_turn("move:earthquake", "move:tackle")

    assert result is not None
```

---

## 최적화 팁

### 성능 프로파일링

```python
import cProfile
import pstats

def profile_mcts():
    """MCTS 성능 측정"""
    battle = SimplifiedBattle(...)

    profiler = cProfile.Profile()
    profiler.enable()

    mcts_search(battle, iterations=10000)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumtime')
    stats.print_stats(20)
```

---

### 병렬화

```python
from multiprocessing import Pool

def parallel_mcts(
    battle: SimplifiedBattle,
    iterations: int = 10000,
    workers: int = 4,
) -> str:
    """병렬 MCTS"""
    iterations_per_worker = iterations // workers

    with Pool(workers) as pool:
        results = pool.starmap(
            mcts_search,
            [(battle.clone(), iterations_per_worker)] * workers
        )

    # 결과 집계
    from collections import Counter
    votes = Counter(results)
    return votes.most_common(1)[0][0]
```

---

### 메모이제이션

```python
from functools import lru_cache

class SimplifiedBattle:
    @lru_cache(maxsize=10000)
    def _type_effectiveness_cached(
        self,
        move_type: PokemonType,
        def_type1: PokemonType,
        def_type2: Optional[PokemonType],
    ) -> float:
        """타입 상성 캐싱"""
        return move_type.damage_multiplier(def_type1, def_type2, self.type_chart)
```

---

## 자주 하는 실수

### 1. 얕은 복사

```python
# ❌ 잘못된 예
def clone(self):
    return copy.copy(self)  # 얕은 복사!

# ✅ 올바른 예
def clone(self):
    return SimplifiedPokemon(
        # ... 모든 필드 명시적 복사
        boosts=self.boosts.copy(),  # Dict 복사
        effects=self.effects.copy(),  # Set 복사
    )
```

---

### 2. 불변 객체 수정

```python
# ❌ 잘못된 예
@dataclass
class SimplifiedMove:
    boosts: Dict[str, int]  # 가변!

move.boosts['atk'] = 2  # 다른 곳에서도 변경됨!

# ✅ 올바른 예
@dataclass(frozen=True)
class SimplifiedMove:
    boosts: Optional[Dict[str, int]]  # 불변
```

---

### 3. 랜덤 시드

```python
# ❌ 잘못된 예 (재현 불가)
damage = calculate_damage(...)  # 매번 다른 결과

# ✅ 올바른 예 (재현 가능)
random.seed(42)
damage = calculate_damage(...)
```

---

### 4. 기절 후 행동

```python
# ❌ 잘못된 예
def simulate_turn(...):
    execute_move(player_move)
    execute_move(opponent_move)  # 플레이어 기절했는데 상대가 행동!

# ✅ 올바른 예
def simulate_turn(...):
    execute_move(first_move)
    if not self._check_fainted():
        execute_move(second_move)
```

---

### 5. 능력치 랭크 범위

```python
# ❌ 잘못된 예
def boost(self, stat, amount):
    self.boosts[stat] += amount  # -10까지 갈 수 있음!

# ✅ 올바른 예
def boost(self, stat, amount):
    self.boosts[stat] = max(-6, min(6, self.boosts[stat] + amount))
```

---

## 체크리스트

### Phase 1: 기본 구조

- [ ] SimplifiedPokemon 클래스 작성
- [ ] SimplifiedMove 클래스 작성
- [ ] SimplifiedBattle 클래스 작성
- [ ] `clone()` 메서드 테스트
- [ ] `from_battle()` 변환 테스트

### Phase 2: 데미지 계산

- [ ] 기본 공식 구현
- [ ] 타입 상성 적용
- [ ] STAB 보너스
- [ ] 급소 판정
- [ ] 날씨 보정
- [ ] 화상 보정

### Phase 3: 턴 시뮬레이션

- [ ] 행동 순서 결정
- [ ] 우선도 처리
- [ ] 스피드 계산
- [ ] 기술 실행
- [ ] 교체 처리
- [ ] 기절 처리

### Phase 4: 고급 기능

- [ ] 상태이상 (화상/마비/독)
- [ ] 날씨 효과
- [ ] 능력치 랭크
- [ ] 명중/회피
- [ ] 턴 종료 처리

### Phase 5: MCTS 통합

- [ ] MCTSNode 구현
- [ ] UCB1 알고리즘
- [ ] 플레이아웃
- [ ] 역전파
- [ ] 성능 테스트

---

## 다음 단계

1. **코드 작성**: 위 예제를 `SimplifiedBattle.py`에 작성
2. **테스트**: 단위 테스트 작성 및 실행
3. **디버깅**: 실제 배틀과 비교
4. **최적화**: 프로파일링 후 병목 제거
5. **확장**: 특성/아이템 효과 추가

---

**끝!** 🚀 이제 SimplifiedBattle을 구현할 준비가 되었습니다!
