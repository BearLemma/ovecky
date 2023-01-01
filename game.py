from __future__ import annotations
import random
import typing
import time

from typing import List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

class Season(Enum):
    Spring = 1
    Summer = 2
    Autumn = 3
    Winter = 4

class Card(Enum):
    Needle = 1
    Hay = 2
    Yeet = 3
    No = 4
    Skrrt = 5
    Swap = 6

HAY_COUNT = 45
YEET_COUNT = 5
NO_COUNT = 8
SKRRT_COUNT = 2
SWAP_COUNT = 5

def make_card_stack():
    cards = [Card.Needle]
    cards.extend([Card.Hay   for _ in range(HAY_COUNT)])
    cards.extend([Card.Yeet  for _ in range(YEET_COUNT)])
    cards.extend([Card.No    for _ in range(NO_COUNT)])
    cards.extend([Card.Skrrt for _ in range(SKRRT_COUNT)])
    cards.extend([Card.Swap  for _ in range(SWAP_COUNT)])
    random.shuffle(cards)
    return cards

def make_residual_deck(players: List[Player]) -> List[Card]:
    needle = True
    hay = HAY_COUNT
    yeet = YEET_COUNT
    no = NO_COUNT
    skrrt = SKRRT_COUNT
    swap = SWAP_COUNT

    for player in players:
        hand = player.hand
        if hand.needle:
            needle = False
        hay -= hand.hay
        yeet -= hand.yeet
        no -= hand.no
        skrrt -= hand.skrrt
        swap -= hand.swap

    cards: List[Card] = []
    if needle:
        cards.append(Card.Needle)
    cards.extend([Card.Hay   for _ in range(hay)])
    cards.extend([Card.Yeet  for _ in range(yeet)])
    cards.extend([Card.No    for _ in range(no)])
    cards.extend([Card.Skrrt for _ in range(skrrt)])
    cards.extend([Card.Swap  for _ in range(swap)])
    random.shuffle(cards)
    return cards

class ActionKind(Enum):
    Pass = 1
    BuySheep = 2
    PlayYeet = 3
    PlaySkrrt = 4
    PlaySwap = 5
    PlayNo = 6
    DropCard = 7
    PlayAutumnSwap = 8

@dataclass
class Action:
    kind: ActionKind

    @staticmethod
    def argless_action(kind: ActionKind) -> Action:
        if kind == ActionKind.Pass:
            return PassAction()
        elif kind == ActionKind.BuySheep:
            return BuySheepAction()
        elif kind == ActionKind.PlayNo:
            return PlayNoAction()
        else:
            assert False

    def is_targeted_action(self) -> bool:
        return self.kind in [ActionKind.PlayYeet, ActionKind.PlaySkrrt, ActionKind.PlaySwap]

class PassAction(Action):
    def __init__(self):
        super().__init__(ActionKind.Pass)

class BuySheepAction(Action):
    def __init__(self):
        super().__init__(ActionKind.BuySheep)

class TargetedAction(Action):
    def __init__(self, kind: ActionKind, target: Player):
        super().__init__(kind)
        self.target = target

    @staticmethod
    def make(kind: ActionKind, target: Player) -> TargetedAction:
        if kind == ActionKind.PlayYeet:
            return YeetAction(target)
        elif kind == ActionKind.PlaySkrrt:
            return SkrrtAction(target)
        elif kind == ActionKind.PlaySwap:
            return SwapAction(target)
        else:
            assert False

class YeetAction(TargetedAction):
    def __init__(self, target: Player):
        super().__init__(ActionKind.PlayYeet, target)

class SkrrtAction(TargetedAction):
    def __init__(self, target: Player):
        super().__init__(ActionKind.PlaySkrrt, target)

class SwapAction(TargetedAction):
    def __init__(self, target: Player):
        super().__init__(ActionKind.PlaySwap, target)

class AutumnSwapAction(TargetedAction):
    def __init__(self, target: Player):
        super().__init__(ActionKind.PlayAutumnSwap, target)

class PlayNoAction(Action):
    def __init__(self):
        super().__init__(ActionKind.PlayNo)

class DropCardAction(Action):
    def __init__(self, card: Card):
        super().__init__(ActionKind.DropCard)
        self.card = card

@dataclass
class Hand:
    needle: bool = False
    hay: int = 0
    yeet: int = 0
    no: int = 0
    skrrt: int = 0
    swap: int = 0

    def take_card(self, card: Card):
        if card == Card.Needle:
            self.needle = True
        elif card == Card.Hay:
            self.hay += 1
        elif card == Card.Yeet:
            self.yeet += 1
        elif card == Card.No:
            self.no += 1
        elif card == Card.Skrrt:
            self.skrrt += 1
        elif card == Card.Swap:
            self.swap += 1
        else:
            assert False

    def drop_cards(self, card: Card, count=1):
        if card == Card.Needle:
            assert self.needle
            self.needle = False
        elif card == Card.Hay:
            assert self.hay >= count
            self.hay -= count
        elif card == Card.Yeet:
            assert self.yeet >= count
            self.yeet -= count
        elif card == Card.No:
            assert self.no >= count
            self.no -= count
        elif card == Card.Skrrt:
            assert self.skrrt >= count
            self.skrrt -= count
        elif card == Card.Swap:
            assert self.swap >= count
            self.swap -= count
        else:
            assert False

    def drop_random(self) -> Optional[Card]:
        cards = []
        if self.needle:
            cards.append(Card.Needle)
        cards.extend(Card.Hay for _ in range(self.hay))
        cards.extend(Card.Yeet for _ in range(self.yeet))
        cards.extend(Card.No for _ in range(self.no))
        cards.extend(Card.Skrrt for _ in range(self.skrrt))
        cards.extend(Card.Swap for _ in range(self.swap))
        if not cards:
            return None
        return random.choice(cards)

    def drop_all_cards(self):
        self.needle = False
        self.hay = 0
        self.yeet = 0
        self.no = 0
        self.skrrt = 0
        self.swap = 0

    def count(self) -> int:
        return (1 if self.needle else 0) + self.hay + self.yeet + self.no + self.skrrt + self.swap

    def available_actions(self, season: Season) -> List[ActionKind]:
        actions = [ActionKind.Pass]
        if self.hay >= 4:
            actions.append(ActionKind.BuySheep)
        if self.yeet > 0:
            actions.append(ActionKind.PlayYeet)
        if self.skrrt > 0 and season != Season.Spring:
            actions.append(ActionKind.PlaySkrrt)
        if self.swap > 0:
            actions.append(ActionKind.PlaySwap)
        return actions

class Strategy(ABC):

    @abstractmethod
    def best_action(self, player: Player, season: Season, other_players: List[Player]) -> Action:
        pass

    @abstractmethod
    def chose_buy_sheep_reaction(self, player: Player) -> Action:
        pass

    @abstractmethod
    def chose_yeet_reaction(self, player: Player, aggressor: Player) -> Action:
        pass

    @abstractmethod
    def maybe_autumn_card_swap(self, player: Player, state: GameState) -> Optional[AutumnSwapAction]:
        pass

    @abstractmethod
    def play_no(self, player: Player, action: TargetedAction, current_result: bool) -> bool:
        pass

    @abstractmethod
    def select_card_to_drop(self, player: Player, other_players: List[Player]) -> Card:
        pass

class BasicStrategy(Strategy):

    def best_action(self, player: Player, season: Season, other_players: List[Player]) -> Action:
        actions = player.hand.available_actions(season)
        if ActionKind.BuySheep in actions:
            return BuySheepAction()
        action = random.choice(actions)
        if action in (ActionKind.PlayYeet, ActionKind.PlaySkrrt, ActionKind.PlaySwap):
            target = random.choice(other_players)
            return TargetedAction.make(action, target)
        return Action.argless_action(action)

    # This will only get called during Spring when other player is buying sheep
    def chose_buy_sheep_reaction(self, player: Player) -> Action:
        if player.hand.skrrt > 0:
            return SkrrtAction(player)
        else:
            return PassAction()

    def chose_yeet_reaction(self, player: Player, aggressor: Player) -> Action:
        if player.hand.yeet > 0:
            return YeetAction(aggressor)
        else:
            return PassAction()

    def maybe_autumn_card_swap(self, player: Player, state: GameState) -> Optional[AutumnSwapAction]:
        if player.hand.needle or player.sheep < 4:
            return None
        other_players = state.other_players(player.idx)
        target = max(other_players, key=lambda p: p.sheep)
        return AutumnSwapAction(target)

    def play_no(self, player: Player, action: TargetedAction, current_result: bool) -> bool:
        if player.hand.no > 0:
            if player.idx == action.target.idx and current_result == True:
                return True
            else:
                return False
        else:
            return False

    def select_card_to_drop(self, player: Player, other_players: List[Player]) -> Card:
        if player.sheep >= 4 and player.hand.hay > 0:
            return Card.Hay
        elif player.hand.swap > 0:
            return Card.Swap
        elif player.hand.yeet > 0:
            return Card.Yeet
        elif player.hand.skrrt > 0:
            return Card.Skrrt
        elif player.hand.hay > 0:
            return Card.Hay
        elif player.hand.no > 0:
            return Card.No
        assert False

@dataclass
class Player:
    idx: int
    name: str
    strategy: Strategy
    hand: Hand = field(default_factory=Hand)
    sheep: int = 0

    def play_best_action(self,  season: Season, other_players: List[Player]) -> Action:
        action = self.strategy.best_action(self, season, other_players)
        self.drop_card_on_action(action)
        return action

    def react_to_yeet(self, aggressor: Player) -> Action:
        action = self.strategy.chose_yeet_reaction(self, aggressor)
        self.drop_card_on_action(action)
        return action

    def react_to_buy_sheep(self) -> Action:
        action = self.strategy.chose_buy_sheep_reaction(self)
        self.drop_card_on_action(action)
        return action

    def maybe_play_no(self, action: TargetedAction, current_result: bool) -> bool:
        play_no = self.strategy.play_no(self, action, current_result)
        if play_no:
            self.drop_card_on_action(PlayNoAction())
        return play_no

    def maybe_play_autumn_card_swap(self, state: GameState) -> Optional[AutumnSwapAction]:
        if self.hand.count() < 2:
            return None

        action = self.strategy.maybe_autumn_card_swap(self, state)
        if action is not None:
            self.drop_card(state)
            self.drop_card(state)
        return action

    def drop_card(self, state: GameState):
        other_players = state.other_players(self.idx)
        card = self.strategy.select_card_to_drop(self, other_players)
        self.hand.drop_cards(card)
        if card == Card.Needle:
            state.return_needle()

    def drop_card_on_action(self, action: Action):
        if action.kind == ActionKind.PlayYeet:
            self.hand.drop_cards(Card.Yeet)
        elif action.kind == ActionKind.PlaySkrrt:
            self.hand.drop_cards(Card.Skrrt)
        elif action.kind == ActionKind.PlaySwap:
            self.hand.drop_cards(Card.Swap)
        elif action.kind == ActionKind.PlayNo:
            self.hand.drop_cards(Card.No)
        elif action.kind == ActionKind.BuySheep:
            self.hand.drop_cards(Card.Hay, 4)

    def buy_sheep(self):
        self.sheep += 1

    def suffer_yeet(self, state: GameState):
        if self.hand.needle:
            state.return_needle()
        self.hand.drop_all_cards()

    def suffert_partial_yeet(self, state: GameState):
        for _ in range(self.hand.count() // 2):
            self.drop_card(state)

    def suffer_skrrt(self):
        self.sheep = max(self.sheep - 1, 0)

@dataclass
class GameState:
    players: List[Player]
    cards: List[Card]
    season: Season

    def other_players(self, player_idx: int) -> List[Player]:
        return self.players[player_idx + 1:] + self.players[:player_idx]

    def return_needle(self):
        self.cards.insert(random.randint(0, len(self.cards)), Card.Needle)

def do_season(state: GameState):
    while len(state.cards) != 0:
        for player in state.players:
            if len(state.cards) == 0:
                break

            other_players = state.other_players(player.idx)
            while True:
                action = player.play_best_action(state.season, other_players)
                if action.kind == ActionKind.Pass:
                    break
                print(f"{player.name} played {action}. Resulting hand: {player.hand}")

                if action.kind == ActionKind.BuySheep:
                    player.buy_sheep()
                    if state.season == Season.Spring:
                        handle_sheep_buying_reactions(state, player)
                elif action.is_targeted_action():
                    assert isinstance(action, TargetedAction)
                    handle_targeted_actions(state, player, action)
                else:
                    assert False

            if state.season == Season.Autumn:
                card_swap = player.maybe_play_autumn_card_swap(state)
                if card_swap is None:
                    player.hand.take_card(state.cards.pop())
                else:
                    card = card_swap.target.hand.drop_random()
                    if card is not None:
                        player.hand.take_card(card)
            else:
                player.hand.take_card(state.cards.pop())

            if player.hand.count() > 6:
                player.drop_card(state)

def handle_sheep_buying_reactions(state: GameState, buyer: Player):
    other_players = state.other_players(buyer.idx)
    action_played = True
    while action_played:
        action_played = False
        for other in other_players:
            action = other.react_to_buy_sheep()
            if action.kind == ActionKind.PlaySkrrt:
                action_played = True

                assert isinstance(action, TargetedAction)
                if handle_no_contest(state, action):
                    other.buy_sheep()

def handle_targeted_actions(state: GameState, aggressor: Player, action: TargetedAction):
    if action.kind == ActionKind.PlayYeet:
        handle_yeet_action(state, aggressor, action.target)
    elif action.kind == ActionKind.PlaySkrrt:
        handle_skrrt_action(state, action.target)
    elif action.kind == ActionKind.PlaySwap:
        handle_swap_action(state, aggressor, action.target)
    else:
        assert False

def handle_yeet_action(state: GameState, aggressor: Player, target: Player) -> bool:
    yeet_passed = handle_no_contest(state, YeetAction(target))
    if not yeet_passed:
        return False

    reaction = target.react_to_yeet(aggressor)
    if reaction.kind == ActionKind.PlayYeet:
        if handle_yeet_action(state, target, aggressor):
            # Counter-yeet was successful, we don't have to burn ourselves
            return True

    target.suffer_yeet(state)
    if state.season == Season.Summer:
        target_neighbors = state.other_players(target.idx)

        right_neighbour = target_neighbors[0]
        if right_neighbour.idx != aggressor.idx:
            right_neighbour.suffert_partial_yeet(state)

        left_neighbour = target_neighbors[-1]
        if left_neighbour.idx != aggressor.idx:
            left_neighbour.suffert_partial_yeet(state)

    return True

def handle_skrrt_action(state: GameState, target: Player):
    assert state.season != Season.Spring
    skrrt_passed = handle_no_contest(state, SkrrtAction(target))
    if not skrrt_passed:
        return
    target.suffer_skrrt()

def handle_swap_action(state: GameState, aggressor: Player, target: Player):
    swap_passed = handle_no_contest(state, SwapAction(target))
    if not swap_passed:
        return
    aggressor.hand, target.hand = target.hand, aggressor.hand

# Returns true, if the actions wasn't denied, false if denied
def handle_no_contest(state: GameState, action: TargetedAction) -> bool:
    result = True
    action_played = True
    while action_played:
        action_played = False
        for player in state.players:
            played_no = player.maybe_play_no(action, result)
            if played_no:
                result = not result
                action_played = True
    return result


names = ["Jan", "Megie", "Katka", "Tobik"]
def run(players_n: int):
    cards = make_card_stack()
    players = []
    for player_idx in range(players_n):
        player = Player(idx = player_idx, name=names[player_idx], strategy=BasicStrategy())
        for _ in range(4):
            player.hand.take_card(cards.pop())
        players.append(player)

    state = GameState(players=players, cards=cards, season=Season.Spring)

    for season in (Season.Spring, Season.Summer, Season.Autumn):
        print(f"------------ {season} ------------")
        state.season = season
        do_season(state)

        # Check winning conditions
        for player in state.players:
            if player.hand.needle and player.sheep >= 4:
                print(f"Player {player.name} (idx={player.idx}) is the Winner!")
                break
        else:
            state.cards = make_residual_deck(state.players)
            continue
        break
    else:
        pass
        print("💀💀💀 Everybody died  💀💀💀")

    print(f"Final standings {state.players}")


t = time.time()
for i in range(100000):
    run(4)
    break
    if (i + 1) % 1000 == 0:
        print(f"Current speed {i / (time.time() - t)} games/s")
