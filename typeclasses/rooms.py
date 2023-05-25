"""
Room

Rooms are simple containers that has no location of their own.

"""
from evennia.objects.objects import DefaultRoom, DefaultObject
from evennia import create_object
from .objects import ObjectParent, Scenery, make_prompt, generate_text, zip_up_to_str
from world.ai import Messages, chat_complete, scenic_objects

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

    def describe(self):
        addl_info = []

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

        # While we're here let's get new descriptions for the scenery items.
        for i in self.contents_get(content_type="scenery"):
            assert isinstance(i, Scenery)
            i.describe()
        # addl_info.append(("Description", ""))

        # prompt = make_prompt(
        #     f"Location: {location}.\nExits:\n-{'-'.join(exits)}\nItems:\n{', '.join(items)}\nLocation description:")

        prompt = f"Provide a very short description of a location: {location}.\n" \
                 f"Exits:\n-{'-'.join(exits)}\n" \
                 f"Scenery:\n{', '.join(items)}\n"

        # self.msg_contents(f"|gSending prompt::|n\n|G{prompt}|n")
        # new_text = generate_text(prompt)

        # At this time we're generating the Message log on every describe.
        chat_log = Messages()
        chat_log.user(prompt)

        new_text = chat_complete(messages=chat_log())[0]["message"]

        if new_text:
            self.db.desc = new_text["content"]
            self.db.used_prompt = prompt
            self.save()

    def spawn_items(self):
        # It would be interesting if the # of items generated is a property of the object
        num_of_items = randint(2, 6)
        items_spawned = 0

        location = _INFLECT.a(self.key)

        # Remove all the old items spawned, keep the MUD 'tidy' for now.
        for old_item in self.contents_get(content_type="object"):
            if old_item.db.ephemera or old_item.tags.has("ephemera"):
                self.msg_contents(f"Removing {old_item.key}")
                old_item.delete()

        # Starting the list with the items already in the room
        items = [_INFLECT.an(i.key) for i in self.contents_get(content_type="object")]

        sep = "\n-"
        prompt = make_prompt(f"Provide a list of items found in {location}{sep}{sep.join(items)}")
        # self.msg_contents(f"|gSending prompt::|n\n|G{prompt}|n")

        # Sometimes the LLM keeps going after the list.
        # I can set a stop sequence, but for now I find them interesting.
        new_items, *dream = generate_text(prompt).split("\n\n", 1)

        # For now, only using some of the items generated.
        # Randomizing so that we can get the weirder ones at the bottom of the list
        # have a chance of getting in.
        new_item_list = new_items.split(sep.strip())
        shuffle(new_item_list)

        # Simple parser for now, but this is holding a place for when I get more advanced parsing
        # Although really this should be in the ai.py file if it gets more complex
        def parse(item_str):
            return item_str \
                .strip() \
                .strip("-")\
                .removeprefix("a ").removeprefix("A ")\
                .removeprefix("an ").removeprefix("An ")\

        for item in new_item_list:
            if items_spawned >= num_of_items:
                break

            if not item:
                continue

            item_name = parse(item)
            typeclass = "typeclasses.objects.Object"

            # So for now I'm doing some simple matching, seeing if various names from `scenic_objects`
            # are present in the item string, for ex "building", "window", "tree"
            # An interesting idea is using the evennia prototype system to handle all this
            for s in scenic_objects:
                if s in item_name:
                    typeclass = "typeclasses.objects.Scenery"

            obj = create_object(
                typeclass=typeclass,
                key=item_name,
                location=self,
                home=self,
                # locks="get:false()",  # Gonna try to handle this at the typeclass level
                tags=["ephemera"]
            )
            items_spawned += 1

        self.msg_contents("|G{}|n".format("".join(dream)))

        self.describe()
