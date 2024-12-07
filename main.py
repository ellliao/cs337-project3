import urllib.request
import re
import json

from recipe import Ingredient, Recipe, Step
from util import nlp, RecipeSource, VerbType

# Global Recipe object to store parsed recipe information
recipe = Recipe()

# Common cooking tools to identify in recipe steps
COMMON_TOOLS = [
    "pan", "saucepan", "skillet", "grater", "whisk", "knife", "spatula",
    "bowl", "oven", "mixer", "peeler", "measuring cup", "blender", "microwave", 
    "cutting board", "tongs", "pressure cooker", "baking sheet", "baking dish",
    "baking tray", "pot", "wok"
]

VEGETARIAN_SUBSTITUTIONS = {
    "chicken broth": "vegetable broth",
    "chicken": "extra-firm tofu, cubed",
    "sausage": "plant-based sausage",
    "beef": "mushrooms",
    "pork": "tempeh",
    "fish": "cauliflower steak",
    "gelatin": "agar-agar",
    "bacon": "coconut bacon",
    "meatballs": "lentil balls",
    "shrimp": "jackfruit",
    "mussels": "mushrooms",
    "squid": "king oyster mushroom",
    "bone": "", 
    "breast": "", 
    "thigh": "",
    "drumstick": "",
    "wing": "",
    "rib": "",
    "cutlet": "",
}

NON_VEGETARIAN_SUBSTITUTIONS = {
    "vegetable broth": "chicken broth",
    "tofu": "chicken",
    "black beans": "beef",
    "kidney beans": "pork",
    "zucchini slices": "fish",
    "agar": "gelatin",
    "tempeh": "bacon",
    "beans": "meatballs",
    "chickpeas": "shrimp",
    "plant-based": "",
    "vegetarian": "",
    "portobello mushrooms": "steak",
    "crumbled tofu": "ground beef",
}

def fetch_url(url):
    """
    Fetch the HTML content of a given URL.
    
    Args:
        url (str): The URL to fetch
    
    Returns:
        str: HTML content of the page or empty string if error occurs
    """
    try:
        # Remove any trailing characters from Slack
        url = url.strip(">")

        # Check that this is an Allrecipes URL
        if RecipeSource.from_url(url) == RecipeSource.UNKNOWN:
            print(f"Error fetching URL: {url} is from an unsupported site.")
            return ""
        
        # Open and read the URL
        response = urllib.request.urlopen(url)
        data = response.read()
        html = data.decode("utf-8")
        return html
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return ""

def parse_recipe(html):
    """
    Parse recipe information from HTML using JSON-LD and regex.
    
    Args:
        html (str): HTML content of the recipe page
    
    Returns:
        bool: True if recipe parsing is successful, False otherwise
    """
    # Extract title
    title = re.search(r"<title>(.*?)</title>", html)
    
    # Find JSON-LD script
    findjson = re.search(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', 
        html, 
        re.DOTALL
    )
    
    if not findjson:
        print("JSON-LD not found in the HTML.")
        return False
    
    try:
        # Parse JSON-LD data
        jsondata = json.loads(findjson.group(1))
        
        # Handle potential list of JSON objects
        if isinstance(jsondata, list):
            jsondata = jsondata[0] if jsondata else {}
        
        # Populate recipe
        recipe.title = title.group(1) if title else "Unknown Title"
        
        # Extract description
        des = re.search(r'<meta name="description" content="(.*?)"', html)
        recipe.other["description"] = des.group(1) if des else "No description available"
        
        # Extract ingredients and steps
        recipe.ingredients = [Ingredient.from_str(ingr) for ingr in jsondata.get("recipeIngredient", [])]
        recipe.steps = [Step(step["text"]) for step in jsondata.get("recipeInstructions", [])]
        
        # Identify and update cooking methods
        update_cooking_methods()
        
        # Identify tools used in the recipe
        for step in recipe.steps:
            for tool in COMMON_TOOLS:
                if re.search(rf"\b{tool}\b", step.text, re.IGNORECASE):
                    step.tools.add(tool)
                    recipe.tools.add(tool)
        
        return True
    
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return False

def update_cooking_methods():
    """
    Identify cooking methods used in the recipe steps using spaCy and save to
    the Step objects and the Recipe.
    
    Args:
        None
    
    Returns:
        None
    """
    recipe.methods = set()
    for step in recipe.steps:
        doc = nlp(step.text)
        verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
        for sentence in doc.sents:
            if sentence[0].pos_ in ['NOUN', 'PROPN']:
                verbs.append(sentence[0].lemma_.lower())
        for verb in verbs:
            if VerbType.from_str(verb) == VerbType.PRIMARY_METHOD:
                step.methods.add(verb)
                recipe.methods.add(verb)
    return None

    
def to_from_vegetarian(recipe, to_vegetarian=True):
    substitutions = VEGETARIAN_SUBSTITUTIONS if to_vegetarian else NON_VEGETARIAN_SUBSTITUTIONS
    sorted_substitutions = dict(sorted(substitutions.items(), key=lambda x: len(x[0]), reverse=True))

    def clean_verbs(text):
        verbs = r'\b(deveined|debearded|disjointed|skinned|boned|trimmed)\b'
        return re.sub(verbs, '', text, flags=re.IGNORECASE).strip()

    def clean_trailing_and(text):
        return re.sub(r'\b(and|,)\s*$', '', text, flags=re.IGNORECASE).strip()

    def substitute_text(text):
        new_text = text
        for original, substitute in sorted_substitutions.items():
            pattern = rf'\b{re.escape(original)}\b'
            if re.search(pattern, new_text, flags=re.IGNORECASE):
                new_text = re.sub(pattern, substitute, new_text, flags=re.IGNORECASE)
                new_text = clean_verbs(new_text)
        new_text = clean_trailing_and(new_text)
        new_text = re.sub(r'\s+', ' ', new_text).strip()
        return new_text

    transformed_ingredients = []
    for ingredient in recipe.ingredients:
        if ingredient and ingredient.name:  
            transformed_name = substitute_text(ingredient.name)
            transformed_ingredients.append(Ingredient(
                name=transformed_name,
                quantity=ingredient.quantity,
                unit=ingredient.unit
            ))

    transformed_steps = []
    for step in recipe.steps:
        transformed_text = substitute_text(step.text)
        transformed_step = Step(
            text=transformed_text
        )
        transformed_step.ingredients = step.ingredients
        transformed_step.tools = step.tools
        transformed_step.methods = step.methods
        transformed_step.times = step.times
        transformed_step.temps = step.temps
        transformed_steps.append(transformed_step)

    transformed_recipe = Recipe()
    transformed_recipe.title = recipe.title
    transformed_recipe.ingredients = transformed_ingredients
    transformed_recipe.steps = transformed_steps
    transformed_recipe.tools = recipe.tools
    transformed_recipe.methods = recipe.methods
    transformed_recipe.other = recipe.other

    return transformed_recipe

# https://www.allrecipes.com/recipe/12728/paella-i/
# https://www.allrecipes.com/recipe/72508/the-best-vegetarian-chili-in-the-world/


def display_transformed(transformed: Recipe, transformation: str):
    '''Displays and saves a transformed recipe.'''
    
    transformed.title = ' '.join([transformation, transformed.title])
    print(transformed)

    fname = transformed.title.lower().replace(' ', '_')
    with open(f'{fname}.txt', 'w', encoding='utf-8') as file:
        print(f'Transformation: {transformation}', file=file)
        print('\n---------------------', file=file)
        print(recipe, file=file)
        print('\n---------------------', file=file)
        print(transformed, file=file)
    
    print(f'\nRecipe saved to {fname}.txt!')


# Example usage
def main():
    url = input("Enter recipe URL: ")
    html = fetch_url(url)
    if html and parse_recipe(html):
        print("Recipe parsed successfully!")
        print(recipe)

        # The following are metadata that should not be shown to the user
        print("\nTools:")
        print(recipe.tools)
        print("\nMethods:")
        print(recipe.methods)


        while True:
            print("\nWhat would you like to do?")
            print("1. Transform to Vegetarian")
            print("2. Transform to Non-Vegetarian")
            print("3. Exit")
            
            choice = input("Enter your choice: ")

            if choice == "1":
                print("\nTransforming to Vegetarian...")
                vegetarian_recipe = to_from_vegetarian(recipe, to_vegetarian=True)
                display_transformed(vegetarian_recipe, "Vegetarian")

            elif choice == "2":
                print("\nTransforming to Non-Vegetarian...")
                non_vegetarian_recipe = to_from_vegetarian(recipe, to_vegetarian=False)
                display_transformed(non_vegetarian_recipe, "Non-Vegetarian")

            elif choice == "3":
                print("Exiting the transformation menu")
                break

            else:
                print("Invalid choice, try again.")
    else:
        print("Failed to parse recipe.")

if __name__ == "__main__":
    main()