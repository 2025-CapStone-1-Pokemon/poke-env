import asyncio
import sys
import os

# ==========================================
# 1. 경로 설정 (MCTS 모듈 가져오기 위해 필수)
# ==========================================
# 현재 파일 위치 기준으로 상위 폴더들을 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'player', 'mcts'))

# MCTS 모듈 임포트
try:
    from player.mcts.MCTS_temp_parallel import mcts_search
except ImportError:
    print("❌ 오류: 'player.mcts.MCTS_temp_parallel' 모듈을 찾을 수 없습니다.")
    print("   파일 경로 구조를 확인해주세요.")
    sys.exit(1)

# ==========================================
# 2. poke-env 관련 임포트 (보내주신 코드 스타일 적용)
# ==========================================
from poke_env.player import Player
from poke_env.ps_client.account_configuration import AccountConfiguration
from poke_env.ps_client.server_configuration import LocalhostServerConfiguration
from poke_env.battle import Battle


# ==========================================
# 3. MCTS 플레이어 클래스 정의
# ==========================================
class MCTSPlayer(Player):
    def _convert_simplified_action_to_battle_action(self, battle: Battle, simplified_action):
        """MCTS 결과를 poke-env 행동 객체로 변환"""
        if simplified_action is None: return None
        
        action_class_name = simplified_action.__class__.__name__
        
        # 기술(Move)인 경우
        if action_class_name == "SimplifiedMove":
            move_id = simplified_action.id
            for move in battle.available_moves:
                if move.id == move_id: return move
        
        # 교체(Pokemon)인 경우
        elif action_class_name == "SimplifiedPokemon":
            pokemon_species = simplified_action.species
            for pokemon in battle.available_switches:
                if pokemon.species == pokemon_species: return pokemon
        
        return None

    async def choose_move(self, battle: Battle):
        """매 턴마다 호출되는 메인 함수"""
        
        # 1. 선택지가 없으면(발버둥 등) 랜덤
        if len(battle.available_moves) == 0:
            return self.choose_random_move(battle)
        
        # 2. 터미널에 생각 중임을 표시
        print(f"\n🤔 [MCTS] {battle.player_username} 턴 {battle.turn} 계산 중...", end="", flush=True)
        
        # 3. 비동기 환경에서 MCTS 실행 (Blocking 방지)
        loop = asyncio.get_running_loop()
        try:
            # iterations: 시뮬레이션 횟수 (높을수록 똑똑하지만 느림)
            # 여기서는 500회로 설정 (필요하면 1000으로 늘려도 됨)
            simplified_action = await loop.run_in_executor(
                None, 
                mcts_search, 
                battle, 
                500,    # iterations
                True,  # verbose (로그 켬)
                1       # n_workers
            )
        except Exception as e:
            print(f"\n❌ [MCTS Error] {e}")
            import traceback
            traceback.print_exc()
            return self.choose_random_move(battle)

        print(" 완료! ⚡") # 줄바꿈

        # 4. 결과 변환 및 실행
        if simplified_action is None:
            return self.choose_random_move(battle)
        
        try:
            original_action = self._convert_simplified_action_to_battle_action(battle, simplified_action)
            
            if original_action is None:
                return self.choose_random_move(battle)
            
            # 봇이 무엇을 선택했는지 출력
            action_name = original_action.id if hasattr(original_action, 'id') else original_action.species
            print(f"👉 [MCTS] 선택: {action_name}")
            
            return self.create_order(original_action)
        except Exception:
            return self.choose_random_move(battle)


# ==========================================
# 4. 메인 실행 함수
# ==========================================
async def main():
    # 봇 계정 설정 (비밀번호 불필요)
    bot_username = "MCTS_Bot"
    bot_account_config = AccountConfiguration(bot_username, None)

    # 봇 생성
    mcts_bot = MCTSPlayer(
        account_configuration=bot_account_config,
        server_configuration=LocalhostServerConfiguration,
        battle_format="gen9randombattle", 
        max_concurrent_battles=10,        
    )

    print("\n==================================================")
    print(f"🚀 {bot_username} 가 로컬 서버에 접속했습니다!")
    print("==================================================")
    print("1. 브라우저를 켭니다.")
    print("2. 주소창에 입력: http://play.pokemonshowdown.com/?Server=localhost:8000")
    print("3. 'Find a User' -> 'MCTS_Bot' 검색 -> 'Challenge'")
    print("4. Format을 '[Gen 9] Random Battle'로 맞추고 대결 시작!")
    print("==================================================\n")

    # [수정된 부분] 무한 대기 로직 변경
    # accept_challenges(None, 1)은 "누구든 상관없이(None) 1번(1) 싸우겠다"는 뜻입니다.
    # 이걸 while True로 감싸서 게임이 끝나면 다시 대기 상태로 만듭니다.
    while True:
        try:
            await mcts_bot.accept_challenges(None, 1)
        except Exception as e:
            print(f"⚠️ 에러 발생 (재접속 시도): {e}")
            await asyncio.sleep(1) # 에러 시 1초 대기 후 재시도


if __name__ == "__main__":
    # 윈도우 환경 asyncio 정책 설정
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 봇을 종료합니다.")