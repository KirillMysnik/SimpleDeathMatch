from cvars.public import PublicConVar
from plugins.info import PluginInfo


info = PluginInfo()
info.name = "Simple DeathMatch"
info.basename = 'simple_deathmatch'
info.author = 'Kirill "iPlayer" Mysnik'
info.version = '0.1'
info.variable = 'sdm_version'
info.convar = PublicConVar(
    info.variable, info.version, "{} version".format(info.name))
