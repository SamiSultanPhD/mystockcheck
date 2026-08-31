from flask import (
    Flask, render_template, request,
    jsonify, redirect, url_for, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from werkzeug.security import (
    generate_password_hash, check_password_hash
)
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
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "change-this-to-a-random-secret-string"
)
db = SQLAlchemy(app)

# ---------------------------------------------------------
# Login manager
# ---------------------------------------------------------
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------
FREE_RECIPE_LIMIT = 6

# ---------------------------------------------------------
# Database models
# ---------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )
    email = db.Column(
        db.String(200),
        unique=True,
        nullable=False
    )
    password_hash = db.Column(
        db.String(200),
        nullable=False
    )
    role = db.Column(
        db.String(20),
        nullable=False,
        default="free"
    )


class Recipes(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
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
    number = db.Column(
        db.Integer
    )
    sort_order = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )
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
def get_recipe_sort_order(
    recipe_number, user_id
):
    recipe = Recipes.query.filter_by(
        number=recipe_number,
        user_id=user_id
    ).first()
    if recipe:
        return recipe.sort_order
    return None


def get_next_recipe_number():
    highest_number = db.session.query(
        db.func.max(Recipes.number)
    ).scalar()
    if highest_number is None:
        return 0
    return highest_number + 1


def get_next_sort_order(user_id):
    highest_sort_order = db.session.query(
        db.func.max(Recipes.sort_order)
    ).filter_by(
        user_id=user_id
    ).scalar()
    if highest_sort_order is None:
        return 0
    return highest_sort_order + 1


def get_user_recipe_count(user_id):
    count = db.session.query(
        db.func.count(
            db.distinct(Recipes.number)
        )
    ).filter_by(
        user_id=user_id
    ).scalar()
    return count or 0

# ---------------------------------------------------------
# Authentication
# ---------------------------------------------------------
@app.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get(
            "username", ""
        ).strip()
        password = request.form.get(
            "password", ""
        )

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password_hash, password
        ):
            login_user(user)
            return redirect(url_for("home"))

        flash("Invalid username or password.")

    return render_template("login.html")


@app.route(
    "/register/", methods=["GET", "POST"]
)
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get(
            "username", ""
        ).strip()
        email = request.form.get(
            "email", ""
        ).strip().lower()
        password = request.form.get(
            "password", ""
        )
        confirm = request.form.get(
            "confirm_password", ""
        )

        if not username or not email or not password:
            flash("All fields are required.")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.")
            return render_template("register.html")

        if len(password) < 4:
            flash(
                "Password must be at least"
                " 4 characters."
            )
            return render_template("register.html")

        if User.query.filter_by(
            username=username
        ).first():
            flash("Username already taken.")
            return render_template("register.html")

        if User.query.filter_by(
            email=email
        ).first():
            flash("Email already registered.")
            return render_template("register.html")

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(
                password
            ),
            role="free"
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("home"))

    return render_template("register.html")


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------------------------------------------------------
# Home / shopping list
# ---------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
@login_required
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

            for recipe_number in selected_recipe_numbers:
                recipe_rows = Recipes.query.filter_by(
                    number=int(recipe_number),
                    user_id=current_user.id
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
            recipe = Recipes.query.filter_by(
                number=int(recipe_to_modify),
                user_id=current_user.id
            ).first()
            if not recipe:
                return jsonify(
                    success=False,
                    error="Recipe not found."
                ), 404
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

            recipe = Recipes.query.filter_by(
                number=recipe_number,
                user_id=current_user.id
            ).first()
            if not recipe:
                return jsonify(
                    success=False,
                    error="Recipe not found."
                ), 404

            Recipes.query.filter_by(
                number=recipe_number,
                user_id=current_user.id
            ).delete(
                synchronize_session=False
            )
            db.session.commit()

            recipes = Recipes.query.filter_by(
                user_id=current_user.id
            ).order_by(
                Recipes.sort_order.asc()
            ).all()

            seen_numbers = set()
            sort_order = 0
            for recipe in recipes:
                if recipe.number in seen_numbers:
                    continue
                seen_numbers.add(
                    recipe.number
                )
                Recipes.query.filter_by(
                    number=recipe.number,
                    user_id=current_user.id
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

    all_recipes, meta_info = db_all_recipes(
        current_user.id
    )
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
@login_required
def recipetomodify(recipe_to_modify):
    if recipe_to_modify == "favicon.ico":
        return ""

    recipe_number = recipe_to_modify.split(
        "_",
        1
    )[0]

    recipe = Recipes.query.filter_by(
        number=int(recipe_number),
        user_id=current_user.id
    ).first()
    if not recipe:
        return redirect(url_for("home"))

    previous_ingredients = previousingredients(
        current_user.id
    )

    recipe_name = recipe_to_modify.split(
        "_",
        1
    )[1]

    all_recipes, meta_info = db_all_recipes(
        current_user.id
    )
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
@login_required
def newrecipe():
    previous_ingredients = previousingredients(
        current_user.id
    )

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

        is_modification = (
            recipe_number_to_remove
            != "submit_new_recipe"
        )

        # -------------------------------------------------
        # Recipe limit for free users
        # -------------------------------------------------
        if not is_modification:
            if current_user.role == "free":
                count = get_user_recipe_count(
                    current_user.id
                )
                if count >= FREE_RECIPE_LIMIT:
                    return jsonify(
                        success=False,
                        error="Free trial limit reached!"
                              " You can save up to "
                              + str(FREE_RECIPE_LIMIT)
                              + " recipes. A full version"
                              " with unlimited recipes"
                              " is in development!"
                    ), 403

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

            recipe = Recipes.query.filter_by(
                number=old_recipe_number,
                user_id=current_user.id
            ).first()
            if not recipe:
                return jsonify(
                    success=False,
                    error="Recipe not found."
                ), 404

            existing_sort_order = get_recipe_sort_order(
                old_recipe_number,
                current_user.id
            )
            if existing_sort_order is None:
                existing_sort_order = get_next_sort_order(
                    current_user.id
                )

            Recipes.query.filter_by(
                number=old_recipe_number,
                user_id=current_user.id
            ).delete(
                synchronize_session=False
            )

            recipe_number = old_recipe_number
            sort_order = existing_sort_order
        else:
            recipe_number = get_next_recipe_number()
            sort_order = get_next_sort_order(
                current_user.id
            )

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
            for combined_input in combined_inputs:
                new_upload = Recipes(
                    user_id=current_user.id,
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

            db.session.commit()

    return render_template(
        "new_recipe.html",
        previous_ingredients=previous_ingredients
    )

# ---------------------------------------------------------
# Get all recipes for a user
# ---------------------------------------------------------
def db_all_recipes(user_id):
    conn = sqlite3.connect(
        "instance/database.db"
    )
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            number,
            name,
            ingredient,
            qualtity,
            measure,
            type
        FROM Recipes
        WHERE user_id = ?
        ORDER BY sort_order ASC, id ASC
    """, (user_id,))
    all_recipes = cursor.fetchall()

    cursor.execute("""
        SELECT
            number,
            name,
            days,
            complete_meal
        FROM Recipes
        WHERE user_id = ?
        ORDER BY sort_order ASC, id ASC
    """, (user_id,))
    meta_info = cursor.fetchall()

    conn.close()

    all_recipes = group_data(
        all_recipes
    )
    meta_info = group_data(
        meta_info
    )

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
        key = "_".join(
            [
                str(item[0]),
                str(item[1])
            ]
        )
        if key not in grouped_data:
            grouped_data[key] = []

        grouped_data[key].append(
            item[2:]
        )

    return grouped_data

# ---------------------------------------------------------
# Previous ingredients for a user
# ---------------------------------------------------------
def previousingredients(user_id):
    conn = sqlite3.connect(
        "instance/database.db"
    )
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ingredient FROM Recipes"
        " WHERE user_id = ?",
        (user_id,)
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
@login_required
def reorder_recipes():
    data = request.get_json()
    if not data or "order" not in data:
        return jsonify(
            success=False,
            error="No recipe order received."
        ), 400

    recipe_order = data["order"]

    try:
        for sort_order, recipe_number in enumerate(
            recipe_order
        ):
            Recipes.query.filter_by(
                number=int(recipe_number),
                user_id=current_user.id
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
@login_required
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
                error="Original ingredient name"
                      " is missing"
            ), 400

        if not new_ingredient:
            return jsonify(
                success=False,
                error="Ingredient name cannot"
                      " be empty"
            ), 400

        if not new_type:
            return jsonify(
                success=False,
                error="Ingredient type cannot"
                      " be empty"
            ), 400

        try:
            Recipes.query.filter_by(
                ingredient=old_ingredient,
                user_id=current_user.id
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

    ingredient_rows = db.session.execute(
        db.text("""
            SELECT
                ingredient,
                MAX(type) AS type
            FROM Recipes
            WHERE user_id = :user_id
                AND ingredient IS NOT NULL
                AND TRIM(ingredient) != ''
            GROUP BY ingredient
            ORDER BY LOWER(ingredient) ASC
        """),
        {"user_id": current_user.id}
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
# Admin
# ---------------------------------------------------------
@app.route("/admin/", methods=["GET"])
@login_required
def admin():
    if current_user.role != "admin":
        return redirect(url_for("home"))

    users = User.query.order_by(
        User.id.asc()
    ).all()

    user_data = []
    for user in users:
        recipe_count = db.session.query(
            db.func.count(
                db.distinct(Recipes.number)
            )
        ).filter_by(
            user_id=user.id
        ).scalar() or 0

        user_data.append({
            "user": user,
            "recipe_count": recipe_count
        })

    return render_template(
        "admin.html",
        user_data=user_data
    )


@app.route(
    "/admin/update-role/",
    methods=["POST"]
)
@login_required
def admin_update_role():
    if current_user.role != "admin":
        return redirect(url_for("home"))

    user_id = request.form.get("user_id")
    new_role = request.form.get("role")

    if not user_id or not new_role:
        flash("Missing user or role.")
        return redirect(url_for("admin"))

    if new_role not in [
        "free", "member", "admin"
    ]:
        flash("Invalid role.")
        return redirect(url_for("admin"))

    user = User.query.get(int(user_id))
    if not user:
        flash("User not found.")
        return redirect(url_for("admin"))

    user.role = new_role
    db.session.commit()
    flash(
        user.username + " is now "
        + new_role + "."
    )
    return redirect(url_for("admin"))


@app.route(
    "/admin/reset-password/",
    methods=["POST"]
)
@login_required
def admin_reset_password():
    if current_user.role != "admin":
        return redirect(url_for("home"))

    user_id = request.form.get("user_id")
    new_password = request.form.get(
        "new_password"
    )

    if not user_id or not new_password:
        flash("Missing user or password.")
        return redirect(url_for("admin"))

    user = User.query.get(int(user_id))
    if not user:
        flash("User not found.")
        return redirect(url_for("admin"))

    user.password_hash = generate_password_hash(
        new_password
    )
    db.session.commit()
    flash(
        "Password reset for "
        + user.username + "."
    )
    return redirect(url_for("admin"))

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
