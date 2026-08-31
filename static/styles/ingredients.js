document.addEventListener("DOMContentLoaded", function () {
    const saveButtons = document.querySelectorAll(
        ".ingredient__save__button"
    );
    const message = document.getElementById("save__message");

    saveButtons.forEach(function (button) {
        button.addEventListener("click", async function () {
            const row = button.closest(".ingredient__row");
            const ingredientInput = row.querySelector(
                ".ingredient__name"
            );
            const typeInput = row.querySelector(
                ".ingredient__type"
            );

            const oldIngredient = row.dataset.originalIngredient;
            const newIngredient = ingredientInput.value.trim();
            const newType = typeInput.value;

            // Do not allow an empty ingredient name.
            if (newIngredient === "") {
                message.textContent =
                    "Ingredient name cannot be empty.";
                return;
            }

            // Ask for confirmation when changing the ingredient name,
            // because this changes it in every recipe.
            if (newIngredient !== oldIngredient) {
                const confirmed = confirm(
                    'Change "' +
                    oldIngredient +
                    '" to "' +
                    newIngredient +
                    '" in every recipe that uses it?'
                );
                if (!confirmed) {
                    return;
                }
            }

            button.disabled = true;
            button.textContent = "Updating...";

            try {
                const response = await fetch("/ingredients/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        old_ingredient: oldIngredient,
                        ingredient: newIngredient,
                        type: newType
                    })
                });

                const data = await response.json();

                if (!response.ok || !data.success) {
                    throw new Error(
                        data.error || "Unable to update ingredient."
                    );
                }

                window.location.reload();
            } catch (error) {
                console.error(error);
                message.textContent =
                    "Error updating ingredient: " + error.message;
                button.textContent = "Update";
                button.disabled = false;
            }
        });
    });
});
