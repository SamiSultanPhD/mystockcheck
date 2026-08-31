/*
 * Recipes selected for the shopping list.
 *
 * These are recipe numbers rather than the visible
 * text of the recipe card.
 */
var selectedItems = [];

/*
 * Get all recipe cards.
 */
var selectionElements =
    document.querySelectorAll(
        ".recipe__container"
    );

/*
 * Add click listeners.
 */
selectionElements.forEach(
    function (element) {
        element.addEventListener(
            "click",
            handleContainerClick
        );
    }
);

/*
 * Handle selecting/deselecting a recipe.
 */
function handleContainerClick(event) {
    /*
     * Do not select a recipe when the user clicks
     * Modify or Delete.
     */
    if (
        event.target.closest(
            ".modification__button"
        ) ||
        event.target.closest(
            ".delete__button"
        )
    ) {
        return;
    }

    /*
     * Do not select a recipe when clicking the
     * drag handle.
     */
    if (
        event.target.closest(
            ".recipe__drag__handle"
        )
    ) {
        return;
    }

    var clickedContainer =
        findParentContainer(
            event.target,
            "recipe__container"
        );
    if (!clickedContainer) {
        return;
    }

    /*
     * The recipe number lives on the outer
     * .recipe__container__full element.
     */
    var recipeCard =
        clickedContainer.closest(
            ".recipe__container__full"
        );
    if (!recipeCard) {
        return;
    }

    var recipeNumber =
        recipeCard.dataset.recipeNumber;

    /*
     * FIX: This handler fires BEFORE button_colour.js
     * toggles the "clicked" class.  So when the class
     * is NOT yet present the user is clicking to SELECT,
     * and when it IS present they are clicking to DESELECT.
     *
     * The old code had these two branches the wrong way
     * round, which is why recipes only appeared on the
     * second (un-)click.
     */

    /*
     * Add recipe (class is about to be added by
     * button_colour.js).
     */
    if (
        !clickedContainer.classList.contains(
            "clicked"
        )
    ) {
        if (
            !selectedItems.includes(
                recipeNumber
            )
        ) {
            selectedItems.push(
                recipeNumber
            );
        }
    }
    /*
     * Remove recipe (class is about to be removed
     * by button_colour.js).
     */
    else {
        var removeIndex =
            selectedItems.indexOf(
                recipeNumber
            );
        if (removeIndex !== -1) {
            selectedItems.splice(
                removeIndex,
                1
            );
        }
    }

    /*
     * Generate shopping list.
     */
    sendSelectedItems();
}

/*
 * Find nearest parent container.
 */
function findParentContainer(
    element,
    className
) {
    while (
        element &&
        element !== document
    ) {
        if (
            element.classList.contains(
                className
            )
        ) {
            return element;
        }
        element =
            element.parentNode;
    }
    return null;
}

/*
 * Send selected recipe numbers to Flask.
 */
function sendSelectedItems() {
    var formData =
        new FormData();
    formData.append(
        "selectedItems",
        JSON.stringify(
            selectedItems
        )
    );
    formData.append(
        "request_type",
        "shopping_list"
    );

    fetch(
        "/",
        {
            method: "POST",
            body: formData
        }
    )
    .then(
        response =>
            response.json()
    )
    .then(
        data => {
            /*
             * Create one object for every
             * ingredient returned by Flask.
             */
            const dataArray = [];
            for (
                let i = 0;
                i < data.ingredients.length;
                i++
            ) {
                dataArray.push(
                    {
                        type:
                            data.ingredients_type[i],
                        ingredient:
                            data.ingredients[i],
                        quantity:
                            parseFloat(
                                data.quantities[i]
                            ),
                        unit:
                            data.units[i]
                    }
                );
            }

            /*
             * Convert measurements into common units.
             */
            function convertMeasurement(
                quantity,
                unit
            ) {
                const cleanUnit =
                    unit
                        .toLowerCase()
                        .trim();

                /*
                 * Table spoon -> teaspoon.
                 */
                if (
                    cleanUnit ===
                        "table spoon" ||
                    cleanUnit ===
                        "tablespoon"
                ) {
                    return {
                        quantity:
                            quantity * 2,
                        unit:
                            "teaspoon"
                    };
                }

                /*
                 * Cup -> ml.
                 */
                if (
                    cleanUnit === "cup"
                ) {
                    return {
                        quantity:
                            quantity * 240,
                        unit:
                            "ml"
                    };
                }

                /*
                 * Tea spoon -> teaspoon.
                 */
                if (
                    cleanUnit ===
                        "tea spoon" ||
                    cleanUnit ===
                        "teaspoon"
                ) {
                    return {
                        quantity:
                            quantity,
                        unit:
                            "teaspoon"
                    };
                }

                return {
                    quantity:
                        quantity,
                    unit:
                        unit
                };
            }

            /*
             * Convert all measurements.
             */
            const convertedIngredients =
                dataArray.map(
                    function (item) {
                        const converted =
                            convertMeasurement(
                                item.quantity,
                                item.unit
                            );
                        return {
                            type:
                                item.type,
                            ingredient:
                                item.ingredient,
                            quantity:
                                converted.quantity,
                            unit:
                                converted.unit
                        };
                    }
                );

            /*
             * Group by ingredient type +
             * ingredient name.
             */
            const groupedIngredients = {};
            convertedIngredients.forEach(
                function (item) {
                    const key =
                        item.type +
                        "|" +
                        item.ingredient;
                    if (
                        !groupedIngredients[key]
                    ) {
                        groupedIngredients[key] = {
                            type:
                                item.type,
                            ingredient:
                                item.ingredient,
                            measurements: {}
                        };
                    }

                    /*
                     * Approximately is treated
                     * as an estimated amount.
                     */
                    let measurementUnit =
                        item.unit;
                    let estimated =
                        false;

                    if (
                        measurementUnit
                            .toLowerCase()
                            .trim() ===
                        "approximately"
                    ) {
                        estimated = true;
                        measurementUnit =
                            "approximately";
                    }

                    const measurementKey =
                        (
                            estimated
                                ? "est|"
                                : ""
                        ) +
                        measurementUnit;

                    if (
                        !groupedIngredients[key]
                            .measurements[
                                measurementKey
                            ]
                    ) {
                        groupedIngredients[key]
                            .measurements[
                                measurementKey
                            ] = {
                                quantity: 0,
                                unit:
                                    measurementUnit,
                                estimated:
                                    estimated
                            };
                    }

                    groupedIngredients[key]
                        .measurements[
                            measurementKey
                        ]
                        .quantity +=
                            item.quantity;
                }
            );

            /*
             * Turn grouped objects into a list.
             */
            const condensedIngredients =
                Object.values(
                    groupedIngredients
                );

            /*
             * FIX: Sort by ingredient type first,
             * then alphabetically by ingredient name.
             *
             * The old code only sorted by ingredient
             * name, ignoring type entirely.
             */
            condensedIngredients.sort(
                function (a, b) {
                    var typeCompare =
                        a.type.localeCompare(
                            b.type
                        );
                    if (typeCompare !== 0) {
                        return typeCompare;
                    }
                    return a.ingredient.localeCompare(
                        b.ingredient
                    );
                }
            );

            /*
             * Create shopping-list table.
             */
            const table =
                document.createElement(
                    "table"
                );
            const thead =
                table.createTHead();
            const headerRow =
                thead.insertRow(0);
            const headerCells = [
                "Type",
                "Ingredient",
                "Amounts"
            ];
            headerCells.forEach(
                function (headerText) {
                    const th =
                        document.createElement(
                            "th"
                        );
                    th.textContent =
                        headerText;
                    headerRow.appendChild(
                        th
                    );
                }
            );

            const tbody =
                table.createTBody();
            condensedIngredients.forEach(
                function (item) {
                    const row =
                        tbody.insertRow();
                    const typeCell =
                        row.insertCell(0);
                    const ingredientCell =
                        row.insertCell(1);
                    const amountCell =
                        row.insertCell(2);

                    typeCell.textContent =
                        item.type;
                    ingredientCell.textContent =
                        item.ingredient;

                    const measurements =
                        Object.values(
                            item.measurements
                        );
                    const measurementText =
                        measurements.map(
                            function (measurement) {
                                let quantity =
                                    measurement.quantity;
                                quantity =
                                    Number(
                                        quantity.toFixed(2)
                                    );
                                if (
                                    measurement.unit ===
                                    "approximately"
                                ) {
                                    return (
                                        "est " +
                                        quantity
                                    );
                                }
                                return (
                                    (
                                        measurement.estimated
                                            ? "est "
                                            : ""
                                    ) +
                                    quantity +
                                    " " +
                                    measurement.unit
                                );
                            }
                        ).join(", ");

                    amountCell.textContent =
                        "(" +
                        measurementText +
                        ")";
                }
            );

            /*
             * Replace the old shopping-list table.
             */
            const tableContainer =
                document.getElementById(
                    "table__container"
                );
            tableContainer.innerHTML = "";
            tableContainer.appendChild(
                table
            );

            /*
             * Update selected recipe list.
             */
            const recipeList =
                document.getElementById(
                    "recipe__list"
                );
            recipeList.textContent =
                "Selected recipes: " +
                data.recipe_list.join(", ");

            var downloadContainer =
                document.getElementById(
                    "download__container"
                );
            if (downloadContainer) {
                downloadContainer.style.display =
                    selectedItems.length > 0
                        ? "block"
                        : "none";
            }
        }
    )
    .catch(
        function (error) {
            console.error(
                "Error:",
                error
            );
        }
    );
}
