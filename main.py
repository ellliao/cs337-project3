import urllib.request
import re
import json

from recipe import Ingredient, Recipe, Step
from util import nlp, RecipeSource, VerbType

# Global Recipe object to store parsed recipe information
recipe = Recipe()

# Common cooking tools to identify in recipe steps
COMMON_TOOLS = [
    "pan", "skillet", "grater", "whisk", "knife", "spatula", "bowl", 
    "oven", "mixer", "peeler", "measuring cup", "blender", "microwave", 
    "cutting board", "tongs", "pressure cooker", "baking sheet"
]

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

# Example usage
def main():
    url = input("Enter recipe URL: ")
    html = fetch_url(url)
    if html and parse_recipe(html):
        print("Recipe parsed successfully!")
        print(f"Title: {recipe.title}")
        print("\nIngredients:")
        for ingredient in recipe.ingredients:
            print(f"- {ingredient}")
        print("\nSteps:")
        for i, step in enumerate(recipe.steps, 1):
            print(f"{i}. {step.text}")

        # The following are metadata that should not be shown to the user
        print("\nTools:")
        print(recipe.tools)
        print("\nMethods:")
        print(recipe.methods)
    else:
        print("Failed to parse recipe.")

if __name__ == "__main__":
    main()