from entities import TakeDamageInfo
from entities.helpers import index_from_pointer
from entities.hooks import EntityCondition, EntityPreHook
from events import Event
from listeners import OnClientDisconnect
from memory import make_object
from players.entity import Player
from players.helpers import index_from_userid

from spam_proof_commands.say import SayCommand

from .cvars import config_manager
from .dm_player import broadcast, player_manager, tell
from .internal_events import InternalEvent
from .popups import popups
from .strings import strings


ANTI_SPAM_DELAY = 2

# Let everybody die after hot plug so we start with a fresh round
_round_end = True


def load():
    InternalEvent.fire('load')
    broadcast(strings['load'])


def unload():
    InternalEvent.fire('unload')
    broadcast(strings['unload'])


@Event('round_start')
def on_round_start(game_event):
    global _round_end
    _round_end = False


@Event('round_end')
def on_round_end(game_event):
    global _round_end
    _round_end = True

    for dm_player in player_manager.values():
        dm_player.cancel_respawn_delay()


@Event('player_death')
def on_player_death(game_event):
    dm_player = player_manager.get_by_userid(game_event['userid'])
    attacker_uid = game_event['attacker']

    try:
        attacker = Player(index_from_userid(attacker_uid))
        if attacker.team != dm_player.player.team and not attacker.dead:
            attacker.health += config_manager['health_bonus_on_kill']

    except (ValueError, OverflowError):
        pass

    dm_player.cancel_protection_delay()

    if _round_end:
        return

    dm_player.delayed_respawn()


@InternalEvent('player_respawn')
def on_player_spawn(event_var):
    dm_player = event_var['dm_player']

    # Cancel respawn delay - sometimes the game respawns player before we do
    dm_player.cancel_respawn_delay()

    # Spawn protection
    dm_player.protect()

    # Strip off stock weapons
    dm_player.strip()

    # Equip new weapons
    if dm_player.show_menu_on_spawn:
        popups['primary'].send(dm_player.player.index)
    else:
        dm_player.equip_latest()


@OnClientDisconnect
def listener_client_disconnect(index):
    dm_player = player_manager[index]
    dm_player.cancel_protection_delay()
    dm_player.cancel_respawn_delay()


@EntityPreHook(EntityCondition.is_player, 'on_take_damage')
def on_take_damage(args):
    dm_player_victim = player_manager[index_from_pointer(args[0])]

    if dm_player_victim.protected:
        return True

    info = make_object(TakeDamageInfo, args[1])
    try:
        dm_player_attacker = player_manager[info.attacker]
    except KeyError:
        return

    if dm_player_attacker.protected:
        dm_player_attacker.cancel_protection_delay()
        dm_player_attacker.unprotect()
        return True


@SayCommand(ANTI_SPAM_DELAY, ['guns', '!guns'])
def say_guns(command, index, team_only):
    dm_player = player_manager[index]

    if dm_player.show_menu_on_spawn:
        tell(dm_player, strings['guns_menu disabled'])

    else:
        tell(dm_player, strings['guns_menu enabled'])

    dm_player.show_menu_on_spawn = not dm_player.show_menu_on_spawn
