
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Event
from nonebot.rule import Rule

from . import shared


async def forbidden_id(event: Event) -> bool:
    try:
        if int(event.get_user_id()) in shared.plugin_config.forbidden_users:
            return False
    except ValueError:
        pass
    if isinstance(event, GroupMessageEvent) and event.group_id in shared.plugin_config.forbidden_groups:
        return False
    return True


async def forbidden_word(event: Event) -> bool:
    for w in shared.plugin_config.forbidden_words:
        if str(w).lower() in event.get_message().extract_plain_text().lower():
            if shared.plugin_config.debug:
                shared.logger.info(f'检测到屏蔽词 {w}')
            return False
    return True


async def available_message(event: Event) -> bool:
    plaintext = event.get_plaintext()
    if not plaintext:
        if shared.plugin_config.debug:
            shared.logger.info(f'跳过空消息')
        return False
    for i in shared.nonebot_config.command_start:
        if i and plaintext.lstrip().startswith(i):
            return False
    return True


rule_forbidden_id = Rule(forbidden_id)
rule_forbidden_word = Rule(forbidden_word)
rule_available_message = Rule(available_message)
