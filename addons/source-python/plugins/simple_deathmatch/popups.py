from menus import PagedMenu, PagedOption
from players.teams import teams_by_name
from weapons.manager import weapon_manager

from .dm_player import player_manager
from .strings import strings


def get_guns_denial_reason(dm_player):
    player = dm_player.player
    if player.dead:
        return "DEAD"

    if player.team not in (teams_by_name['t'], teams_by_name['ct']):
        return "WRONG_TEAM"

    return None


def popup_primary_select_callback(popup, player_index, option):
    dm_player = player_manager[player_index]

    if get_guns_denial_reason(dm_player) is not None:
        return

    dm_player.last_primary = option.value

    popups['pistol'].send(dm_player.player.index)


def popup_pistol_select_callback(popup, player_index, option):
    dm_player = player_manager[player_index]

    if get_guns_denial_reason(dm_player) is not None:
        return

    dm_player.last_pistol = option.value

    dm_player.equip_latest()


popups = {}

popups['primary'] = PagedMenu(
    select_callback=popup_primary_select_callback,
    title=strings['popup_primary title']
)

popups['pistol'] = PagedMenu(
    select_callback=popup_pistol_select_callback,
    title=strings['popup_pistol title']
)


for weapon_instance in weapon_manager.values():
    for tag, popup in popups.items():
        if tag not in weapon_instance.tags:
            continue

        popup.append(PagedOption(
            text=weapon_instance.basename,
            value=weapon_instance.name,
        ))
        break
