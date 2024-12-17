
from collections import deque
from typing import Optional
from time import time

from . import shared

history_data: dict[str, 'ChatHistory'] = {}

class ChatHistory:
    def __init__(self, chat_key: str):
        super().__init__()
        self.chat_key = chat_key
        self.other_history: deque[tuple[float, dict, int]] = deque()
        self.other_history_token_count = 0
        self.last_other_text = None
        self.chat_history: deque[tuple[float, dict, int]] = deque()
        self.chat_history_token_count = 0
        self.last_chat_text = None
        history_data[chat_key] = self

    def get_chat_messages(self, sys_prompt: Optional[str] = None):
        messages = [{"role": "system", "content": sys_prompt}] if sys_prompt else []
        histories = sorted(self.other_history + self.chat_history, key=lambda x: x[0])
        messages.extend(i[1] for i in histories)
        return messages

    def add_other_history(self, text: str, sender: str, auto_remove=True):
        if self.last_other_text == text:
            token_count = self.other_history.pop()[-1]
        else:
            self.last_other_text = text
            token_count = self.count_token(text)
            self.other_history_token_count += token_count
        self.other_history.append((time(), self.gen_text_json(text, sender), token_count))
        if not auto_remove:
            return
        while len(self.other_history) > 0 and self.other_history_token_count > shared.plugin_config.record_other_context_token_limit:
            self.other_history_token_count -= self.other_history.popleft()[-1]

    def add_chat_history(self, text: str, sender: Optional[str] = None, auto_remove=True):
        if self.last_chat_text == text:
            token_count = self.chat_history.pop()[-1]
        else:
            self.last_chat_text = text
            token_count = self.count_token(text)
            self.chat_history_token_count += token_count
        self.chat_history.append((time(), self.gen_text_json(text, sender), token_count))
        if not auto_remove:
            return
        while len(self.chat_history) > 0 and self.chat_history_token_count > shared.plugin_config.record_chat_context_token_limit:
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


def record_chat_history(chat_key: str, text: str, sender: Optional[str] = None, auto_remove=True) -> 'ChatHistory':
    history = history_data.get(chat_key)
    if history is None:
        history = ChatHistory(chat_key)
    history.add_chat_history(text, sender, auto_remove)
    return history


def record_other_history(chat_key: str, text: str, sender: str, auto_remove=True):
    history = history_data.get(chat_key)
    if history is None:
        history = ChatHistory(chat_key)
    history.add_other_history(text, sender, auto_remove)
