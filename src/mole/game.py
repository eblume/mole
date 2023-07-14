"""Play a game with AI"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import textwrap
import json

import typer
import openai


MAX_TOKENS = 2048  # gpt-4 max tokens is 4096
MAX_ROUNDS_REMEMBERED = 10
MODEL = "gpt-3.5-turbo"


@dataclass
class Game:
    player: Player
    recent_rounds: list[Round] = field(default_factory=list)

    def __post_init__(self):
        if not self.recent_rounds:
            # New Game
            self.recent_rounds.append(Round(
                action="META: New Game",
                challenge=Challenge(),
                result=Result(),
                situation="META: New Game. Storyteller, please make up a situation on your own.",
            ))

    def run(self) -> None:
        """Run forever"""
        action = "META: New Game"
        while True:
            challenge = self.gen_challenge(action)
            result = self.resolve_challenge(challenge)
            situation = self.gen_situation(action, challenge, result)
            self.recent_rounds.append(Round(action, challenge, result, situation))
            if len(self.recent_rounds) > MAX_ROUNDS_REMEMBERED:
                self.recent_rounds.pop(0)
            prompt = self.player_prompt()
            action = typer.prompt(prompt)

    def player_prompt(self) -> str:
        """Return a prompt for the player representing the game state, using LLMs.

        The prompt will include:
        * The challenge from the previous action
        * The result of that challenge
        * The current situation
        """
        last_round = self.recent_rounds[-1]

        return textwrap.dedent(f"""\
            Challenge:
            {last_round.challenge.text}

            Result:
            {last_round.result.text}

            Situation:
            {last_round.situation}

            What do you do?>\
        """)

    def gen_situation(self, player_action: str, challenge: Challenge, result: Result) -> str:
        prompt = textwrap.dedent(f"""\
            You're creating text for a text adventure game. Below you'll see the game state, player's action, challenge,
            and result. Please write a creative description of the result, leading to the next event. Follow 'show,
            don't tell' and iceberg storytelling. Aim for 1-3 paragraphs.
            ---
            {json.dumps(asdict(self))}
            ---
            {player_action}
            ---
            {challenge.text}
            ---
            {result.text}
        """)

        response = openai.Completion.create(
            model=MODEL,
            prompt=prompt,
            max_tokens=MAX_TOKENS - len(prompt),
            temperature=0.9,
        )
        return response["choices"][0]["text"]  # type: ignore

    def gen_challenge(self, player_action: str) -> Challenge:
        prompt = textwrap.dedent(f"""\
            You're creating a scripted gameplay challenge for a text adventure game. The challenge will be loaded in python dataclasses like so:

            @dataclass
            class ChallengeStruct:
                check: dict[str, int]
                success_cost: Optional[dict[str, int]]
                failure_cost: Optional[dict[str, int]]
                cost: Optional[dict[str, int]]

            @dataclass
            class Challenge:
                attributes: ChallengeStruct
                items: Optional[ChallengeStruct]

            response = openai.Completion.create(...)
            challenge = Challenge(**json.loads(response["choices"][0]["text"]))
            ---
            First, you'll see the game state, then the player's action.

            Please generate such a Challenge json document to represent the challenge for the player's action below. If
            the user says something like "I sit down", maybe a very easy dexterity check is made. If the user says "I
            experience apotheosis and become God", maybe an absurdly high 'divinity' check is made, with a religious
            consequence if it fails.
            ---
            {json.dumps(asdict(self))}
            ---
            {player_action}
        """)

        response = openai.Completion.create(
            model=MODEL,
            prompt=prompt,
            max_tokens=MAX_TOKENS - len(prompt),
            temperature=0.3,
        )
        data = json.loads(response["choices"][0]["text"].strip())  # type: ignore
        return Challenge(**data)  # no way in hell this works

    def resolve_challenge(self, challenge: Challenge) -> Result:
        success = self.check_item(challenge.items.check) and self.check_attribute(challenge.attributes.check)
        item_cost = _dict_add(challenge.items.cost, challenge.items.success_cost if success else challenge.items.failure_cost)
        attribute_cost = _dict_add(challenge.attributes.cost, challenge.attributes.success_cost if success else challenge.attributes.failure_cost)

        return Result(
            success=success,
            item_cost=item_cost,
            attribute_cost=attribute_cost,
        )

    def check_item(self, check: dict[str, int]) -> bool:
        """Check if the player has the items required for the challenge"""
        return all(self.player.items.get(item, 0) >= count for item, count in check.items())

    def check_attribute(self, check: dict[str, int]) -> bool:
        """Check if the player has the attributes required for the challenge"""
        return all(self.player.attributes.get(attribute, 0) >= count for attribute, count in check.items())


@dataclass
class Round:
    action: str
    challenge: Challenge
    result: Result
    situation: str


@dataclass
class ChallengeStruct:
    check: dict[str, int] = field(default_factory=dict)
    success_cost: dict[str, int] = field(default_factory=dict)
    failure_cost: dict[str, int] = field(default_factory=dict)
    cost: dict[str, int] = field(default_factory=dict)


@dataclass
class Challenge:
    attributes: ChallengeStruct = field(default_factory=ChallengeStruct)
    items: ChallengeStruct = field(default_factory=ChallengeStruct)

    @property
    def text(self) -> str:
        # TODO prettify
        return json.dumps(asdict(self))


@dataclass
class Result:
    success: bool = True
    attribute_cost: dict[str, int] = field(default_factory=dict)
    item_cost: dict[str, int] = field(default_factory=dict)

    @property
    def text(self) -> str:
        # TODO prettify
        return json.dumps(asdict(self))


@dataclass
class Player:
    # TODO remove defaults, this is just an example
    name: str = "Steve"
    attributes: dict[str, int] = field(default_factory=dict)
    items: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # TODO remove defaults, this is just an example
        if not self.attributes:
            self.attributes = {'strength': 10, 'dexterity': 10, 'intelligence': 10, 'charisma': 10, 'divinity': 10, 'sanity': 10, 'hp_current': 100, 'hp_max': 100}

        if not self.items:
            self.items = {'sword': 1, 'shield': 1, 'potion': 1, 'gold': 1}


def _dict_add(a: dict[str, int], b: dict[str, int]) -> dict[str, int]:
    """Add two dicts of ints, return the result"""
    result = {}
    for key, value in a.items():
        result[key] = value + b.get(key, 0)
    for key, value in b.items():
        if key not in result:
            result[key] = value
    return result
