
from collections import deque
from typing import Optional
from time import asctime, time, localtime

from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import MessageEvent, PrivateMessageEvent, GroupMessageEvent, Bot

from .utils import get_chat_type, get_user_name
from .config import InstanceConfig
from . import shared


#-----------------------------
#
#           聊天实例
#
#-----------------------------

chat_instances: dict[str, 'ChatInstance'] = {}

class ChatInstance:
    def __init__(self, chat_key: str, is_group: bool) -> None:
        self.name = None
        self.is_group = is_group
        self.last_msg_time: int | float = 0
        self.chat_key = chat_key
        self.config = InstanceConfig(chat_key)
        self.history = ChatHistory(self)
        chat_instances[self.chat_key] = self

    @classmethod
    async def async_init(cls, bot: Bot, event: MessageEvent, chat_key: str, is_group: bool):
        self = cls(chat_key, is_group)
        if isinstance(event, GroupMessageEvent):
            self.name = (await bot.get_group_info(group_id=event.group_id))['group_name']
        elif isinstance(event, PrivateMessageEvent):
            self.name = await self.get_user_name(event, bot)
        return self

    async def get_user_name(self, event: MessageEvent, bot: Bot):
        if self.is_group or self.name is None:
            return await get_user_name(event=event, bot=bot, user_id=event.user_id) or '未知'
        else:
            return self.name

    def record_chat_history(self, text: str, sender: Optional[str] = None, auto_remove=True):
        self.history.add_chat_history(text, sender, auto_remove)

    def record_other_history(self, text: str, sender: str, auto_remove=True):
        self.history.add_other_history(text, sender, auto_remove)

    def clear_history(self):
        self.history = ChatHistory(self)

    def get_chat_messages(self) -> list[dict[str, str]]:
        return self.history.get_chat_messages()

    @property
    def enabled(self):
        return self.is_group or self.config.reply_on_private


#-----------------------------
#
#           历史记录
#
#-----------------------------

class ChatHistory:
    def __init__(self, instance: ChatInstance):
        self.instance = instance
        self.other_history: deque[tuple[float, str, dict, int]] = deque()
        self.other_history_token_count = 0
        self.last_other_text = None
        self.chat_history: deque[tuple[float, str, dict, int]] = deque()
        self.chat_history_token_count = 0
        self.last_chat_text = None

    def get_chat_messages(self) -> list[dict[str, str]]:
        sys_prompt = self.instance.config.system_prompt
        messages = [{"role": "system", "content": sys_prompt}] if sys_prompt else []
        histories = sorted(self.other_history + self.chat_history, key=lambda x: x[0])
        if self.instance.config.provide_username or self.instance.config.provide_local_time:
            for i in histories:
                msg = i[2]
                if msg['role'] == 'user':
                    extra = ''
                    if self.instance.config.provide_local_time:
                        extra = f'[{i[3]}] '
                    if self.instance.config.provide_username:
                        extra = f'{extra}{msg['name']}说 '
                    msg['content'] = f'{extra}{msg['content']}'
                messages.append(msg)
        else:
            messages.extend(i[2] for i in histories)
        return messages

    def add_other_history(self, text: str, sender: str, auto_remove=True):
        if self.last_other_text == text:
            token_count = self.other_history.pop()[-1]
        else:
            self.last_other_text = text
            token_count = self.count_token(text)
            self.other_history_token_count += token_count
        self.other_history.append((time(), asctime(), self.gen_text_json(text, sender), token_count))
        if not auto_remove:
            return
        while len(self.other_history) > 0 and self.other_history_token_count > self.instance.config.record_other_context_token_limit:
            self.other_history_token_count -= self.other_history.popleft()[-1]

    def add_chat_history(self, text: str, sender: Optional[str] = None, auto_remove=True):
        if self.last_chat_text == text:
            token_count = self.chat_history.pop()[-1]
        else:
            self.last_chat_text = text
            token_count = self.count_token(text)
            self.chat_history_token_count += token_count
        self.chat_history.append((time(), asctime(), self.gen_text_json(text, sender), token_count))
        if not auto_remove:
            return
        while len(self.chat_history) > 0 and self.chat_history_token_count > self.instance.config.record_chat_context_token_limit:
            self.chat_history_token_count -= self.chat_history.popleft()[-1]

    @staticmethod
    def gen_text_json(text: str, sender: Optional[str] = None):
        return {
            'role': 'assistant',
            'content': text
        } if sender is None else {
            'role': 'user',
            'name': sender,
            'content': text
        }

    @staticmethod
    def count_token(text: str):
        return len(shared.tiktoken.encode(text))


async def get_chat_instance(matcher: type[Matcher], event: MessageEvent, bot: Bot):
    chat_key, is_group = await get_chat_type(event)
    if chat_key in chat_instances:
        return chat_instances[chat_key]
    else:
        if is_group is None:
            await matcher.finish('未知的消息来源')
        return await ChatInstance.async_init(bot, event, chat_key, is_group)


def get_chat_instances():
    return chat_instances.values()