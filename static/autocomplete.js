document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("ticker-input");
    const suggestions = document.getElementById("suggestions");

    if (!input || !suggestions) return;

    fetch("/static/nse_stock_list.json")
        .then(res => res.json())
        .then(stockList => {
            input.addEventListener("input", function () {
                const value = this.value.toLowerCase();
                suggestions.innerHTML = "";

                if (value.length === 0) return;

                const matches = stockList.filter(stock =>
                    stock.name.toLowerCase().includes(value)
                ).slice(0, 5);

                matches.forEach(stock => {
                    const div = document.createElement("div");
                    div.classList.add("suggestion");
                    div.innerText = stock.name;
                    div.addEventListener("click", () => {
                        input.value = stock.name;
                        suggestions.innerHTML = "";
                    });
                    suggestions.appendChild(div);
                });
            });
        });
});
