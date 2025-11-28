# 랜덤으로 포켓몬을 추정했을 때, 해당 포켓몬의 추정이 약하게 되는지를 확인하는 코드

"""
MCTS + SimplifiedBattle 통합 테스트
"""
import asyncio
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# 상위 디렉토리들을 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from poke_env.player import Player
from sim.SimplifiedBattle import SimplifiedBattle
from sim.battle.SimplifiedBattleEngine import SimplifiedBattleEngine


# SimplifiedBattleEngine 로그만 필터 (다른 모든 로그 제외)
class SimplifiedBattleEngineFilter(logging.Filter):
    """SimplifiedBattleEngine에서 나오는 로그만 필터링"""
    
    def filter(self, record):
        # SimplifiedBattleEngine에서 출력하는 로그만 허용
        # 로거 이름이 SimplifiedBattleEngine인 경우
        if "SimplifiedBattleEngine" in record.name:
            return True
        # 메시지에 SimplifiedBattleEngine 관련 내용이 있으면 허용
        if "SimplifiedBattleEngine" in record.getMessage():
            return True
        if "[Sim]" in record.getMessage():
            return True
        if "시뮬레이션" in record.getMessage():
            return True
        # 그 외 모든 로그는 제외
        return False


# 로깅 설정
def setup_logging():
    """파일과 콘솔에 모두 출력하는 로깅 설정"""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 로그 파일명 (타임스탬프 포함)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"test_simplified_battle_{timestamp}.log"
    
    # 로거 설정
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 파일 핸들러 (SimplifiedBattleEngine 로그만)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.addFilter(SimplifiedBattleEngineFilter())
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # 포맷
    formatter = logging.Formatter(
        '%(message)s'  # 배틀 상태는 간단한 포맷
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logging.info(f"배틀 로그 파일: {log_file}")
    
    return logger, log_file


class RandomPlayer(Player):
    """간단한 랜덤 플레이어"""
    
    def choose_move(self, battle):
        return self.choose_random_move(battle)


class TestPlayer(Player):
    """SimplifiedBattle 테스트 플레이어"""
    logger = logging.getLogger("SimplifiedBattleEngine")
    
    # SimplifiedBattleEngine을 클래스 레벨에서 캐싱
    _engine = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 엔진이 없으면 한 번만 생성
        if TestPlayer._engine is None:
            TestPlayer.logger.info("SimplifiedBattleEngine 초기화 (프로세스당 한 번)")
            TestPlayer._engine = SimplifiedBattleEngine(gen=9)
    
    def choose_move(self, battle):
        logger = logging.getLogger("TestPlayer.choose_move")
        
        if battle.turn == 1:
            logger.info(f"=== Turn {battle.turn}: SimplifiedBattle 시뮬레이션 시작 ===")
            logger.info(f"플레이어 포켓몬: {battle.active_pokemon}")
            logger.info(f"상대방 포켓몬: {battle.opponent_active_pokemon}")
            
            try:
                # SimplifiedBattle로 변환
                simplified_battle = SimplifiedBattle(battle)
                logger.info("SimplifiedBattle 변환 완료")
                
                # SimplifiedBattleEngine을 사용하여 시뮬레이션
                logger.info("SimplifiedBattleEngine.simulate_full_battle() 실행 중...")
                result = TestPlayer._engine.simulate_full_battle(
                    battle=simplified_battle,
                    verbose=True
                )
                
                logger.info("=== SimplifiedBattleEngine 시뮬레이션 완료 ===")
                logger.info(f"결과:\n{result}")
                
            except Exception as e:
                logger.error(f"시뮬레이션 중 오류 발생: {e}", exc_info=True)

        return self.choose_random_move(battle)


async def test_mcts_vs_random():
    """MCTS vs Random 테스트"""
    logger = logging.getLogger("test_mcts_vs_random")
    
    logger.info("=" * 60)
    logger.info("MCTS vs Random Bot 테스트 시작")
    logger.info("=" * 60)
    
    # 플레이어 생성
    logger.info("플레이어 생성 중...")
    mcts_player = TestPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1
    )
    
    random_player = RandomPlayer(
        battle_format="gen9randombattle",
        max_concurrent_battles=1
    )
    logger.info("플레이어 생성 완료")
    
    # 배틀 시작
    logger.info("\n배틀 시작...")
    
    try:
        await mcts_player.battle_against(random_player, n_battles=1)
    except Exception as e:
        logger.error(f"배틀 중 오류 발생: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
    
    # 결과 출력
    logger.info("\n" + "=" * 60)
    logger.info("배틀 결과")
    logger.info("=" * 60)
    logger.info(f"TestPlayer (SimplifiedBattle): {mcts_player.n_won_battles}승 {mcts_player.n_lost_battles}패")
    logger.info(f"RandomPlayer: {random_player.n_won_battles}승 {random_player.n_lost_battles}패")
    logger.info("=" * 60)


if __name__ == "__main__":
    # 로깅 초기화
    logger, log_file = setup_logging()
    logger.info("=" * 60)
    logger.info("테스트 시작")
    logger.info(f"로그 파일: {log_file}")
    logger.info("=" * 60)
    
    try:
        asyncio.run(test_mcts_vs_random())
    except KeyboardInterrupt:
        logger.info("사용자 중단")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}", exc_info=True)
    finally:
        logger.info("=" * 60)
        logger.info("테스트 종료")
        logger.info("=" * 60)
