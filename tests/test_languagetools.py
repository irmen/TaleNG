"""
Unittests for languagetools

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import pytest
import tale_ng.lang as lang


def test_a():
    assert lang.a("") == ""
    assert lang.a("e") == "an e"
    assert lang.a("q") == "a q"
    assert lang.a("house") == "a house"
    assert lang.a("a house") == "a house"
    assert lang.a("House") == "a House"
    assert lang.a("egg") == "an egg"
    assert lang.a("an egg") == "an egg"
    assert lang.a("An egg") == "An egg"
    assert lang.a("the egg") == "the egg"
    assert lang.a("The egg") == "The egg"
    assert lang.a("university") == "a university"
    assert lang.a("university magazine") == "a university magazine"
    assert lang.a("user") == "a user"
    assert lang.a("unforgettable experience") == "an unforgettable experience"
    assert lang.a("umbrella") == "an umbrella"
    assert lang.a("history") == "a history"
    assert lang.a("hour") == "an hour"
    assert lang.a("honour") == "an honour"
    assert lang.a("historic day") == "a historic day"
    assert lang.A("user") == "A user"
    assert lang.A("hour") == "An hour"
    assert lang.a("uno") == "an uno"
    assert lang.a("hourglass") == "an hourglass"
    assert lang.a("unicycle") == "a unicycle"
    assert lang.a("universe") == "a universe"
    assert lang.a("honest mistake") == "an honest mistake"
    assert lang.a("yard") == "a yard"
    assert lang.a("yves") == "a yves"
    assert lang.a("igloo") == "an igloo"
    assert lang.a("yard") == "a yard"
    assert lang.a("YARD") == "a YARD"
    assert lang.A("YARD") == "A YARD"
    assert lang.a("ycleped") == "an ycleped"
    assert lang.a("YCLEPED") == "a YCLEPED"
    assert lang.a("yttric") == "an yttric"
    assert lang.a("yggdrasil") == "an yggdrasil"


def test_a_capital():
    assert lang.A("") == ""
    assert lang.A("e") == "An e"
    assert lang.A("q") == "A q"
    assert lang.A("house") == "A house"
    assert lang.A("a house") == "A house"
    assert lang.A("House") == "A House"
    assert lang.A("egg") == "An egg"
    assert lang.A("an egg") == "An egg"
    assert lang.A("An egg") == "An egg"
    assert lang.A("the egg") == "The egg"
    assert lang.A("The egg") == "The egg"


def test_a_exceptions():
    assert lang.a("some egg") == "some egg"
    assert lang.a("someone's egg") == "someone's egg"
    assert lang.A("someone's egg") == "Someone's egg"
    assert lang.A("Someone's egg") == "Someone's egg"
    assert lang.a("five eggs") == "five eggs"
    assert lang.a("fifth egg") == "the fifth egg"
    assert lang.a("seventieth egg") == "the seventieth egg"
    assert lang.A("seventieth egg") == "The seventieth egg"


def test_fullstop():
    assert lang.fullstop("a") == "a."
    assert lang.fullstop("a ") == "a."
    assert lang.fullstop("a.") == "a."
    assert lang.fullstop("a?") == "a?"
    assert lang.fullstop("a!") == "a!"
    assert lang.fullstop("a", punct=";") == "a;"


def test_join():
    assert lang.join([]) == ""
    assert lang.join(x for x in []) == ""
    assert lang.join(["a"]) == "a"
    assert lang.join(["a", "b"]) == "a and b"
    assert lang.join(x for x in ["a", "b"]) == "a and b"
    assert lang.join(["a", "b", "c"]) == "a, b, and c"
    assert lang.join(["a", "b", "c"], conj="or") == "a, b, or c"
    assert lang.join(["c", "b", "a"], conj="or") == "c, b, or a"


def test_join_multi():
    assert lang.join(["bike"] * 2) == "two bikes"
    assert lang.join(["a bike"] * 2) == "two bikes"
    assert lang.join(["a bike"] * 3) == "three bikes"
    assert lang.join(["bike"] * 3, group_multi=False) == "bike, bike, and bike"
    assert lang.join(["key"] * 12) == "twelve keys"
    assert lang.join(["a key"] * 12) == "twelve keys"
    assert lang.join(["key", "bike"] * 2) == "two keys and two bikes"
    assert lang.join(["bike", "key"] * 2) == "two bikes and two keys"
    assert lang.join(["a bike", "an apple"] * 2) == "two bikes and two apples"
    assert lang.join(["bike", "key", "mouse"] * 2) == "two bikes, two keys, and two mice"
    assert lang.join(["a bike", "an apple", "the mouse"] * 2) == "two bikes, two apples, and two mice"
    assert lang.join(["apple", "apple", "bike", "key", "key"]) == "two apples, bike, and two keys"
    assert lang.join(["apple", "apple", "key", "bike", "key"]) == "two apples, two keys, and bike"
    assert lang.join(["an apple", "an apple", "a key", "a bike", "a key"]) == "two apples, two keys, and a bike"
    assert lang.join(["an apple", "an apple", "the key", "an apple", "someone", "the key"]) == "three apples, two keys, and someone"
    assert lang.join(["key", "bike"] * 2, group_multi=False) == "key, bike, key, and bike"


def test_possessive():
    assert lang.possessive_letter("") == ""
    assert lang.possessive_letter("julie") == "'s"
    assert lang.possessive_letter("tess") == "'s"
    assert lang.possessive_letter("your own") == ""
    assert lang.possessive_letter("") == ""
    assert lang.possessive("julie") == "julie's"
    assert lang.possessive("tess") == "tess's"
    assert lang.possessive("your own") == "your own"


def test_capital():
    assert lang.capital("") == ""
    assert lang.capital("x") == "X"
    assert lang.capital("xyz AbC") == "Xyz AbC"


def test_split():
    assert lang.split("") == []
    assert lang.split("a") == ["a"]
    assert lang.split("a b c") == ["a", "b", "c"]
    assert lang.split(" a   b  c    ") == ["a", "b", "c"]
    assert lang.split("a 'b c d' e") == ["a", "b c d", "e"]
    assert lang.split("a  '  b c d '   e") == ["a", "b c d", "e"]
    assert lang.split("a 'b c d' e \"f g   \" h") == ["a", "b c d", "e", "f g", "h"]
    assert lang.split("a  '  b c \"hi!\" d '   e") == ["a", "b c \"hi!\" d", "e"]
    assert lang.split("a 'b") == ["a", "'b"]
    assert lang.split("a \"b") == ["a", "\"b"]


def test_fullverb():
    assert lang.fullverb("say") == "saying"
    assert lang.fullverb("ski") == "skiing"
    assert lang.fullverb("poke") == "poking"
    assert lang.fullverb("polka") == "polkaing"
    assert lang.fullverb("snivel") == "sniveling"
    assert lang.fullverb("fart") == "farting"
    assert lang.fullverb("try") == "trying"


def test_numberspell():
    assert lang.spell_number(0) == "zero"
    assert lang.spell_number(1) == "one"
    assert lang.spell_number(20) == "twenty"
    assert lang.spell_number(45) == "forty-five"
    assert lang.spell_number(70) == "seventy"
    assert lang.spell_number(-45) == "minus forty-five"
    assert lang.spell_number(99) == "ninety-nine"
    assert lang.spell_number(-99) == "minus ninety-nine"
    assert lang.spell_number(100) == "100"
    assert lang.spell_number(-100) == "minus 100"
    assert lang.spell_number(-1) == "minus one"
    assert lang.spell_number(-20) == "minus twenty"
    assert lang.spell_number(2.5) == "two and a half"
    assert lang.spell_number(2.25) == "two and a quarter"
    assert lang.spell_number(2.75) == "two and three quarters"
    assert lang.spell_number(-2.75) == "minus two and three quarters"
    assert lang.spell_number(99.5) == "ninety-nine and a half"
    assert lang.spell_number(-99.5) == "minus ninety-nine and a half"
    assert lang.spell_number(1.234) == "1.234"
    assert lang.spell_number(2.994) == "2.994"
    assert lang.spell_number(2.996) == "about three"
    assert lang.spell_number(3.004) == "about three"
    assert lang.spell_number(3.004) == "about three"
    assert lang.spell_number(99.004) == "about ninety-nine"
    assert lang.spell_number(99.996) == "about 100"
    assert lang.spell_number(-2.996) == "about minus three"
    assert lang.spell_number(-3.004) == "about minus three"
    assert lang.spell_number(-99.004) == "about minus ninety-nine"
    assert lang.spell_number(-3.006) == "-3.006"


def test_ordinal():
    assert lang.ordinal(0) == "0th"
    assert lang.ordinal(1) == "1st"
    assert lang.ordinal(1.4) == "1st"
    assert lang.ordinal(2) == "2nd"
    assert lang.ordinal(3) == "3rd"
    assert lang.ordinal(4) == "4th"
    assert lang.ordinal(-2) == "-2nd"
    assert lang.ordinal(10) == "10th"
    assert lang.ordinal(11) == "11th"
    assert lang.ordinal(12) == "12th"
    assert lang.ordinal(13) == "13th"
    assert lang.ordinal(14) == "14th"
    assert lang.ordinal(20) == "20th"
    assert lang.ordinal(21) == "21st"
    assert lang.ordinal(99) == "99th"
    assert lang.ordinal(100) == "100th"
    assert lang.ordinal(101) == "101st"
    assert lang.ordinal(102) == "102nd"
    assert lang.ordinal(110) == "110th"
    assert lang.ordinal(111) == "111th"
    assert lang.ordinal(123) == "123rd"


def test_spell_ordinal():
    assert lang.spell_ordinal(0) == "zeroth"
    assert lang.spell_ordinal(1) == "first"
    assert lang.spell_ordinal(1.4) == "first"
    assert lang.spell_ordinal(2) == "second"
    assert lang.spell_ordinal(3) == "third"
    assert lang.spell_ordinal(-2) == "minus second"
    assert lang.spell_ordinal(10) == "tenth"
    assert lang.spell_ordinal(11) == "eleventh"
    assert lang.spell_ordinal(20) == "twentieth"
    assert lang.spell_ordinal(21) == "twenty-first"
    assert lang.spell_ordinal(70) == "seventieth"
    assert lang.spell_ordinal(76) == "seventy-sixth"
    assert lang.spell_ordinal(99) == "ninety-ninth"
    assert lang.spell_ordinal(100) == "100th"
    assert lang.spell_ordinal(101) == "101st"


def test_pluralize():
    assert lang.pluralize("car") == "cars"
    assert lang.pluralize("car", amount=0) == "cars"
    assert lang.pluralize("car", amount=1) == "car"
    assert lang.pluralize("box") == "boxes"
    assert lang.pluralize("boss") == "bosses"
    assert lang.pluralize("bush") == "bushes"
    assert lang.pluralize("church") == "churches"
    assert lang.pluralize("gas") == "gases"
    assert lang.pluralize("quiz") == "quizzes"
    assert lang.pluralize("volcano") == "volcanoes"
    assert lang.pluralize("photo") == "photos"
    assert lang.pluralize("piano") == "pianos"
    assert lang.pluralize("lady") == "ladies"
    assert lang.pluralize("crisis") == "crises"
    assert lang.pluralize("wolf") == "wolves"
    assert lang.pluralize("lady") == "ladies"
    assert lang.pluralize("key") == "keys"
    assert lang.pluralize("homy") == "homies"
    assert lang.pluralize("buoy") == "buoys"


def test_yesno():
    assert lang.yesno("y")
    assert lang.yesno("Yes")
    assert lang.yesno("SURE")
    assert not lang.yesno("n")
    assert not lang.yesno("NO")
    assert not lang.yesno("Hell No")
    with pytest.raises(ValueError):
        lang.yesno(None)
    with pytest.raises(ValueError):
        lang.yesno("")
    with pytest.raises(ValueError):
        lang.yesno("i dunno")


def test_gender():
    assert lang.validate_gender("f") == "f"
    assert lang.validate_gender("m") == "m"
    assert lang.validate_gender("n") == "n"
    assert lang.validate_gender("F") == "f"
    assert lang.validate_gender("Female") == "female"
    assert lang.validate_gender("MALE") == "male"
    with pytest.raises(ValueError):
        lang.validate_gender(None)
    with pytest.raises(ValueError):
        lang.validate_gender("")
    with pytest.raises(ValueError):
        lang.validate_gender("nope")


def test_gender_mf():
    assert lang.validate_gender_mf("f") == "f"
    assert lang.validate_gender_mf("m") == "m"
    assert lang.validate_gender_mf("F") == "f"
    assert lang.validate_gender_mf("Female") == "female"
    assert lang.validate_gender_mf("MALE") == "male"
    with pytest.raises(ValueError):
        assert lang.validate_gender_mf("n") == "n"
    with pytest.raises(ValueError):
        lang.validate_gender_mf(None)
    with pytest.raises(ValueError):
        lang.validate_gender_mf("")
    with pytest.raises(ValueError):
        lang.validate_gender_mf("nope")
