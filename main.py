import urllib.request
import re
import json
import spacy

# Global recipe dictionary to store parsed recipe information
recipe = {
    "title": "",
    "description": "",
    "ingredients": [],
    "steps": [],
    "methods": [],
}

# Common cooking tools to identify in recipe steps
COMMON_TOOLS = [
    "pan", "skillet", "grater", "whisk", "knife", "spatula", "bowl", 
    "oven", "mixer", "peeler", "measuring cup", "blender", "microwave", 
    "cutting board", "tongs", "pressure cooker", "baking sheet"
]

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

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
        
        # Populate recipe dictionary
        recipe["title"] = title.group(1) if title else "Unknown Title"
        
        # Extract description
        des = re.search(r'<meta name="description" content="(.*?)"', html)
        recipe["description"] = des.group(1) if des else "No description available"
        
        # Extract ingredients and steps
        recipe["ingredients"] = jsondata.get("recipeIngredient", [])
        recipe["steps"] = [step["text"] for step in jsondata.get("recipeInstructions", [])]
        
        # Identify cooking methods
        recipe["methods"] = cooking_methods(recipe["steps"])
        
        # Identify tools used in the recipe
        tools_found = set()
        for step in recipe["steps"]:
            for tool in COMMON_TOOLS:
                if re.search(rf"\b{tool}\b", step, re.IGNORECASE):
                    tools_found.add(tool)
        recipe["tools"] = list(tools_found)
        
        return True
    
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return False

def cooking_methods(steps):
    """
    Identify cooking methods used in recipe steps using spaCy.
    
    Args:
        steps (list): List of recipe steps
    
    Returns:
        dict: Dictionary of steps and their identified cooking methods
    """
    cooking_methods = {}
    for step in steps:
        doc = nlp(step)
        verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
        found_methods = [method for method in cooking_methods if method in verbs]
        if found_methods:
            cooking_methods[step] = found_methods
    return cooking_methods

# Example usage
def main():
    url = input("Enter recipe URL: ")
    html = fetch_url(url)
    if html and parse_recipe(html):
        print("Recipe parsed successfully!")
        print(f"Title: {recipe['title']}")
        print("\nIngredients:")
        for ingredient in recipe['ingredients']:
            print(f"- {ingredient}")
        print("\nSteps:")
        for i, step in enumerate(recipe['steps'], 1):
            print(f"{i}. {step}")
        print("\nTools:")
        print(", ".join(recipe['tools']))
    else:
        print("Failed to parse recipe.")

if __name__ == "__main__":
    main()