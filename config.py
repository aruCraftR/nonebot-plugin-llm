from os import makedirs
from pathlib import Path
from typing import Any, Callable
import yaml

import openai

from . import shared


def is_one_of_instance(x, types: tuple):
    for t in types:
        if x is t or isinstance(x, t):
            return True
    return False


class Filter:
    def __init__(self, func) -> None:
        self.filter: Callable[[Any], bool] = func


class PluginConfig:
    config_path = Path('data/llm/config.yml')
    config_checkers = {
        'openai_api_v1': (str, None, ''),
        'model_identifier': (str, None, ''),
        'api_timeout': (int, lambda x: x > 0, 60),
        'reply_throttle_time': ((int, float), lambda x: x >= 0, 3),
        'system_prompt': ((str, None), None, None),
        'chat_top_p': ((int, float), lambda x: 0 <= x <= 1, 0.95),
        'chat_temperature': ((int, float), lambda x: 0 <= x <= 1, 0.75),
        'chat_presence_penalty': ((int, float), lambda x: -2 <= x <= 2, 0.8),
        'chat_frequency_penalty': ((int, float), lambda x: -2 <= x <= 2, 0.8),
        'bot_name': (str, None, 'LLM'),
        'reply_on_private': (bool, None, True),
        'reply_on_name_mention': (bool, None, True),
        'reply_on_at': (bool, None, True),
        'reply_on_welcome': (bool, None, True),
        'use_group_card': (bool, None, True),
        'record_other_context': (bool, None, True),
        'record_other_context_token_limit': (int, lambda x: x > 0, 2048),
        'record_chat_context': (bool, None, True),
        'record_chat_context_token_limit': (int, lambda x: x > 0, 2048),
        'forbidden_users': (list, Filter(lambda x: isinstance(x, int)), []),
        'forbidden_groups': (list, Filter(lambda x: isinstance(x, int)), []),
        'forbidden_words': (list, Filter(lambda x: isinstance(x, str)), []),
        'event_priority': (int, None, 99),
        'block_event': (bool, None, False),
        'debug': (bool, None, False)
    }

    openai_api_v1: str
    model_identifier: str
    api_timeout: int
    reply_throttle_time: int | float
    system_prompt: str | None
    chat_top_p: int | float
    chat_temperature: int | float
    chat_presence_penalty: int | float
    chat_frequency_penalty: int | float
    bot_name: str
    reply_on_private: bool
    reply_on_name_mention: bool
    reply_on_at: bool
    reply_on_welcome: bool
    use_group_card: bool
    record_other_context: bool
    record_other_context_token_limit: int
    record_chat_context: bool
    record_chat_context_token_limit: int
    forbidden_users: list[int]
    forbidden_groups: list[int]
    forbidden_words: list[str]
    event_priority: int
    block_event: bool
    debug: bool

    def __init__(self):
        makedirs('data/llm', exist_ok=True)
        self.yaml: dict = None # type: ignore
        self.load_yaml()

    def load_yaml(self):
        if self.config_path.is_file():
            with open(self.config_path, mode='r', encoding='utf-8') as f:
                self.yaml = yaml.load(f, Loader=yaml.FullLoader)
        else:
            self.yaml = {}
        self.apply_yaml()
        with open(self.config_path, mode='w', encoding='utf-8') as f:
            yaml.dump(self.get_dict(), f, allow_unicode=True, sort_keys=False)
        openai.api_base = self.openai_api_v1
        openai.api_key = 'none'

    def get_dict(self):
        return {k: getattr(self, k) for k in self.config_checkers.keys()}

    def apply_yaml(self):
        for key, (types, condition, default) in self.config_checkers.items():
            value = self.yaml.get(key)
            use_default = False
            if value is None:
                use_default = True
            else:
                if types is None:
                    pass
                elif isinstance(types, tuple):
                    use_default = not is_one_of_instance(value, types)
                else:
                    use_default = not isinstance(value, types)
                if (not use_default) and condition is not None:
                    if isinstance(condition, Filter):
                        setattr(self, key, type(value)(filter(condition.filter, value)))
                        continue
                    else:
                        use_default = not condition(value)
            if use_default:
                setattr(self, key, default)
            else:
                setattr(self, key, value)


shared.plugin_config = PluginConfig()
