from entities.entity import Entity
from events import Event
from filters.players import PlayerIter
from listeners import OnClientActive, OnClientDisconnect, OnLevelEnd
from listeners.tick import Delay
from messages import SayText2
from players.entity import Player
from players.helpers import index_from_userid

from mathlib import NULL_VECTOR

from .cvars import config_manager
from .internal_events import InternalEvent
from .strings import COLOR_SCHEME, strings


class DMPlayer:
    def __init__(self, player):
        self.player = player

        self._protected = False
        self._protection_delay = None
        self._respawn_delay = None

        self.show_menu_on_spawn = True

        self.last_primary = None
        self.last_pistol = None

    def cancel_respawn_delay(self):
        if self._respawn_delay is None:
            return

        if self._respawn_delay.running:
            self._respawn_delay.cancel()

        self._respawn_delay = None

    def cancel_protection_delay(self):
        if self._protection_delay is None:
            return

        if self._protection_delay.running:
            self._protection_delay.cancel()

        self._protection_delay = None

    def delayed_respawn(self):
        self._respawn_delay = Delay(
            config_manager['respawn_delay'], self.player.respawn)

    def protect(self):
        if config_manager['protection_timeout'] == 0:
            return

        self._protected = True
        self._protection_delay = Delay(
            config_manager['protection_timeout'], self.unprotect)

    @property
    def protected(self):
        return self._protected

    def unprotect(self):
        self._protected = False

    def strip(self):
        for index in self.player.weapon_indexes():
            weapon = Entity(index)
            self.player.drop_weapon(weapon.pointer, NULL_VECTOR, NULL_VECTOR)
            weapon.remove()

    def give(self, weapon_classname):
        self.player.give_named_item(weapon_classname, 0)

    def equip_latest(self):
        self.give('weapon_knife')

        if self.last_primary is not None:
            self.give(self.last_primary)

        if self.last_pistol is not None:
            self.give(self.last_pistol)


class DMPlayerManager(dict):
    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        InternalEvent.fire('player_registered', dm_player=value)

    def __delitem__(self, key):
        InternalEvent.fire('player_unregistered', dm_player=self[key])
        dict.__delitem__(self, key)

    def get_by_userid(self, userid):
        return self[index_from_userid(userid)]

player_manager = DMPlayerManager()
_initial_spawns = []


@OnClientActive
def listener_on_client_active(index):
    player_manager[index] = DMPlayer(Player(index))


@OnClientDisconnect
def listener_on_client_disconnect(index):
    player_manager.pop(index, None)


@OnLevelEnd
def listener_on_level_shutdown():
    for index in tuple(player_manager.keys()):
        del player_manager[index]


@InternalEvent('load')
def on_load():
    for player in PlayerIter():
        player_manager[player.index] = DMPlayer(player)


@InternalEvent('unload')
def on_unload():
    for index in tuple(player_manager.keys()):
        del player_manager[index]


@Event('player_spawn')
def on_player_spawn(game_event):
    dm_player = player_manager.get_by_userid(game_event['userid'])
    if dm_player.player.index not in _initial_spawns:
        _initial_spawns.append(dm_player.player.index)
        return

    InternalEvent.fire(
        'player_respawn',
        dm_player=dm_player,
    )


def tell(players, message, **tokens):
    if isinstance(players, DMPlayer):
        players = (players, )

    player_indexes = [dm_player.player.index for dm_player in players]

    tokens.update(COLOR_SCHEME)

    message = message.tokenize(**tokens)
    message = strings['chat_base'].tokenize(message=message, **COLOR_SCHEME)

    SayText2(message=message).send(*player_indexes)


def broadcast(message, **tokens):
    tell(player_manager.values(), message, **tokens)
