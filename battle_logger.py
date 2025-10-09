# battle_logger.py
import re

class BattleLogMixin:
    """
    Player 클래스에 실시간 배틀 로그 출력 기능을 추가해 주는 믹스인 클래스.
    이 클래스를 다른 Player와 함께 상속하면 로그 기능이 자동으로 활성화됩니다.
    """
    def _format_pokemon_name(self, raw_name: str) -> str:
        """'p1a: Ribombee' 같은 형식에서 포켓몬 이름만 추출합니다."""
        clean_name = re.sub(r' \|.*', '', raw_name)
        if ': ' in clean_name:
            return clean_name.split(': ')[1].split(',')[0]
        return clean_name

    async def _handle_battle_message(self, split_message: list) -> None:
        """
        메시지를 가로채서 로그를 출력하고, 원래 Player의 기능도 호출합니다.
        """
        # 부모 클래스(Player)의 _handle_battle_message를 먼저 호출해야
        # 봇의 상태가 정상적으로 업데이트됩니다.
        await super()._handle_battle_message(split_message)

        for sub_message in split_message:
            if not isinstance(sub_message, list) or len(sub_message) < 2:
                continue

            key = sub_message[1]
            try:
                if key == 'turn':
                    print(f"\n턴 {sub_message[2]} {'-'*20}")
                elif key == 'switch':
                    p_name = self._format_pokemon_name(sub_message[2])
                    print(f"{sub_message[2][:2]}가 {p_name}을(를) 꺼냈다.")
                elif key == 'move':
                    source = self._format_pokemon_name(sub_message[2])
                    target = self._format_pokemon_name(sub_message[4])
                    move = sub_message[3]
                    print(f"{source}의 {move} 공격! -> {target}")
                elif key == '-damage':
                    target = self._format_pokemon_name(sub_message[2])
                    hp = sub_message[3]
                    if hp != '0 fnt':
                        print(f"  └ {target}의 HP: {hp}")
                elif key == 'faint':
                    target = self._format_pokemon_name(sub_message[2])
                    print(f"💀 {target}이(가) 쓰러졌다!")
                elif key == 'win':
                    winner = sub_message[2]
                    print(f"\n🎉 {winner}이(가) 배틀에서 승리했습니다!")
                    print("="*30)
                elif key == '-weather':
                    weather = sub_message[2]
                    print(f"🌦️ 날씨가 '{weather}' 상태가 되었다!")
            except (IndexError, ValueError):
                pass