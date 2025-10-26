# MCTS 구현 가이드 - Pokemon Showdown Battle AI

## 📋 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [구현 과정에서 발생한 문제들](#구현-과정에서-발생한-문제들)
3. [핵심 해결 방법](#핵심-해결-방법)
4. [직접 구현 시 가이드](#직접-구현-시-가이드)
5. [최종 성능](#최종-성능)

---

## 프로젝트 개요

### 목표

- **Monte Carlo Tree Search (MCTS)** 알고리즘을 사용하여 Pokemon Showdown 배틀 AI 구현
- RandomPlayer보다 높은 승률 달성 (목표: 50% 이상)

### 사용 기술

- **Framework**: poke-env (Python Pokemon Showdown 라이브러리)
- **Algorithm**: MCTS with UCB1 (Upper Confidence Bound)
- **Battle Format**: gen8randombattle (Generation 8 Random Battle)
- **Simulation**: Custom BattleState 클래스로 경량화된 시뮬레이션

### 구현한 파일

1. **temp_battle_state.py** - 시뮬레이션 가능한 경량 배틀 상태
2. **temp_mcts_simulation.py** - MCTS 알고리즘 구현
3. **temp_test_mcts_current.py** - 성능 테스트 코드

---

## 구현 과정에서 발생한 문제들

### 문제 1: evaluate() 함수가 항상 1.0을 반환 (0% 승률)

**증상:**

```
[MCTS Debug] Initial evaluation: 1.000
[MCTS Debug] Successful iterations: 9/50
All children: win_rate=100.00%
Win Rate: 0.0%
```

**원인:**

- 게임 초반에 `battle.opponent_team`이 **실제로 나타난 포켓몬만** 포함함
- 예: 상대가 1-2마리만 보여줬을 때, 나머지는 아직 `opponent_team`에 없음
- `evaluate()` 함수가 "내 팀 6마리 vs 상대 팀 2마리"로 계산 → 항상 1.0에 가까운 값

**해결:**

```python
def evaluate(self) -> float:
    # 잘못된 방식: 전체 팀 크기로 비교
    # my_alive = sum(1 for p in self.my_team if not p['fainted'])
    # opp_alive = sum(1 for p in self.opp_team if not p['fainted'])

    # 올바른 방식: 현재 필드 포켓몬 중심 평가
    my_active = next((p for p in self.my_team if p['active']), None)
    opp_active = next((p for p in self.opp_team if p['active']), None)

    if my_active and opp_active:
        field_score = my_active['hp_fraction'] / (my_active['hp_fraction'] + opp_active['hp_fraction'])

    # 가중치 합산
    final_score = (
        field_score * 0.5 +   # 현재 필드가 가장 중요 (50%)
        alive_score * 0.3 +   # 포켓몬 수 (30%)
        hp_score * 0.2        # 총 HP (20%)
    )
```

---

### 문제 2: MCTS가 9/50 iterations만 성공

**증상:**

```
[MCTS Debug] Successful iterations: 9/50
Root visits: 9
Children created: 9 (각각 visits=1)
```

**원인:**

- 루트 노드에만 `set_available_actions()` 호출
- Child 노드들은 `available_actions = []` (빈 리스트)
- Selection 단계에서 child로 이동 → `is_fully_expanded() = True` (액션이 0개) → Expansion 건너뜀 → 무한 루프

**해결:**

```python
def expand(self, original_battle) -> Optional['MCTSNode']:
    # ... 액션 적용 후 ...

    child = MCTSNode(new_state, parent=self, action=action)

    # *** 중요: Child 노드도 available actions 설정 ***
    child.set_available_actions(self.available_actions)

    self.children.append(child)
    return child
```

---

### 문제 3: 모든 Child가 동일한 Win Rate (Selection이 작동 안 함)

**증상:**

```
Child 0: visits=1, win_rate=67.86%
Child 1: visits=1, win_rate=67.86%
Child 2: visits=1, win_rate=67.86%
```

**원인:**

- `_simulate_opponent_turn()`이 주석 처리되어 있음
- 모든 child가 "교체만 하고 데미지 없음" → 동일한 평가

**해결:**

```python
def _simulate_opponent_turn(self, state: BattleState, original_battle):
    """상대 턴 시뮬레이션 (랜덤 공격)"""
    # 상대의 타입 기반 가상 기술 생성
    class FakeMove:
        def __init__(self, power, move_type, category):
            self.base_power = power
            self.type = f"PokemonType.{move_type.upper()}"
            self.category = f"MoveCategory.{category.upper()}"

    # 랜덤 위력 (50~80)
    power = random.randint(50, 80)
    fake_move = FakeMove(power, move_type, category)

    # 데미지 적용
    damage_fraction = state._calculate_damage(opp_active, my_active, fake_move)
    my_active['hp_fraction'] = max(0.0, my_active['hp_fraction'] - damage_fraction)
```

---

### 문제 4: 잘못된 최종 액션 선택 (0% → 30%)

**증상:**

- 50 iterations로 30% 승률
- 모든 child가 비슷한 방문 횟수 (5-6회)

**원인:**

```python
# 잘못된 방식: 방문 횟수로 선택
best_child = max(root.children, key=lambda c: c.visits)
```

- 방문 횟수가 비슷하면 **첫 번째 child** 선택
- 실제 성능(win rate)과 무관

**해결:**

```python
# 올바른 방식: Win rate로 선택
best_child = max(root.children, key=lambda c: c.wins / c.visits)
```

---

## 핵심 해결 방법

### 1. BattleState 클래스 설계

**목적:**

- poke-env의 Battle 객체를 **시뮬레이션 가능한 경량 상태**로 변환
- `clone()` 메서드로 MCTS 트리 확장 시 독립적인 상태 생성

**핵심 메서드:**

```python
class BattleState:
    def clone(self) -> 'BattleState':
        """깊은 복사로 독립적인 상태 생성"""
        return BattleState(state_dict={
            'my_team': copy.deepcopy(self.my_team),
            'opp_team': copy.deepcopy(self.opp_team),
            # ... 기타 상태
        })

    def apply_move(self, move, is_my_turn: bool):
        """기술 사용 시뮬레이션 (데미지 계산)"""
        # Showdown 데미지 공식 적용
        damage = ((2 * level / 5 + 2) * power * A / D / 50 + 2)
        damage *= STAB * type_effectiveness * random(0.85, 1.0)

    def apply_switch(self, switch_idx: int, is_my_turn: bool):
        """포켓몬 교체 시뮬레이션"""
        # active 플래그 업데이트

    def evaluate(self) -> float:
        """현재 상태 평가 (0.0 ~ 1.0)"""
        # 필드 HP (50%) + 포켓몬 수 (30%) + 총 HP (20%)
```

**주요 데이터 구조:**

```python
pokemon_dict = {
    'species': 'pikachu',
    'types': ('electric',),
    'hp_fraction': 0.75,  # 현재 HP 비율
    'fainted': False,
    'active': True,       # 필드에 나와있는지
    'status': None,       # 'PAR', 'BRN', 'PSN', etc.
    'boosts': {'atk': 0, 'def': 0, ...},
    'stats': {'hp': 211, 'atk': 146, ...}
}
```

---

### 2. MCTS 알고리즘 구현

**핵심 구조:**

```python
class MCTSNode:
    def __init__(self, state: BattleState, parent=None, action=None):
        self.state = state              # BattleState 인스턴스
        self.parent = parent
        self.action = action            # 이 노드로 오게 한 액션
        self.children = []
        self.visits = 0
        self.wins = 0.0
        self.available_actions = []
        self.untried_actions = []

def mcts_search(battle, iterations=100):
    root = MCTSNode(BattleState(battle))
    root.set_available_actions(battle.available_moves + battle.available_switches)

    for i in range(iterations):
        node = root

        # 1. Selection: UCB1로 최선의 child 선택
        while not node.is_terminal() and node.is_fully_expanded():
            node = node.best_child()

        # 2. Expansion: 새 child 생성
        if not node.is_terminal() and not node.is_fully_expanded():
            node = node.expand(battle)

        # 3. Simulation: 상태 평가
        result = node.rollout()

        # 4. Backpropagation: 결과 전파
        node.backpropagate(result)

    # 최고 win rate의 액션 선택
    best_child = max(root.children, key=lambda c: c.wins / c.visits)
    return best_child.action
```

**UCB1 공식:**

```python
def best_child(self, exploration_weight=1.4):
    def ucb_score(child):
        exploit = child.wins / child.visits
        explore = exploration_weight * math.sqrt(math.log(self.visits) / child.visits)
        return exploit + explore

    return max(self.children, key=ucb_score)
```

---

### 3. 상대 턴 시뮬레이션

**문제점:**

- 실제 배틀에서는 상대의 기술 정보를 알 수 없음
- `battle.opponent_active_pokemon`의 moves는 빈 리스트

**해결책:**

```python
def _simulate_opponent_turn(self, state, original_battle):
    """
    랜덤 공격 시뮬레이션
    - 상대 포켓몬의 타입으로 기술 타입 추정 (STAB 보너스)
    - 랜덤 위력 (50~80)
    - 물리/특수 랜덤 선택
    """
    opp_types = opp_active.get('types', ('normal',))
    move_type = opp_types[0]  # 첫 번째 타입 사용
    category = random.choice(['physical', 'special'])
    power = random.randint(50, 80)

    fake_move = FakeMove(power, move_type, category)
    damage = state._calculate_damage(opp_active, my_active, fake_move)
```

---

## 직접 구현 시 가이드

### 단계 1: BattleState 클래스 작성

**체크리스트:**

- [ ] `clone()` 메서드 구현 (deepcopy 사용)
- [ ] `_extract_team()`: Battle 객체 → dict 변환
- [ ] `apply_move()`: 데미지 계산 및 HP 업데이트
- [ ] `apply_switch()`: active 플래그 변경
- [ ] `_calculate_damage()`: Showdown 공식 적용
- [ ] `_get_type_effectiveness()`: type_chart.json 로드
- [ ] `evaluate()`: **현재 필드 중심** 평가 (상대 팀 불완전 고려)
- [ ] `is_terminal()`: 게임 종료 조건

**주의사항:**

```python
# ❌ 잘못된 예: 전체 팀 크기로 평가
if len(self.my_team) > len(self.opp_team):
    return 1.0

# ✅ 올바른 예: 현재 필드 + 살아있는 포켓몬
my_active_hp = my_active['hp_fraction']
opp_active_hp = opp_active['hp_fraction']
field_score = my_active_hp / (my_active_hp + opp_active_hp)
```

---

### 단계 2: MCTSNode 클래스 작성

**체크리스트:**

- [ ] `__init__`: state, parent, action, visits, wins
- [ ] `set_available_actions()`: **루트 + child 모두**
- [ ] `is_fully_expanded()`: `len(untried_actions) == 0`
- [ ] `expand()`:
  - [ ] 랜덤 액션 선택
  - [ ] 상태 clone
  - [ ] 액션 적용
  - [ ] **상대 턴 시뮬레이션** (중요!)
  - [ ] **Child에 available_actions 설정** (중요!)
- [ ] `best_child()`: UCB1 공식
- [ ] `rollout()`: `state.evaluate()`
- [ ] `backpropagate()`: 부모는 `1.0 - result`

**주의사항:**

```python
# ❌ 잘못된 예
child = MCTSNode(new_state, parent=self, action=action)
self.children.append(child)  # available_actions 없음!

# ✅ 올바른 예
child = MCTSNode(new_state, parent=self, action=action)
child.set_available_actions(self.available_actions)
self.children.append(child)
```

---

### 단계 3: mcts_search 함수 작성

**체크리스트:**

- [ ] BattleState 생성
- [ ] 루트 노드 생성 및 액션 설정
- [ ] MCTS 4단계 반복:
  1. **Selection**: `while fully_expanded: best_child()`
  2. **Expansion**: `node.expand(battle)`
  3. **Simulation**: `node.rollout()`
  4. **Backpropagation**: `node.backpropagate(result)`
- [ ] **최고 win rate 선택** (방문 횟수 아님!)

**코드 템플릿:**

```python
def mcts_search(battle, iterations=100, debug=False):
    initial_state = BattleState(battle)
    root = MCTSNode(initial_state)

    # 액션 수집
    available_actions = []
    available_actions.extend(list(battle.available_moves))
    available_actions.extend(list(battle.available_switches))

    root.set_available_actions(available_actions)

    for i in range(iterations):
        node = root

        # Selection
        while not node.is_terminal() and node.is_fully_expanded():
            node = node.best_child()
            if node is None:
                break

        # Expansion
        if node is not None and not node.is_terminal() and not node.is_fully_expanded():
            node = node.expand(battle)

        if node is None:
            continue

        # Simulation
        result = node.rollout()

        # Backpropagation
        node.backpropagate(result)

    # *** 중요: Win rate로 선택 ***
    if root.children:
        valid_children = [c for c in root.children if c.visits > 0]
        best_child = max(valid_children, key=lambda c: c.wins / c.visits)
        return best_child.action

    return available_actions[0] if available_actions else None
```

---

### 단계 4: Player 클래스 통합

```python
from poke_env.player import Player
import temp_mcts_simulation as MCTS

class MCTSPlayer(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iterations = 100

    def choose_move(self, battle):
        if battle.available_moves:
            best_action = MCTS.mcts_search(battle, iterations=self.iterations)
            if best_action:
                return self.create_order(best_action)

        return self.choose_random_move(battle)
```

---

### 단계 5: 성능 테스트

```python
async def test_performance():
    mcts_player = MCTSPlayer(battle_format="gen8randombattle")
    random_player = RandomPlayer(battle_format="gen8randombattle")

    await mcts_player.battle_against(random_player, n_battles=30)

    print(f"Win Rate: {mcts_player.win_rate:.1%}")
```

**목표 지표:**

- Iterations=50: ~30-40% 승률
- Iterations=100: ~60-70% 승률
- Iterations=200: ~70-80% 승률 (시간이 오래 걸림)

---

## 최종 성능

### 테스트 결과

| Iterations | Battles | Wins   | Losses | Win Rate  |
| ---------- | ------- | ------ | ------ | --------- |
| 50         | 10      | 3      | 7      | 30.0%     |
| 50         | 30      | 11     | 19     | 36.7%     |
| **100**    | **30**  | **21** | **9**  | **70.0%** |

### 성능 분석

**장점:**

- ✅ RandomPlayer 대비 2배 이상 승률 (70% vs 30%)
- ✅ 실제 시뮬레이션 기반 의사결정
- ✅ UCB1으로 exploration/exploitation 균형

**개선 가능한 부분:**

1. **더 깊은 시뮬레이션**: 현재는 1턴만 시뮬레이션 (내 턴 + 상대 턴)
2. **더 똑똑한 상대 모델링**: 현재는 랜덤 공격, 실제로는 타입 상성 고려
3. **상태 특징 추가**: 날씨, 필드 효과, 능력치 변화 등
4. **병렬화**: 여러 시뮬레이션 동시 실행
5. **신경망 통합**: AlphaGo처럼 정책/가치 네트워크 추가

---

## 핵심 교훈

### 1. 불완전 정보 처리

Pokemon Showdown은 **불완전 정보 게임**입니다:

- 상대의 전체 팀을 모름 (나타난 것만 보임)
- 상대의 기술, 아이템을 모름
- 상대의 능력치를 정확히 모름

→ **현재 보이는 정보**에 집중한 평가 함수 설계

### 2. Child 노드 초기화

MCTS에서 child 노드도 **독립적인 게임 상태**로 취급:

- 각 child가 자신의 `available_actions` 보유
- 상태 복사 시 깊은 복사 필수

### 3. 최종 선택 기준

- **방문 횟수** ≠ **최고 성능**
- **Win rate** = 실제 성능 지표
- Exploration이 충분했다면 win rate로 선택

### 4. 시뮬레이션 밸런스

- 상대 턴 시뮬레이션이 너무 강하면 모든 액션이 나빠 보임
- 너무 약하면 모든 액션이 좋아 보임
- **적절한 랜덤성** (위력 50~80) 필요

---

## 참고 자료

### MCTS 이론

- [MCTS Survey Paper](https://ieeexplore.ieee.org/document/6145622)
- [UCB Algorithm](https://en.wikipedia.org/wiki/Monte_Carlo_tree_search#Exploration_and_exploitation)

### Pokemon Showdown

- [Damage Calculator](https://calc.pokemonshowdown.com/)
- [Battle Simulator](https://github.com/smogon/pokemon-showdown)
- [poke-env Documentation](https://poke-env.readthedocs.io/)

### 구현 코드

- `temp_battle_state.py` - BattleState 클래스
- `temp_mcts_simulation.py` - MCTS 알고리즘
- `temp_test_mcts_current.py` - 테스트 코드

---

## 다음 단계

더 강한 AI를 만들려면:

1. **Minimax + Alpha-Beta Pruning** 시도
2. **Deep Q-Learning (DQN)** 구현
3. **AlphaZero-style** 신경망 + MCTS
4. **Ensemble**: 여러 AI의 투표로 결정

화이팅! 🚀
