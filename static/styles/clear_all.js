document.addEventListener(
    "DOMContentLoaded",
    function () {
        var clearButton =
            document.getElementById(
                "clear__all__button"
            );
        if (!clearButton) {
            return;
        }

        clearButton.addEventListener(
            "click",
            function () {
                /*
                 * Remove the clicked class from
                 * every recipe card.
                 */
                var containers =
                    document.querySelectorAll(
                        ".recipe__container.clicked"
                    );
                containers.forEach(
                    function (container) {
                        container.classList.remove(
                            "clicked"
                        );
                    }
                );

                /*
                 * Clear the selected items array
                 * used by generate_shopping_list.js.
                 */
                selectedItems.length = 0;

                /*
                 * Clear the shopping list display.
                 */
                var tableContainer =
                    document.getElementById(
                        "table__container"
                    );
                if (tableContainer) {
                    tableContainer.innerHTML = "";
                }

                var recipeList =
                    document.getElementById(
                        "recipe__list"
                    );
                if (recipeList) {
                    recipeList.textContent = "";
                }

                /*
                 * Hide the download button.
                 */
                var downloadContainer =
                    document.getElementById(
                        "download__container"
                    );
                if (downloadContainer) {
                    downloadContainer.style.display =
                        "none";
                }
            }
        );
    }
);
