"""
Written by Irmen de Jong (irmen@razorvine.net)
Based on ancient soul.c v1.2 written in LPC by profezzorn@nannymud (Fredrik Hübinette)
Only the verb table is more or less intact (with some additions and fixes).
The verb parsing and message generation have been fully rewritten.

'Tale-NG' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import re
from collections import defaultdict
from typing import Tuple, AbstractSet, Optional, List, MutableMapping, Mapping, Sequence
from . import verbs, adverbs
from .. import lang
from ..objects import MudObject, Living
from ..errors import TaleError


class ParseError(TaleError):
    """Problem with parsing the user input. Should be shown to the user as a nice error message."""
    pass


class NonSoulVerbError(ParseError):
    """
    The soul's parser encountered a verb that cannot be handled by the soul itself.
    However the command string has been parsed and the calling code could try
    to handle the verb by itself instead.
    """

    def __init__(self, parseresult) -> None:
        super().__init__(parseresult.verb)
        self.parsed = parseresult


class UnknownVerbError(ParseError):
    """
    The soul doesn't recognise the verb that the user typed.
    The engine can and should search for other places that define this verb first.
    If nothing recognises it, this error should be shown to the user in a nice way.
    """

    def __init__(self, verb: str, words: Sequence[str], qualifier: str) -> None:
        super().__init__(verb)
        self.verb = verb
        self.words = words
        self.qualifier = qualifier


class ParseResult:
    """Captures the result of a parsed input line."""

    class WhoInfo:
        """parse details of this Who in the line"""

        def __init__(self, seqnr: int = 0) -> None:
            self.sequence = seqnr  # at what position does this Who occur
            self.previous_word = ""  # what is the word preceding it

        def __str__(self) -> str:
            return "[seq=%d, prev_word=%s]" % (self.sequence, self.previous_word)

    def __init__(self, verb: str, *, adverb: str = "", message: str = "", bodypart: str = "", qualifier: str = "",
                 args: List[str] = None, who_info: MutableMapping[MudObject, WhoInfo] = None,
                 unrecognized: List[str] = None, unparsed: str = "", who_list: List[MudObject] = None) -> None:
        self.verb = verb
        self.adverb = adverb
        self.message = message
        self.bodypart = bodypart
        self.qualifier = qualifier
        self.args = args or []
        self.unrecognized = unrecognized or []
        self.unparsed = unparsed
        self.who_info = who_info or defaultdict(ParseResult.WhoInfo)
        if who_list and not self.who_info:
            # initialize the who_info dictionary from the given list and check for duplicates
            # if who_info is ALSO provided, we ignore who_list.
            duplicates = set()
            for sequence, who in enumerate(who_list):
                if who in self.who_info:
                    duplicates.add(who)
                self.who_info[who] = ParseResult.WhoInfo(sequence)
            if duplicates:
                raise ParseError(
                    "You can do only one thing at the same time with {}. Try to use multiple separate commands instead."
                        .format(lang.join(s.name for s in duplicates)))
        self.who_count = len(self.who_info)

    def __str__(self) -> str:
        who_info_str = [" %s->%s" % (living.name, info) for living, info in self.who_info.items()]
        s = [
            "ParseResult:",
            " verb=%s" % self.verb,
            " qualifier=%s" % self.qualifier,
            " adverb=%s" % self.adverb,
            " bodypart=%s" % self.bodypart,
            " message=%s" % self.message,
            " args=%s" % self.args,
            " unrecognized=%s" % self.unrecognized,
            " who_count=%d" % self.who_count,
            " who_info=%s" % "\n   ".join(who_info_str),
            " unparsed=%s" % self.unparsed
        ]
        return "\n".join(s)

    @property
    def who_1(self) -> Optional[MudObject]:
        """Gets the first occurring ParsedWhoType from the parsed line (or None if it doesn't exist)"""
        return next(iter(self.who_info)) if self.who_info else None     # type: ignore

    @property
    def who_12(self) -> Tuple[Optional[MudObject], Optional[MudObject]]:
        """
        Returns a tuple (ParsedWhoType, ParsedWhoType) representing the first two occurring Whos in the parsed line.
        If no such subject exists, None is returned in its place.
        """
        whos = list(self.who_info)    # this is in order because who_info is OrderedDict
        return tuple((whos + [None, None])[:2])  # type: ignore

    @property
    def who_123(self) -> Tuple[Optional[MudObject], Optional[MudObject], Optional[MudObject]]:
        """
        Returns a tuple (ParsedWhoType, ParsedWhoType, ParsedWhoType) representing the first three occurring Whos in the parsed line.
        If no such subject exists, None is returned in its place.
        """
        whos = list(self.who_info)    # this is in order because who_info is OrderedDict
        return tuple((whos + [None, None, None])[:3])  # type: ignore

    @property
    def who_last(self) -> Optional[MudObject]:
        """Gets the last occurring ParsedWhoType on the line (or None if there wasn't any)"""
        if self.who_info:
            return list(self.who_info)[-1]
        return None


class Soul:
    """
    The 'soul' of a SoulLiving (most importantly, a Player).
    Handles the high level verb actions and allows for social player interaction.
    Verbs that actually do something in the environment (not purely social messages) are implemented elsewhere.
    """

    _quoted_message_regex = re.compile(
        r"('(?P<msg1>.*)')|(\"(?P<msg2>.*)\")")  # greedy single-or-doublequoted string match
    _skip_words = {"and", "&", "at", "to", "before", "in", "into", "on", "off", "onto",
                   "the", "with", "from", "after", "before", "under", "above", "next"}

    def __init__(self) -> None:
        self.__previously_parsed = ParseResult("")

    def is_verb(self, verb: str) -> bool:
        return verb in verbs.VERBS

    def process_verb(self, player: Living, commandstring: str, external_verbs: Optional[AbstractSet[str]] = None) \
        -> Tuple[str, Tuple[AbstractSet[MudObject], str, str, str]]:
        """
        Parse a command string and return a tuple containing the main verb (tickle, ponder, ...)
        and another tuple containing the targets of the action (excluding the player) and the various action messages.
        Any action qualifier is added to the verb string if it is present ("fail kick").
        """
        parsed = self.parse(player, commandstring, external_verbs or set())
        if external_verbs and parsed.verb in external_verbs:
            raise NonSoulVerbError(parsed)
        result = self.process_verb_parsed(player, parsed)
        if parsed.qualifier:
            verb = parsed.qualifier + " " + parsed.verb
        else:
            verb = parsed.verb
        return verb, result

    def process_verb_parsed(self, player: Living, parsed: ParseResult) -> Tuple[AbstractSet[MudObject], str, str, str]:
        """
        This function takes a verb and the arguments given by the user,
        creates various display messages that can be sent to the players and room,
        and returns a tuple: (targets-without-player, playermessage, roommessage, targetmessage)
        Target can be a SoulLiving, an Item or an Exit.
        """
        if not player:
            raise TaleError("no player in process_verb_parsed")
        verbdata = verbs.VERBS.get(parsed.verb)
        if not verbdata:
            raise UnknownVerbError(parsed.verb, [], parsed.qualifier)

        message = parsed.message
        adverb = parsed.adverb

        vtype = verbdata[0]
        if not message and verbdata[1] and len(verbdata[1]) > 1:
            message = verbdata[1][1]  # get the message from the verbs table
        if message:
            if message.startswith("'"):
                # use the message without single quotes around it
                msg = message = self.spacify(message[1:])
            else:
                msg = " '" + message + "'"
                message = " " + message
        else:
            msg = message = ""
        if not adverb:
            if verbdata[1]:
                adverb = verbdata[1][0]  # normal-adverb
            else:
                adverb = ""
        where = ""
        if parsed.bodypart:
            where = " " + verbs.BODY_PARTS[parsed.bodypart]
        elif not parsed.bodypart and verbdata[1] and len(verbdata[1]) > 2 and verbdata[1][2]:
            where = " " + verbdata[1][2]  # replace bodyparts string by specific one from verbs table
        how = self.spacify(adverb)

        def result_messages(action: str, action_room: str) -> Tuple[AbstractSet[MudObject], str, str, str]:
            action = action.strip()
            action_room = action_room.strip()
            if parsed.qualifier:
                qual_action, qual_room, use_room_default = verbs.ACTION_QUALIFIERS[parsed.qualifier]
                action_room = qual_room % action_room if use_room_default else qual_room % action
                action = qual_action % action
            # construct message seen by player
            targetnames = [self.who_replacement(player, target, player) for target in parsed.who_info]
            player_msg = action.replace(" \nWHO", " " + lang.join(targetnames))
            player_msg = player_msg.replace(" \nYOUR", " your")
            player_msg = player_msg.replace(" \nMY", " your")
            # construct message seen by room
            targetnames = [self.who_replacement(player, target, None) for target in parsed.who_info]
            room_msg = action_room.replace(" \nWHO", " " + lang.join(targetnames))
            room_msg = room_msg.replace(" \nYOUR", " " + player.possessive)
            room_msg = room_msg.replace(" \nMY", " " + player.objective)
            # construct message seen by targets
            target_msg = action_room.replace(" \nWHO", " you")
            target_msg = target_msg.replace(" \nYOUR", " " + player.possessive)
            target_msg = target_msg.replace(" \nPOSS", " your")
            target_msg = target_msg.replace(" \nIS", " are")
            target_msg = target_msg.replace(" \nSUBJ", " you")
            target_msg = target_msg.replace(" \nMY", " " + player.objective)
            # fix up POSS, IS, SUBJ in the player and room messages
            if parsed.who_count == 1:
                only_living = parsed.who_1
                subjective = getattr(only_living, "subjective", "it")  # if no subjective attr, use "it"
                player_msg = player_msg.replace(" \nIS", " is")
                player_msg = player_msg.replace(" \nSUBJ", " " + subjective)
                player_msg = player_msg.replace(" \nPOSS", " " + Soul.poss_replacement(player, only_living, player))
                room_msg = room_msg.replace(" \nIS", " is")
                room_msg = room_msg.replace(" \nSUBJ", " " + subjective)
                room_msg = room_msg.replace(" \nPOSS", " " + Soul.poss_replacement(player, only_living, None))
            else:
                targetnames_player = lang.join(
                    [Soul.poss_replacement(player, living, player) for living in parsed.who_info])
                targetnames_room = lang.join(
                    [Soul.poss_replacement(player, living, None) for living in parsed.who_info])
                player_msg = player_msg.replace(" \nIS", " are")
                player_msg = player_msg.replace(" \nSUBJ", " they")
                player_msg = player_msg.replace(" \nPOSS", " " + lang.possessive(targetnames_player))
                room_msg = room_msg.replace(" \nIS", " are")
                room_msg = room_msg.replace(" \nSUBJ", " they")
                room_msg = room_msg.replace(" \nPOSS", " " + lang.possessive(targetnames_room))
            # add fullstops at the end
            player_msg = lang.fullstop("You " + player_msg)
            room_msg = lang.capital(lang.fullstop(player.title + " " + room_msg))
            target_msg = lang.capital(lang.fullstop(player.title + " " + target_msg))
            if player in parsed.who_info:
                who = set(parsed.who_info)
                who.remove(player)  # the player should not be part of the remaining targets.
                whof = set(who)
            else:
                whof = set(parsed.who_info)
            return whof, player_msg, room_msg, target_msg

        # construct the action string
        action = None
        if vtype == verbs.VerbType.DEUX:
            action = verbdata[2]
            action_room = verbdata[3]
            if not self.check_person(action, parsed):
                raise ParseError("The verb %s needs a person." % parsed.verb)
            action = action.replace(" \nWHERE", where)
            action_room = action_room.replace(" \nWHERE", where)
            action = action.replace(" \nWHAT", message)
            action = action.replace(" \nMSG", msg)
            action_room = action_room.replace(" \nWHAT", message)
            action_room = action_room.replace(" \nMSG", msg)
            action = action.replace(" \nHOW", how)
            action_room = action_room.replace(" \nHOW", how)
            return result_messages(action, action_room)
        elif vtype == verbs.VerbType.QUAD:
            if parsed.who_info:
                action = verbdata[4]
                action_room = verbdata[5]
            else:
                action = verbdata[2]
                action_room = verbdata[3]
            action = action.replace(" \nWHERE", where)
            action_room = action_room.replace(" \nWHERE", where)
            action = action.replace(" \nWHAT", message)
            action = action.replace(" \nMSG", msg)
            action_room = action_room.replace(" \nWHAT", message)
            action_room = action_room.replace(" \nMSG", msg)
            action = action.replace(" \nHOW", how)
            action_room = action_room.replace(" \nHOW", how)
            return result_messages(action, action_room)
        elif vtype == verbs.VerbType.FULL:
            raise TaleError("vtype verbs.VerbType.FULL")  # doesn't matter, verbs.VerbType.FULL is not used yet anyway
        elif vtype == verbs.VerbType.DEFA:
            action = parsed.verb + "$ \nHOW \nAT"
        elif vtype == verbs.VerbType.PREV:
            action = parsed.verb + "$" + self.spacify(verbdata[2]) + " \nWHO \nHOW"
        elif vtype == verbs.VerbType.PHYS:
            action = parsed.verb + "$" + self.spacify(verbdata[2]) + " \nWHO \nHOW \nWHERE"
        elif vtype == verbs.VerbType.SHRT:
            action = parsed.verb + "$" + self.spacify(verbdata[2]) + " \nHOW"
        elif vtype == verbs.VerbType.PERS:
            action = verbdata[3] if parsed.who_count else verbdata[2]
        elif vtype == verbs.VerbType.SIMP:
            action = verbdata[2]
        else:
            raise TaleError("invalid vtype " + vtype)

        if parsed.who_info and len(verbdata) > 3:
            action = action.replace(" \nAT", self.spacify(verbdata[3]) + " \nWHO")
        else:
            action = action.replace(" \nAT", "")

        if not self.check_person(action, parsed):
            raise ParseError("The verb %s needs a person." % parsed.verb)

        action = action.replace(" \nHOW", how)
        action = action.replace(" \nWHERE", where)
        action = action.replace(" \nWHAT", message)
        action = action.replace(" \nMSG", msg)
        action_room = action
        action = action.replace("$", "")
        action_room = action_room.replace("$", "s")
        return result_messages(action, action_room)

    def parse(self, player: Living, cmd: str, external_verbs: Optional[AbstractSet[str]] = None) -> ParseResult:
        """Parse a command string, returns a ParseResult object."""
        qualifier = ""
        message_verb = False  # does the verb expect a message?
        external_verb = False  # is it a non-soul verb?
        adverb = ""
        message: List[str] = []
        bodypart = ""
        arg_words: List[str] = []
        unrecognized_words: List[str] = []
        who_info: MutableMapping[MudObject, ParseResult.WhoInfo] = defaultdict(ParseResult.WhoInfo)
        who_list: List[MudObject] = []
        who_sequence = 0
        unparsed = cmd

        # a substring enclosed in quotes will be extracted as the message
        m = self._quoted_message_regex.search(cmd)
        if m:
            message = [(m.group("msg1") or m.group("msg2")).strip()]
            cmd = cmd[:m.start()] + cmd[m.end():]

        if not cmd:
            raise ParseError("What?")
        words = cmd.split()
        if words[0] in verbs.ACTION_QUALIFIERS:  # suddenly, fail, ...
            qualifier = words.pop(0)
            unparsed = unparsed[len(qualifier):].lstrip()
            if qualifier == "dont":
                qualifier = "don't"  # little spelling suggestion
            # note: don't add qualifier to arg_words
        if words and words[0] in self._skip_words:
            skipword = words.pop(0)
            unparsed = unparsed[len(skipword):].lstrip()

        if not words:
            raise ParseError("What?")
        verb = None
        if words[0] in (external_verbs or {}):  # external verbs have priority above soul verbs
            verb = words.pop(0)
            external_verb = True
            # note: don't add verb to arg_words
        elif words[0] in verbs.VERBS:
            verb = words.pop(0)
            verbdata = verbs.VERBS[verb][2]
            message_verb = "\nMSG" in verbdata or "\nWHAT" in verbdata
            # note: don't add verb to arg_words
        elif player.location.exits:
            # check if the words are the name of a room exit.
            move_action = None
            if words[0] in verbs.MOVEMENT_VERBS:
                move_action = words.pop(0)
                if not words:
                    raise ParseError("%s where?" % lang.capital(move_action))
            exit, exit_name, wordcount = self.check_name_with_spaces(words, 0, {}, {}, player.location.exits)
            if exit:
                if wordcount != len(words):
                    raise ParseError("What do you want to do with that?")
                unparsed = unparsed[len(exit_name or ""):].lstrip()
                who_info = defaultdict(ParseResult.WhoInfo)
                raise NonSoulVerbError(
                    ParseResult(verb=exit_name or "", who_list=[exit], qualifier=qualifier, unparsed=unparsed))
            elif move_action:
                raise ParseError("You can't %s there." % move_action)
            else:
                # can't determine verb at this point, just continue with verb=None
                pass
        else:
            # can't determine verb at this point, just continue with verb=None
            pass

        if verb:
            unparsed = unparsed[len(verb):].lstrip()
        include_flag = True
        collect_message = False
        all_livings = {}  # livings in the room (including player) by name + aliases
        all_items = {}  # all items in the room or player's inventory, by name + aliases
        for living in player.location.livings:
            all_livings[living.name] = living
            for alias in living.aliases:
                all_livings[alias] = living
        for item in player.location.items:
            all_items[item.name] = item
            for alias in item.aliases:
                all_items[alias] = item
        for item in player.inventory:
            all_items[item.name] = item
            for alias in item.aliases:
                all_items[alias] = item
        previous_word = ""
        words_enumerator = enumerate(words)
        for index, word in words_enumerator:
            if collect_message:
                message.append(word)
                arg_words.append(word)
                previous_word = word
                continue
            if not message_verb and not collect_message:
                word = word.rstrip(",")
            if word in ("them", "him", "her", "it"):
                if self.__previously_parsed:
                    # try to connect the pronoun to a previously parsed item/living
                    prev_who_list = self.match_previously_parsed(player, word)
                    if prev_who_list:
                        for who, name in prev_who_list:
                            if include_flag:
                                who_info[who].sequence = who_sequence
                                who_info[who].previous_word = previous_word
                                who_sequence += 1
                                who_list.append(who)
                            else:
                                del who_info[who]
                                who_list.remove(who)
                            arg_words.append(name)  # put the replacement-name in the args instead of the pronoun
                    previous_word = ""
                    continue
                raise ParseError("It is not clear who you mean.")
            if word in ("me", "myself", "self"):
                if include_flag:
                    who_info[player].sequence = who_sequence
                    who_info[player].previous_word = previous_word
                    who_sequence += 1
                    who_list.append(player)
                elif player in who_info:
                    del who_info[player]
                    who_list.remove(player)
                arg_words.append(word)
                previous_word = ""
                continue
            if word in verbs.BODY_PARTS:
                if bodypart:
                    raise ParseError(
                        "You can't do that both %s and %s." % (verbs.BODY_PARTS[bodypart], verbs.BODY_PARTS[word]))
                if (word not in all_items and word not in all_livings) or previous_word == "my":
                    bodypart = word
                    arg_words.append(word)
                    continue
            if word in ("everyone", "everybody", "all"):
                if include_flag:
                    if not all_livings:
                        raise ParseError("There is nobody here.")
                    # include every *living* thing visible, don't include items, and skip the player itself
                    for living in player.location.livings:
                        if living is not player:
                            who_info[living].sequence = who_sequence
                            who_info[living].previous_word = previous_word
                            who_sequence += 1
                            who_list.append(living)
                else:
                    who_info.clear()
                    who_list.clear()
                    who_sequence = 0
                arg_words.append(word)
                previous_word = ""
                continue
            if word == "everything":
                raise ParseError("You can't do something to everything around you, be more specific.")
            if word in ("except", "but"):
                include_flag = not include_flag
                arg_words.append(word)
                continue
            if word in adverbs.ADVERBS:
                if adverb:
                    raise ParseError("You can't do that both %s and %s." % (adverb, word))
                adverb = word
                arg_words.append(word)
                continue
            if word in all_livings:
                living = all_livings[word]
                if include_flag:
                    who_info[living].sequence = who_sequence
                    who_info[living].previous_word = previous_word
                    who_sequence += 1
                    who_list.append(living)
                elif living in who_info:
                    del who_info[living]
                    who_list.remove(living)
                arg_words.append(word)
                previous_word = ""
                continue
            if word in all_items:
                item = all_items[word]
                if include_flag:
                    who_info[item].sequence = who_sequence
                    who_info[item].previous_word = previous_word
                    who_sequence += 1
                    who_list.append(item)
                elif item in who_info:
                    del who_info[item]
                    who_list.remove(item)
                arg_words.append(word)
                previous_word = ""
                continue
            if player.location:
                exit, exit_name, wordcount = self.check_name_with_spaces(words, index, {}, {}, player.location.exits)
                if exit:
                    who_info[exit].sequence = who_sequence
                    who_info[exit].previous_word = previous_word
                    previous_word = ""
                    who_sequence += 1
                    who_list.append(exit)
                    if exit_name:
                        arg_words.append(exit_name)
                    while wordcount > 1:
                        next(words_enumerator)
                        wordcount -= 1
                    continue
            item_or_living, full_name, wordcount = self.check_name_with_spaces(words, index, all_livings, all_items, {})
            if item_or_living:
                while wordcount > 1:
                    next(words_enumerator)
                    wordcount -= 1
                if include_flag:
                    who_info[item_or_living].sequence = who_sequence
                    who_info[item_or_living].previous_word = previous_word
                    who_sequence += 1
                    who_list.append(item_or_living)
                elif item_or_living in who_info:
                    del who_info[item_or_living]
                    who_list.remove(item_or_living)
                if full_name:
                    arg_words.append(full_name)
                previous_word = ""
                continue
            if message_verb and not message:
                collect_message = True
                message.append(word)
                arg_words.append(word)
                continue
            if word not in self._skip_words:
                # unrecognized word, check if it could be a person's name or an item. (prefix)
                if not who_list:
                    for name in all_livings:
                        if name.startswith(word):
                            raise ParseError("Perhaps you meant %s?" % name)
                    for name in all_items:
                        if name.startswith(word):
                            raise ParseError("Perhaps you meant %s?" % name)
                if not external_verb:
                    if not verb:
                        raise UnknownVerbError(word, words, qualifier)
                    # check if it is a prefix of an adverb, if so, suggest a few adverbs
                    prefixed_adverbs = adverbs.search_prefix(word)
                    if len(prefixed_adverbs) == 1:
                        word = prefixed_adverbs[0]
                        if adverb:
                            raise ParseError("You can't do that both %s and %s." % (adverb, word))
                        adverb = word
                        arg_words.append(word)
                        previous_word = word
                        continue
                    elif len(prefixed_adverbs) > 1:
                        raise ParseError("What adverb did you mean: %s?" % lang.join(prefixed_adverbs, conj="or"))

                if external_verb:
                    arg_words.append(word)
                    unrecognized_words.append(word)
                else:
                    if word in verbs.VERBS or word in verbs.ACTION_QUALIFIERS or word in verbs.BODY_PARTS:
                        # in case of a misplaced verb, qualifier or bodypart give a little more specific error
                        raise ParseError("The word %s makes no sense at that location." % word)
                    else:
                        # no idea what the user typed, generic error
                        errormsg = "It's not clear what you mean by '%s'." % word
                        if word[0].isupper():
                            errormsg += " Just type in lowercase ('%s')." % word.lower()
                        raise ParseError(errormsg)
            previous_word = word

        message_text = " ".join(message)
        if not verb:
            # This is interesting: there's no verb.
            # but maybe the thing the user typed refers to an object or creature.
            # In that case, set the verb to that object's default verb.
            if len(who_list) == 1:
                verb = getattr(who_list[0], "default_verb", "examine")
            else:
                raise UnknownVerbError(words[0], words, qualifier)
        return ParseResult(verb or "", who_info=who_info, who_list=who_list,
                           adverb=adverb, message=message_text, bodypart=bodypart, qualifier=qualifier,
                           args=arg_words, unrecognized=unrecognized_words, unparsed=unparsed)

    def remember_previous_parse(self, parsed: ParseResult) -> None:
        self.__previously_parsed = parsed

    def match_previously_parsed(self, player: Living, pronoun: str) -> List[Tuple[MudObject, str]]:
        """
        Try to connect the pronoun (it, him, her, them) to a previously parsed item/living.
        Returns a list of (who, replacement-name) tuples.
        The reason we return a replacement-name is that the parser can replace the
        pronoun by the proper name that would otherwise have been used in that place.
        """
        if pronoun == "them":
            # plural (any item/living qualifies)
            matches = list(self.__previously_parsed.who_info)
            for who in matches:
                if not player.search_item(who.name) and who not in player.location.livings:
                    raise ParseError("%s is no longer around." % lang.capital(who.subjective))
            if matches:
                return [(who, who.name) for who in matches]
            else:
                raise ParseError("It is not clear who or what you're referring to.")
        for who in self.__previously_parsed.who_info:
            # first see if it is an exit
            if pronoun == "it":
                for direction, exit in player.location.exits.items():
                    if exit is who:
                        return [(who, direction)]
            # not an exit, try an item or a living
            if pronoun == who.objective:
                if player.search_item(who.name) or who in player.location.livings:
                    return [(who, who.name)]
                raise ParseError("%s is no longer around." % lang.capital(who.subjective))
        raise ParseError("It is not clear who or what you're referring to.")

    @staticmethod
    def poss_replacement(actor: Living, target: Optional[MudObject], observer: Optional[Living]) -> str:
        """determines what word to use for a POSS"""
        if target is actor:
            if actor is observer:
                return "your own"  # your own foot
            else:
                return actor.possessive + " own"  # his own foot
        else:
            if target is observer:
                return "your"  # your foot
            elif target:
                return lang.possessive(target.title)
            else:
                raise TaleError("cannot determine POSS for None target")

    def spacify(self, string: str) -> str:
        """returns string prefixed with a space, if it has contents. If it is empty, prefix nothing"""
        return " " + string.lstrip(" \t") if string else ""

    def who_replacement(self, actor: Living, target: MudObject, observer: Optional[Living]) -> str:
        """determines what word to use for a WHO"""
        if target is actor:
            if actor is observer:
                return "yourself"  # you kick yourself
            else:
                return actor.objective + "self"  # ... kicks himself
        else:
            if target is observer:
                return "you"  # ... kicks you
            else:
                return target.title  # ... kicks ...

    def check_person(self, action: str, parsed: ParseResult) -> bool:
        if not parsed.who_info and ("\nWHO" in action or "\nPOSS" in action):
            return False
        return True

    def check_name_with_spaces(self, words: Sequence[str], startindex: int, all_livings: Mapping[str, Living],
                               all_items: Mapping[str, MudObject], all_exits: Mapping[str, MudObject]) \
        -> Tuple[Optional[MudObject], str, int]:
        """
        Searches for a name used in sentence where the name consists of multiple words (separated by space).
        You provide the sequence of words that forms the sentence and the startindex of the first word
        to start searching.
        Searching is done in the livings, items, and exits dictionaries, in that order.
        The name being searched for is gradually extended with more words until a match is found.
        The return tuple is (matched_object, matched_name, number of words used in match).
        If nothing is found, a tuple (None, None, 0) is returned.
        """
        wordcount = 1
        name = words[startindex]
        try:
            while wordcount < 6:  # an upper bound for the number of words to concatenate to avoid long runtime
                if name in all_livings:
                    return all_livings[name], name, wordcount
                if name in all_items:
                    return all_items[name], name, wordcount
                if name in all_exits:
                    return all_exits[name], name, wordcount
                name = name + " " + words[startindex + wordcount]
                wordcount += 1
        except IndexError:
            pass
        return None, "", 0
