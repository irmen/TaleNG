from typing import Optional, AbstractSet, MutableSet, MutableMapping, FrozenSet, Union, Sequence
from . import lang

# TODO migrate away from direct references and more towards an E/C system with id's as reference?


class MudObject:
    def __init__(self, name: str, title: str = "", gender: str = "n", aliases: Optional[AbstractSet[str]] = None) -> None:
        self.name = name.lower()
        self.title = title or name
        self.aliases = aliases or set()
        self.gender = gender
        self.subjective = lang.SUBJECTIVE[gender]
        self.possessive = lang.POSSESSIVE[gender]
        self.objective = lang.OBJECTIVE[gender]


class Location(MudObject):
    def __init__(self, name: str) -> None:
        super().__init__(name, )
        self.exits: MutableMapping[str, MudObject] = {}
        self.livings: MutableSet[Living] = set()
        self.items: MutableSet[MudObject] = set()


class Exit(MudObject):
    def __init__(self, directions: Union[str, Sequence[str]], target_location: Union[str, Location], short_descr: str) -> None:
        self.target = limbo
        if isinstance(directions, str):
            direction = directions
            aliases: MutableSet[str] = set()
        else:
            direction = directions[0]
            aliases = set(directions[1:])
        if isinstance(target_location, Location):
            self.target = target_location
            self._target_str = ""
            title = "Exit to " + self.target.title
        else:
            self._target_str = target_location
            title = "Exit to <unbound:%s>" % target_location
        # the name of the exit/door is the first direction given (any others are aliases)
        super().__init__(direction, title=title)
        self.aliases = aliases

    def bind(self, location: Location) -> None:
        """Binds the exit to a location."""
        directions = self.aliases | {self.name}
        for direction in directions:
            location.exits[direction] = self


limbo = Location("Limbo")


class Living(MudObject):
    def __init__(self, name: str, gender: str, title: str = "", location: Location = limbo) -> None:
        super().__init__(name, title, gender)
        self.location = location
        self.__inventory: MutableSet[MudObject] = set()

    @property
    def inventory(self) -> FrozenSet[MudObject]:
        return frozenset(self.__inventory)

    def search_item(self, name: str,
                    include_inventory: bool = True,
                    include_location: bool = True,
                    include_containers_in_inventory: bool = True) -> Optional[MudObject]:
        """
        If an item with the given name is found in the specified places, it is returned.
        Otherwise, None is returned.
        """
        pass

    def move(self, location: Location) -> None:
        self.location.livings.discard(self)
        self.location = location
        location.livings.add(self)


class Item(MudObject):
    # class for items
    pass
