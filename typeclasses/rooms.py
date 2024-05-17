"""
Room

Rooms are simple containers that has no location of their own.

"""
from evennia.objects.objects import DefaultRoom
from evennia.utils.utils import delay
from evennia import create_object
from .objects import ObjectParent, Scenery, make_prompt, generate_text
from world.ai import Messages, chat_complete, scenic_objects, container_objects, simple_openai_chat_complete

import inflect
import spacy
from random import randint, shuffle

_INFLECT = inflect.engine()
nlp = spacy.load('en_core_web_sm')


def item_string_noun_phrase(item):
    _item = ""
    first_noun = ""

    print(f"processing '{item}'")

    for token in nlp(item):
        print(token.text, token.pos_, token.dep_)
        if token.dep_ == "compound":
            _item += token.text + " "
        elif token.pos_ == "NOUN":
            if not first_noun:
                first_noun = _item + token.lemma_
            if token.dep_ == "ROOT":
                _item += token.lemma_
                break
        else:
            _item = ""

    # Putting this after so I can see the parts of speech in stdout
    if len(item.split()) < 4:
        return item

    return _item or first_noun


class Room(ObjectParent, DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """

    def at_object_creation(self):
        self.db.preposition = "at"

    def at_init(self):
        self.item_ideas = []

    def describe(self):
        # addl_info = []

        # This is sort of a placeholder. I think different types of rooms will have different
        # "prepositions" or I guess it's just 'what is before the self.name in the prompt'
        # Ex: "Trapped in"
        prep = self.db.preposition or "at"

        location = " ".join(
            [prep, _INFLECT.a(self.key), self.db.addl_location_prompt or ""]).strip()
        # addl_info.append(("Name of location", location))

        exits = ["{} to {}\n".format(e.key, _INFLECT.an(e.destination.key))
                 for e in self.exits]
        # addl_info.append(("Exits", "; ".join(exits)))

        # I found giving all the items to chatgpt3.5 to produce really tedious descriptions.
        # Making scenery special allows for some control
        items = [_INFLECT.an(i.key) for i in self.contents_get(content_type="scenery")]

        # addl_info.append(("Description", ""))

        # prompt = make_prompt(
        #     f"Location: {location}.\nExits:\n-{'-'.join(exits)}\nItems:\n{', '.join(items)}\nLocation description:")

        prompt = f"Location: {location}.\n" \
                 f"Exits:\n-{'-'.join(exits)}\n" \
                 f"Scenery:\n{', '.join(items)}\n" \
                 f"Provide a short description:\n"

        # self.msg_contents(f"|gSending prompt::|n\n|G{prompt}|n")
        # new_text = generate_text(prompt)

        # At this time we're generating the Message log on every describe.
        chat_log = Messages()
        chat_log.user(prompt)

        # While migrating this, it occurs to me that perhaps 'openai' stuff is too exposed here
        # This code should be agnostic as to how/which model generated the text.
        new_text = chat_complete(messages=chat_log())[0].message

        if new_text:
            self.db.desc = new_text.content
            self.db.used_prompt = prompt
            self.save()

        # While we're here let's get new descriptions for the scenery items.
        for i in self.contents_get(content_type="scenery"):
            assert isinstance(i, Scenery)
            delay(1, i.describe)

    def spawn_items(self):
        print(f"Spawning items in {self.name}")
        if not self.item_ideas:
            print(f"Coming up with some new item ideas")
            delay(1, self.new_possible_items)
            return

        # It would be interesting if the # of items generated is a property of the object
        num_of_items = randint(2, 6)
        items_spawned = 0

        new_item_list = self.item_ideas.copy()

        for item in new_item_list:
            if items_spawned >= num_of_items:
                break

            if not item:
                continue

            item_name = item_string_noun_phrase(item)
            typeclass = "typeclasses.objects.Object"

            # So for now I'm doing some simple matching, seeing if various names from `scenic_objects`
            # are present in the item string, for ex "building", "window", "tree"
            # An interesting idea is using the evennia prototype system to handle all this
            for s in scenic_objects:
                if s in item_name:
                    typeclass = "typeclasses.objects.Scenery"
                    break

            for c in container_objects:
                if c in item_name:
                    typeclass = "typeclasses.containers.Container"
                    break

            obj = create_object(
                typeclass=typeclass,
                key=item_name,
                location=self,
                home=self,
                tags=["ephemera"]
            )
            self.item_ideas.remove(item)

            items_spawned += 1

        # self.msg_contents("|G{}|n".format("".join(dream)))

        delay(1, self.describe())

    def clear_ephemera(self):
        """Remove spawned items from the room"""
        for old_item in self.contents_get(content_type="object"):
            if old_item.db.ephemera or old_item.tags.has("ephemera"):
                self.msg_contents(f"Removing {old_item.key}")
                old_item.delete()
        # Weird thing when I invoked this method using evennia shell interactively, is that the objects stayed when
        # I 'looked' in the room, but I couldn't look 'at' the objects, since they were deleted.  So I'm going to try
        # saving the room at the end.  Might be some weird db thing.
        self.save()

    def new_possible_items(self):
        print(f"Getting a list of possible items in {self.name}")

        chat_log = Messages()

        chat_log.assistant(self.db.desc)
        chat_log.user(f"A simple list of in {_INFLECT.a(self.key)}")

        # Starting the list with the items already in the room
        items = [i.key for i in self.contents_get(content_type="object")]

        # Make sure the prompt ends with the list item delimiter, so that the LLM starts with
        # a new item, rather than appending to the last item in the list
        sep = "\n-"
        if items:
            chat_log.assistant(f"{sep}{sep.join(items)}".strip())

        new_items = simple_openai_chat_complete(messages=chat_log())

        self.item_ideas.extend([i.strip() for i in new_items.split(sep.strip()) if i])
        shuffle(self.item_ideas)
