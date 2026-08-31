document.addEventListener("DOMContentLoaded", function () {

/*
========================================================
RECIPE SELECTION

Clicking the main recipe card selects/deselects it.

Buttons inside the recipe card are ignored so that:

- Show ingredients doesn't select the recipe
- Other interactive controls don't accidentally select it
========================================================
*/

const recipeContainers =
    document.querySelectorAll(".recipe__container");


recipeContainers.forEach(function (container) {

    container.addEventListener("click", function (event) {

        /*
        ------------------------------------------------
        Don't select the recipe when clicking a button.
        ------------------------------------------------
        */

        if (event.target.closest("button")) {
            return;
        }


        /*
        ------------------------------------------------
        Toggle selected state.
        ------------------------------------------------
        */

        if (container.classList.contains("clicked")) {

            container.classList.remove("clicked");

        } else {

            container.classList.add("clicked");

        }

    });

});

});
