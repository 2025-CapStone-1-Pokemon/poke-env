"""
데미지 보정 클래스들 (책임 연쇄 패턴)
"""
from abc import ABC, abstractmethod
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SimplifiedPokemon import SimplifiedPokemon
from SimplifiedMove import SimplifiedMove
from poke_env.battle.status import Status
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.weather import Weather
from poke_env.battle.move_category import MoveCategory


class DamageModifier(ABC):
    """데미지 보정 인터페이스"""
    
    @abstractmethod
    def apply(
        self,
        damage: float,
        attacker: SimplifiedPokemon,
        defender: SimplifiedPokemon,
        move: SimplifiedMove,
        crit: bool,
        battle_context: dict
    ) -> float:
        """
        데미지 보정을 적용합니다.
        
        Args:
            damage: 현재 데미지 값
            attacker: 공격자 포켓몬
            defender: 방어자 포켓몬
            move: 사용된 기술
            crit: 급소 여부
            battle_context: 배틀 컨텍스트 (weather, fields 등)
            
        Returns:
            보정된 데미지 값
        """
        pass


class BurnModifier(DamageModifier):
    """화상 보정 - 물리 공격 데미지 절반"""
    
    def apply(self, damage: float, attacker: SimplifiedPokemon, defender: SimplifiedPokemon, 
              move: SimplifiedMove, crit: bool, battle_context: dict) -> float:
        if (move.category == MoveCategory.PHYSICAL and 
            attacker.status == Status.BRN and 
            not crit):
            return damage * 0.5
        return damage


class WeatherModifier(DamageModifier):
    """날씨 보정"""
    
    def apply(self, damage: float, attacker: SimplifiedPokemon, defender: SimplifiedPokemon, 
              move: SimplifiedMove, crit: bool, battle_context: dict) -> float:
        weather = battle_context.get('weather', {})
        
        if Weather.RAINDANCE in weather:
            if move.type == PokemonType.WATER:
                return damage * 1.5
            elif move.type == PokemonType.FIRE:
                return damage * 0.5
                
        elif Weather.SUNNYDAY in weather:
            if move.type == PokemonType.FIRE:
                return damage * 1.5
            elif move.type == PokemonType.WATER:
                return damage * 0.5
                
        return damage


class CriticalHitModifier(DamageModifier):
    """급소 보정"""
    
    def apply(self, damage: float, attacker: SimplifiedPokemon, defender: SimplifiedPokemon, 
              move: SimplifiedMove, crit: bool, battle_context: dict) -> float:
        if crit:
            return damage * 1.5
        return damage


class STABModifier(DamageModifier):
    """STAB (Same Type Attack Bonus) 보정"""
    
    def apply(self, damage: float, attacker: SimplifiedPokemon, defender: SimplifiedPokemon, 
              move: SimplifiedMove, crit: bool, battle_context: dict) -> float:
        if move.type in [attacker.type_1, attacker.type_2]:
            return damage * 1.5
        return damage


class TypeEffectivenessModifier(DamageModifier):
    """타입 상성 보정"""
    
    def apply(self, damage: float, attacker: SimplifiedPokemon, defender: SimplifiedPokemon, 
              move: SimplifiedMove, crit: bool, battle_context: dict) -> float:
        type_chart = battle_context.get('type_chart')
        effectiveness = move.type.damage_multiplier(
                defender.type_1,
                defender.type_2,
                type_chart=type_chart
            )
        return damage * effectiveness


class RandomModifier(DamageModifier):
    """랜덤 보정 (0.85 ~ 1.0)"""
    
    def apply(self, damage: float, attacker: SimplifiedPokemon, defender: SimplifiedPokemon, 
              move: SimplifiedMove, crit: bool, battle_context: dict) -> float:
        import random
        return damage * random.uniform(0.85, 1.0)


class DamageModifierChain:
    """보정 체인"""
    
    def __init__(self):
        self.modifiers = []
        
    def add_modifier(self, modifier: DamageModifier):
        """보정 추가"""
        self.modifiers.append(modifier)
        
    def apply_all(
        self,
        damage: float,
        attacker: SimplifiedPokemon,
        defender: SimplifiedPokemon,
        move: SimplifiedMove,
        crit: bool,
        battle_context: dict
    ) -> float:
        """모든 보정 적용"""
        for modifier in self.modifiers:
            damage = modifier.apply(damage, attacker, defender, move, crit, battle_context)
        return damage
