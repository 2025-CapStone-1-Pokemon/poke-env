# main_bot.py
import asyncio

from poke_env.player import Player
from poke_env.ps_client.account_configuration import AccountConfiguration
from poke_env.ps_client.server_configuration import LocalhostServerConfiguration
from battle_logger import BattleLogMixin


# Player 클래스와 BattleLogMixin을 함께 상속
class RandomBotWithLogs(BattleLogMixin, Player):
    """
    RandomBot의 로직은 그대로 가지면서, BattleLogMixin의 로그 기능만 추가된 클래스.
    """
    def choose_move(self, battle):
        if battle.available_moves:
            return self.choose_random_move(battle)
        else:
            return self.choose_random_move(battle)

# --- 아래는 실행 코드 (기존과 동일) ---
async def main():
    bot_account_config = AccountConfiguration("LoggerRandomBot", None)

    # 3. 새로 만든 클래스로 봇을 생성합니다.
    bot = RandomBotWithLogs(
        account_configuration=bot_account_config,
        server_configuration=LocalhostServerConfiguration,
        log_level=25
    )
    print("로그 기능이 추가된 랜덤 봇이 실행되었습니다.")
    while True:
        await bot.accept_challenges(None, 1)

if __name__ == "__main__":
    asyncio.run(main())