
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.permission import SUPERUSER

from .utils import get_chat_type
from . import history
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


cmd_clear_history = on_command(
    ('llm', 'new')
)

@cmd_clear_history.handle()
async def clear_history(event: MessageEvent):
    chat_key, is_group = get_chat_type(event)
    if not (is_group or shared.plugin_config.reply_on_private):
        return
    history.clear_history(chat_key)
    await cmd_reload.finish(f'已清除当前会话的历史记录')


cmd_reset_history = on_command(
    ('llm', 'reset', 'history'),
    permission=SUPERUSER
)

@cmd_reset_history.handle()
async def reset_all_history():
    await cmd_reload.finish(f'已重置 {history.reset_all_history()} 个会话的历史记录')
