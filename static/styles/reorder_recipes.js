document.addEventListener(
    "DOMContentLoaded",
    function () {

        const recipeList =
            document.getElementById(
                "recipeList"
            );


        if (!recipeList) {
            return;
        }


        let draggedRecipe = null;


        const recipes =
            recipeList.querySelectorAll(
                ".recipe__container__full"
            );


        recipes.forEach(
            function (recipe) {


                /*
                 * Start dragging.
                 */

                recipe.addEventListener(
                    "dragstart",
                    function (event) {

                        draggedRecipe =
                            recipe;


                        recipe.classList.add(
                            "dragging"
                        );


                        event.dataTransfer.effectAllowed =
                            "move";

                    }
                );


                /*
                 * While dragging over another recipe,
                 * move the dragged recipe before or after
                 * it depending on the mouse position.
                 */

                recipe.addEventListener(
                    "dragover",
                    function (event) {

                        event.preventDefault();


                        if (
                            !draggedRecipe ||
                            draggedRecipe === recipe
                        ) {
                            return;
                        }


                        const rect =
                            recipe.getBoundingClientRect();


                        const halfway =
                            rect.top +
                            rect.height / 2;


                        if (
                            event.clientY <
                            halfway
                        ) {

                            recipeList.insertBefore(
                                draggedRecipe,
                                recipe
                            );

                        } else {

                            recipeList.insertBefore(
                                draggedRecipe,
                                recipe.nextSibling
                            );

                        }

                    }
                );


                /*
                 * Finished dragging.
                 */

                recipe.addEventListener(
                    "dragend",
                    async function () {

                        recipe.classList.remove(
                            "dragging"
                        );


                        draggedRecipe = null;


                        await saveRecipeOrder();

                    }
                );

            }
        );


        /*
         * Send the new order to Flask.
         */

        async function saveRecipeOrder() {

            const recipes =
                Array.from(
                    recipeList.querySelectorAll(
                        ".recipe__container__full"
                    )
                );


            const recipeOrder =
                recipes.map(
                    function (recipe) {

                        return recipe.dataset.recipeNumber;

                    }
                );


            try {

                const response =
                    await fetch(
                        "/reorder-recipes/",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                order: recipeOrder
                            })
                        }
                    );


                const data =
                    await response.json();


                if (
                    !response.ok ||
                    !data.success
                ) {

                    throw new Error(
                        data.error ||
                        "Unable to save recipe order."
                    );

                }

            } catch (error) {

                console.error(
                    "Error saving recipe order:",
                    error
                );

            }

        }

    }
);