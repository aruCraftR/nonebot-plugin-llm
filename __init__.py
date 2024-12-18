
from nonebot import get_driver


from . import shared
from . import config
from . import command
from . import message
from .chat import get_chat_instances

driver = get_driver()
shared.nonebot_config = driver.config


@driver.on_shutdown
async def on_shutdown():
    shared.logger.info("正在保存数据，完成前请勿强制结束！")
    for i in get_chat_instances():
        i.history.save_pickle()
    shared.logger.info("保存完成！")
