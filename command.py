
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Bot, Message
from nonebot.permission import SUPERUSER
from nonebot.params import CommandArg

from .config import DEFAULT
from .chat import get_chat_instance, get_chat_instances
from . import shared

cmd_reload = on_command(
    ('llm', 'reload'),
    permission=SUPERUSER
)

@cmd_reload.handle()
async def reload_config():
    try:
        shared.plugin_config.load_yaml()
        for i in get_chat_instances():
            i.config.load_yaml()
    except Exception as e:
        await cmd_reload.finish(f'LLM插件配置重载失败: {repr(e)}')
    else:
        await cmd_reload.finish(f'LLM插件配置重载成功')


cmd_clear_history = on_command(
    ('llm', 'new')
)

@cmd_clear_history.handle()
async def clear_history(event: MessageEvent, bot: Bot):
    chat_instance = await get_chat_instance(cmd_clear_history, event, bot)
    chat_instance.clear_history()
    await cmd_clear_history.finish(f'已清除当前会话的历史记录')


cmd_reset_history = on_command(
    ('llm', 'reset', 'history'),
    permission=SUPERUSER
)

@cmd_reset_history.handle()
async def reset_all_history():
    count = 0
    for i in get_chat_instances():
        count += 1
        i.clear_history()
    await cmd_reset_history.finish(f'已清除 {count} 个会话的历史记录')


cmd_change_bot = on_command(
    ('llm', 'change', 'bot'),
    permission=SUPERUSER
)

@cmd_change_bot.handle()
async def change_bot_name(event: MessageEvent, bot: Bot, args: Message = CommandArg()):
    chat_instance = await get_chat_instance(cmd_change_bot, event, bot)
    bot_name = args.extract_plain_text()
    if bot_name not in shared.plugin_config.system_prompts:
        await cmd_change_bot.finish(f'系统提示词预设 {bot_name} 不存在\n当前可用预设: {', '.join(shared.plugin_config.system_prompts.keys())}')
    chat_instance.config.set_value('bot_name', args.extract_plain_text())
    chat_instance.config.save_yaml()
    await cmd_change_bot.finish(f'已切换到系统提示词预设 {bot_name}\n提示词内容: {chat_instance.config.system_prompt}')


cmd_discard_bot = on_command(
    ('llm', 'discard', 'bot'),
    permission=SUPERUSER
)

@cmd_discard_bot.handle()
async def discard_bot_name(event: MessageEvent, bot: Bot):
    chat_instance = await get_chat_instance(cmd_change_bot, event, bot)
    chat_instance.config.set_value('bot_name', DEFAULT)
    await cmd_discard_bot.finish(f'已切换到默认系统提示词预设 {chat_instance.config.bot_name}\n提示词内容: {chat_instance.config.system_prompt}')


cmd_info_history = on_command(
    ('llm', 'info', 'history'),
    permission=SUPERUSER
)

@cmd_info_history.handle()
async def info_history(event: MessageEvent, bot: Bot):
    chat_instance = await get_chat_instance(cmd_change_bot, event, bot)
    await cmd_info_history.finish(
        f'对话条数: {len(chat_instance.history.chat_history)}\n'
        f'对话Token数: {chat_instance.history.chat_history_token_count} / {chat_instance.config.record_chat_context_token_limit}\n'
        f'上下文条数: {len(chat_instance.history.other_history)}\n'
        f'上下文Token数: {chat_instance.history.other_history_token_count} / {chat_instance.config.record_other_context_token_limit}'
    )
