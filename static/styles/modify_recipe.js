document.addEventListener(
    "DOMContentLoaded",
    function () {

        let modify_btns =
            document.querySelectorAll(
                ".modification__button"
            );


        modify_btns.forEach(
            function (modify_btn) {

                modify_btn.addEventListener(
                    "click",
                    async function (event) {

                        event.preventDefault();


                        await modifyfunction(
                            modify_btn.value
                        );

                    }
                );

            }
        );


        async function modifyfunction(
            recipeNumber
        ) {

            var formData =
                new FormData();


            formData.append(
                "button",
                recipeNumber
            );


            formData.append(
                "request_type",
                "modify_recipe"
            );


            try {

                const response =
                    await fetch(
                        "/",
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                const data =
                    await response.json();


                /*
                 * Flask returns the recipe number.
                 *
                 * We then need to find the recipe name
                 * to construct the URL.
                 */

                const recipeCard =
                    document.querySelector(
                        '[data-recipe-number="' +
                        data +
                        '"]'
                    );


                if (!recipeCard) {

                    throw new Error(
                        "Recipe could not be found."
                    );

                }


                const recipeTitle =
                    recipeCard.querySelector(
                        ".recipe__title"
                    );


                const recipeName =
                    recipeTitle.textContent.trim();


                window.location.href =
                    "/" +
                    data +
                    "_" +
                    encodeURIComponent(
                        recipeName
                    ) +
                    "/";


            } catch (error) {

                console.error(
                    error
                );

            }

        }

    }
);