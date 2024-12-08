'''
Recipe data representations.

Modified from code written by Ellen Liao (@ellliao) for Project 2.
'''

from fractions import Fraction

from util import nlp, NounType, str_to_fraction, fraction_to_str

class Ingredient:
    '''Struct holding ingredient information'''

    def __init__(self, name: str = '',
                 quantity: Fraction | None = None,
                 unit: str | None = None):
        self.name = name
        '''Name of the ingredient, e.g. salt'''
        self.quantity = quantity
        '''Quantity of the ingredient, e.g. 1/2'''
        self.unit = unit
        '''Unit of the ingredient, e.g. tsp'''
        self.descriptors: str = ''
        '''Descriptions, e.g. extra-virgin'''
        self.preparation: str = ''
        '''Preparation instructions, e.g. chopped'''
        self.used: set[tuple[int, int]] = set()
        '''Set of (step, step.ingr) indices where this ingredient is used'''

    def __str__(self):
        # return f"{self.quantity}|{self.unit}|{self.descriptors}|{self.name}|{self.preparation}"
        return ''.join([
            fraction_to_str(self.quantity) if self.quantity else '',
            ' ' if self.quantity else '',
            self.unit if self.unit else '',
            ' ' if self.unit else '',
            self.descriptors if self.descriptors else '',
            ' ' if self.descriptors else '',
            self.name,
            ', ' if self.preparation else '',
            self.preparation if self.preparation else ''
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
        i = 0  # token index
        idx = 0  # start char index
        for ind in range(len(doc)):
            if str_to_fraction(doc[ind].text) == Fraction():
                i = ind
                ingr.quantity = str_to_fraction(name[idx:doc[i].idx].strip())
                idx = doc[i].idx
                break

        # Find unit, if available
        parens = 0
        for ind in range(i, len(doc) - 1):
            if doc[ind].text == '(':
                parens += 1
            elif doc[ind].text == ')':
                parens -= 1
            elif parens == 0:
                if NounType.MEASURE in NounType.from_str(doc[ind].text):
                    i = ind + 1
                    ingr.unit = name[idx:doc[i].idx].strip()
                    idx = doc[i].idx
                break
        
        # Find descriptors, if available
        for ind in range(i, len(doc)):
            if doc[ind].pos_ in ['NOUN', 'PROPN']:
                i = ind
                ingr.descriptors = name[idx:doc[i].idx].strip()
                idx = doc[i].idx
                break

        # Find name and check if it's a food item
        is_food = False
        parens = 0
        post_punct = False
        for ind in range(i, len(doc)):
            if doc[ind].text == '(':
                parens += 1
                continue
            elif doc[ind].text == ')':
                parens -= 1
                continue
            elif parens > 0:
                continue
            if (doc[ind].pos_ not in ['NOUN', 'PROPN', 'ADJ'] and \
                doc[ind].dep_ != 'ROOT' and \
                doc[ind].text != ',') or \
                    (post_punct and \
                     (doc[ind].pos_ not in ['NOUN', 'PROPN', 'ADJ'] or \
                      doc[ind].head.i < ind)):
                i = ind
                ingr.name = name[idx:doc[i].idx].strip(' .,;:!-')
                idx = doc[i].idx
                break
            if doc[ind].text == ',':
                post_punct = True
            elif post_punct:
                post_punct = False
            if NounType.FOOD in NounType.from_str(doc[ind].text):
                is_food = True
            if is_food and ind == len(doc) - 1:
                i = ind + 1
                ingr.name = name[idx:].strip(' .,;:!-')
        
        # Find preparation, if available
        if i < len(doc):
            ingr.preparation = name[idx:].strip(' .,;:!-')

        # return ingr
        if is_food:
            return ingr
        return None

class Step:
    '''Struct holding step information'''

    def __init__(self, text: str):
        self.text: str = text
        '''Text associated with the step'''
        self.ingredients: list[Ingredient] = []
        '''List of ingredients used in this step'''
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

    def __str__(self):
        recipe = []
        recipe.append(f'\n{self.title}')
        recipe.append(f'\nIngredients:')
        for ingredient in self.ingredients:
            recipe.append(f'- {ingredient}')
        recipe.append(f'\nSteps:')
        for i, step in enumerate(self.steps, 1):
            recipe.append(f'{i}. {step.text}')
        return f'\n'.join(recipe)
