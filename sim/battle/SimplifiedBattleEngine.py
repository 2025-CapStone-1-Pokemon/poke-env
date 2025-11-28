"""
SimplifiedBattle 시뮬레이션 엔진
"""
import copy
import random
from typing import Optional, Tuple
import sys
import os

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
        new_battle: SimplifiedBattle,
        player_move_idx: Optional[int] = None,
        opponent_move_idx: Optional[int] = None,
        opponent_move_name: Optional[str] = None,
        player_switch_to: Optional[str] = None,
        opponent_switch_to: Optional[str] = None,
        verbose: bool = False
    ) -> SimplifiedBattle:
        """
        1턴 시뮬레이션 (완전 랜덤)
        
        Args:
            battle: SimplifiedBattle 객체
            player_move_idx: 플레이어 기술 인덱스 (None이면 랜덤)
            opponent_move_idx: 상대 기술 인덱스 (None이면 랜덤)
            opponent_move_name: 상대 기술 이름 (opponent_move_idx 대신 사용 가능)
            
        Returns:
            새로운 SimplifiedBattle 객체 (원본 유지)
        """
        # 1. 배틀 턴수 증가 TODO new battle 수정하기

        if verbose:
            print(f"Simulating turn {new_battle.turn}")
            
        new_battle.turn += 1
        
        # 2. 활성 포켓몬 확인
        if not new_battle.active_pokemon or not new_battle.opponent_active_pokemon:
            if verbose:
                print("One of the active Pokemon is missing. Ending simulation.")
            return new_battle
        else:
            if verbose:
                print(f"Player's active Pokemon: {new_battle.active_pokemon.species} "
                      f"(HP: {new_battle.active_pokemon.current_hp}/{new_battle.active_pokemon.max_hp})")
                print(f"Opponent's active Pokemon: {new_battle.opponent_active_pokemon.species} "
                      f"(HP: {new_battle.opponent_active_pokemon.current_hp}/{new_battle.opponent_active_pokemon.max_hp})")
            
        if new_battle.active_pokemon.current_hp <= 0 or new_battle.opponent_active_pokemon.current_hp <= 0:
            if verbose:
                print("One of the active Pokemon has fainted. Ending simulation.")
            return new_battle
        
        # 3. 기술 혹은 교체 선택
        if verbose:
                print("=========== [Move Selection] =================")

        # 플레이어가 교체 한 경우
        if player_switch_to:
            # 반복문 돌려서 이름 같은거 확인
            for pokemon in new_battle.team.values():
                    if pokemon.species.lower() == player_switch_to.lower() and pokemon.current_hp > 0:
                        new_battle.active_pokemon = pokemon
                        if verbose:
                            print(f"Player switches to {pokemon.species}")
                        break
            else:
                if verbose:
                    print(f"Player attempted to switch to {player_switch_to}, but it's not available.")
            # 교체했으면 기술 선택 스킵
            player_move = "switch"
        else:
            player_move = self._select_random_move(new_battle.active_pokemon, player_move_idx, verbose=verbose)
        
        if opponent_switch_to:
            # 반복문 돌려서 이름 같은거 확인
            for pokemon in new_battle.opponent_team.values():
                    # 대소문자 구분 없이 비교
                    if pokemon.species.lower() == opponent_switch_to.lower() and pokemon.current_hp > 0:
                        new_battle.opponent_active_pokemon = pokemon
                        if verbose:
                            print(f"Opponent switches to {pokemon.species}")
                        break
            else:
                if verbose:
                    print(f"Opponent attempted to switch to {opponent_switch_to}, but it's not available.")
            # 교체했으면 기술 선택 스킵
            opponent_move = "switch"
        else:
            if opponent_move_name:
                opponent_move = self._select_move_by_name(new_battle.opponent_active_pokemon, opponent_move_name, verbose=verbose)
            else:
                opponent_move = self._select_random_move(new_battle.opponent_active_pokemon, opponent_move_idx, verbose=verbose)

        if verbose:
            print("===============================================")
        
        if not player_move or not opponent_move:
            if verbose:
                print("One of the selected moves is invalid. Ending simulation.")
            return new_battle
        
        # 4. 행동 순서 결정
        first_attacker, first_move, second_attacker, second_move = self._determine_order(
            new_battle.active_pokemon, player_move,
            new_battle.opponent_active_pokemon, opponent_move
        )
        
        # 5. 선공 실행
        if verbose:
            print("=========== [Turn Execution] =================")

        if first_attacker == new_battle.active_pokemon:
            self._execute_move(new_battle, new_battle.active_pokemon, new_battle.opponent_active_pokemon, first_move, switch_to=player_switch_to, verbose=verbose)
        else:
            self._execute_move(new_battle, new_battle.opponent_active_pokemon, new_battle.active_pokemon, first_move, switch_to=opponent_switch_to, verbose=verbose)
        
        # 6. 후공 실행 (둘 다 살아있으면)
        if new_battle.active_pokemon.current_hp > 0 and new_battle.opponent_active_pokemon.current_hp > 0:
            if second_attacker == new_battle.active_pokemon:
                self._execute_move(new_battle, new_battle.active_pokemon, new_battle.opponent_active_pokemon, second_move, switch_to=player_switch_to, verbose=verbose)
            else:
                self._execute_move(new_battle, new_battle.opponent_active_pokemon, new_battle.active_pokemon, second_move, switch_to=opponent_switch_to, verbose=verbose)

        if verbose:
            print("===============================================")
        
        # 7. 턴 종료 처리
        self._end_of_turn(new_battle)
        
        # 8. 활성 포켓몬 기절 시 교체
        if new_battle.active_pokemon and new_battle.active_pokemon.current_hp <= 0:
            self._auto_switch(new_battle, is_player=True)
        
        if new_battle.opponent_active_pokemon and new_battle.opponent_active_pokemon.current_hp <= 0:
            self._auto_switch(new_battle, is_player=False)
        
        # 9. 승패 확인
        self._check_winner(new_battle)

        if verbose:
            self._print_battle_status(battle=new_battle, label=f"After Turn {new_battle.turn}")
        
        return new_battle
    
    def _select_random_move(self, pokemon: SimplifiedPokemon, move_idx: Optional[int] = None, verbose: bool = False) -> Optional[SimplifiedMove]:
        """랜덤 기술 선택"""

        # 기술이 없으면 기본 기술 생성
        if not pokemon or not pokemon.moves or len(pokemon.moves) == 0:
            default_move = self._create_default_move(pokemon)
            if default_move:
                if verbose:
                    print(f"Pokemon has no moves. Using default move for Pokemon {pokemon.species}")
                return default_move
            return None
        
        # 특정 기술 인덱스 선택
        if move_idx is not None and 0 <= move_idx < len(pokemon.moves):
            if verbose:
                print(f"move_idx is not None. Selecting {pokemon.moves[move_idx].id} for Pokemon {pokemon.species}")
            return pokemon.moves[move_idx]
            
        # PP가 남은 기술 중 랜덤 선택
        available_moves = [move for move in pokemon.moves if move.current_pp > 0]

        if not available_moves:
            if verbose:
                print(f"No available moves with PP left. Using default move for Pokemon {pokemon.species}")
            # PP가 모두 없으면 기본 기술
            default_move = self._create_default_move(pokemon)
            if default_move:
                if verbose:
                    print(f"Using default move for Pokemon {pokemon.species}")
                return default_move
            return None
        
        random_move = random.choice(available_moves)
        if verbose:
            print(f"Randomly selected move {random_move.id} for Pokemon {pokemon.species}")
            print(f" power: {random_move.base_power}, accuracy: {random_move.accuracy}, category: {random_move.category}")
            
        return random_move
    
    def _select_move_by_name(self, pokemon: SimplifiedPokemon, move_name: str, verbose: bool = False) -> Optional[SimplifiedMove]:
        """
        기술 이름으로 기술 선택
        
        Args:
            pokemon: 포켓몬 객체
            move_name: 기술 이름 (예: "Earthquake", "Sunny Day")
            verbose: 상세 출력 여부
            
        Returns:
            선택된 기술 객체 (찾지 못하면 랜덤 선택)
        """
        # 기술이 없으면 기본 기술 생성
        if not pokemon or not pokemon.moves or len(pokemon.moves) == 0:
            default_move = self._create_default_move(pokemon)
            if default_move:
                if verbose:
                    print(f"Pokemon has no moves. Using default move for Pokemon {pokemon.species}")
                return default_move
            return None
        
        # move_name과 일치하는 기술 찾기
        # 공백, 하이픈 제거하고 소문자로 정규화하여 비교
        normalized_name = move_name.lower().replace(' ', '').replace('-', '')
        
        # 🔍 디버깅: 가용한 기술 목록 확인
        available_moves = [move.id for move in pokemon.moves]
        
        for move in pokemon.moves:
            normalized_id = move.id.lower().replace(' ', '').replace('-', '')
            if normalized_id == normalized_name:
                if verbose:
                    print(f"✅ Found move by name '{move_name}' -> {move.id} for Pokemon {pokemon.species}")
                # 성공 통계 기록
                self._move_name_match_success = getattr(self, '_move_name_match_success', 0) + 1
                return move
        
        # 찾지 못하면 랜덤 선택
        if verbose:
            print(f"❌ Move '{move_name}' not found for Pokemon {pokemon.species}.")
            print(f"   Available moves: {available_moves}")
            print(f"   Selecting random move instead.")
        # 실패 통계 기록
        self._move_name_match_failure = getattr(self, '_move_name_match_failure', 0) + 1
        return self._select_random_move(pokemon, move_idx=None, verbose=verbose)
    
    def _create_default_move(self, pokemon: SimplifiedPokemon) -> Optional[SimplifiedMove]:
        """포켓몬의 기본 기술 생성"""
        if not pokemon:
            return None
        
        class DefaultMove:
            def __init__(self, pokemon):
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
        
        return SimplifiedMove(DefaultMove(pokemon))
    
    def _determine_order(
        self,
        attacker1: SimplifiedPokemon, move1: SimplifiedMove,
        attacker2: SimplifiedPokemon, move2: SimplifiedMove
    ) -> Tuple[SimplifiedPokemon, SimplifiedMove, SimplifiedPokemon, SimplifiedMove]:
        """행동 순서 결정"""

        # TODO 따라가때리기 구현 (pursuit)

        # 0. switch 우선
        if move1 == "switch" and move2 != "switch":
            return attacker1, move1, attacker2, move2
        elif move2 == "switch" and move1 != "switch":
            return attacker2, move2, attacker1, move1
        elif move1 == "switch" and move2 == "switch":
            # 둘 다 교체면 랜덤 순서
            if random.random() < 0.5:
                return attacker1, move1, attacker2, move2
            else:
                return attacker2, move2, attacker1, move1

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
        move: SimplifiedMove,
        switch_to: Optional[str] = None,
        verbose: bool = False
    ):
        """기술 실행"""

        if move == "switch":
            self.swtich_active_pokemon(battle, pokemon_name=switch_to, is_player=(attacker == battle.active_pokemon))
            if verbose:
                print(f"{attacker.species} switches out!")
            return
        
        if(verbose):
            print(f"Attacker: {attacker.species}, Move: {move.id}, Defender: {defender.species}")

        # 0. PP 소모
        move.current_pp = max(0, move.current_pp - 1)
        
        # 1. 명중 판정 (STATUS 기술은 정확도 체크 필요)
        # STATUS 기술도 정확도가 있을 수 있으므로 체크
        if not self._check_accuracy(attacker, defender, move, verbose=verbose):
            if(verbose):
                print(f"{attacker.species}'s {move.id} missed!")
            return
        
        # 2. 급소 판정 (데미지 기술만)
        crit = False
        if move.category != MoveCategory.STATUS:
            crit = self._check_critical_hit(attacker, move)

        if(verbose and crit):
            print(f"Critical hit by {attacker.species} using {move.id}!")
        
        # 3. 데미지 계산 및 적용
        damage = 0
        if move.category != MoveCategory.STATUS:
            damage = self._calculate_damage(battle, attacker, defender, move, crit)
            defender.damage(damage)

            if(verbose):
                print(f"{attacker.species} used {move.id} dealing {damage} damage to {defender.species}!")
                print(f"{defender.species} HP is now {defender.current_hp}/{defender.max_hp}")
        
        # 4. 추가 효과 적용 ✅
        self._apply_move_effects(attacker, defender, move, damage, verbose=verbose)
        
    
    def _check_accuracy(
        self,
        attacker: SimplifiedPokemon,
        defender: SimplifiedPokemon,
        move: SimplifiedMove,
        verbose: bool = False
    ) -> bool:
        """명중 판정"""

        # poke-env에서 정확도는 0-1.0 범위 (소수점) 또는 None
        if move.accuracy is None or move.accuracy >= 1.0:
            return True
        
        # 명중률 계산 (능력치 부스트 적용)
        acc_boost = attacker.boosts.get('accuracy', 0)
        eva_boost = defender.boosts.get('evasion', 0)

        if verbose:
            print(f"acc_boost: {acc_boost}, eva_boost: {eva_boost}")
            print(f"Base accuracy: {move.accuracy}")
        
        # 능력치 부스트 배율 계산
        # 공격 부스트: (3 + boost) / 3
        # 회피 부스트: 3 / (3 + boost)
        if acc_boost >= 0:
            acc_mult = (3 + acc_boost) / 3
        else:
            acc_mult = 3 / (3 - acc_boost)
        
        if eva_boost >= 0:
            eva_mult = 3 / (3 + eva_boost)
        else:
            eva_mult = (3 - eva_boost) / 3
        
        # 최종 명중률 = 기술 명중률 * 공격자 정확도 배율 * 방어자 회피 배율
        # 주의: move.accuracy는 이미 0-1.0 범위의 소수점
        final_accuracy = move.accuracy * acc_mult * eva_mult
        
        # 0~1.0 범위로 정규화 (소수점)
        final_accuracy = max(0.01, min(1.0, final_accuracy))
        
        # 확률 판정 (0~1.0 범위)
        return random.random() < final_accuracy
    
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
        
        # 급소율 (생성 9세대 기준)
        # stage 0: 1/24, stage 1: 1/8, stage 2: 1/2, stage 3: 1/4 (max)
        crit_ratios = [1/24, 1/8, 1/2, 1/4]
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
        # 1. 능력치 타이머 업데이트 (만료된 boost 해제)
        self._update_boost_timers(battle)
        
        # 2. 날씨 데미지
        self._apply_weather_damage(battle)
        
        # 3. 상태이상 데미지
        self._apply_status_damage(battle.active_pokemon)
        self._apply_status_damage(battle.opponent_active_pokemon)
    
    def _apply_move_effects(
        self,
        attacker: SimplifiedPokemon,
        defender: SimplifiedPokemon,
        move: SimplifiedMove,
        damage: int,
        verbose: bool = False
    ):
        """기술의 추가 효과 적용
        
        - 상태이상 (Status)
        - 능력치 변화 (Boosts)
        - 자신 능력치 변화 (Self Boost)
        - 반동/흡혈 (Recoil/Drain)
        """
        
        # 1️⃣ 상태이상 적용 (상대방)
        if move.status:
            defender.status = move.status
            # 강독은 카운터 초기화
            if move.status == Status.TOX:
                defender.status_counter = 0
        
        # 2️⃣ 자신 능력치 강화 (self_boost)
        # 예: Swords Dance (+2 Atk), Dragon Dance (+1 Atk +1 Spe)
        if move.self_boost:
            for stat, amount in move.self_boost.items():
                # 대부분의 능력치 강화는 배틀 종료까지 유지 (turns=None)
                attacker.set_boost_with_timer(stat, amount, turns=None)
        
        # 3️⃣ 상대 능력치 변화 (boosts)
        # 예: Close Combat (-1 Def -1 SpDef), Toxic Thread (-1 Spe)
        if move.boosts:
            for stat, amount in move.boosts.items():
                # 대부분은 영구지만, 일부 기술은 1턴만 지속
                turns = self._get_boost_duration(move.id, stat)
                defender.set_boost_with_timer(stat, amount, turns=turns)
        
        # 4️⃣ 반동 (Recoil)
        # 예: Brave Bird (1/3 반동), Double-Edge (1/3 반동)
        if move.recoil and isinstance(move.recoil, (list, tuple)) and len(move.recoil) >= 2:
            recoil_damage = damage * move.recoil[0] // move.recoil[1]
            attacker.damage(recoil_damage)
        
        # 5️⃣ 흡수 (Drain)
        # 예: Drain Punch (1/2 흡수), Draining Kiss (1/2 흡수)
        if move.drain and isinstance(move.drain, (list, tuple)) and len(move.drain) >= 2:
            heal_amount = damage * move.drain[0] // move.drain[1]
            attacker.heal(heal_amount)
    
    def _get_boost_duration(self, move_id: str, stat: str) -> Optional[int]:
        """기술별 능력치 변화 지속 턴 수
        
        Returns:
            None = 배틀 종료까지 영구
            숫자 = N턴 지속
        """
        # 반동 효과 기술들 (1턴만 지속)
        recoil_boosts = {
            'closecombat': ['def', 'spd'],  # Close Combat: -1 Def -1 SpDef
            'hammerarm': ['spe'],            # Hammer Arm: -1 Spe
        }
        
        for move, boost_stats in recoil_boosts.items():
            if move_id == move and stat in boost_stats:
                return 1  # 1턴만 지속
        
        # 나머지는 모두 영구 (None)
        return None
    
    def _update_boost_timers(self, battle: SimplifiedBattle):
        """턴 종료 시 능력치 타이머 업데이트 및 만료된 boost 해제"""
        if battle.active_pokemon:
            if not hasattr(battle.active_pokemon, 'boost_timers'):
                battle.active_pokemon.boost_timers = {}
            battle.active_pokemon.decrement_boost_timers()
        
        if battle.opponent_active_pokemon:
            if not hasattr(battle.opponent_active_pokemon, 'boost_timers'):
                battle.opponent_active_pokemon.boost_timers = {}
            battle.opponent_active_pokemon.decrement_boost_timers()
    
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
            # 플레이어 패배
            battle.finished = True
            battle.won = False
            battle.lost = True
        elif not opponent_alive:
            # 플레이어 승리
            battle.finished = True
            battle.won = True
            battle.lost = False
    
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
            self.simulate_turn(current_battle, verbose=verbose)
            
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
            # 모든 포켓몬이 기절했으면 교체 불가
            if is_player:
                battle.active_pokemon = None
            else:
                battle.opponent_active_pokemon = None
            return
        
        # 현재 활성 포켓몬이 없거나 기절했으면 교체 필요
        current_active = battle.active_pokemon if is_player else battle.opponent_active_pokemon
        
        if current_active and current_active.current_hp > 0:
            # 현재 활성 포켓몬이 살아있으면 교체 불필요
            return
        
        # 살아있는 포켓몬 중에서 현재 활성 포켓몬 제외하고 선택
        available = [p for p in alive_pokemon if p != current_active]
        
        if not available:
            # 살아있는 포켓몬이 현재 활성 포켓몬뿐이면 그것 선택
            new_active = alive_pokemon[0]
        else:
            new_active = random.choice(available)
        
        if is_player:
            battle.active_pokemon = new_active
        else:
            battle.opponent_active_pokemon = new_active
        
        # first_turn 초기화
        new_active.first_turn = True

    def swtich_active_pokemon(
        self,
        battle: SimplifiedBattle,
        pokemon_name: str,
        is_player: bool
    ):
        """
        특정 포켓몬으로 교체
        
        Args:
            battle: SimplifiedBattle 객체
            pokemon_name: 교체할 포켓몬 이름
            is_player: True면 플레이어, False면 상대
        """
        team = battle.team if is_player else battle.opponent_team
        switch_pokemon = team.get(pokemon_name)
        
        if switch_pokemon and switch_pokemon.current_hp > 0:
            if is_player:
                battle.active_pokemon = switch_pokemon
            else:
                battle.opponent_active_pokemon = switch_pokemon
            
            # first_turn 초기화
            switch_pokemon.first_turn = True
    
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
        # player_alive = sum(1 for p in battle.team.values() if p.current_hp > 0)
        # opponent_alive = sum(1 for p in battle.opponent_team.values() if p.current_hp > 0)

        for pokemon in battle.team.values():
            status = "기절" if pokemon.current_hp <= 0 else f"HP: {pokemon.current_hp}/{pokemon.max_hp}"
            print(f"플레이어 팀 - {pokemon.species}: {status}")
        
        for pokemon in battle.opponent_team.values():
            status = "기절" if pokemon.current_hp <= 0 else f"HP: {pokemon.current_hp}/{pokemon.max_hp}"
            print(f"상대 팀 - {pokemon.species}: {status}")
    
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
