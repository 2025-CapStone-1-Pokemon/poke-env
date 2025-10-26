from platform import node
from random import random
from poke_env.player import Player
import math

class MCTSNode:
    def __init__(self, state, parent=None, action=None):
        self.state = state                    # 현재 상태
        self.action = action                  # 이 노드에 도달하기 위한 행동
        self.parent = parent                  # 부모 노드
        self.children = []                    # 자식 노드 목록
        self.visits = 0                       # 방문 횟수
        self.wins = 0                         # 승리 횟수
        self.available_actions = self.get_actions()  # 가능한 이동
        self.untried_actions = self.available_actions.copy()  # 시도하지 않은 이동들

    def best_child(self, exploration_weight=1.4):

        # 자식 노드가 없으면 None 반환
        if not self.children:
            return None

        # UCT(Upper Confidence Bound for Trees) 공식을 사용하여 최적의 자식 노드를 선택합니다.
        return max(self.children, key=lambda child:
                   (child.wins / child.visits) +
                   exploration_weight * math.sqrt(math.log(self.visits) / child.visits))

    def expand(self):
        # 새로운 자식 노드를 생성하고 추가하는 로직을 구현합니다.
        # 알파-베타 가지치기 (Alpha-Beta Pruning) 구현 예정
        # 시도하지 않은 행동이 남아있는지 확인
        if not self.untried_actions:
            return None  # 더 이상 확장할 수 없음
        
        action = self.untried_actions.pop()
        child_node = MCTSNode(action, parent=self)
        self.children.append(child_node)
        return child_node

    def update(self, reward):
        # 노드의 방문 횟수와 가치를 업데이트하는 로직을 구현합니다.
        self.visits += 1
        self.wins += reward

    def is_terminal(self):
        # 현재 상태가 종료 상태인지 확인하는 로직
        # 더 이상 확장 할 수 없는지 확인
        # 게임이 종료되었는지 확인
        # 내 포켓몬이 모두 기절했거나 상대 포켓몬이 모두 기절했는지 확인

        if all(pokemon.current_hp == 0 for pokemon in self.state.team.values()):
            return True

            # 상대 포켓몬 확인
        if all(pokemon.current_hp == 0 for pokemon in self.state.opponent_team.values()):
            return True

        return False

    def rollout(self):
        # 시뮬레이션을 통해 게임을 끝까지 진행하는 로직을 구현합니다.
        # 이 부분 구현 필요

        return random.choice([0, 1])  # 임시로 랜덤 결과 반환

    def backpropagate(self, result):
        # 결과를 바탕으로 노드와 그 부모 노드들의 값을 업데이트
        # 재귀적으로 부모 노드를 찾아서 결과를 업데이트 함
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
def mcts_search(root_state, iterations=100):


    root = MCTSNode(root_state)

    print("Root Node Created : ", root)

    for i in range(iterations):
        

        node = root

        print(f"Iteration {i}: node={node}, terminal={node.is_terminal() if node else 'None'}")

        # Selection
        while not node.is_terminal():
            node = node.best_child()
            if node is None:
                node = root  # 자식 노드가 없으면 루트로 돌아감
                break

        # Expansion
        if not node.is_terminal():
            node = node.expand()

        # Simulation
        result = node.rollout()

        # Backpropagation
        node.backpropagate(result)

    return root.best_child(c=0).action  # Return best move

