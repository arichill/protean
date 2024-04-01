"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""
from evennia.objects.objects import DefaultExit

from .objects import ObjectParent, make_prompt, generate_text, zip_up_to_str
from typeclasses.rooms import Room

import inflect
_INFLECT = inflect.engine()


class Exit(ObjectParent, DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they defines the `destination` property. It also does work in the
    following methods:

     basetype_setup() - sets default exit locks (to change, use `at_object_creation` instead).
     at_cmdset_get(**kwargs) - this is called when the cmdset is accessed and should
                              rebuild the Exit cmdset along with a command matching the name
                              of the Exit object. Conventionally, a kwarg `force_init`
                              should force a rebuild of the cmdset, this is triggered
                              by the `@alias` command when aliases are changed.
     at_failed_traverse() - gives a default error message ("You cannot
                            go there") if exit traversal fails and an
                            attribute `err_traverse` is not defined.

    Relevant hooks to overload (compared to other types of Objects):
        at_traverse(traveller, target_loc) - called to do the actual traversal and calling of the other hooks.
                                            If overloading this, consider using super() to use the default
                                            movement implementation (and hook-calling).
        at_post_traverse(traveller, source_loc) - called by at_traverse just after traversing.
        at_failed_traverse(traveller) - called by at_traverse if traversal failed for some reason. Will
                                        not be called if the attribute `err_traverse` is
                                        defined, in which case that will simply be echoed.
    """

    def describe(self):
        here = self.location
        dest = self.destination

        assert isinstance(dest, Room)
        new_text = f"You see {_INFLECT.a(dest.name)}"

        # This doesn't make sense.  I should just provide some kind of short description of the
        # destination.
        # addl_info = \
        #     f"Location: {' '.join([here.db.article or '', here.key]).strip()}\n" +\
        #     f"Exit {' '.join([self.db.article or '', self.key]).strip()}. " +\
        #     f"It goes to {' '.join([dest.db.article or '', dest.key]).strip()}.\n" +\
        #     "\n\nExit Description:\n"
        #
        # prompt = make_prompt(addl_info)
        # # self.location.msg_contents(f"|gSending prompt::|n\n|G{prompt}|n")
        #
        # new_text = generate_text(prompt)
        #
        if new_text:
            self.db.desc = new_text
            self.save()


class BlockedExit(Exit):
    pass


class Above(Exit):
    """An exit that needs a ladder to traverse"""
    lockstring = (
        "control:id({id}) or perm(Admin);"
        "delete:id({id}) or perm(Admin);"
        "edit:id({id}) or perm(Admin);"
        "traverse:holds(ladder)"
    )

    def at_init(self):
        print(Above.lockstring)
        self.locks.add(Above.lockstring)

    def at_failed_traverse(self, traversing_object, **kwargs):
        traversing_object.msg("Can't reach up that far.")
