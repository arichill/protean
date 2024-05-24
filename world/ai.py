"""
Where I'm putting functions for talking to LLMs.  OpenAI stuff basically
"""

from evennia import settings
from evennia.utils import logger
import openai
from openai import OpenAI, OpenAIError

if not openai.api_key:
    try:
        import os
        openai.api_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_KEY
    except AttributeError:
        raise OpenAIError(
            "Put your OpenAI api key in either the environmental variable OPENAI_API_KEY or in the Evennia settings as "
            "OPENAI_KEY.  See /server/conf/settings.py for details")

client = OpenAI()

DECLARATION = "This is a text based game in a post-apocalyptic overgrown urban landscape. "

TONE = "Tone should be gritty, but wistful. "  # \
# "This is a text based game in a post-apocalyptic overgrown urban landscape. "\
# "The city generally has dilapidated, abandoned buildings with various plants " \
# "of all types growing all over.  "\
# "Tone should be gritty, but wistful. "\
# "Emphasize the enormous amount of junk left by the old society "\
# "as well as the vigorous growth and activity by nature."\
# "\n\n"

SETTING_DESCRIPTION = \
    "The city generally has dilapidated, abandoned buildings with various plants " \
    "of all types growing all over.  " \
    "Emphasize the enormous amount of junk left by the old society " \
    "as well as the vigorous growth and activity by nature."

# not sure yet about the style of the var names for the various prompts and prompt fragments
pickup_item_prompt = \
    "A character can pick up any item if it can be added to a character's inventory.\n\n" \
    "A baseball bat is not too heavy to pick up. A window is part of a building, so cannot be picked up.\n\n" \
    "Item:TRUE or FALSE, can it be picked up?\n" \
    "crowbar: True\n" \
    "window: False\n"

# I'm still pretty sure these *_objects lists should be in prototypes.py
scenic_objects = [
    "window", "car", "building", "pile", "rubble", "tree", "vine", "house", "plant", "wall", "pavement"
]

container_objects = [
    "box", "backpack", "crate", "bag"
]


def log(msg):
    logger.log_file(msg, filename="prompt.log")


def make_prompt(additional_text, tone=True, setting=True):
    text_items = [DECLARATION]
    if tone:
        text_items.append(TONE)
    if setting:
        text_items.append(SETTING_DESCRIPTION)
    text_items.append("\n\n")
    text_items.append(additional_text)

    return "".join(text_items)


def generate_text(prompt, max_tokens=150, model='gpt-3.5-turbo-instruct'):
    """Returns the text of a completion prompt"""
    print(f"Prompt:\n{prompt[-60:]}")
    log(f"Prompt:\n{prompt}")
    completion = client.completions.create(
        model=model,
        prompt=prompt,
        max_tokens=max_tokens,
        top_p=.9,
        frequency_penalty=.35
    )
    log(f"Completion:\n{completion}")

    return completion.choices[0].text


def chat_complete(messages, model="gpt-3.5-turbo"):
    """Simple wrapper for the Chat Completion endpoint. Returns list of choices."""
    print(f"Sending messages to {model}::\n{messages[-1]}")
    log(f"Messages::\n{messages}")
    completion = openai.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=175,
        top_p=.9,
        frequency_penalty=.6
    )
    if completion:
        print(f"Received completion. Used {completion.usage.total_tokens} tokens")
        log(f"Completion:\n{completion}")

    return completion.choices or []


def simple_openai_chat_complete(messages):
    choices = chat_complete(messages)
    if choices:
        return choices[0].message.content


def basic_chat_start(additional_text=""):
    return [{"role": "system", "content": DECLARATION + TONE + SETTING_DESCRIPTION + additional_text}]


class Messages:
    """Manager of the array that the ChatCompletion uses.
    :return list of dicts {"role": "system" "user" or "assistant" :, "content": str}"""
    def __init__(self, chat_log=None, additional_text=""):
        self.list = []
        if isinstance(chat_log, Messages):
            self.list = chat_log()
        elif isinstance(chat_log, list):
            for msg in chat_log:
                self.add_message(msg)

        if not self.list:
            self.list = basic_chat_start(additional_text)

    def __call__(self, *args, **kwargs):
        return self.list

    def __str__(self):
        sep = ', \n'
        return f"[{sep.join([repr(d) for d in self.list])}]"

    def user(self, text):
        self.list.append({"role": "user", "content": text})

    def assistant(self, text):
        self.list.append({"role": "assistant", "content": text})

    def add_message(self, message_dict):
        if "role" in message_dict and "content" in message_dict:
            self.list.append(message_dict)
        else:
            raise TypeError("Message dictionary must have a 'role' and a 'content'")

    def last(self):
        return self.list[-1]

    def last_message(self):
        return self.last()["content"]
