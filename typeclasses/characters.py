"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from evennia.objects.objects import DefaultCharacter

from .objects import ObjectParent


class Character(ObjectParent, DefaultCharacter):
    """
    The Character defaults to reimplementing some of base Object's hook methods with the
    following functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead).
    at_post_move(source_location) - Launches the "look" command after every move.
    at_post_unpuppet(account) -  when Account disconnects from the Character, we
                    store the current location in the pre_logout_location Attribute and
                    move it to a None-location so the "unpuppeted" character
                    object does not need to stay on grid. Echoes "Account has disconnected"
                    to the room.
    at_pre_puppet - Just before Account re-connects, retrieves the character's
                    pre_logout_location Attribute and move it back on the grid.
    at_post_puppet - Echoes "AccountName has entered the game" to the room.

    """

    def at_post_puppet(self, **kwargs):
        """
        Copied structure from Evennia lib.
        :param kwargs:
        :return:
        """
        self.msg("""
         |cWake up {name}|n. 
        
Huh, what was that? You rub the sand out of your eyes, leaving behind a blurry mess.
What happened? Oh yeah, the world stopped... right? Hard to know what's real these days. Maybe this is all a bad dream...
You look around.
""".format(name=self.key))
        self.msg((self.at_look(self.location), {"type": "look"}), options=None)

        def message(obj, from_obj):
            obj.msg(
                "{name} has entered the game.".format(name=self.get_display_name(obj)),
                from_obj=from_obj,
            )

        self.location.for_contents(message, exclude=[self], from_obj=self)
