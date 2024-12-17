
from nonebot import get_driver

from . import shared as Shared
from . import config
from . import command
from . import message

Shared.nonebot_config = get_driver().config
