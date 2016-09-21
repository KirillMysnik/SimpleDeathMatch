from controlled_cvars import ControlledConfigManager
from controlled_cvars.handlers import int_handler, InvalidValue

from .info import info


def uint_handler(cvar):
    val = int_handler(cvar)
    if val < 0:
        raise InvalidValue

    return val


with ControlledConfigManager(
        info.basename, cvar_prefix="sdm_") as config_manager:

    config_manager.controlled_cvar(
        uint_handler,
        "respawn_delay",
        default=1,
        description="Respawn delay"
    )
    config_manager.controlled_cvar(
        uint_handler,
        "health_bonus_on_kill",
        default=15,
        description="Health bonus on kill"
    )
    config_manager.controlled_cvar(
        uint_handler,
        "protection_timeout",
        default=1,
        description="Protection timeout"
    )
