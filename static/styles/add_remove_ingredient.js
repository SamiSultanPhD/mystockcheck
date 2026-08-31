document.addEventListener(
    "DOMContentLoaded",
    function () {

        const ingredientContainer =
            document.getElementById(
                "ingredientContainer"
            );


        const newIngredientButton =
            document.getElementById(
                "button__new__ingredient"
            );


        /*
         * Remove an ingredient.
         */

        ingredientContainer.addEventListener(
            "click",
            function (event) {

                if (
                    !event.target.classList.contains(
                        "button__remove__ingredient"
                    )
                ) {

                    return;

                }


                const contentInstance =
                    event.target.closest(
                        ".new__recipe__content"
                    );


                const updateContentInstance =
                    event.target.closest(
                        ".update__recipe__content"
                    );


                if (contentInstance) {

                    contentInstance.remove();

                }


                else if (
                    updateContentInstance
                ) {

                    updateContentInstance.remove();

                }

            }
        );


        /*
         * Add a new ingredient.
         */

        newIngredientButton.addEventListener(
            "click",
            function () {

                /*
                 * The hidden template is the
                 * .new__recipe__content element.
                 */

                const template =
                    document.querySelector(
                        ".new__recipe__content"
                    );


                if (!template) {
                    return;
                }


                const newContent =
                    template.cloneNode(
                        true
                    );


                /*
                 * Clear the ingredient field.
                 */

                const ingredient =
                    newContent.querySelector(
                        "#new__recipe__ingredient"
                    );


                if (ingredient) {

                    ingredient.value = "";

                }


                /*
                 * Clear the quantity.
                 */

                const quantity =
                    newContent.querySelector(
                        "#new__recipe__quantity"
                    );


                if (quantity) {

                    quantity.value = "";

                }


                /*
                 * Make the new ingredient visible.
                 */

                newContent.style.display =
                    "block";


                ingredientContainer.appendChild(
                    newContent
                );

            }
        );

    }
);