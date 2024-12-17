from typing import Tuple

import openai

from . import shared

def get_chat_response(messages: list[dict[str, str]])->Tuple[str, bool]:
    """对话文本生成"""
    try:
        response = openai.ChatCompletion.create(
            model=shared.plugin_config.model_identifier,
            messages=messages,
            temperature=shared.plugin_config.chat_temperature,
            # max_tokens=self.config['max_tokens'],
            top_p=shared.plugin_config.chat_top_p,
            frequency_penalty=shared.plugin_config.chat_frequency_penalty,
            presence_penalty=shared.plugin_config.chat_presence_penalty,
            timeout=shared.plugin_config.api_timeout,
        )
        res = response['choices'][0]['message']['content'].strip() # type: ignore
        return res, True
    except Exception as e:
        return f"请求 OpenAi Api 时发生错误: {repr(e)}", False


