# Import packages
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import re
import sqlite3
import webbrowser


# ---------------------------------------------------------
# Database setup
# ---------------------------------------------------------

db_path = os.path.join(
    os.path.dirname(__file__),
    "instance",
    "database.db"
)


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db = SQLAlchemy(app)


# ---------------------------------------------------------
# Database model
# ---------------------------------------------------------

class Recipes(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(1000)
    )

    days = db.Column(
        db.Float,
        nullable=False
    )

    complete_meal = db.Column(
        db.String(20)
    )

    # Internal recipe identifier.
    #
    # This is NOT the display order.
    number = db.Column(
        db.Integer
    )

    # Controls the order recipes appear on the
    # shopping-list page.
    sort_order = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    # Kept in the database for compatibility with
    # existing databases.
    #
    # The application no longer uses this field.
    group = db.Column(
        db.Integer
    )

    ingredient = db.Column(
        db.String(1000)
    )

    qualtity = db.Column(
        db.Numeric(
            precision=10,
            scale=2
        ),
        nullable=False
    )

    measure = db.Column(
        db.String(20)
    )

    type = db.Column(
        db.String(20)
    )


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def get_recipe_sort_order(recipe_number):
    """
    Return the current sort order for a recipe.

    This is particularly important when modifying a recipe.
    The recipe rows are deleted and recreated, but the recipe
    should stay in the same position.
    """

    recipe = Recipes.query.filter_by(
        number=recipe_number
    ).first()

    if recipe:
        return recipe.sort_order

    return None


def get_next_recipe_number():
    """
    Return the next available internal recipe number.
    """

    highest_number = db.session.query(
        db.func.max(Recipes.number)
    ).scalar()

    if highest_number is None:
        return 0

    return highest_number + 1


def get_next_sort_order():
    """
    Return the position for a newly-created recipe.

    New recipes are placed at the bottom.
    """

    highest_sort_order = db.session.query(
        db.func.max(Recipes.sort_order)
    ).scalar()

    if highest_sort_order is None:
        return 0

    return highest_sort_order + 1


# ---------------------------------------------------------
# Home / shopping list
# ---------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        request_type = request.form.get(
            "request_type"
        )


        # -------------------------------------------------
        # Generate shopping list
        # -------------------------------------------------

        if request_type == "shopping_list":

            selected_items = request.form.get(
                "selectedItems",
                "[]"
            )

            try:
                import json

                selected_recipe_numbers = json.loads(
                    selected_items
                )

            except Exception:
                return jsonify(
                    success=False,
                    error="Invalid recipe selection."
                ), 400


            recipe_list = []

            ingredients = []
            quantities = []
            units = []
            ingredients_type = []


            # Get the selected recipes in the exact order
            # in which the user selected them.
            for recipe_number in selected_recipe_numbers:

                recipe_rows = Recipes.query.filter_by(
                    number=int(recipe_number)
                ).all()

                if not recipe_rows:
                    continue


                recipe_name = recipe_rows[0].name

                recipe_list.append(
                    recipe_name
                )


                for row in recipe_rows:

                    ingredients.append(
                        row.ingredient
                    )

                    quantities.append(
                        float(row.qualtity)
                    )

                    units.append(
                        row.measure
                    )

                    ingredients_type.append(
                        row.type
                    )


            return jsonify(
                recipe_list=recipe_list,
                ingredients=ingredients,
                quantities=quantities,
                units=units,
                ingredients_type=ingredients_type
            )


        # -------------------------------------------------
        # Modify recipe
        # -------------------------------------------------

        elif request_type == "modify_recipe":

            recipe_to_modify = request.form[
                "button"
            ]

            return jsonify(
                recipe_to_modify
            )


        # -------------------------------------------------
        # Delete recipe
        # -------------------------------------------------

        elif request_type == "delete_recipe":

            recipe_to_delete = request.form[
                "button"
            ]

            try:

                recipe_number = int(
                    recipe_to_delete
                )

            except ValueError:

                return jsonify(
                    success=False,
                    error="Invalid recipe number."
                ), 400


            Recipes.query.filter_by(
                number=recipe_number
            ).delete(
                synchronize_session=False
            )

            db.session.commit()


            # Re-number sort_order values so there are
            # no unnecessary gaps after deletion.
            recipes = Recipes.query.order_by(
                Recipes.sort_order.asc()
            ).all()


            # Each recipe has several ingredient rows.
            # Only change sort_order once per recipe.
            seen_numbers = set()
            sort_order = 0


            for recipe in recipes:

                if recipe.number in seen_numbers:
                    continue

                seen_numbers.add(
                    recipe.number
                )


                Recipes.query.filter_by(
                    number=recipe.number
                ).update(
                    {
                        Recipes.sort_order: sort_order
                    },
                    synchronize_session=False
                )


                sort_order += 1


            db.session.commit()


            return jsonify(
                success=True
            )


    all_recipes, meta_info = db_all_recipes()


    return render_template(
        "shopping_list.html",
        all_recipes=all_recipes,
        meta_info=meta_info
    )


# ---------------------------------------------------------
# Modify recipe page
# ---------------------------------------------------------

@app.route(
    "/<recipe_to_modify>/",
    methods=["GET", "POST"]
)
def recipetomodify(recipe_to_modify):

    if recipe_to_modify == "favicon.ico":
        return ""


    previous_ingredients = previousingredients()


    # Recipe key is:
    #
    # number_name
    #
    # The number is the first part.
    recipe_number = recipe_to_modify.split(
        "_",
        1
    )[0]


    recipe_name = recipe_to_modify.split(
        "_",
        1
    )[1]


    all_recipes, meta_info = db_all_recipes()


    all_recipes = all_recipes[
        recipe_to_modify
    ]


    meta_info = meta_info[
        recipe_to_modify
    ][0]


    return render_template(
        "modify_recipe.html",
        all_recipes=all_recipes,
        meta_info=meta_info,
        recipe_name=recipe_name,
        recipe_number=recipe_number,
        previous_ingredients=previous_ingredients
    )


# ---------------------------------------------------------
# Create / update recipe
# ---------------------------------------------------------

@app.route(
    "/newrecipe/",
    methods=["GET", "POST"]
)
def newrecipe():

    previous_ingredients = previousingredients()


    if request.method == "POST":

        # -------------------------------------------------
        # Recipe name
        # -------------------------------------------------

        recipe_input = request.form.get(
            "recipe",
            ""
        ).strip()


        if not recipe_input:
            recipe_name = "Unnamed Recipe"
        else:
            recipe_name = recipe_input.title()


        # -------------------------------------------------
        # Number of days
        # -------------------------------------------------

        day_input = request.form.get(
            "day",
            "1"
        )


        if not day_input:
            number_days = 1
        else:

            try:
                number_days = float(
                    day_input
                )

            except ValueError:
                number_days = 1


        # -------------------------------------------------
        # Complete meal
        # -------------------------------------------------

        complete_meal_input = request.form.get(
            "complete",
            "No"
        )


        # -------------------------------------------------
        # Ingredient inputs
        # -------------------------------------------------

        ingredients = request.form.get(
            "ingredient",
            ""
        ).split(",")


        quantities = request.form.get(
            "quantity",
            ""
        ).split(",")


        measures = request.form.get(
            "measure",
            ""
        ).split(",")


        type_inputs = request.form.get(
            "type",
            ""
        ).split(",")


        # -------------------------------------------------
        # Recipe number
        # -------------------------------------------------

        recipe_number_to_remove = request.form.get(
            "button",
            "submit_new_recipe"
        )


        # -------------------------------------------------
        # Determine whether this is a new recipe
        # or a modification.
        # -------------------------------------------------

        is_modification = (
            recipe_number_to_remove
            != "submit_new_recipe"
        )


        # -------------------------------------------------
        # Preserve existing position when modifying.
        # -------------------------------------------------

        if is_modification:

            try:

                old_recipe_number = int(
                    recipe_number_to_remove
                )

            except ValueError:

                return jsonify(
                    success=False,
                    error="Invalid recipe number."
                ), 400


            existing_sort_order = get_recipe_sort_order(
                old_recipe_number
            )


            if existing_sort_order is None:
                existing_sort_order = get_next_sort_order()


            # Delete the old ingredient rows.
            Recipes.query.filter_by(
                number=old_recipe_number
            ).delete(
                synchronize_session=False
            )


            # Reuse the same recipe number.
            recipe_number = old_recipe_number

            sort_order = existing_sort_order


        else:

            # New recipe gets a new number and goes
            # to the bottom of the list.
            recipe_number = get_next_recipe_number()

            sort_order = get_next_sort_order()


        # -------------------------------------------------
        # Clean ingredients
        # -------------------------------------------------

        combined_inputs = []


        for ingredient, quantity, measure, type_input in zip(
            ingredients,
            quantities,
            measures,
            type_inputs
        ):

            ingredient = ingredient.strip()
            quantity = quantity.strip()
            measure = measure.strip()
            type_input = type_input.strip()


            # Ignore incomplete ingredient rows.
            if not ingredient:
                continue


            if not quantity:
                continue


            try:

                quantity = round(
                    float(quantity),
                    2
                )

            except ValueError:

                continue


            combined_inputs.append(
                [
                    ingredient.capitalize(),
                    quantity,
                    measure,
                    type_input
                ]
            )


        # -------------------------------------------------
        # Only save if at least one ingredient exists.
        # -------------------------------------------------

        if len(combined_inputs) > 0:

            # Add every ingredient row.
            #
            # IMPORTANT:
            # We do NOT commit inside this loop.
            for combined_input in combined_inputs:

                new_upload = Recipes(
                    name=recipe_name,
                    days=number_days,
                    complete_meal=complete_meal_input,
                    number=recipe_number,
                    sort_order=sort_order,
                    ingredient=combined_input[0],
                    qualtity=combined_input[1],
                    measure=combined_input[2],
                    type=combined_input[3]
                )

                db.session.add(
                    new_upload
                )


            # One commit for the entire recipe.
            db.session.commit()


    return render_template(
        "new_recipe.html",
        previous_ingredients=previous_ingredients
    )


# ---------------------------------------------------------
# Get all recipes
# ---------------------------------------------------------

def db_all_recipes():

    conn = sqlite3.connect(
        "instance/database.db"
    )

    cursor = conn.cursor()


    # -----------------------------------------------------
    # Get ingredients
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            number,
            name,
            ingredient,
            qualtity,
            measure,
            type
        FROM Recipes
        ORDER BY sort_order ASC, id ASC
    """)


    all_recipes = cursor.fetchall()


    # -----------------------------------------------------
    # Get metadata
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            number,
            name,
            days,
            complete_meal
        FROM Recipes
        ORDER BY sort_order ASC, id ASC
    """)


    meta_info = cursor.fetchall()


    conn.close()


    all_recipes = group_data(
        all_recipes
    )


    meta_info = group_data(
        meta_info
    )


    # Metadata is repeated for every ingredient.
    # Keep only one copy.
    for key in meta_info:

        meta_info[key] = list(
            set(meta_info[key])
        )


    return all_recipes, meta_info


# ---------------------------------------------------------
# Group recipe rows
# ---------------------------------------------------------

def group_data(data):

    grouped_data = {}


    for item in data:

        # Recipe number + recipe name.
        #
        # Example:
        #
        # 4_Chicken Curry
        #
        key = "_".join(
            [
                str(item[0]),
                str(item[1])
            ]
        )


        if key not in grouped_data:

            grouped_data[key] = []


        # Remove number and name.
        grouped_data[key].append(
            item[2:]
        )


    return grouped_data


# ---------------------------------------------------------
# Previous ingredients
# ---------------------------------------------------------

def previousingredients():

    conn = sqlite3.connect(
        "instance/database.db"
    )

    cursor = conn.cursor()


    cursor.execute(
        "SELECT ingredient FROM Recipes"
    )


    ingredients = cursor.fetchall()


    conn.close()


    return [
        re.sub(
            r"[^a-zA-Z\s]",
            "",
            ingredient[0]
        )

        for ingredient in list(
            set(ingredients)
        )
    ]


# ---------------------------------------------------------
# Reorder recipes
# ---------------------------------------------------------

@app.route(
    "/reorder-recipes/",
    methods=["POST"]
)
def reorder_recipes():

    data = request.get_json()


    if not data or "order" not in data:

        return jsonify(
            success=False,
            error="No recipe order received."
        ), 400


    recipe_order = data["order"]


    try:

        # recipe_order contains recipe numbers:
        #
        # ["4", "2", "7", "1"]
        #
        # The array position becomes sort_order.

        for sort_order, recipe_number in enumerate(
            recipe_order
        ):

            Recipes.query.filter_by(
                number=int(recipe_number)
            ).update(
                {
                    Recipes.sort_order: sort_order
                },
                synchronize_session=False
            )


        db.session.commit()


        return jsonify(
            success=True
        )


    except Exception as error:

        db.session.rollback()


        return jsonify(
            success=False,
            error=str(error)
        ), 500


# ---------------------------------------------------------
# Ingredient management
# ---------------------------------------------------------

@app.route(
    "/ingredients/",
    methods=["GET", "POST"]
)
def ingredients():

    if request.method == "POST":

        data = request.get_json()


        if not data:

            return jsonify(
                success=False,
                error="No data received"
            ), 400


        old_ingredient = data.get(
            "old_ingredient",
            ""
        ).strip()


        new_ingredient = data.get(
            "ingredient",
            ""
        ).strip()


        new_type = data.get(
            "type",
            ""
        ).strip()


        if not old_ingredient:

            return jsonify(
                success=False,
                error="Original ingredient name is missing"
            ), 400


        if not new_ingredient:

            return jsonify(
                success=False,
                error="Ingredient name cannot be empty"
            ), 400


        if not new_type:

            return jsonify(
                success=False,
                error="Ingredient type cannot be empty"
            ), 400


        try:

            Recipes.query.filter_by(
                ingredient=old_ingredient
            ).update(
                {
                    Recipes.ingredient: new_ingredient,
                    Recipes.type: new_type
                },
                synchronize_session=False
            )


            db.session.commit()


            return jsonify(
                success=True
            )


        except Exception as error:

            db.session.rollback()


            return jsonify(
                success=False,
                error=str(error)
            ), 500


    # Get one entry for each ingredient.
    ingredient_rows = db.session.execute(
        db.text("""
            SELECT
                ingredient,
                MAX(type) AS type
            FROM Recipes
            WHERE ingredient IS NOT NULL
                AND TRIM(ingredient) != ''
            GROUP BY ingredient
            ORDER BY LOWER(ingredient) ASC
        """)
    ).fetchall()


    ingredients_list = [

        {
            "ingredient": row[0],
            "type": row[1]
            if row[1]
            else "Other"
        }

        for row in ingredient_rows
    ]


    return render_template(
        "ingredients.html",
        ingredients=ingredients_list
    )


# ---------------------------------------------------------
# Run application
# ---------------------------------------------------------

if __name__ == "__main__":

    webbrowser.open_new(
        "http://127.0.0.1:5000/"
    )

    app.run(
        debug=False
    )