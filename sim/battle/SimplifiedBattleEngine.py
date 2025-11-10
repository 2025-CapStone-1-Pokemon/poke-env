"""
SimplifiedBattle 시뮬레이션 엔진
"""
import copy
import random
from typing import Optional, Dict, List, Tuple
import sys
import os

# 상위 디렉토리(sim)를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SimplifiedBattle import SimplifiedBattle
from SimplifiedPokemon import SimplifiedPokemon
from SimplifiedMove import SimplifiedMove
from .DamageModifiers import (
    DamageModifierChain,
    BurnModifier,
    WeatherModifier,
    CriticalHitModifier,
    STABModifier,
    TypeEffectivenessModifier,
    RandomModifier
)
from poke_env.battle.effect import Effect
from poke_env.battle.move_category import MoveCategory
from poke_env.battle.status import Status
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.weather import Weather
from poke_env.battle.field import Field
from poke_env.battle.side_condition import SideCondition
from poke_env.data import GenData


class SimplifiedBattleEngine:
    """SimplifiedBattle 시뮬레이션 엔진"""
    
    def __init__(self, gen: int = 9):
        """
        Args:
            gen: 세대 (기본값: 9)
        """
        # GenData에서 타입 차트 가져오기
        data = GenData.from_gen(gen)
        self.type_chart = data.type_chart
        self.gen = gen
        
        # 데미지 보정 체인 초기화
        self.damage_modifiers = DamageModifierChain()
        self.damage_modifiers.add_modifier(BurnModifier())
        self.damage_modifiers.add_modifier(WeatherModifier())
        self.damage_modifiers.add_modifier(CriticalHitModifier())
        self.damage_modifiers.add_modifier(STABModifier())
        self.damage_modifiers.add_modifier(TypeEffectivenessModifier())
        self.damage_modifiers.add_modifier(RandomModifier())
    
    def simulate_turn(
        self,
        battle: SimplifiedBattle,
        player_move_idx: Optional[int] = None,
        opponent_move_idx: Optional[int] = None
    ) -> SimplifiedBattle:
        """
        1턴 시뮬레이션 (완전 랜덤)
        
        Args:
            battle: SimplifiedBattle 객체
            player_move_idx: 플레이어 기술 인덱스 (None이면 랜덤)
            opponent_move_idx: 상대 기술 인덱스 (None이면 랜덤)
            
        Returns:
            새로운 SimplifiedBattle 객체 (원본 유지)
        """
        # 1. 배틀 상태 복사 (deepcopy로 완전 독립)
        new_battle = copy.deepcopy(battle)
        new_battle.turn += 1
        
        # 2. 활성 포켓몬 확인
        if not new_battle.active_pokemon or not new_battle.opponent_active_pokemon:
            return new_battle
            
        if new_battle.active_pokemon.current_hp <= 0 or new_battle.opponent_active_pokemon.current_hp <= 0:
            return new_battle
        
        # 3. 기술 선택 (랜덤)
        player_move = self._select_random_move(new_battle.active_pokemon, player_move_idx)
        opponent_move = self._select_random_move(new_battle.opponent_active_pokemon, opponent_move_idx)
        
        if not player_move or not opponent_move:
            return new_battle
        
        # 4. 행동 순서 결정
        first_attacker, first_move, second_attacker, second_move = self._determine_order(
            new_battle.active_pokemon, player_move,
            new_battle.opponent_active_pokemon, opponent_move
        )
        
        # 5. 선공 실행
        if first_attacker == new_battle.active_pokemon:
            self._execute_move(new_battle, new_battle.active_pokemon, new_battle.opponent_active_pokemon, first_move)
        else:
            self._execute_move(new_battle, new_battle.opponent_active_pokemon, new_battle.active_pokemon, first_move)
        
        # 6. 후공 실행 (둘 다 살아있으면)
        if new_battle.active_pokemon.current_hp > 0 and new_battle.opponent_active_pokemon.current_hp > 0:
            if second_attacker == new_battle.active_pokemon:
                self._execute_move(new_battle, new_battle.active_pokemon, new_battle.opponent_active_pokemon, second_move)
            else:
                self._execute_move(new_battle, new_battle.opponent_active_pokemon, new_battle.active_pokemon, second_move)
        
        # 7. 턴 종료 처리
        self._end_of_turn(new_battle)
        
        # 8. 승패 확인
        self._check_winner(new_battle)
        
        return new_battle
    
    def _select_random_move(self, pokemon: SimplifiedPokemon, move_idx: Optional[int] = None) -> Optional[SimplifiedMove]:
        """랜덤 기술 선택"""
        # 기술이 없으면 기본 기술 생성 (상대 포켓몬의 경우)
        if not pokemon.moves:
            # 기본 공격 기술 생성 (Tackle 수준)
            class DefaultMove:
                def __init__(self):
                    self.id = 'tackle'
                    self.base_power = 40
                    self.accuracy = 100
                    self.priority = 0
                    self.type = pokemon.type_1 if pokemon.type_1 else PokemonType.NORMAL
                    self.category = MoveCategory.PHYSICAL
                    self.current_pp = 35
                    self.max_pp = 35
                    # 추가 효과 속성
                    self.boosts = None
                    self.self_boost = None
                    self.status = None
                    self.secondary = None
                    # 데미지 관련 속성
                    self.crit_ratio = 0
                    self.expected_hits = 1
                    self.recoil = 0
                    self.drain = 0
                    # 플래그 속성
                    self.flags = set()
                    self.breaks_protect = False
                    self.is_protect_move = False
            
            default_move = SimplifiedMove(DefaultMove())
            pokemon.moves = [default_move]  # 기본 기술 할당
            
        if move_idx is not None and 0 <= move_idx < len(pokemon.moves):
            return pokemon.moves[move_idx]
            
        # PP가 남은 기술 중 랜덤 선택
        available_moves = [move for move in pokemon.moves if move.current_pp > 0]
        if not available_moves:
            return None
            
        return random.choice(available_moves)
    
    def _determine_order(
        self,
        attacker1: SimplifiedPokemon, move1: SimplifiedMove,
        attacker2: SimplifiedPokemon, move2: SimplifiedMove
    ) -> Tuple[SimplifiedPokemon, SimplifiedMove, SimplifiedPokemon, SimplifiedMove]:
        """행동 순서 결정"""
        # 1. 우선도 비교
        priority1 = move1.priority
        priority2 = move2.priority
        
        if priority1 > priority2:
            return attacker1, move1, attacker2, move2
        elif priority2 > priority1:
            return attacker2, move2, attacker1, move1
        
        # 2. 스피드 비교
        speed1 = attacker1.get_effective_stat('spe')
        speed2 = attacker2.get_effective_stat('spe')
        
        if speed1 > speed2:
            return attacker1, move1, attacker2, move2
        elif speed2 > speed1:
            return attacker2, move2, attacker1, move1
        
        # 3. 동속: 랜덤 (50:50)
        if random.random() < 0.5:
            return attacker1, move1, attacker2, move2
        else:
            return attacker2, move2, attacker1, move1
    
    def _execute_move(
        self,
        battle: SimplifiedBattle,
        attacker: SimplifiedPokemon,
        defender: SimplifiedPokemon,
        move: SimplifiedMove
    ):
        """기술 실행"""
        # 0. PP 소모
        move.current_pp = max(0, move.current_pp - 1)
        
        # 1. 명중 판정
        if not self._check_accuracy(attacker, defender, move):
            return
        
        # 2. 급소 판정
        crit = self._check_critical_hit(attacker, move)
        
        # 3. 데미지 계산 및 적용
        if move.category != MoveCategory.STATUS:
            damage = self._calculate_damage(battle, attacker, defender, move, crit)
            defender.damage(damage)
        
        # 4. 추가 효과 (TODO: 나중에 구현)
        # - 상태이상
        # - 능력치 변화
        # - 반동/흡혈
    
    def _check_accuracy(
        self,
        attacker: SimplifiedPokemon,
        defender: SimplifiedPokemon,
        move: SimplifiedMove
    ) -> bool:
        """명중 판정"""
        # 임시: 명중률 테스트를 위해 항상 명중
        return True
        
        # 필중 기술
        if move.accuracy is None or move.accuracy >= 100:
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
    
    def _check_critical_hit(
        self,
        attacker: SimplifiedPokemon,
        move: SimplifiedMove
    ) -> bool:
        """급소 판정"""
        crit_stage = 0
        
        # 기합 효과
        if Effect.FOCUS_ENERGY in attacker.effects:
            crit_stage += 2
        
        # 급소에 맞기 쉬운 기술
        if move.id in ['stoneedge', 'crosschop', 'razorleaf', 'crabhammer']:
            crit_stage += 1
        
        # 급소율
        crit_ratios = [1/24, 1/8, 1/2, 1/1]
        crit_ratio = crit_ratios[min(crit_stage, 3)]
        
        return random.random() < crit_ratio
    
    def _calculate_damage(
        self,
        battle: SimplifiedBattle,
        attacker: SimplifiedPokemon,
        defender: SimplifiedPokemon,
        move: SimplifiedMove,
        crit: bool = False
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
            A = attacker.get_effective_stat('atk')
            D = defender.get_effective_stat('def')
        else:  # SPECIAL
            A = attacker.get_effective_stat('spa')
            D = defender.get_effective_stat('spd')
        
        # 4. 기본 데미지
        base_damage = ((2 * level / 5 + 2) * power * A / D) / 50 + 2
        
        # 5. 보정 적용 (책임 연쇄 패턴)
        battle_context = {
            'weather': battle.weather,
            'fields': battle.fields,
            'type_chart': self.type_chart
        }
        
        final_damage = self.damage_modifiers.apply_all(
            base_damage, attacker, defender, move, crit, battle_context
        )
        
        return max(1, int(final_damage))
    
    def _end_of_turn(self, battle: SimplifiedBattle):
        """턴 종료 처리"""
        # 날씨 데미지
        self._apply_weather_damage(battle)
        
        # 상태이상 데미지
        self._apply_status_damage(battle.active_pokemon)
        self._apply_status_damage(battle.opponent_active_pokemon)
    
    def _apply_weather_damage(self, battle: SimplifiedBattle):
        """날씨 데미지"""
        if Weather.SANDSTORM in battle.weather:
            for pokemon in [battle.active_pokemon, battle.opponent_active_pokemon]:
                if pokemon and pokemon.current_hp > 0:
                    # 바위/땅/강철 타입은 샌드스톰 데미지 면역
                    if pokemon.type_1 not in [PokemonType.ROCK, PokemonType.GROUND, PokemonType.STEEL]:
                        if pokemon.type_2 is None or pokemon.type_2 not in [PokemonType.ROCK, PokemonType.GROUND, PokemonType.STEEL]:
                            damage = pokemon.max_hp // 16
                            pokemon.damage(damage)
        
        elif Weather.HAIL in battle.weather:
            for pokemon in [battle.active_pokemon, battle.opponent_active_pokemon]:
                if pokemon and pokemon.current_hp > 0:
                    # 얼음 타입은 우박 데미지 면역
                    if PokemonType.ICE not in [pokemon.type_1, pokemon.type_2]:
                        damage = pokemon.max_hp // 16
                        pokemon.damage(damage)
    
    def _apply_status_damage(self, pokemon: SimplifiedPokemon):
        """상태이상 데미지"""
        if not pokemon or pokemon.current_hp <= 0:
            return
        
        if pokemon.status == Status.BRN:
            pokemon.damage(pokemon.max_hp // 16)
        elif pokemon.status == Status.PSN:
            pokemon.damage(pokemon.max_hp // 8)
        elif pokemon.status == Status.TOX:
            pokemon.status_counter += 1
            damage = (pokemon.max_hp * pokemon.status_counter) // 16
            pokemon.damage(damage)
    
    def _check_winner(self, battle: SimplifiedBattle):
        """승패 확인"""
        # 활성 포켓몬이 기절했는지 확인
        player_fainted = battle.active_pokemon.current_hp <= 0 if battle.active_pokemon else True
        opponent_fainted = battle.opponent_active_pokemon.current_hp <= 0 if battle.opponent_active_pokemon else True
        
        # 팀 전체가 기절했는지 확인
        player_alive = any(p.current_hp > 0 for p in battle.team.values())
        opponent_alive = any(p.current_hp > 0 for p in battle.opponent_team.values())
        
        if not player_alive:
            battle.finished = True
            battle.won = False
        elif not opponent_alive:
            battle.finished = True
            battle.won = True
    
    def simulate_full_battle(
        self,
        battle: SimplifiedBattle,
        max_turns: int = 100,
        verbose: bool = False
    ) -> SimplifiedBattle:
        """
        승패가 결정될 때까지 시뮬레이션 반복
        
        Args:
            battle: SimplifiedBattle 객체
            max_turns: 최대 턴 수 (무한 루프 방지)
            verbose: 각 턴 정보 출력 여부
            
        Returns:
            최종 SimplifiedBattle 객체
        """
        current_battle = copy.deepcopy(battle)
        turn_count = 0
        
        if verbose:
            print(f"\n=== 배틀 시뮬레이션 시작 (최대 {max_turns}턴) ===")
            self._print_battle_status(current_battle, "초기 상태")
        
        while not current_battle.finished and turn_count < max_turns:
            turn_count += 1
            
            if verbose:
                print(f"\n--- 턴 {turn_count} ---")
            
            # 1턴 시뮬레이션
            current_battle = self.simulate_turn(current_battle)
            
            if verbose:
                self._print_turn_result(current_battle, turn_count)
            
            # 활성 포켓몬이 기절했으면 교체 (랜덤)
            if current_battle.active_pokemon and current_battle.active_pokemon.current_hp <= 0:
                self._auto_switch(current_battle, is_player=True)
            
            if current_battle.opponent_active_pokemon and current_battle.opponent_active_pokemon.current_hp <= 0:
                self._auto_switch(current_battle, is_player=False)
        
        if verbose:
            print(f"\n=== 배틀 종료 ===")
            print(f"총 턴 수: {turn_count}")
            if current_battle.finished:
                winner = "플레이어" if current_battle.won else "상대"
                print(f"승자: {winner}")
            else:
                print(f"최대 턴 수 도달 (무승부)")
        
        return current_battle
    
    def _auto_switch(self, battle: SimplifiedBattle, is_player: bool):
        """
        자동 교체 (살아있는 포켓몬 중 랜덤 선택)
        
        Args:
            battle: SimplifiedBattle 객체
            is_player: True면 플레이어, False면 상대
        """
        team = battle.team if is_player else battle.opponent_team
        
        # 살아있는 포켓몬 찾기
        alive_pokemon = [p for p in team.values() if p.current_hp > 0]
        
        if not alive_pokemon:
            return
        
        # 랜덤으로 선택
        new_active = random.choice(alive_pokemon)
        
        if is_player:
            battle.active_pokemon = new_active
        else:
            battle.opponent_active_pokemon = new_active
        
        # first_turn 초기화
        new_active.first_turn = True
    
    def _print_battle_status(self, battle: SimplifiedBattle, label: str):
        """배틀 상태 출력"""
        print(f"\n[{label}]")
        
        if battle.active_pokemon:
            print(f"플레이어: {battle.active_pokemon.species} "
                  f"(HP: {battle.active_pokemon.current_hp}/{battle.active_pokemon.max_hp})")
        
        if battle.opponent_active_pokemon:
            print(f"상대: {battle.opponent_active_pokemon.species} "
                  f"(HP: {battle.opponent_active_pokemon.current_hp}/{battle.opponent_active_pokemon.max_hp})")
        
        # 팀 상태
        player_alive = sum(1 for p in battle.team.values() if p.current_hp > 0)
        opponent_alive = sum(1 for p in battle.opponent_team.values() if p.current_hp > 0)
        
        print(f"남은 포켓몬 - 플레이어: {player_alive}/{len(battle.team)}, "
              f"상대: {opponent_alive}/{len(battle.opponent_team)}")
    
    def _print_turn_result(self, battle: SimplifiedBattle, turn: int):
        """턴 결과 출력"""
        if battle.active_pokemon:
            hp_percent = (battle.active_pokemon.current_hp / battle.active_pokemon.max_hp) * 100
            print(f"플레이어: {battle.active_pokemon.species} "
                  f"(HP: {battle.active_pokemon.current_hp}/{battle.active_pokemon.max_hp} = {hp_percent:.1f}%)")
        else:
            print(f"플레이어: 기절")
        
        if battle.opponent_active_pokemon:
            hp_percent = (battle.opponent_active_pokemon.current_hp / battle.opponent_active_pokemon.max_hp) * 100
            print(f"상대: {battle.opponent_active_pokemon.species} "
                  f"(HP: {battle.opponent_active_pokemon.current_hp}/{battle.opponent_active_pokemon.max_hp} = {hp_percent:.1f}%)")
        else:
            print(f"상대: 기절")
