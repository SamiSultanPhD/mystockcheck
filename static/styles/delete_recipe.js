document.addEventListener(
    "DOMContentLoaded",
    function () {

        let btns_delete =
            document.querySelectorAll(
                ".delete__button"
            );


        btns_delete.forEach(
            function (btn_delete) {

                btn_delete.addEventListener(
                    "click",
                    async function (event) {

                        event.preventDefault();


                        var result =
                            confirm(
                                "Are you sure you want to DELETE this recipe?"
                            );


                        if (!result) {
                            return;
                        }


                        await deletefunction(
                            btn_delete.value
                        );


                        /*
                         * Reload the page so the recipe
                         * disappears and the new order
                         * is displayed.
                         */

                        window.location.reload();

                    }
                );

            }
        );


        async function deletefunction(
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
                "delete_recipe"
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


                if (
                    !response.ok ||
                    !data.success
                ) {

                    throw new Error(
                        data.error ||
                        "Unable to delete recipe."
                    );

                }


            } catch (error) {

                console.error(
                    error
                );

                alert(
                    "Unable to delete recipe: " +
                    error.message
                );

            }

        }

    }
);