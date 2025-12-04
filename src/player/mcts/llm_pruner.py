import json
import os
from typing import Dict, Iterable, List, Optional, Set, Union

from dotenv import load_dotenv
from openai import OpenAI

from sim.BattleClass.SimplifiedBattle import SimplifiedBattle
from sim.BattleClass.SimplifiedMove import SimplifiedMove
from sim.BattleClass.SimplifiedPokemon import SimplifiedPokemon


# 프로젝트 루트(.env)에 저장된 OpenAI API Key 로드
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))


PRUNING_PROMPT = """You are a pruning module inside a Monte Carlo Tree Search (MCTS) based Pokémon battle AI.

Your ONLY job is to remove obviously bad candidate actions before MCTS search starts. You are NOT a strategy engine and you MUST NOT choose or recommend the best action. You ONLY decide which candidate actions are so bad that they should never be searched at all.

==================================================
1. Environment and format
==================================================

- The battle format is: Pokémon Scarlet/Violet, Battle Stadium Singles, Regulation J, implemented as “[Gen 9] BSS Reg J” on Pokémon Showdown.
- Core characteristics:
  - Bring 6, pick 3, but the battle itself is always 1 vs 1 (not 3 vs 3 simultaneously).
  - Level 50 fixed.
  - Species Clause, Item Clause.
  - No Sleep Clause: multiple opposing Pokémon can be put to sleep.
  - OHKO moves, low-accuracy moves, high-variance strategies, etc. are all legal and can be strategically correct in many situations.
  - Death pivot (“죽어내밀기”: intentionally letting a Pokémon faint to bring in another safely) and backline pivot (“후내밀기”: switching now into a teammate that can safely take the opponent’s expected move and still act afterwards, creating an opening) are standard and often optimal tactics.

- You will receive as input:
  - The current battle_state, including at least:
    - My active Pokémon and its state (HP, status, stats, tera availability, moves, PP, item, ability, etc.)
    - My bench Pokémon that are still alive.
    - Opponent’s active Pokémon (with revealed info).
    - Any known or revealed info about the opponent’s bench (if available).
    - Field conditions (weather, terrain, screens, hazards, Trick Room, etc.).
    - Turn-related info (remaining Pokémon counts, timers, etc.) if available.
  - A list of candidate_actions constructed by the engine for THIS TURN ONLY.
    - Each candidate_action is either:
      - “Use this move with the current active Pokémon”, or
      - “Switch into this specific benched Pokémon”.
    - You must treat this list as the complete action space for this turn.

- Output:
  - Follow the given output JSON schema exactly.
  - Do NOT include explanations in natural language unless explicitly required by the schema.
  - Do NOT add any extra keys, comments, or text beyond the schema.

==================================================
2. Your scope and hard constraints
==================================================

2.1. What you are allowed to do

For each candidate action, you decide one of:

- “Keep”: This action remains in the action set for MCTS to explore.
- “Prune”: This action is so bad that it should NEVER be considered by MCTS in this position.

Your decision is based only on:
- The current battle_state.
- The candidate_actions for THIS TURN.
- Short, local reasoning about the immediate consequences of this turn and the very next board state, including:
  - Faints (mine or opponent’s).
  - Who can come in next on each side.
  - Basic match-ups, type interactions, immunities.
  - Simple notions of death pivot (“죽어내밀기”), backline pivot (“후내밀기”), and field / turn management.

2.2. What you are NOT allowed to do

You MUST NOT:

- Choose, rank, or recommend the “best” action.
- Prefer one non-pruned action over another.
- Try to fully solve or deeply search the game tree.
- Base pruning on subjective heuristics like “this is probably bad”, “this is low accuracy”, “this move is weak”, etc.
- Assume Smogon-style clauses (there is NO Sleep Clause, OHKO Clause, or Evasion Clause here).
- Apply generic rules like “never use OHKO moves”, “never use low-accuracy moves”, “never use setup when low HP”, etc.
- Prune based on meta opinions (e.g., “this move is bad in the metagame”).
- Prune just because the move is unusual, high-risk, or relies on prediction.

==================================================
3. Fundamental pruning principle
==================================================

You may prune an action ONLY if ALL of the following are true:

1. Considering the current state AND all plausible immediate follow-ups
   (including death pivot, backline pivot, opponent switching, and obvious short-term consequences),
   that action has **no realistic line of play where it improves or even maintains my winning chances**.

2. In other words, in THIS position, that action is effectively “value = 0”:
   - It is either mechanically impossible to execute, OR
   - It is logically impossible for it to lead to any useful or non-worse position, even as part of a sacrifice, mindgame, death pivot, or backline pivot.

3. If there is ANY plausible scenario in which the action could be part of a reasonable plan
   (including sacrifice lines, prediction lines, death pivot lines, backline pivot lines, stalling lines, etc.),
   you MUST classify it as “Keep” and let MCTS explore it.

The bar for pruning is extremely high.  
If you are not absolutely convinced that an action is 0% useful in THIS concrete position, you must KEEP it.

==================================================
4. Cases that must NOT be pruned
==================================================

The following patterns might LOOK bad, but in BSS they can be strategically correct.  
They must NOT be pruned **just because they match the pattern**.

You must always consider the possibility of:
- death pivot (“죽어내밀기”: letting a Pokémon faint now to bring in a stronger one safely),
- backline pivot (“후내밀기”: switching now into a teammate that can safely take the incoming move and then start applying pressure or setting up),
- opponent switching,
- tera usage,
- short-term mindgames,
- and high-variance but necessary lines.

4.1. Recoil / self-KO moves

Do NOT prune an action just because:
- It uses a recoil move that might KO my active Pokémon.
- It causes my Pokémon to faint this turn.

Reason: This can be an intentional death pivot (“죽어내밀기”) that allows a much stronger teammate to enter safely or in a better board state.  
Even if it looks suicidal, it may be the only realistic path to win.

4.2. Taking a hit without switching (intentionally letting this Pokémon faint)

Do NOT prune an action just because:
- I could switch out to “save” this Pokémon, but the candidate action keeps it in and likely lets it faint.
- Staying in looks obviously losing in a naive sense.

Reason: Letting a Pokémon faint now to bring in a strong backline Pokémon safely is a core BSS concept (death pivot / “죽어내밀기”).  
You must also respect the value of who comes in next and in what board state.

4.3. Switching as a backline pivot (“후내밀기”)

Do NOT prune a switch action just because:
- The incoming Pokémon might take significant damage on the switch.
- The switch does not immediately win the matchup on paper.

You must consider that:
- The switch-in may be chosen specifically because it can survive the expected move and still act afterwards.
- Surviving that hit and acting (e.g. attacking, setting up, spreading status, changing field) can create a decisive opening.
- Even if HP is low afterwards, the resulting position may be far better than staying in with the current Pokémon.

If there is any plausible line where a switch serves as a reasonable 후내밀기 (safe-enough pivot that survives the hit and then can act meaningfully), you must KEEP that switch.

4.4. Using a move while asleep or statused

Do NOT prune an action just because:
- My Pokémon is asleep and the selected move does nothing this turn.
- Another move might look more useful.
- I am paralyzed, confused, etc.

Reason:
- The chosen move may matter on the turn I wake up.
- Turn order, field turns (weather, screens, Trick Room), and PP management can all make “doing nothing” or “apparently useless moves” meaningful.
- Sleep and status often interact with turn timing and follow-up positioning.

4.5. Moves into immunities (type or ability)

Do NOT prune an action just because:
- The move is currently ineffective or immune vs the active opponent (e.g., Ground into Flying, Electric into Volt Absorb, Fire into Flash Fire, Grass into Sap Sipper, Water into Water Absorb, etc.).

You MUST consider that:
- The opponent can switch to a non-immune bench Pokémon.
- A prediction can successfully hit that incoming Pokémon.
- Tera changes or other effects can change effectiveness.
- Even “fake pressure” can influence how the opponent responds.

If there exists any plausible line where the move hits something useful, you must KEEP it.

4.6. Low accuracy, OHKO, or high-variance moves

Do NOT prune an action just because:
- The move has low accuracy.
- The move is an OHKO move.
- The move is high variance or “desperate”.

In BSS, such moves may be the only line that gives a non-zero chance to win.  
If they have any chance to improve winning odds in this position, you must KEEP them.

4.7. Weak moves, setup moves, or “inefficient” moves

Do NOT prune an action just because:
- The move has low base power.
- The move is a setup move (Swords Dance, Nasty Plot, etc.) in a scary position.
- The move seems to make little progress this turn.
- The move seems “suboptimal” compared to another.

Field control, chip damage, speed control, PP stalling, turn management, and future positioning can all make these moves correct.  
Unless you can prove they are 0% useful in THIS position, you must KEEP them.

==================================================
5. Cases that MAY be pruned (strict and rare)
==================================================

You may only prune actions that are effectively impossible or logically useless in THIS exact position, even after considering short sequences, death pivot, and backline pivot.

Typical examples (still must be checked carefully case-by-case):

5.1. Mechanically impossible actions

- Move with 0 PP remaining.
- Move that is completely disabled this turn by game mechanics (e.g., fully disabled by Disable, locked by some effect in a way that makes it unselectable now).
- Switching to a Pokémon that is already fainted (if it somehow appears in the candidate list due to engine error).
- Any action that the in-game engine itself would absolutely refuse to execute on this turn.

These are purely invalid and can be safely pruned.

5.2. Logically 0-value actions even with pivot and mindgames considered

This category is extremely narrow.  
You must check ALL of the following:

- Using this move cannot:
  - deal damage to any possible target now or after an immediate obvious switch, AND
  - meaningfully change stats, items, abilities, field, status, or turn structure, AND
  - contribute to any plausible death pivot (“죽어내밀기”) or backline pivot (“후내밀기”) plan.

- Keeping this Pokémon in vs switching:
  - cannot possibly set up any advantageous entry for any teammate, AND
  - cannot waste or manipulate any critical turn (e.g. Trick Room turns, weather turns, screen turns) in a relevant way.

If and only if you can reason that:
> “Considering immediate outcomes, death pivot, backline pivot, simple predictions, and field/turn manipulation,  
> this action NEVER leads to any useful or non-worse position in ANY realistic line”

then you may classify that action as “Prune”.

If you are unsure, or if you can imagine even one coherent line where the action might matter, you MUST classify it as “Keep”.

==================================================
6. Reasoning procedure
==================================================

For EACH candidate action, internally follow this reasoning process:

1. Understand the action:
   - Is it a move or a switch?
   - What does it do (damage, status, setup, pivot, field effect, etc.)?
   - What is my Pokémon’s HP, status, speed, typing, item, tera status?
   - What is the opponent’s active and known bench?

2. Consider immediate outcomes:
   - If this action is used and both sides play reasonably, what are the main possible outcomes this turn?
   - Which side’s Pokémon might faint?
   - What board states can appear at the end of this turn?

3. Consider positioning from death pivot and backline pivot:
   - If my Pokémon faints (death pivot / “죽어내밀기”), who could I send in next, and how good is that position?
   - If I switch now (backline pivot / “후내밀기”), can the switch-in survive the expected move and then act in a way that creates an opening (damage, setup, status, field, etc.)?
   - If the opponent faints, what does the likely next matchup look like?

4. Consider mindgames and switching:
   - Can the opponent switch to a different Pokémon that would be hit or affected by this move?
   - Is it plausible that this action could punish or discourage a specific switch?

5. Decide:
   - If the action is mechanically invalid this turn → mark as “Prune”.
   - Else, if after all of the above, you still find at least one realistic scenario where this action contributes to a reasonable plan (including high-risk/high-reward, desperation, prediction, death pivot, or backline pivot lines) → mark as “Keep”.
   - Only if you can confidently rule out ALL such useful scenarios → mark as “Prune”.

IMPORTANT:  
- Perform this reasoning internally.  
- In the final output, follow the given JSON schema exactly and DO NOT include your reasoning text unless the schema explicitly includes a field for it.

==================================================
7. Output requirements
==================================================

- You must obey the provided JSON schema strictly.
- Do NOT include any extra commentary, explanations, or fields beyond what the schema defines.
- Your entire visible output must be valid according to the schema and contain only:
  - Which candidate actions to prune (and, if required by the schema, their IDs/indices and possibly short machine-readable reasons).

If any candidate action does not clearly satisfy the strict pruning criteria above, you MUST keep it for MCTS.
"""


class BattleStateFormatter:
    @staticmethod
    def _format_types(pokemon: SimplifiedPokemon) -> List[str]:
        return [str(p_type) for p_type in getattr(pokemon, "types", []) if p_type]

    @staticmethod
    def format_move(move: SimplifiedMove) -> Dict:
        return {
            "id": move.id,
            "type": str(move.type),
            "category": getattr(move.category, "name", None),
            "base_power": move.base_power,
            "accuracy": move.accuracy,
            "current_pp": move.current_pp,
            "max_pp": move.max_pp,
            "priority": getattr(move, "priority", None),
            "status": str(getattr(move, "status", None)),
        }

    @staticmethod
    def format_pokemon(pokemon: SimplifiedPokemon, include_moves: bool = True) -> Dict:
        if pokemon is None:
            return {}
        formatted = {
            "species": pokemon.species,
            "types": BattleStateFormatter._format_types(pokemon),
            "level": pokemon.level,
            "current_hp": pokemon.current_hp,
            "max_hp": pokemon.max_hp,
            "status": str(pokemon.status),
            "boosts": pokemon.boosts,
            "item": pokemon.item,
            "ability": pokemon.ability,
            "active": pokemon.active,
            "must_recharge": getattr(pokemon, "must_recharge", False),
        }

        if include_moves:
            formatted["moves"] = [BattleStateFormatter.format_move(m) for m in pokemon.moves]

        return formatted

    @staticmethod
    def format_battle_state(battle: SimplifiedBattle) -> Dict:
        state = {
            "turn": battle.turn,
            "finished": battle.finished,
            "won": getattr(battle, "won", False),
            "lost": getattr(battle, "lost", False),
            "weather": battle.weather,
            "fields": battle.fields,
            "side_conditions": battle.side_conditions,
            "opponent_side_conditions": battle.opponent_side_conditions,
            "active_pokemon": BattleStateFormatter.format_pokemon(battle.active_pokemon),
            "opponent_active_pokemon": BattleStateFormatter.format_pokemon(battle.opponent_active_pokemon),
            "bench": [
                BattleStateFormatter.format_pokemon(p, include_moves=False)
                for name, p in battle.team.items()
                if not p.active and p.current_hp > 0
            ],
            "opponent_bench": [
                BattleStateFormatter.format_pokemon(p, include_moves=bool(p.moves))
                for name, p in battle.opponent_team.items()
                if not p.active and p.current_hp > 0
            ],
        }

        state["available_moves"] = [BattleStateFormatter.format_move(m) for m in battle.available_moves]
        state["available_switches"] = [
            BattleStateFormatter.format_pokemon(p, include_moves=False) for p in battle.available_switches
        ]
        return state

    @staticmethod
    def format_candidate_actions(actions: Iterable[Union[SimplifiedMove, SimplifiedPokemon]]) -> List[Dict]:
        formatted_actions = []
        for action in actions:
            if hasattr(action, "id"):
                formatted_actions.append(
                    {
                        "id": LLMPruner.action_identifier(action),
                        "type": "move",
                        "move": BattleStateFormatter.format_move(action),
                    }
                )
            else:
                formatted_actions.append(
                    {
                        "id": LLMPruner.action_identifier(action),
                        "type": "switch",
                        "pokemon": BattleStateFormatter.format_pokemon(action, include_moves=False),
                    }
                )
        return formatted_actions


class LLMPruner:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client: Optional[OpenAI] = None
        if os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI()

    @property
    def is_available(self) -> bool:
        return self.client is not None

    @staticmethod
    def action_identifier(action: Union[SimplifiedMove, SimplifiedPokemon]) -> str:
        if hasattr(action, "id"):
            return f"move:{action.id}"
        return f"switch:{action.species}"

    def prune_actions(
        self,
        battle: SimplifiedBattle,
        candidate_actions: Iterable[Union[SimplifiedMove, SimplifiedPokemon]],
    ) -> Set[str]:
        if not self.client:
            return set()

        battle_state = BattleStateFormatter.format_battle_state(battle)
        formatted_actions = BattleStateFormatter.format_candidate_actions(candidate_actions)

        user_content = {
            "battle_state": battle_state,
            "candidate_actions": formatted_actions,
            "instructions": "Return pruned_action_ids from candidate_actions."
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PRUNING_PROMPT},
                    {"role": "user", "content": json.dumps(user_content, ensure_ascii=False)},
                ],
                response_format={"type": "json_object"},
            )
        except Exception:
            return set()

        content = response.choices[0].message.content if response.choices else None

        # if content:
        #     print(f"[LLMPruner] OpenAI response: {content}")
        if not content:
            return set()

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return set()

        pruned_ids = parsed.get("pruned_action_ids", []) if isinstance(parsed, dict) else []
        return {pid for pid in pruned_ids if isinstance(pid, str)}