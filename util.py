'''
Utility enums and functions for recipe parsing and display.

Modified from code written by Ellen Liao (@ellliao) for Project 2.
'''

import re
import spacy
import unicodedata

from enum import Enum, auto
from fractions import Fraction
from nltk.corpus import wordnet as wn

#############
# VARIABLES #
#############

nlp = spacy.load("en_core_web_sm")
'''SpaCy model (small)'''

unit_dict = dict([
    ("ounce", r'(?<=\b|-)oz(?:\.|\b)'),
    ("pound", r'(?<=\b|-)lb(?:\.|s\b|\b)'),
    ("gram", r'(?<=\b|-)g(?:\.|\b)'),
    ("kilogram", r'(?<=\b|-)kg(?:\.|s\b|\b)'),
    ("teaspoon", r'(?<=\b|-)tsp(?:\.|s\b|\b)'),
    ("tablespoon", r'(?<=\b|-)tbsp(?:\.|s\b|\b)'),
    ("gallon", r'(?<=\b|-)gal(?:\.|s\b|\b)'),
    ("milliliter", r'(?<=\b|-)ml(?:\.|\b)'),
    ("liter", r'(?<=\b|-)l(?:\.|\b)')
])
'''Dict of common unit abbreviation patterns'''

#########
# ENUMS #
#########

class RecipeSource(Enum):
    '''Enum of recipe sources'''
    UNKNOWN = auto()
    ALLRECIPES = auto()

    @classmethod
    def from_url(cls, url: str):
        if re.findall(r'allrecipes\.com/recipe/.*', url):
            return RecipeSource.ALLRECIPES
        return RecipeSource.UNKNOWN

class NounType(Enum):
    '''Enum of relevant noun types'''
    UNKNOWN = auto()
    FOOD = auto()
    MEASURE = auto()
    TEMPERATURE = auto()
    TOOL = auto()

    @classmethod
    def from_str(cls, noun: str):
        ntypes = set()
        sets = wn.synsets(noun, wn.NOUN)
        for s in sets:
            for ss in s.hypernym_paths():
                if wn.synset('kitchen_utensil.n.01') in ss or \
                    wn.synset('kitchen_appliance.n.01') in ss or \
                    wn.synset('container.n.01') in ss:
                    ntypes.add(NounType.TOOL)
                elif wn.synset('measure.n.02') in ss or \
                    wn.synset('container.n.01') in ss or \
                    wn.synset('clove.n.03') in ss:
                    ntypes.add(NounType.MEASURE)
                elif wn.synset('food.n.01') in ss or \
                    wn.synset('food.n.02') in ss or \
                    wn.synset('leaven.n.01') in ss:
                    ntypes.add(NounType.FOOD)
                elif wn.synset('temperature.n.01') in ss or \
                    wn.synset('fire.n.03') in ss or \
                    wn.synset('temperature_unit.n.01') in ss:
                    ntypes.add(NounType.TEMPERATURE)
        return ntypes

class VerbType(Enum):
    '''Enum of relevant verb types'''
    UNKNOWN = auto()
    PRIMARY_METHOD = auto()
    OTHER_METHOD = auto()

    @classmethod
    def from_str(cls, verb: str):
        sets = wn.synsets(verb, wn.VERB)
        if verb == 'cook':
            return VerbType.UNKNOWN
        for s in sets:
            for ss in s.hypernym_paths():
                if wn.synset('cook.v.03') in ss:
                    return VerbType.PRIMARY_METHOD
        return VerbType.UNKNOWN

#############
# FUNCTIONS #
#############

def standardize_units(string: str):
    "Un-abbreviate all cooking units in a given string"
    for unit in unit_dict:
        string = re.sub(unit_dict[unit], unit, string, flags=re.IGNORECASE)
    return string

def str_to_fraction(data: str):
    sum = Fraction()
    table = str.maketrans({u'⁄': '/'})
    data = unicodedata.normalize('NFKD', data).translate(table).split()
    for val in data:
        try:
            f = Fraction(val)
            if f.denominator > 1 and f.numerator > 10:
                f = Fraction(f.numerator % 10 + \
                    int(f.numerator / 10) * f.denominator, f.denominator)
            sum += f
        except:
            continue
    return sum

def fraction_to_str(frac: Fraction):
    if frac.denominator == 1:
        return str(frac.numerator)
    elif frac.numerator >= frac.denominator:
        return ' '.join([str(frac.numerator // frac.denominator),
                         str(Fraction(frac.numerator % frac.denominator,
                                      frac.denominator))])
    else:
        return str(frac)