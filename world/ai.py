"""
Where I'm putting functions for talking to LLMs.  OpenAI stuff basically
"""

from evennia import settings
import openai
openai.api_key = settings.OPENAI_KEY

TONE = \
    "This is a text based game in a post-apocalyptic overgrown urban landscape. "\
    "The city generally has dilapidated, abandoned buildings with various plants " \
    "of all types growing all over.  "\
    "Tone should be gritty, but wistful. "\
    "Emphasize the enormous amount of junk left by the old society "\
    "as well as the vigorous growth and activity by nature."\
    "\n\n"

# not sure yet about the style of the var names for the various prompts and prompt fragments
pickup_item_prompt = \
    "A character can pick up any item if it can be added to a character's inventory.\n\n" \
    "A baseball bat is not too heavy to pick up. A window is part of a building, so cannot be picked up.\n\n" \
    "Item:TRUE or FALSE, can it be picked up?\n" \
    "crowbar: True\n" \
    "window: False\n"

# I'm still pretty sure these *_objects lists should be in prototypes.py
scenic_objects = [
    "window", "car", "building", "pile", "rubble", "tree", "vine", "house", "plant"
]

container_objects = [
    "box", "backpack", "crate", "bag"
]


def make_prompt(additional_text):
    return TONE + additional_text  # + "\nDescription:\n"


def generate_text(prompt, max_tokens=150, model='text-curie-001'):
    """Returns the text of a completion prompt"""
    print(f"Prompt:\n{prompt}")
    completion = openai.Completion.create(
        model=model,
        prompt=prompt,
        max_tokens=max_tokens,
        top_p=.9,
        frequency_penalty=.2
    )
    print(f"Completion:\n{completion}")

    if completion and "choices" in completion:
        return completion["choices"][0]["text"]
    return ""


def chat_complete(messages):
    """Simple wrapper for the Chat Completion endpoint. Returns list of choices."""
    print(f"Messages:\n{messages}")
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=175,
        top_p=.9
    )
    print(f"Completion:\n{completion}")

    if completion and "choices" in completion:
        return completion["choices"]
    return []


def basic_chat_start(additional_text=""):
    return [{"role": "system", "content": TONE + additional_text}]


class Messages:
    """Manager of the array that the ChatCompletion uses.
    :return list of dicts {"role": "system" "user" or "assistant" :, "content": str}"""
    def __init__(self, additional_text=""):
        self.list = basic_chat_start(additional_text)

    def __call__(self, *args, **kwargs):
        return self.list

    def __repr__(self):
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
            raise TypeError
