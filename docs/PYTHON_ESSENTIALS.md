# Python 필수 개념 정리 (C/Java 개발자용)

C/Java 경험자가 Python에서 꼭 알아야 할 핵심 개념들을 정리한 문서입니다.

---

## 1️⃣ 동적 타이핑 (Dynamic Typing)

### C/Java

```c
int x = 5;           // 타입 선언 필수
x = "hello";         // ❌ 컴파일 에러
```

### Python

```python
x = 5               # 타입 자동 추론
x = "hello"         # ✅ 가능! 타입 변경 자유
x = [1, 2, 3]       # ✅ 또 변경 가능
```

### 타입 힌트 (권장)

```python
def add(a: int, b: int) -> int:  # 힌트일 뿐, 강제 아님
    return a + b

result: int = add(5, 3)
```

---

## 2️⃣ 들여쓰기 (Indentation) - **매우 중요!**

### C/Java (중괄호 사용)

```java
if (condition) {
    doSomething();
    doMore();
}
```

### Python (들여쓰기로 블록 구분)

```python
if condition:
    do_something()
    do_more()          # 같은 레벨

do_other()            # if 블록 밖
```

### ❌ 가장 흔한 실수

```python
def my_function():
    x = 5
  y = 10  # ❌ IndentationError! (공백 2개 vs 4개)
```

### ✅ 일관된 들여쓰기 사용 (보통 공백 4개)

```python
def my_function():
    x = 5
    if x > 0:
        print("positive")  # 8칸 들여쓰기
```

---

## 3️⃣ None (null 대신)

```python
# Java: null
# Python: None

value = None

if value is None:      # ✅ 올바른 비교
    print("값 없음")

if value == None:      # ⚠️ 동작하지만 비권장
    print("값 없음")
```

---

## 4️⃣ 불린(Boolean) 값

```python
# True, False (첫 글자 대문자!)
is_active = True      # ✅
is_active = true      # ❌ NameError

# 조건문에서 자동 변환 (Falsy 값들)
if 0:           # False
if "":          # False
if []:          # False
if None:        # False
if {}:          # False

# Truthy 값들
if 1:           # True
if "hello":     # True
if [1, 2]:      # True
```

---

## 5️⃣ 리스트 vs 튜플 vs 딕셔너리 vs 세트

### List (가변, 순서 O)

```python
my_list = [1, 2, 3, "hello"]
my_list.append(4)          # 추가
my_list[0] = 10            # 수정 가능
```

### Tuple (불변, 순서 O)

```python
my_tuple = (1, 2, 3)
my_tuple[0] = 10           # ❌ TypeError (수정 불가)
```

### Dictionary (Key-Value, 순서 O - Python 3.7+)

```python
my_dict = {"name": "Pikachu", "level": 25}
my_dict["hp"] = 100        # 추가
value = my_dict["name"]    # 접근
value = my_dict.get("item", "없음")  # 안전한 접근 (기본값)
```

### Set (중복 제거, 순서 X)

```python
my_set = {1, 2, 3, 3, 3}   # → {1, 2, 3}
my_set.add(4)
```

---

## 6️⃣ 리스트 컴프리헨션 (List Comprehension) ⭐

### Java

```java
List<Integer> squares = new ArrayList<>();
for (int i = 0; i < 10; i++) {
    squares.add(i * i);
}
```

### Python (훨씬 간결!)

```python
squares = [i * i for i in range(10)]

# 조건 포함
evens = [i for i in range(10) if i % 2 == 0]

# 중첩
matrix = [[i * j for j in range(3)] for i in range(3)]
```

---

## 7️⃣ 언패킹 (Unpacking)

```python
# 튜플 언패킹
x, y = (1, 2)
x, y = y, x              # 스왑 (임시 변수 필요 없음!)

# 리스트 언패킹
first, *rest, last = [1, 2, 3, 4, 5]
# first = 1, rest = [2, 3, 4], last = 5

# 딕셔너리 언패킹
def greet(name, age):
    print(f"{name} is {age}")

info = {"name": "Pikachu", "age": 25}
greet(**info)  # greet(name="Pikachu", age=25)
```

---

## 8️⃣ 매개변수 (Arguments)

### 위치 인자 vs 키워드 인자

```python
def battle(attacker, defender, damage=10):
    pass

# 위치 인자
battle("Pikachu", "Charizard")

# 키워드 인자
battle(attacker="Pikachu", defender="Charizard", damage=20)

# 혼합 (위치 → 키워드 순서!)
battle("Pikachu", defender="Charizard", damage=20)
```

### \*args, \*\*kwargs

```python
def func(*args, **kwargs):
    print(args)    # 튜플: (1, 2, 3)
    print(kwargs)  # 딕셔너리: {'a': 10, 'b': 20}

func(1, 2, 3, a=10, b=20)
```

---

## 9️⃣ 예외 처리 (Exception Handling)

### Java

```java
try {
    // code
} catch (Exception e) {
    // handle
} finally {
    // cleanup
}
```

### Python

```python
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"에러: {e}")
except Exception as e:           # 모든 예외
    print("알 수 없는 에러")
else:                           # 예외 없을 때 실행
    print("성공")
finally:                        # 항상 실행
    print("정리 작업")
```

---

## 🔟 컨텍스트 매니저 (with 문)

### Java

```java
FileReader file = new FileReader("data.txt");
try {
    // use file
} finally {
    file.close();  // 수동으로 닫아야 함
}
```

### Python (자동으로 정리!)

```python
with open("data.txt", "r") as file:
    content = file.read()
    # 자동으로 close() 호출됨!

# 파일이 이미 닫혀있음
```

---

## 1️⃣1️⃣ Lambda (익명 함수)

```python
# 일반 함수
def add(x, y):
    return x + y

# Lambda
add = lambda x, y: x + y

# 자주 쓰이는 곳
numbers = [1, 2, 3, 4, 5]
squares = list(map(lambda x: x**2, numbers))
evens = list(filter(lambda x: x % 2 == 0, numbers))
sorted_data = sorted(data, key=lambda x: x['score'])
```

---

## 1️⃣2️⃣ f-string (포맷팅) ⭐

```python
name = "Pikachu"
level = 25
hp = 100

# 구식
print("Name: " + name + ", Level: " + str(level))

# ✅ f-string (Python 3.6+)
print(f"Name: {name}, Level: {level}")

# 표현식 사용 가능
print(f"HP: {hp / 100 * 100:.1f}%")
print(f"Next level: {level + 1}")
```

---

## 1️⃣3️⃣ 슬라이싱 (Slicing)

```python
text = "Hello World"
numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# [start:end:step]
text[0:5]        # "Hello"
text[:5]         # "Hello" (처음부터)
text[6:]         # "World" (끝까지)
text[::2]        # "HloWrd" (2칸씩)
text[::-1]       # "dlroW olleH" (역순!)

numbers[-1]      # 9 (뒤에서 첫번째)
numbers[-3:]     # [7, 8, 9] (뒤에서 3개)
```

---

## 1️⃣4️⃣ 이터레이터 & 제너레이터

### 이터레이터

```python
for item in [1, 2, 3]:       # 리스트
    print(item)

for char in "hello":         # 문자열
    print(char)

for key in {"a": 1}:         # 딕셔너리
    print(key)
```

### 제너레이터 (메모리 효율!)

```python
# 일반 리스트 (메모리에 전부 로드)
squares = [x**2 for x in range(1000000)]  # 메모리 많이 사용

# 제너레이터 (필요할 때만 생성)
squares = (x**2 for x in range(1000000))  # 메모리 효율적!

# 제너레이터 함수
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a          # return 대신 yield
        a, b = b, a + b

for num in fibonacci(10):
    print(num)
```

---

## 1️⃣5️⃣ 데코레이터 (Decorator) ⭐

```python
# 함수를 꾸며주는 함수
def timer(func):
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        print(f"실행 시간: {time.time() - start:.2f}초")
        return result
    return wrapper

# 사용법
@timer  # 데코레이터 적용
def slow_function():
    import time
    time.sleep(1)
    print("완료")

slow_function()  # 자동으로 시간 측정됨
```

### 실전 예제

```python
from functools import lru_cache

@lru_cache(maxsize=128)  # 결과 캐싱
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

---

## 1️⃣6️⃣ 클래스 & 상속

### 기본 클래스

```python
class Pokemon:
    # 클래스 변수
    total_count = 0

    def __init__(self, name, level):  # 생성자 (self는 this)
        self.name = name              # 인스턴스 변수
        self.level = level
        Pokemon.total_count += 1

    def attack(self):                 # 메서드
        print(f"{self.name} 공격!")

    @property                          # getter
    def info(self):
        return f"{self.name} Lv.{self.level}"

    @staticmethod                      # 정적 메서드
    def species_info():
        return "포켓몬"

    @classmethod                       # 클래스 메서드
    def get_total(cls):
        return cls.total_count
```

### 상속

```python
class ElectricPokemon(Pokemon):
    def __init__(self, name, level, voltage):
        super().__init__(name, level)  # 부모 생성자
        self.voltage = voltage

    def attack(self):                  # 오버라이딩
        print(f"{self.name} 전기 공격! ({self.voltage}V)")
```

### **slots** (메모리 최적화)

```python
class LightPokemon:
    __slots__ = ('name', 'level', 'hp')  # 속성 제한

    def __init__(self, name, level, hp):
        self.name = name
        self.level = level
        self.hp = hp
        # self.new_attr = 1  # ❌ AttributeError!

# 장점: 메모리 50-70% 절감
# 단점: 동적 속성 추가 불가
```

---

## 1️⃣7️⃣ 모듈 & 패키지

### 모듈 불러오기

```python
# 전체 import
import math
print(math.sqrt(16))

# 특정 함수만
from math import sqrt, pow
print(sqrt(16))

# 별칭 사용
import numpy as np
import pandas as pd

# 상대 경로 import
from .pokemon import Pokemon        # 같은 폴더
from ..battle import Battle         # 상위 폴더
from .sim.mcts import mcts_search  # 하위 폴더
```

### if **name** == "**main**"

```python
# pokemon.py
class Pokemon:
    def __init__(self, name):
        self.name = name

# 직접 실행할 때만 테스트 코드 실행
if __name__ == "__main__":
    pikachu = Pokemon("Pikachu")
    print(pikachu.name)
```

**동작 방식:**

- `python pokemon.py` 실행 시: `__name__ == "__main__"` → 테스트 코드 실행
- `import pokemon` 시: `__name__ == "pokemon"` → 테스트 코드 실행 안 됨

---

## 1️⃣8️⃣ async/await (비동기) ⭐

### 동기 (순차 실행)

```python
import time

def battle():
    time.sleep(1)  # 1초 대기
    return "완료"

result1 = battle()  # 1초
result2 = battle()  # 1초
# 총 2초
```

### 비동기 (동시 실행)

```python
import asyncio

async def battle():
    await asyncio.sleep(1)  # 다른 작업 실행 가능
    return "완료"

async def main():
    # 순차 실행 (2초)
    result1 = await battle()
    result2 = await battle()

    # 동시 실행 (1초)
    results = await asyncio.gather(
        battle(),
        battle()
    )

asyncio.run(main())
```

### 실전 예제

```python
async def main():
    mcts_player = MCTSPlayer(battle_format="gen8randombattle")
    random_player = RandomPlayer(battle_format="gen8randombattle")

    # await 키워드로 비동기 함수 호출
    await mcts_player.battle_against(random_player, n_battles=100)

    print(f"MCTSPlayer won {mcts_player.n_won_battles} / 100 battles")

if __name__ == "__main__":
    asyncio.run(main())  # 이벤트 루프 시작
```

---

## 1️⃣9️⃣ 덕 타이핑 (Duck Typing)

> "오리처럼 걷고 오리처럼 꽥꽥거리면, 그것은 오리다"

```python
# Java: 인터페이스/상속 필요
# Python: 같은 메서드만 있으면 OK!

class Pokemon:
    def attack(self):
        print("공격!")

class Robot:
    def attack(self):
        print("레이저!")

def battle(fighter):
    fighter.attack()  # Pokemon이든 Robot이든 상관없음!

battle(Pokemon())  # 공격!
battle(Robot())    # 레이저!
```

---

## 2️⃣0️⃣ Pythonic 코드 스타일

### ❌ C/Java 스타일 (비권장)

```python
# 인덱스로 반복
for i in range(len(my_list)):
    print(my_list[i])

# getter/setter
class Pokemon:
    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name
```

### ✅ Pythonic 스타일 (권장)

```python
# 직접 반복
for item in my_list:
    print(item)

# enumerate로 인덱스 필요 시
for i, item in enumerate(my_list):
    print(f"{i}: {item}")

# @property 사용
class Pokemon:
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

# 사용
pokemon.name = "Pikachu"  # setter
print(pokemon.name)        # getter
```

---

## 📚 필수 내장 함수

### range (반복문)

```python
for i in range(10):           # 0~9
for i in range(5, 10):        # 5~9
for i in range(0, 10, 2):     # 0,2,4,6,8
```

### enumerate (인덱스+값)

```python
for i, pokemon in enumerate(team):
    print(f"{i}: {pokemon}")
```

### zip (여러 리스트 동시 순회)

```python
names = ["Pikachu", "Charmander"]
levels = [25, 20]
for name, level in zip(names, levels):
    print(f"{name}: Lv.{level}")
```

### map, filter

```python
numbers = [1, 2, 3, 4, 5]
squares = list(map(lambda x: x**2, numbers))
evens = list(filter(lambda x: x % 2 == 0, numbers))
```

### any, all

```python
if any(pokemon.fainted for pokemon in team):
    print("기절한 포켓몬 있음")

if all(pokemon.hp > 0 for pokemon in team):
    print("모두 살아있음")
```

---

## 🔍 얕은 복사 vs 깊은 복사

### 문제 상황

```python
import copy

# 원본
original = {
    "name": "Pikachu",
    "moves": ["Thunder", "Quick Attack"]
}

# ❌ 얕은 복사 - 내부 객체는 참조만 복사
shallow = original.copy()
shallow["moves"].append("Iron Tail")

print(original["moves"])  # ["Thunder", "Quick Attack", "Iron Tail"] 😱
```

### 해결 방법

```python
# ✅ 깊은 복사 - 모든 것을 완전히 복사
deep = copy.deepcopy(original)
deep["moves"].append("Iron Tail")

print(original["moves"])  # ["Thunder", "Quick Attack"] ✅
```

### 적용 규칙

| 타입              | 복사 방법    | 이유            |
| ----------------- | ------------ | --------------- |
| `Dict[str, int]`  | `.copy()`    | int는 불변 타입 |
| `Dict[str, Move]` | `deepcopy()` | Move는 객체!    |
| `List[int]`       | `.copy()`    | int는 불변 타입 |
| `List[Pokemon]`   | `deepcopy()` | Pokemon은 객체! |

---

## 🎓 학습 우선순위

### 즉시 필요 (⭐⭐⭐)

1. 들여쓰기
2. 리스트/딕셔너리/튜플
3. f-string
4. if/for 문법
5. 클래스 기본
6. import 시스템

### 곧 필요 (⭐⭐)

7. 리스트 컴프리헨션
8. lambda
9. @property
10. 예외 처리
11. async/await

### 나중에 (⭐)

12. 데코레이터
13. 제너레이터
14. 컨텍스트 매니저
15. 덕 타이핑

---

## 🔗 추천 학습 자료

- [Python 공식 튜토리얼 (한국어)](https://docs.python.org/ko/3/tutorial/)
- [Python Cheat Sheet](https://www.pythoncheatsheet.org/)
- [Real Python](https://realpython.com/) (영어, 고급)
- [점프 투 파이썬](https://wikidocs.net/book/1) (한국어, 초급)

---

## 💡 프로젝트에서 자주 쓰이는 패턴

### 1. 클래스 상속으로 봇 만들기

```python
from poke_env.player import Player

class MCTSPlayer(Player):
    def choose_move(self, battle):
        if battle.available_moves:
            best_move = self.mcts_search(battle)
            return self.create_order(best_move)
        else:
            return self.choose_random_move(battle)
```

### 2. 비동기로 배틀 실행

```python
async def main():
    player1 = MCTSPlayer(battle_format="gen8randombattle")
    player2 = RandomPlayer(battle_format="gen8randombattle")

    await player1.battle_against(player2, n_battles=100)
    print(f"Win rate: {player1.n_won_battles}%")

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. 경량 객체로 시뮬레이션

```python
import copy

class SimplifiedBattle:
    def __init__(self, original_battle):
        # 자주 변하는 것만 복사
        self.active_pokemon = copy.deepcopy(original_battle.active_pokemon)
        self.opponent_pokemon = copy.deepcopy(original_battle.opponent_active_pokemon)

        # 읽기 전용은 참조만
        self.available_moves = original_battle.available_moves
```

### 4. 리스트 컴프리헨션으로 데이터 처리

```python
# 살아있는 포켓몬만 필터링
alive_pokemon = [p for p in team if not p.fainted]

# HP 비율 계산
hp_ratios = [p.current_hp / p.max_hp for p in team]

# 조건부 리스트
strong_moves = [m for m in moves if m.base_power > 80]
```

---

이 문서를 참고하면서 Python 개발에 익숙해지시길 바랍니다! 🐍✨
