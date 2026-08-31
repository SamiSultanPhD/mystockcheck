document.addEventListener(
    "DOMContentLoaded",
    function () {
        var downloadButton =
            document.getElementById(
                "download__button"
            );
        if (!downloadButton) {
            return;
        }

        downloadButton.addEventListener(
            "click",
            function () {
                /*
                 * Get the selected recipe names.
                 */
                var recipeListEl =
                    document.getElementById(
                        "recipe__list"
                    );
                var recipes = [];
                if (
                    recipeListEl &&
                    recipeListEl.textContent.trim()
                ) {
                    var text =
                        recipeListEl.textContent
                            .replace(
                                "Selected recipes: ",
                                ""
                            );
                    if (text.trim()) {
                        recipes =
                            text.split(",").map(
                                function (s) {
                                    return s.trim();
                                }
                            );
                    }
                }

                /*
                 * Get the shopping list table rows.
                 */
                var ingredients = [];
                var tableContainer =
                    document.getElementById(
                        "table__container"
                    );
                if (tableContainer) {
                    var rows =
                        tableContainer.querySelectorAll(
                            "tbody tr"
                        );
                    rows.forEach(function (row) {
                        var cells =
                            row.querySelectorAll("td");
                        if (cells.length >= 3) {
                            ingredients.push({
                                type:
                                    cells[0].textContent.trim(),
                                ingredient:
                                    cells[1].textContent.trim(),
                                amounts:
                                    cells[2].textContent.trim()
                            });
                        }
                    });
                }

                if (ingredients.length === 0) {
                    return;
                }

                /*
                 * Build the text file.
                 */
                var lines = [];

                lines.push("SELECTED RECIPES");
                lines.push("================");
                recipes.forEach(function (name) {
                    lines.push("- " + name);
                });
                lines.push("");
                lines.push("");
                lines.push("SHOPPING LIST");
                lines.push("=============");
                lines.push("");

                /*
                 * Group ingredients by type.
                 */
                var currentType = "";
                ingredients.forEach(
                    function (item) {
                        if (
                            item.type !== currentType
                        ) {
                            if (currentType !== "") {
                                lines.push("");
                            }
                            currentType = item.type;
                            lines.push(
                                currentType.toUpperCase()
                            );
                            lines.push(
                                "-".repeat(
                                    currentType.length
                                )
                            );
                        }
                        lines.push(
                            "[ ] " +
                            item.ingredient +
                            "  " +
                            item.amounts
                        );
                    }
                );

                var content =
                    lines.join("\n");

                /*
                 * Trigger a file download.
                 */
                var blob = new Blob(
                    [content],
                    { type: "text/plain" }
                );
                var url =
                    URL.createObjectURL(blob);
                var link =
                    document.createElement("a");
                link.href = url;
                                var now = new Date();
                var pad = function (n) {
                    return n < 10 ? "0" + n : n;
                };
                var fileName =
                    "shopping_list_" +
                    now.getFullYear() +
                    "-" + pad(now.getMonth() + 1) +
                    "-" + pad(now.getDate()) +
                    "_" + pad(now.getHours()) +
                    "-" + pad(now.getMinutes()) +
                    ".txt";
                link.download = fileName;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            }
        );
    }
);
