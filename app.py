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
from datetime import datetime
import os
import re
import sqlite3


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
    "SECRET_KEY", "dev-fallback-key"
)
db = SQLAlchemy(app)


# ---------------------------------------------------------
# Flask-Login setup
# ---------------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ---------------------------------------------------------
# Database models
# ---------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )
    email = db.Column(
        db.String(120),
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
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )


class AppSettings(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    key = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )
    value = db.Column(
        db.String(500)
    )


class PasswordResetRequest(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    username = db.Column(
        db.String(80),
        nullable=False
    )
    email = db.Column(
        db.String(120),
        nullable=False
    )
    requested_at = db.Column(
        db.DateTime,
        nullable=False
    )
    pending = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------
# Create tables and default settings
# ---------------------------------------------------------
with app.app_context():
    db.create_all()
    if not AppSettings.query.filter_by(
        key="free_recipe_limit"
    ).first():
        db.session.add(
            AppSettings(
                key="free_recipe_limit",
                value="6"
            )
        )
        db.session.commit()


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def get_setting(key, default=None):
    setting = AppSettings.query.filter_by(
        key=key
    ).first()
    if setting:
        return setting.value
    return default


def get_free_recipe_limit():
    limit = get_setting("free_recipe_limit", "6")
    return int(limit)


def get_user_recipe_count(user_id):
    count = db.session.query(
        db.func.count(
            db.func.distinct(Recipes.number)
        )
    ).filter_by(
        user_id=user_id
    ).scalar()
    return count or 0


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

    previous_ingredients = previousingredients(
        current_user.id
    )

    recipe_number = recipe_to_modify.split(
        "_",
        1
    )[0]
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
        # Safety check: re-verify free limit on POST.
        # -------------------------------------------------
        recipe_number_to_remove = request.form.get(
            "button",
            "submit_new_recipe"
        )
        is_modification = (
            recipe_number_to_remove
            != "submit_new_recipe"
        )

        if (
            not is_modification
            and current_user.role == "free"
        ):
            recipe_count = get_user_recipe_count(
                current_user.id
            )
            limit = get_free_recipe_limit()
            if recipe_count >= limit:
                return jsonify(
                    success=False,
                    error="Free accounts are limited to "
                    + str(limit)
                    + " recipes."
                ), 403

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
        # Determine whether this is a new recipe
        # or a modification.
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
                    name=recipe_name,
                    days=number_days,
                    complete_meal=complete_meal_input,
                    number=recipe_number,
                    sort_order=sort_order,
                    ingredient=combined_input[0],
                    qualtity=combined_input[1],
                    measure=combined_input[2],
                    type=combined_input[3],
                    user_id=current_user.id
                )
                db.session.add(
                    new_upload
                )
            db.session.commit()

    # ---------------------------------------------------------
    # GET: Block free users who have hit the recipe limit.
    # ---------------------------------------------------------
    if current_user.role == "free":
        recipe_count = get_user_recipe_count(
            current_user.id
        )
        limit = get_free_recipe_limit()
        if recipe_count >= limit:
            flash(
                "Free accounts are limited to "
                + str(limit)
                + " recipes. A full version is"
                + " in development!"
            )
            return redirect(url_for("home"))

    return render_template(
        "new_recipe.html",
        previous_ingredients=previous_ingredients
    )


# ---------------------------------------------------------
# Get all recipes
# ---------------------------------------------------------
def db_all_recipes(user_id):
    conn = sqlite3.connect(db_path)
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
# Previous ingredients
# ---------------------------------------------------------
def previousingredients(user_id):
    conn = sqlite3.connect(db_path)
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
            WHERE ingredient IS NOT NULL
                AND TRIM(ingredient) != ''
                AND user_id = :user_id
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
# Forgot password
# ---------------------------------------------------------
@app.route(
    "/forgot-password/",
    methods=["GET", "POST"]
)
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get(
            "username", ""
        ).strip()
        email = request.form.get(
            "email", ""
        ).strip()

        if not username or not email:
            flash("Both fields are required.")
            return render_template(
                "forgot_password.html"
            )

        user = User.query.filter_by(
            username=username,
            email=email
        ).first()

        if not user:
            flash(
                "Username and email do not match"
                " any account."
            )
            return render_template(
                "forgot_password.html"
            )

        existing = PasswordResetRequest.query.filter_by(
            username=username,
            pending=True
        ).first()

        if existing:
            flash(
                "A reset request is already"
                " pending. It will be actioned"
                " soon."
            )
            return render_template(
                "forgot_password.html"
            )

        new_request = PasswordResetRequest(
            username=username,
            email=email,
            requested_at=datetime.utcnow(),
            pending=True
        )
        db.session.add(new_request)
        db.session.commit()

        flash(
            "Thank you. Your password reset"
            " request has been received and"
            " will be actioned manually soon."
        )
        return redirect(url_for("login"))

    return render_template(
        "forgot_password.html"
    )


# ---------------------------------------------------------
# Admin
# ---------------------------------------------------------
@app.route(
    "/admin/",
    methods=["GET", "POST"]
)
@login_required
def admin():
    if current_user.role != "admin":
        return redirect(url_for("home"))

    if request.method == "POST":
        action = request.form.get("action")
        target_user_id = request.form.get(
            "user_id"
        )

        # -------------------------------------------------
        # Change role
        # -------------------------------------------------
        if action == "change_role":
            new_role = request.form.get(
                "new_role"
            )
            if new_role in (
                "free", "member", "admin"
            ):
                User.query.filter_by(
                    id=target_user_id
                ).update(
                    {User.role: new_role},
                    synchronize_session=False
                )
                db.session.commit()
                flash("Role updated.")

        # -------------------------------------------------
        # Reset password
        # -------------------------------------------------
        elif action == "reset_password":
            new_password = request.form.get(
                "new_password", ""
            ).strip()
            if new_password:
                User.query.filter_by(
                    id=target_user_id
                ).update(
                    {
                        User.password_hash:
                            generate_password_hash(
                                new_password
                            )
                    },
                    synchronize_session=False
                )
                db.session.commit()
                flash("Password reset.")

        # -------------------------------------------------
        # Delete user
        # -------------------------------------------------
        elif action == "delete_user":
            user_to_delete = User.query.get(
                int(target_user_id)
            )
            if (
                user_to_delete
                and user_to_delete.id
                != current_user.id
            ):
                Recipes.query.filter_by(
                    user_id=user_to_delete.id
                ).delete(
                    synchronize_session=False
                )
                PasswordResetRequest.query.filter_by(
                    username=user_to_delete.username
                ).delete(
                    synchronize_session=False
                )
                db.session.delete(
                    user_to_delete
                )
                db.session.commit()
                flash(
                    "User '"
                    + user_to_delete.username
                    + "' and all their data"
                    + " deleted."
                )
            else:
                flash(
                    "Cannot delete your own"
                    " account."
                )

        # -------------------------------------------------
        # Update free recipe limit
        # -------------------------------------------------
        elif action == "update_recipe_limit":
            new_limit = request.form.get(
                "recipe_limit", ""
            ).strip()
            try:
                new_limit_int = int(new_limit)
                if new_limit_int < 1:
                    raise ValueError
                setting = AppSettings.query.filter_by(
                    key="free_recipe_limit"
                ).first()
                if setting:
                    setting.value = str(
                        new_limit_int
                    )
                else:
                    db.session.add(
                        AppSettings(
                            key="free_recipe_limit",
                            value=str(
                                new_limit_int
                            )
                        )
                    )
                db.session.commit()
                flash(
                    "Free recipe limit updated"
                    " to "
                    + str(new_limit_int)
                    + "."
                )
            except (ValueError, TypeError):
                flash("Invalid recipe limit.")

        # -------------------------------------------------
        # Dismiss reset request
        # -------------------------------------------------
        elif action == "dismiss_request":
            request_id = request.form.get(
                "request_id"
            )
            reset_req = PasswordResetRequest.query.get(
                int(request_id)
            )
            if reset_req:
                reset_req.pending = False
                db.session.commit()
                flash("Reset request dismissed.")

        return redirect(url_for("admin"))

    # -------------------------------------------------
    # GET: build page data
    # -------------------------------------------------
    users = User.query.order_by(
        User.id.asc()
    ).all()
    user_data = []
    for user in users:
        recipe_count = get_user_recipe_count(
            user.id
        )
        user_data.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "recipe_count": recipe_count
        })

    current_limit = get_free_recipe_limit()

    reset_requests = PasswordResetRequest.query.filter_by(
        pending=True
    ).order_by(
        PasswordResetRequest.requested_at.desc()
    ).all()

    return render_template(
        "admin.html",
        user_data=user_data,
        current_limit=current_limit,
        reset_requests=reset_requests
    )

# ---------------------------------------------------------
# Account settings
# ---------------------------------------------------------
@app.route(
    "/account/",
    methods=["GET", "POST"]
)
@login_required
def account():
    if request.method == "POST":
        action = request.form.get("action")

        # -------------------------------------------------
        # Change email
        # -------------------------------------------------
        if action == "change_email":
            new_email = request.form.get(
                "new_email", ""
            ).strip()
            password = request.form.get(
                "password", ""
            )

            if not new_email or not password:
                flash("All fields are required.")
                return redirect(
                    url_for("account")
                )

            if not check_password_hash(
                current_user.password_hash,
                password
            ):
                flash(
                    "Incorrect password."
                )
                return redirect(
                    url_for("account")
                )

            existing = User.query.filter_by(
                email=new_email
            ).first()
            if (
                existing
                and existing.id
                != current_user.id
            ):
                flash(
                    "That email is already in"
                    " use by another account."
                )
                return redirect(
                    url_for("account")
                )

            current_user.email = new_email
            db.session.commit()
            flash("Email updated.")

        # -------------------------------------------------
        # Change password
        # -------------------------------------------------
        elif action == "change_password":
            current_password = request.form.get(
                "current_password", ""
            )
            new_password = request.form.get(
                "new_password", ""
            )
            confirm_password = request.form.get(
                "confirm_password", ""
            )

            if (
                not current_password
                or not new_password
                or not confirm_password
            ):
                flash("All fields are required.")
                return redirect(
                    url_for("account")
                )

            if not check_password_hash(
                current_user.password_hash,
                current_password
            ):
                flash("Current password is incorrect.")
                return redirect(
                    url_for("account")
                )

            if new_password != confirm_password:
                flash(
                    "New passwords do not match."
                )
                return redirect(
                    url_for("account")
                )

            if len(new_password) < 4:
                flash(
                    "Password must be at least"
                    " 4 characters."
                )
                return redirect(
                    url_for("account")
                )

            current_user.password_hash = (
                generate_password_hash(
                    new_password
                )
            )
            db.session.commit()
            flash("Password updated.")

        return redirect(url_for("account"))

    return render_template("account.html")

# ---------------------------------------------------------
# Login
# ---------------------------------------------------------
@app.route(
    "/login/",
    methods=["GET", "POST"]
)
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


# ---------------------------------------------------------
# Register
# ---------------------------------------------------------
@app.route(
    "/register/",
    methods=["GET", "POST"]
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
        ).strip()
        password = request.form.get(
            "password", ""
        )

        if not username or not email or not password:
            flash("All fields are required.")
            return render_template(
                "register.html"
            )

        if User.query.filter_by(
            username=username
        ).first():
            flash("Username already taken.")
            return render_template(
                "register.html"
            )

        if User.query.filter_by(
            email=email
        ).first():
            flash("Email already registered.")
            return render_template(
                "register.html"
            )

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


# ---------------------------------------------------------
# Logout
# ---------------------------------------------------------
@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------------------------------------------------------
# Run application
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(
        debug=False
    )
