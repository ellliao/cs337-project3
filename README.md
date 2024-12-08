# cs337-project3
Northwestern University CS 337 Project 3: A recipe transformer.
Lydia Ketema, Ellen Liao, Henry Michaelson, Yao Xiao
## Setup

### Prerequisites

Before proceeding with setup, you must have the following installed:

* **Python >= 3.10**
* **Pip**

### Package installation

This project uses the **SpaCy en_core_web_sm** and the **NLTK WordNet** models.

To download these and other required packages for this project, run the following command from within your cloned project directory:

```
pip install -r requirements.txt
```

## Running the Code

### Activation

To activate the transformer, run the following command from within the project directory:

```
python main.py
```

You will be prompted to enter a recipe URL. The transformer can take the URL of any recipe from [allrecipes.com](https://www.allrecipes.com/).

```
Enter recipe URL: [url]
```

Once the recipe is successfully parsed and extracted, it will be displayed, along with a number of options.

### Commands

The following commands are supported by the transformer. When prompted, enter the number associated with the command to choose it.

1. **Transform to Vegetarian** creates a vegetarian version of the recipe.
2. **Transform to Non-Vegetarian** creates a non-vegetarian version of the recipe.
3. **Transform to Healthy** creates a healthier version of the recipe.
4. **Transform to Unhealthy** creates an unhealthier version of the recipe.
5. **Transform to Double** doubles the quantity of the recipe.
6. **Transform to Half** halves the quantity of the recipe.
7. **Transform to Italian Style** creates an Italian-inspired version of the recipe.
8. **Transform to Mexican Style** creates a Mexican-inspired version of the recipe.
9. **Transform to Gluten Free** creates a gluten-free version of the recipe.
10. **Transform to Lactose Free** creates a lactose-free version of the recipe.
11. **Exit** closes the transformer.

## Output Files

After applying the appropriate transformation, the transformer will print the transformed recipe along with a line that reads:

```
Recipe saved to [filename]!
```

where `filename` is of the format `[transformation]_[recipe].txt`.

You can visit this file to see the transformation, the original recipe, and the resulting transformed recipe.

## GitHub Repository

<https://github.com/ellliao/cs337-project3.git>
