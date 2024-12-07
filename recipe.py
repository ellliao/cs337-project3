'''
Recipe data representations.

Modified from code written by Ellen Liao (@ellliao) for Project 2.
'''

from copy import deepcopy
from fractions import Fraction
from util import nlp, NounType, str_to_fraction, fraction_to_str

class Ingredient:
    '''Struct holding ingredient information'''

    def __init__(self, name: str | None = None,
                 quantity: Fraction | None = None,
                 unit: str | None = None):
        self.name = name
        '''Name of the ingredient, e.g. salt'''
        self.quantity = quantity
        '''Quantity of the ingredient, e.g. 1/2'''
        self.unit = unit
        '''Unit of the ingredient, e.g. tsp'''

    def __str__(self):
        return ''.join([
            fraction_to_str(self.quantity) if self.quantity else '',
            ' ' if self.quantity else '',
            self.unit if self.unit else '',
            ' ' if self.unit else '',
            self.name
        ])
    
    @classmethod
    def from_str(cls, name: str):
        '''
        Creates an Ingredient object from an input string.
        
        Args:
            name (str): The suspected ingredient string.
        
        Returns:
            Ingredient | None: The corresponding Ingredient object, if
                possible. Else, None.
        '''

        ingr = Ingredient()
        doc = nlp(name)

        # Find quantity, if available
        i = 0
        li = 0
        quantity = []
        while i < len(doc) and str_to_fraction(doc[i].text) != Fraction():
            quantity.append(doc[i].text)
            li += len(doc[i].text) + 1
            i += 1
        if quantity:
            ingr.quantity = str_to_fraction(' '.join(quantity))
        else:
            i = 0

        # Find unit, if available
        if i < len(doc) and \
            NounType.MEASURE in NounType.from_str(doc[i].text):
            ingr.unit = doc[i].text
            li += len(doc[i].text) + 1
            i += 1
        
        # Find name and return if a food
        for token in doc[i:]:
            if NounType.FOOD in NounType.from_str(token.text):
                ingr.name = name[li:]
                return ingr

        return None

class Step:
    '''Struct holding step information'''

    def __init__(self, text: str, remaining: list[Ingredient] = None):
        self.text: str = text
        '''Text associated with the step'''
        self.ingredients: list[Ingredient] = []
        '''List of ingredients used in this step'''
        self.remaining: list[Ingredient] = \
            deepcopy(remaining) if remaining else []
        '''Remaining unused ingredients at this step'''
        self.tools: set[str] = set()
        '''Tools mentioned in this step'''
        self.methods: set[str] = set()
        '''Methods mentioned in this step'''
        self.times: list[str] = []
        '''Times mentioned in this step'''
        self.temps: list[str] = []
        '''Temperatures / measures of "doneness" mentioned in this step'''
    
class Recipe:
    '''Struct holding recipe information'''

    def __init__(self):
        self.title: str = ""
        '''Title of the recipe'''
        self.ingredients: list[Ingredient] = []
        '''List of ingredients used in the recipe'''
        self.tools: set[str] = set()
        '''Set of tools used in the recipe'''
        self.methods: set[str] = set()
        '''Set of methods used in the recipe'''
        self.steps: list[Step] = []
        '''List of recipe steps'''
        self.other: dict[str, str] = {}
        '''Other miscellaneous recipe information'''
