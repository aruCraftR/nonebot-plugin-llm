
from time import time
from nonebot.plugin import on_message, on_notice
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import MessageEvent, Bot, GroupIncreaseNoticeEvent

from .chat import get_chat_instance
from .interface import request_chat_completion
from .utils import uniform_chat_text, get_user_name
from .rule import rule_forbidden_id, rule_forbidden_word, rule_available_message

from . import shared

message = on_message(
    rule=rule_forbidden_id & rule_forbidden_word & rule_available_message,
    priority=shared.plugin_config.event_priority,
    block=shared.plugin_config.block_event
)

notice = on_notice(
    rule=rule_forbidden_id & rule_forbidden_word,
    priority=20,
    block=False
)


@message.handle()
async def message_handler(event: MessageEvent, bot: Bot):
    chat_instance = await get_chat_instance(message, event, bot)
    if not chat_instance.enabled:
        return

    sender_name = await chat_instance.get_user_name(event, bot)
    chat_text, wake_up = await uniform_chat_text(event=event, bot=bot)

    if not ((
            chat_instance.config.reply_on_name_mention
            and
            chat_instance.config.bot_name in chat_text.lower()
        ) or (
            chat_instance.config.reply_on_at
            and
            (wake_up or event.is_tome())
        )):
        if chat_instance.is_group and chat_instance.config.record_other_context:
            chat_instance.record_other_history(chat_text, sender_name)
        if shared.plugin_config.debug:
            shared.logger.info(f'{sender_name} 的消息 {chat_text} 不满足生成条件, 已跳过')
            shared.logger.info(
                f'reply_on_name_mention: {shared.plugin_config.reply_on_name_mention}\n'
                f'reply_on_at: {shared.plugin_config.reply_on_at}\n'
                f'mention: {shared.plugin_config.bot_name in chat_text.lower()}\n'
                f'wake_up or at: {wake_up or event.is_tome()}'
            )
        return

    chat_instance.record_chat_history(chat_text, sender_name)

    msg_time = time()
    if msg_time - chat_instance.last_msg_time < chat_instance.config.reply_throttle_time:
        return
    chat_instance.last_msg_time = msg_time

    if shared.plugin_config.debug:
        shared.logger.info(f'正在准备为 {sender_name} 生成消息')

    response, success = request_chat_completion(chat_instance)
    if success:
        chat_instance.record_chat_history(response)
    await message.finish(response)


@notice.handle()
async def _(matcher: Matcher, event: GroupIncreaseNoticeEvent, bot: Bot):
    if not shared.plugin_config.reply_on_welcome:
        return
    if isinstance(event, GroupIncreaseNoticeEvent): # 群成员增加通知
        chat_key = 'group_' + event.get_session_id().split("_")[1]
        chat_type = 'group'
    else:
        return

    user_name = await get_user_name(event=event, bot=bot, user_id=int(event.get_user_id())) or f'qq:{event.get_user_id()}'
