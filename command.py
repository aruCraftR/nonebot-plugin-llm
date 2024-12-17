
from nonebot import on_command
from nonebot.params import Command
from nonebot.permission import SUPERUSER

from . import shared

cmd_reload = on_command(
    ('llm', 'reload'),
    permission=SUPERUSER
)

@cmd_reload.handle()
async def reload_config():
    try:
        shared.plugin_config.load_yaml()
    except Exception as e:
        await cmd_reload.finish(f'LLM插件配置重载失败: {repr(e)}')
    else:
        await cmd_reload.finish(f'LLM插件配置重载成功')
