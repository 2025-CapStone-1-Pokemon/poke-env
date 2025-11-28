"""
SimplifiedBattle 시뮬레이션 엔진
"""
import copy
import random
import logging
from typing import List, Optional, Tuple
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
    logger = logging.getLogger("SimplifiedBattleEngine")
    
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
            self.logger.info(f"시뮬레이션 시작 : {new_battle.turn}")

        self._sync_references(new_battle)
            
        new_battle.turn += 1
        
        # 2. 활성 포켓몬 확인
        if not new_battle.active_pokemon or not new_battle.opponent_active_pokemon:
            if verbose:
                self.logger.info("활성 포켓몬 중 하나가 없습니다. 시뮬레이션 종료.")
            return new_battle
        else:
            if verbose:
                self.logger.info("=========== [Active Pokemon] ==============")
                self.logger.info(f"플레이어의 활성 포켓몬: {new_battle.active_pokemon.species} "
                      f"(HP: {new_battle.active_pokemon.current_hp}/{new_battle.active_pokemon.max_hp}) \n"
                      f"스탯 정보: Atk {new_battle.active_pokemon.get_effective_stat('atk')}, "
                      f"Def {new_battle.active_pokemon.get_effective_stat('def')}, "
                      f"SpA {new_battle.active_pokemon.get_effective_stat('spa')}, "
                      f"SpD {new_battle.active_pokemon.get_effective_stat('spd')}, "
                      f"Spe {new_battle.active_pokemon.get_effective_stat('spe')}")
                self.logger.info(f"상대의 활성 포켓몬: {new_battle.opponent_active_pokemon.species} "
                      f"(HP: {new_battle.opponent_active_pokemon.current_hp}/{new_battle.opponent_active_pokemon.max_hp}) \n"
                      f"상대의 기술 정보 : {[move.id for move in new_battle.opponent_active_pokemon.moves]} \n"
                        f"스탯 정보: Atk {new_battle.opponent_active_pokemon.get_effective_stat('atk')}, "
                        f"Def {new_battle.opponent_active_pokemon.get_effective_stat('def')}, "
                        f"SpA {new_battle.opponent_active_pokemon.get_effective_stat('spa')}, "
                        f"SpD {new_battle.opponent_active_pokemon.get_effective_stat('spd')}, "
                        f"Spe {new_battle.opponent_active_pokemon.get_effective_stat('spe')}")
                self.logger.info("===============================================\n\n")
            
        if new_battle.active_pokemon.current_hp <= 0 or new_battle.opponent_active_pokemon.current_hp <= 0:
            if verbose:
                self.logger.info("활성 포켓몬 중 하나가 기절했습니다. 시뮬레이션 종료.")
            return new_battle
        
        # 3. 기술 혹은 교체 선택
        if verbose:
                self.logger.info("=========== [Move Selection] =================")

        # 플레이어가 교체 한 경우
        if player_switch_to:
            # 반복문 돌려서 이름 같은거 확인
            for pokemon in new_battle.team.values():
                    if pokemon.species.lower() == player_switch_to.lower() and pokemon.current_hp > 0:
                        new_battle.active_pokemon = pokemon
                        if verbose:
                            self.logger.info(f"플레이어가 {pokemon.species}로 교체합니다.")
                        break
            else:
                if verbose:
                    self.logger.info(f"플레이어가 {player_switch_to}로 교체를 시도했으나, 사용할 수 없습니다.")
            # 교체했으면 기술 선택 스킵
            player_move = "switch"
        else:
            if new_battle.active_pokemon.volatiles.get('must_recharge'):
                player_move = "recharge" # 특수 행동 키워드
                if verbose: self.logger.info("플레이어는 반동으로 움직일 수 없습니다!")
            else:
                player_move = self.select_move(new_battle.active_pokemon, new_battle.opponent_active_pokemon, new_battle, move_idx=player_move_idx, verbose=verbose)
        
        if opponent_switch_to:
            # 반복문 돌려서 이름 같은거 확인
            for pokemon in new_battle.opponent_team.values():
                    # 대소문자 구분 없이 비교
                    if pokemon.species.lower() == opponent_switch_to.lower() and pokemon.current_hp > 0:
                        new_battle.opponent_active_pokemon = pokemon
                        if verbose:
                            self.logger.info(f"상대가 {pokemon.species}로 교체합니다.")
                        break
            else:
                if verbose:
                    self.logger.info(f"상대가 {opponent_switch_to}로 교체를 시도했으나, 사용할 수 없습니다.")
            # 교체했으면 기술 선택 스킵
            opponent_move = "switch"
        else:
            if new_battle.opponent_active_pokemon.volatiles.get('must_recharge'):
                opponent_move = "recharge" # 특수 행동 키워드
                if verbose: self.logger.info("상대는 반동으로 움직일 수 없습니다!")
            else:
                opponent_move = self.select_move(new_battle.opponent_active_pokemon, new_battle.active_pokemon, new_battle, move_name=opponent_move_name, verbose=verbose)

        if verbose:
            self.logger.info("=============================================== \n\n")
        
        if not player_move or not opponent_move:
            if verbose:
                self.logger.info("선택된 기술 중 하나가 유효하지 않습니다. 시뮬레이션 종료.")
            return new_battle
        
        # 4. 행동 순서 결정
        first_attacker, first_move, second_attacker, second_move = self._determine_order(
            new_battle.active_pokemon, player_move,
            new_battle.opponent_active_pokemon, opponent_move
        )
        
        # 5. 선공 실행
        if verbose:
            self.logger.info("=========== [Turn Execution] =================")

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
            self.logger.info("===============================================")
        
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
    
    def _sync_references(self, battle: SimplifiedBattle):
        """
        활성 포켓몬과 팀 딕셔너리의 포켓몬 객체를 동기화(참조 연결)합니다.
        deepcopy 등으로 인해 객체가 분리되는 현상을 방지
        """
        # 1. 플레이어 측 동기화
        if battle.active_pokemon:
            for key, pokemon in battle.team.items():
                # 종(Species)이 같은 포켓몬을 찾아 연결
                # (Zoroark 같은 일루전 특성이 있다면 주의 필요하지만, 일반적인 경우 작동)
                if pokemon.species == battle.active_pokemon.species:
                    battle.active_pokemon = pokemon 
                    break

        # 2. 상대방 측 동기화 (여기가 문제였음)
        if battle.opponent_active_pokemon:
            for key, pokemon in battle.opponent_team.items():
                if pokemon.species == battle.opponent_active_pokemon.species:
                    battle.opponent_active_pokemon = pokemon  # 참조 덮어쓰기!
                    break
    
    def select_move(
        self, 
        pokemon: SimplifiedPokemon, 
        opponent : SimplifiedPokemon,
        battle : SimplifiedBattle,
        move_idx: Optional[int] = None, 
        move_name: Optional[str] = None, 
        verbose: bool = False
    ) -> Optional[SimplifiedMove]:
        """
        기술 선택 통합 메서드
        우선순위: 1. move_name -> 2. move_idx -> 3. Random -> 4. Default(발버둥/몸통박치기)
        """
        
        # 1. 포켓몬 및 기술 목록 1차 유효성 검사
        if not pokemon or not pokemon.moves:
            if verbose:
                self.logger.info(f"Pokemon {pokemon.species if pokemon else 'Unknown'} has no moves.")
            return self._create_default_move(pokemon)

        selected_move = None

        # 2. 기술 이름으로 선택 시도 (move_name이 있을 경우)
        if move_name:
            selected_move = self._find_move_by_name(pokemon, move_name)
            if selected_move:
                if verbose:
                    self.logger.info(f"Selected move by name: {selected_move.id}")
                # 이름 매칭 성공 통계 등은 여기서 처리
            elif verbose:
                self.logger.info(f"Move '{move_name}' not found. Falling back to other methods.")

        # 3. 기술 인덱스로 선택 시도 (move_name 실패 혹은 미입력 시)
        if not selected_move and move_idx is not None:
            if 0 <= move_idx < len(pokemon.moves):
                selected_move = pokemon.moves[move_idx]
                if verbose:
                    self.logger.info(f"Selected move by index {move_idx}: {selected_move.id}")
            elif verbose:
                self.logger.info(f"Invalid move_idx {move_idx}.")

        available_moves = self._get_available_moves(pokemon)
        
        # 4. 랜덤 선택 (스마트 필터링 적용)
        if not selected_move:
            available_moves = self._get_available_moves(pokemon)
            
            # [수정] 데미지가 0인 기술(무효 상성) 필터링
            valid_moves = []
            for move in available_moves:
                # 변화기(Status)는 데미지 0이어도 OK
                if move.category == MoveCategory.STATUS:
                    valid_moves.append(move)
                    continue
                
                # 데미지 미리 계산 (0이면 제외)
                dmg = self._calculate_damage(battle, pokemon, opponent, move, crit=False, verbose=False)
                if dmg > 0:
                    valid_moves.append(move)
            
            # 유효한 기술이 하나도 없으면(전부 무효면) 어쩔 수 없이 전체 목록 사용 (발버둥 등)
            if not valid_moves:
                valid_moves = available_moves

            if valid_moves:
                selected_move = random.choice(valid_moves)
            else:
                return self._create_default_move(pokemon) # PP 없음

        return selected_move

    def _find_move_by_name(self, pokemon: SimplifiedPokemon, move_name: str) -> Optional[SimplifiedMove]:
        """이름으로 기술 찾기 (내부 로직 분리)"""
        normalized_target = move_name.lower().replace(' ', '').replace('-', '')
        
        for move in pokemon.moves:
            normalized_id = move.id.lower().replace(' ', '').replace('-', '')
            if normalized_id == normalized_target:
                return move
        return None

    def _get_available_moves(self, pokemon: SimplifiedPokemon) -> List[SimplifiedMove]:
        """PP가 남아있는 기술 목록 반환"""
        return [move for move in pokemon.moves if move.current_pp > 0]

    def _create_default_move(self, pokemon: SimplifiedPokemon) -> Optional[SimplifiedMove]:
        """기본 기술 생성 (발버둥 등)"""
        if not pokemon:
            return None
        
        # 내부 클래스 정의 (기존 로직 유지)
        class DefaultMove:
            def __init__(self, pokemon):
                self.id = 'tackle'  # 혹은 'struggle'
                self.base_power = 40
                self.accuracy = 100
                self.priority = 0
                self.type = pokemon.type_1 if pokemon.type_1 else PokemonType.NORMAL
                self.category = MoveCategory.PHYSICAL
                self.current_pp = 35
                self.max_pp = 35
                self.crit_ratio = 0
                self.expected_hits = 1
                self.recoil = 0
                self.drain = 0
                self.flags = set()
                self.breaks_protect = False
                self.is_protect_move = False
                # 필요한 속성들 None으로 초기화
                self.boosts = None
                self.self_boost = None
                self.status = None
                self.secondary = None

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
                self.logger.info(f"{attacker.species} 교체!")
            return
        
        if(verbose):
            self.logger.info(f"공격자: {attacker.species}, 기술: {move.id}, 방어자: {defender.species}")

        if(verbose): 
            self.logger.info(f"기술 정보 - Power: {move.base_power}, Accuracy: {move.accuracy}, Category: {move.category.name}")

        # 0. PP 소모
        move.current_pp = max(0, move.current_pp - 1)
        
        # 1. 명중 판정 (STATUS 기술은 정확도 체크 필요)
        # STATUS 기술도 정확도가 있을 수 있으므로 체크
        if not self._check_accuracy(attacker, defender, move, verbose=verbose):
            if(verbose):
                self.logger.info(f"{attacker.species}'s {move.id} missed!")
            return
        
        # 2. 급소 판정 (데미지 기술만)
        crit = False
        if move.category != MoveCategory.STATUS:
            crit = self._check_critical_hit(attacker, move)

        if(verbose and crit):
            self.logger.info(f"Critical hit by {attacker.species} using {move.id}!")
        
        # 3. 데미지 계산 및 적용
        damage = 0
        if move.category != MoveCategory.STATUS:
            damage = self._calculate_damage(battle, attacker, defender, move, crit, verbose=verbose)
            defender.damage(damage)

            if(verbose):
                self.logger.info(f"{attacker.species} used {move.id} dealing {damage} damage to {defender.species}!")
                self.logger.info(f"{defender.species} HP is now {defender.current_hp}/{defender.max_hp}")
        
        if 'recharge' in move.flags:
            attacker.volatiles['must_recharge'] = True
            if verbose:
                self.logger.info(f"  [Effect] {attacker.species} must recharge next turn!")
        
        # 4. 추가 효과 적용 
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
            self.logger.info(f"acc_boost: {acc_boost}, eva_boost: {eva_boost}")
            self.logger.info(f"Base accuracy: {move.accuracy}")
        
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
        crit: bool = False,
        verbose: bool = False
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
        level_factor = (2 * level / 5 + 2)
        base_damage = (level_factor * power * A / D) / 50 + 2

        if verbose:
            self.logger.info(f"\n[DAMAGE DEBUG] Move: {move.id} (BP: {power})")
            self.logger.info(f" - Level: {level} (Factor: {level_factor})")
            self.logger.info(f" - Attacker A: {A}, Defender D: {D} (Ratio: {A/D:.2f})")
            self.logger.info(f" - Pure Base Damage: {base_damage:.2f}")

        # 5. 보정 적용
        battle_context = {
            'weather': battle.weather,
            'fields': battle.fields,
            'type_chart': self.type_chart
        }
        
        # Modifier 적용 전후 비교
        final_damage = base_damage
        if hasattr(self, 'damage_modifiers'):
             final_damage = self.damage_modifiers.apply_all(
                base_damage, attacker, defender, move, crit, battle_context
            )
        
        if verbose:
             self.logger.info(f" - Final Damage (After Modifiers): {final_damage}")
             self.logger.info(f" - Multiplier Applied: {final_damage / base_damage:.2f}x") # 몇 배가 뻥튀기 됐는지 확인

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

        for p in [battle.active_pokemon, battle.opponent_active_pokemon]:
            if p and p.volatiles.get('must_recharge'):
                # TODO 이번 턴에 행동이 'recharge'였는지 확인하는 로직이 필요하지만,
                # 일단 턴이 지나면 무조건 해제 (약식)
                p.volatiles['must_recharge'] = False
    
    def _apply_move_effects(
        self,
        attacker: SimplifiedPokemon,
        defender: SimplifiedPokemon,
        move: SimplifiedMove,
        damage: int,
        verbose: bool = False
    ):
        """기술의 추가 효과 적용 (랭크업, 상태이상, 반동, 흡수)"""

        if(verbose):
            self.logger.info(f"기술명 : {move.id} / 효과 : {move.boosts}, {move.self_boost}, {move.status}, {move.recoil}, {move.drain}")
        
        # 1. 랭크업 (Self Boost)
        if move.self_boost:
            for stat, amount in move.self_boost.items():
                attacker.boost(stat, amount)
                if verbose: self.logger.info(f"  [Effect] {attacker.species}'s {stat} rose by {amount}!")

        # 2. 상대 랭크 다운 (Boosts)
        if move.boosts:
            for stat, amount in move.boosts.items():
                defender.boost(stat, amount)
                if verbose: self.logger.info(f"  [Effect] {defender.species}'s {stat} changed by {amount}!")

        # 3. 상태이상 (Status)
        if move.status:
            if defender.status is None:
                defender.status = move.status
                if verbose: self.logger.info(f"  [Effect] {defender.species} is now {move.status.name}!")

        # 4. 반동 (Recoil) 구현
        if move.recoil and isinstance(move.recoil, list) and len(move.recoil) == 2:
            numerator, denominator = move.recoil
            if denominator != 0 and damage > 0:
                recoil_damage = max(1, int(damage * numerator / denominator))
                attacker.damage(recoil_damage)
                if verbose: self.logger.info(f"  [Effect] Recoil! {attacker.species} took {recoil_damage} damage.")

        # 5. 흡수 (Drain) 구현
        if move.drain and isinstance(move.drain, list) and len(move.drain) == 2:
            numerator, denominator = move.drain
            if denominator != 0 and damage > 0:
                heal_amount = max(1, int(damage * numerator / denominator))
                attacker.heal(heal_amount)
                if verbose: self.logger.info(f"  [Effect] Drain! {attacker.species} recovered {heal_amount} HP.")
    
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
            self.logger.info(f"\n=== 배틀 시뮬레이션 시작 (최대 {max_turns}턴) ===")
            self._print_battle_status(current_battle, "초기 상태")
        
        while not current_battle.finished and turn_count < max_turns:
            turn_count += 1
            
            if verbose:
                self.logger.info(f"\n--- 턴 {turn_count} ---")
            
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
            self.logger.info(f"\n=== 배틀 종료 ===")
            self.logger.info(f"총 턴 수: {turn_count}")
            if current_battle.finished:
                winner = "플레이어" if current_battle.won else "상대"
                self.logger.info(f"승자: {winner}")
            else:
                self.logger.info(f"최대 턴 수 도달 (무승부)")
        
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
        self.logger.info(f"\n[{label}]")
        
        if battle.active_pokemon:
            self.logger.info(f"플레이어: {battle.active_pokemon.species} "
                  f"(HP: {battle.active_pokemon.current_hp}/{battle.active_pokemon.max_hp})")
        
        if battle.opponent_active_pokemon:
            self.logger.info(f"상대: {battle.opponent_active_pokemon.species} "
                  f"(HP: {battle.opponent_active_pokemon.current_hp}/{battle.opponent_active_pokemon.max_hp})")
        
        # 팀 상태
        # player_alive = sum(1 for p in battle.team.values() if p.current_hp > 0)
        # opponent_alive = sum(1 for p in battle.opponent_team.values() if p.current_hp > 0)

        for pokemon in battle.team.values():
            status = "기절" if pokemon.current_hp <= 0 else f"HP: {pokemon.current_hp}/{pokemon.max_hp}"
            self.logger.info(f"플레이어 팀 - {pokemon.species}: {status}")
        
        for pokemon in battle.opponent_team.values():
            status = "기절" if pokemon.current_hp <= 0 else f"HP: {pokemon.current_hp}/{pokemon.max_hp}"
            self.logger.info(f"상대 팀 - {pokemon.species}: {status}")
    
    def _print_turn_result(self, battle: SimplifiedBattle, turn: int):
        """턴 결과 출력"""
        if battle.active_pokemon:
            hp_percent = (battle.active_pokemon.current_hp / battle.active_pokemon.max_hp) * 100
            self.logger.info(f"플레이어: {battle.active_pokemon.species} "
                  f"(HP: {battle.active_pokemon.current_hp}/{battle.active_pokemon.max_hp} = {hp_percent:.1f}%)")
        else:
            self.logger.info(f"플레이어: 기절")
        
        if battle.opponent_active_pokemon:
            hp_percent = (battle.opponent_active_pokemon.current_hp / battle.opponent_active_pokemon.max_hp) * 100
            self.logger.info(f"상대: {battle.opponent_active_pokemon.species} "
                  f"(HP: {battle.opponent_active_pokemon.current_hp}/{battle.opponent_active_pokemon.max_hp} = {hp_percent:.1f}%)")
        else:
            self.logger.info(f"상대: 기절")

