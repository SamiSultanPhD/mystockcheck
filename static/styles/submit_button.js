document.addEventListener(
    "DOMContentLoaded",
    function () {

        const recipeForm =
            document.getElementById(
                "new__recipe__submit"
            );


        if (!recipeForm) {
            return;
        }


        recipeForm.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();


                await submitRecipe();


                /*
                 * Return to the recipe list.
                 */

                window.location.href = "/";

            }
        );

    }
);


async function submitRecipe() {

    /*
     * Recipe name.
     */

    var recipeValue =
        document.getElementById(
            "new__recipe__name"
        ).value;


    /*
     * Ingredients.
     */

    var elements =
        document.querySelectorAll(
            "#new__recipe__ingredient"
        );


    var ingredientValue = [];


    elements.forEach(
        function (element) {

            ingredientValue.push(
                element.value
            );

        }
    );


    /*
     * Days.
     */

    elements =
        document.querySelectorAll(
            "#meal__days"
        );


    var dayValue = [];


    elements.forEach(
        function (element) {

            dayValue.push(
                element.value
            );

        }
    );


    /*
     * Complete meal.
     */

    elements =
        document.querySelectorAll(
            "#complete__meal"
        );


    var completeValue = [];


    elements.forEach(
        function (element) {

            completeValue.push(
                element.value
            );

        }
    );


    /*
     * Quantities.
     */

    elements =
        document.querySelectorAll(
            "#new__recipe__quantity"
        );


    var quantityValue = [];


    elements.forEach(
        function (element) {

            quantityValue.push(
                element.value
            );

        }
    );


    /*
     * Measures.
     */

    elements =
        document.querySelectorAll(
            "#measure__name"
        );


    var measureValue = [];


    elements.forEach(
        function (element) {

            measureValue.push(
                element.value
            );

        }
    );


    /*
     * Ingredient types.
     */

    elements =
        document.querySelectorAll(
            "#ingredient__type"
        );


    var typeValue = [];


    elements.forEach(
        function (element) {

            typeValue.push(
                element.value
            );

        }
    );


    /*
     * Submit/update button.
     *
     * For a new recipe this is:
     *
     * submit_new_recipe
     *
     * For an existing recipe this is its number.
     */

    var buttonValue =
        document.getElementById(
            "button__submit"
        ).value;


    /*
     * Build form data.
     */

    var formData =
        new FormData();


    formData.append(
        "recipe",
        recipeValue
    );


    formData.append(
        "ingredient",
        ingredientValue
    );


    formData.append(
        "quantity",
        quantityValue
    );


    formData.append(
        "measure",
        measureValue
    );


    formData.append(
        "day",
        dayValue
    );


    formData.append(
        "complete",
        completeValue
    );


    formData.append(
        "type",
        typeValue
    );


    formData.append(
        "button",
        buttonValue
    );


    try {

        const response =
            await fetch(
                "/newrecipe/",
                {
                    method: "POST",
                    body: formData
                }
            );


        if (!response.ok) {

            throw new Error(
                "Unable to save recipe."
            );

        }

    } catch (error) {

        console.error(
            error
        );

        alert(
            "Unable to save recipe: " +
            error.message
        );

        throw error;

    }

}