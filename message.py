
from time import time
from nonebot.plugin import on_message, on_notice
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import MessageEvent, Bot, GroupMessageEvent, PrivateMessageEvent, GroupIncreaseNoticeEvent

from .interface import get_chat_response
from .history import record_chat_history, record_other_history
from .utils import get_chat_type, uniform_chat_text, get_user_name
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

last_msg_time = 0


@message.handle()
async def message_handler(matcher: Matcher, event: MessageEvent, bot: Bot):
    global last_msg_time
    sender_name = await get_user_name(event=event, bot=bot, user_id=event.user_id) or '未知'
    chat_key, is_group = get_chat_type(event)
    if not (is_group or shared.plugin_config.reply_on_private):
        return

    chat_text, wake_up = await uniform_chat_text(event=event, bot=bot)

    if not ((
            shared.plugin_config.reply_on_name_mention
            and
            shared.plugin_config.bot_name in chat_text.lower()
        ) or (
            shared.plugin_config.reply_on_at
            and
            (wake_up or event.is_tome())
        )):
        if is_group:
            record_other_history(chat_key, chat_text, sender_name)
        if shared.plugin_config.debug:
            shared.logger.info(f'{sender_name} 的消息 {chat_text} 不满足生成条件, 已跳过')
            shared.logger.info(
                f'reply_on_name_mention: {shared.plugin_config.reply_on_name_mention}\n'
                f'reply_on_at: {shared.plugin_config.reply_on_at}\n'
                f'mention: {shared.plugin_config.bot_name in chat_text.lower()}\n'
                f'wake_up or at: {wake_up or event.is_tome()}'
            )
        return

    if shared.plugin_config.debug:
        shared.logger.info(f'正在准备为 {sender_name} 生成消息')

    history = record_chat_history(chat_key, chat_text, sender_name)

    msg_time = time()
    if msg_time - last_msg_time < shared.plugin_config.reply_throttle_time:
        return
    last_msg_time = msg_time

    response, success = get_chat_response(history.get_chat_messages(shared.plugin_config.system_prompt))
    if success:
        record_chat_history(chat_key, response)
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
