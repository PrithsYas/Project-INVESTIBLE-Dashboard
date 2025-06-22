// Safe date injection only if the element exists
window.addEventListener('DOMContentLoaded', () => {
    const dateElement = document.getElementById('current-date');
    if (dateElement) {
        dateElement.textContent = new Date().toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    
    const searchInput = document.querySelector('.search-bar input');
    const searchButton = document.querySelector('.search-bar button');

    if (searchInput && searchButton) {
        searchButton.addEventListener('click', () => {
            const query = searchInput.value.trim().toLowerCase();

            // Map or fetch stock symbol from CSV/autocomplete backend
            const stockMap = {
                'asian paints': 'ASIANPAINT.NS',
                'tcs': 'TCS.NS',
                'reliance': 'RELIANCE.NS'
            };

            const symbol = stockMap[query];

            if (symbol) {
                window.location.href = `/dashboard?ticker=${symbol}`;
            } else {
                alert("Stock not found. Please enter a valid stock name.");
            }
        });
    }
});
