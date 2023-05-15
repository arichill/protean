"""
Room

Rooms are simple containers that has no location of their own.

"""
from evennia.objects.objects import DefaultRoom, DefaultObject
from evennia import create_object
from .objects import ObjectParent, make_prompt, generate_text, zip_up_to_str
from world.ai import Messages, chat_complete

import inflect
from random import randint, shuffle

_INFLECT = inflect.engine()


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
        self.db.article = "a"  # We don't need this anymore
        # self.db.inside = False

    def describe(self):
        addl_info = []

        prep = self.db.preposition or "at"

        location = " ".join([prep, _INFLECT.a(self.key), self.db.addl_location_prompt or ""]).strip()
        # addl_info.append(("Name of location", location))

        exits = ["{} to {}\n".format(e.key, _INFLECT.an(e.destination.key))
                 for e in self.exits]
        # addl_info.append(("Exits", "; ".join(exits)))

        items = [_INFLECT.an(i.key) for i in self.contents_get(content_type="scenery")]
        # addl_info.append(("Description", ""))

        # prompt = make_prompt(
        #     f"Location: {location}.\nExits:\n-{'-'.join(exits)}\nItems:\n{', '.join(items)}\nLocation description:")

        prompt = f"Provide a very short description of a location: {location}.\n" \
                 f"Exits:\n-{'-'.join(exits)}\n" \
                 f"Scenery:\n{', '.join(items)}\n"

        # self.msg_contents(f"|gSending prompt::|n\n|G{prompt}|n")
        # new_text = generate_text(prompt)

        chat_log = Messages()
        chat_log.user(prompt)

        new_text = chat_complete(messages=chat_log())

        if new_text:
            self.db.desc = new_text["content"]
            self.db.used_prompt = prompt
            self.save()

    def spawn_items(self):
        sep = "\n-"
        num_of_items = randint(2, 6)
        items_spawned = 0

        location = _INFLECT.a(self.key)

        # Remove all the old items spawned, keep the MUD 'tidy' for now.
        for old_item in self.contents_get(content_type="object"):
            if old_item.db.ephemera:
                self.msg_contents(f"Removing {old_item.key}")
                old_item.delete()

        # Starting the list with the items already in the room
        items = [_INFLECT.an(i.key) for i in self.contents_get(content_type="object")]

        prompt = make_prompt(f"A list of items found in {location}{sep}{sep.join(items)}")
        # self.msg_contents(f"|gSending prompt::|n\n|G{prompt}|n")

        # Sometimes the LLM keeps going after the list.
        # I can set a stop sequence but for now, I find them interesting.
        new_items, *dream = generate_text(prompt).split("\n\n", 1)

        # For now, only using some of the items generated.
        # Randomizing so that we can get the weirder ones at the bottom of the list
        # have a chance of getting in.
        new_item_list = new_items.split(sep)
        shuffle(new_item_list)

        for item in new_item_list:
            if items_spawned >= num_of_items:
                break

            if not item:
                continue

            article, *item_words = item.split(maxsplit=1)
            if not item_words:
                item_name = article
                article = ""
            else:
                item_name = " ".join(item_words)

            create_object(
                typeclass="typeclasses.objects.Object",
                key=item_name,
                location=self,
                home=self,
                attributes=[("ephemera", True)]
            )
            items_spawned += 1

        self.msg_contents("|G{}|n".format("".join(dream)))

        self.describe()
