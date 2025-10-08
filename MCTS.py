from poke_env.player import Player
from poke_env.environment import Battle
import math

class MCTSNode:
    def __init__(self, state, parent=None):
        self.state = state                    # 현재 상태
        self.parent = parent                  # 부모 노드
        self.children = []                    # 자식 노드 목록
        self.visits = 0                       # 방문 횟수
        self.wins = 0                         # 승리 횟수
        self.available_actions = self.get_actions()  # 가능한 이동
        self.replacable_pokemon = self.get_pokemon()  # 교체 가능한 포켓몬들

    def best_child(self, exploration_weight=1.4):
        # UCT(Upper Confidence Bound for Trees) 공식을 사용하여 최적의 자식 노드를 선택합니다.
        return max(self.children, key=lambda child:
                   (child.wins / child.visits) +
                   exploration_weight * math.sqrt(math.log(self.visits) / child.visits))

    def expand(self):
        # 새로운 자식 노드를 생성하고 추가하는 로직을 구현합니다.
        # 알파-베타 가지치기 (Alpha-Beta Pruning)

        for action in self.available_actions:
            new_state = self.state.clone()  # 현재 상태를 복제
            new_state.perform_action(action)  # 이동을 수행하여 새로운 상태 생성
            child_node = MCTSNode(new_state, parent=self)
            child_node.action = action
            self.children.append(child_node)
            return child_node  # 하나의 자식 노드만 확장

    def update(self, reward):
        # 노드의 방문 횟수와 가치를 업데이트하는 로직을 구현합니다.
        self.visits += 1
        self.wins += reward

    def is_terminal(self):
        # 현재 상태가 종료 상태인지 확인하는 로직
        # 더 이상 확장 할 수 없는지 확인
        # 게임이 종료되었는지 확인
        # 내 포켓몬이 모두 기절했거나 상대 포켓몬이 모두 기절했는지 확인
        
        # 내 포켓몬 확인
        if all(pokemon.current_hp == 0 for pokemon in self.state.team):
            return True

        # 상대 포켓몬 확인
        if all(pokemon.current_hp == 0 for pokemon in self.state.opponent_team):
            return True

        return False

    def rollout(self):
        # 시뮬레이션을 통해 게임을 끝까지 진행하는 로직을 구현합니다.
        current_state = self.state.clone()
        
        # 랜덤 플레이어를 사용하여 게임을 시뮬레이션
        while not self.is_terminal():
            possible_moves = current_state.available_moves
            if possible_moves:
                move = self.random.choice(possible_moves)
                current_state.perform_action(move)
            else:
                break  # 더 이상 이동할 수 없으면 종료

    def backpropagate(self, result):
        # 결과를 바탕으로 노드와 그 부모 노드들의 값을 업데이트하는 로직을 구현합니다.
        self.visits += 1
        self.wins += result
        if self.parent:
            self.parent.backpropagate(result)

    def get_actions(self):
        # 현재 상태에서 가능한 모든 이동을 반환하는 로직을 구현합니다.
        return self.state.available_moves
    
    def get_pokemon(self):
        return self.state.active_pokemon

# 여기서 root_state는 최초의 battle 객체를 의미한다.
def mcts_search(root_state, iterations=500):
    root = MCTSNode(root_state)

    for _ in range(iterations):
        node = root

        # Selection
        while not node.is_terminal() and node.is_fully_expanded():
            node = node.best_child()

        # Expansion
        if not node.is_terminal():
            node = node.expand()

        # Simulation
        result = node.rollout()

        # Backpropagation
        node.backpropagate(result)

    return root.best_child(c=0).action  # Return best move

