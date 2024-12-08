from copy import copy
import urllib.request
import re
import json
from fractions import Fraction

from recipe import Ingredient, Recipe, Step
from util import nlp, RecipeSource, VerbType, Transformation

# Global Recipe object to store parsed recipe information
recipe = Recipe()

# Common cooking tools to identify in recipe steps
COMMON_TOOLS = [
    "pan",
    "saucepan",
    "skillet",
    "grater",
    "whisk",
    "knife",
    "spatula",
    "bowl",
    "oven",
    "mixer",
    "peeler",
    "measuring cup",
    "blender",
    "microwave",
    "cutting board",
    "tongs",
    "pressure cooker",
    "baking sheet",
    "baking dish",
    "baking tray",
    "pot",
    "wok",
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

HEALTHY_SUBSTITUTIONS = {
    "butter": "applesauce",
    "sugar": "honey",
    "heavy cream": "Greek yogurt",
    "salt": "herbs",
    "bacon": "turkey bacon",
    "beef": "lean turkey",
    "frying": "baking",
}

UNHEALTHY_SUBSTITUTIONS = {
    "applesauce": "butter",
    "honey": "sugar",
    "Greek yogurt": "heavy cream",
    "herbs": "salt",
    "turkey bacon": "bacon",
    "lean turkey": "beef",
    "baking": "frying",
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
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL
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
        recipe.other["description"] = (
            des.group(1) if des else "No description available"
        )

        # Extract ingredients and steps
        recipe.ingredients = [
            Ingredient.from_str(ingr) for ingr in jsondata.get("recipeIngredient", [])
        ]
        recipe.steps = [
            Step(step["text"]) for step in jsondata.get("recipeInstructions", [])
        ]

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
            if sentence[0].pos_ in ["NOUN", "PROPN"]:
                verbs.append(sentence[0].lemma_.lower())
        for verb in verbs:
            if VerbType.from_str(verb) == VerbType.PRIMARY_METHOD:
                step.methods.add(verb)
                recipe.methods.add(verb)
    return None


def handle_transformation(recipe: Recipe, trans: Transformation):
    """Performs a transformation on a recipe, displays it, and saves it."""
    sorted_substitutions = {}

    def quantity_change(ingredients, factor):
        for ingredient in ingredients:
            if ingredient is not None and ingredient.quantity:
                if isinstance(factor, float):
                    factor = Fraction(factor).limit_denominator()
                ingredient.quantity *= factor

    def get_substitutions(trans: Transformation) -> dict[str, str]:
        match trans:
            case Transformation.TO_VEGETARIAN:
                return VEGETARIAN_SUBSTITUTIONS
            case Transformation.FROM_VEGETARIAN:
                return NON_VEGETARIAN_SUBSTITUTIONS
            case Transformation.TO_HEALTHY:
                return HEALTHY_SUBSTITUTIONS
            case Transformation.FROM_UNHEALTHY:
                return UNHEALTHY_SUBSTITUTIONS

    if trans not in [Transformation.DOUBLE, Transformation.HALF]:
        substitutions = get_substitutions(trans)
        sorted_substitutions.update(
            dict(sorted(substitutions.items(), key=lambda x: len(x[0]), reverse=True))
        )

    if trans in [Transformation.DOUBLE, Transformation.HALF]:
        if trans == Transformation.DOUBLE:
            quantity_change(recipe.ingredients, 2)
        elif trans == Transformation.HALF:
            quantity_change(recipe.ingredients, 0.5)

    def clean_verbs(text):
        verbs = r"\b(deveined|debearded|disjointed|skinned|boned|trimmed)\b"
        return re.sub(verbs, "", text, flags=re.IGNORECASE).strip()

    def clean_trailing_and(text):
        return re.sub(r"\b(and|,)\s*$", "", text, flags=re.IGNORECASE).strip()

    def substitute_text(text):
        new_text = text
        for original, substitute in sorted_substitutions.items():
            pattern = rf"\b{re.escape(original)}\b"
            if re.search(pattern, new_text, flags=re.IGNORECASE):
                new_text = re.sub(pattern, substitute, new_text, flags=re.IGNORECASE)
                new_text = clean_verbs(new_text)
        new_text = clean_trailing_and(new_text)
        new_text = re.sub(r"\s+", " ", new_text).strip()
        return new_text

    def display_transformed(transformed: Recipe, trans: Transformation):
        """Displays and saves a transformed recipe."""

        transformed.title = " ".join([str(trans), transformed.title])
        print(transformed)

        fname = re.sub(r"\W", "_", transformed.title.lower())
        with open(f"{fname}.txt", "w", encoding="utf-8") as file:
            print(f"Transformation: {trans}", file=file)
            print("\n---------------------", file=file)
            print(recipe, file=file)
            print("\n---------------------", file=file)
            print(transformed, file=file)

        print(f"\nRecipe saved to {fname}.txt!")

    transformed_ingredients = []
    for ingredient in recipe.ingredients:
        if ingredient and ingredient.name:
            transformed_ingredient = copy(ingredient)
            transformed_ingredient.name = substitute_text(ingredient.name)
            transformed_ingredients.append(transformed_ingredient)

    transformed_steps = []
    for step in recipe.steps:
        transformed_step = copy(step)
        transformed_step.text = substitute_text(step.text)
        transformed_steps.append(transformed_step)

    transformed_recipe = copy(recipe)
    transformed_recipe.ingredients = transformed_ingredients
    transformed_recipe.steps = transformed_steps

    display_transformed(transformed_recipe, trans)


# https://www.allrecipes.com/recipe/12728/paella-i/
# https://www.allrecipes.com/recipe/72508/the-best-vegetarian-chili-in-the-world/


# Example usage
def main():
    url = input("Enter recipe URL: ")
    html = fetch_url(url)
    if html and parse_recipe(html):
        print("Recipe parsed successfully!")
        print(recipe)

        while True:
            print("\nWhat would you like to do?")
            i = 1
            for trans in Transformation:
                print(f"{i}. Transform to {trans}")
                i += 1
            print(f"{i}. Exit")

            choice = input("Enter your choice: ")

            try:
                choice = int(choice)
            except:
                choice

            if choice in [t.value for t in Transformation]:
                trans = Transformation(choice)
                print(f"\nTransforming to {trans}...")
                handle_transformation(recipe, trans)

            elif choice == len(Transformation) + 1:
                print("Exiting the transformation menu")
                break

            else:
                print("Invalid choice, try again.")
    else:
        print("Failed to parse recipe.")


if __name__ == "__main__":
    main()
