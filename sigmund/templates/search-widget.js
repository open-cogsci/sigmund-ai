class SearchWidget extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({mode: 'open'});
        this.offset = 0; // Initialize offset
        this.numResults = 0; // To store number of results returned

        this.shadowRoot.innerHTML = `
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.9.0/css/all.min.css" integrity="sha512-q3eWabyZPc1XTCmF+8/LuE1ozpg5xxn7iO89yfSOd5/oKvyqLngoNGsx8jq92Y8eXJ/IRxQbEC+FGSYxtk2oiw==" crossorigin="anonymous" referrerpolicy="no-referrer" />
<style>
    :host {
        display: block;
        position: relative;
        margin-bottom: 32px;
    }

    input[type="text"] {
        width: 100%;
        padding: 12px 16px 12px 16px; /* Increased padding for better touch targets */
        border: none;
        border-bottom: 1px solid #ccc; /* Minimal and clean underline style */
        border-radius: 4px 4px 0 0; /* Rounded corners on the top */
        box-sizing: border-box;
        transition: all 0.3s; /* Smooth transition for focus and hover */
        outline: none; /* Remove the default focus outline */
        font-family: "Roboto Condensed";
        font-size: 1em;
    }
    
    ul {
        margin: 0px;
        padding-inline-start: 24px;
    }
    
    a,
    a:visited {
        color: #0277bd;
    }
    
    a:hover {
        color: #FF5722;
    }

    input[type="text"]:focus {
        border-bottom-color: #0277bd; /* Material Design Primary Color when focused */
    }

    #search-button, .spinner {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        border: none;
        background: none;
        cursor: pointer;
        color: #0277bd; /* Making it consistent with Material Design primary color */
    }

    .spinner {
        display: none;
        right: 18px;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        100% { transform: translateY(-50%) rotate(360deg); }
    }

    #controls {
        display: none;
        position: absolute;
        background: white;
        border-radius: 0 0 4px 4px; /* Rounded corners on the bottom */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); /* Subtle shadow for depth */
        width: 100%;
        box-sizing: border-box;
        padding: 16px; /* Inner spacing */
        z-index: 100;
        transition: all 0.3s;
    }
    
    #powered-by-sigmund {
        float: right;
        font-family: "Roboto Condensed";
    }

    :host(.show-controls) #controls {
        display: block;
        animation: slideDown 0.3s ease-out; /* Animating appearance */
    }

    @keyframes slideDown {
        from { transform: translateY(-10px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }

    #more-button {
        display: none;
        margin-top: 16px;
        background-color: #0277bd; /* Primary color for the button */
        color: white;
        border: none;
        border-radius: 4px;
        padding: 10px 20px;
        cursor: pointer;
        transition: background-color 0.3s;
        outline: none;
        font-size: 1em;
    }

    #more-button:hover {
        background-color: #FF5722; /* Darker shade on hover */
    }
    
    #search-results ul:first-child {
        margin-top: 10px;
    }

    label {
        display: inline-block;
        font-family: "Roboto Condensed";
    }

    input[type="checkbox"] {
        accent-color: #0277bd; /* MD primary color for the checkbox */
    }
</style>

<div id="sigmund-search-widget-container">
    <input type="text" id="search-input" placeholder="Enter search query">
    <button id="search-button" aria-label="Search">
        <i class="fas fa-search"></i>
    </button>
    <span class="spinner" id="spinner">
        <i class="far fa-hourglass"></i>
    </span>
    <div id="controls">
        <div id="powered-by-sigmund">Powered by <a href="https://sigmundai.eu">SigmundAI</a></div>
        <label><input type="checkbox" id="source-checkbox"> Include forum posts</label>
        <div id="search-results"></div>
        <button id="more-button">More …</button>
    </div>
</div>`;

        this.searchInput = this.shadowRoot.getElementById('search-input');
        this.searchButton = this.shadowRoot.getElementById('search-button');
        this.spinner = this.shadowRoot.getElementById('spinner');
        this.sourceCheckbox = this.shadowRoot.getElementById('source-checkbox');
        this.searchResults = this.shadowRoot.getElementById('search-results');
        this.moreButton = this.shadowRoot.getElementById('more-button');
        this.controls = this.shadowRoot.getElementById('controls');

        this.searchButton.addEventListener('click', this.performNewSearch.bind(this));
        this.searchInput.addEventListener('keypress', this.handleSearch.bind(this));
        this.moreButton.addEventListener('click', this.handleMore.bind(this));
        this.searchInput.addEventListener('focus', () => this.classList.add('show-controls'));
        document.addEventListener('click', this.handleOutsideClick.bind(this));
    }
    
    // Handle outside click to close controls
    handleOutsideClick(e) {
        if (!this.contains(e.target)) {
            this.classList.remove('show-controls');
        }
    }
    

    handleSearch(e) {
        if (e.key === 'Enter') {
            this.performNewSearch();
        }
    }

    handleMore() {
        this.offset += 1; // Increment offset
        this.performSearch();
    }

    performNewSearch() {
        this.offset = 0; // Reset offset if a new search is initiated
        this.searchResults.innerHTML = '';
        this.performSearch();
    }

    performSearch() {
        const query = this.searchInput.value;
        if (query.length === 0) {
            return;
        }
        const source = this.sourceCheckbox.checked ? 'public-with-forum' : 'public-without-forum';
        this.classList.add('searching');
        this.searchInput.disabled = true;
        this.searchButton.style.display = 'none'; // Hide the search button
        this.spinner.style.display = 'inline'; // Show spinner        
        this.moreButton.style.display = 'none'; // Hide more button during search

        const queryObject = {
            query: query,
            source: source,
            offset: this.offset
        };

        fetch(this.endpoint, {
            method: "POST",
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(queryObject)
        })
        .then(response => response.json())
        .then(data => {
            if (data.results.length) {
                this.searchResults.innerHTML += data.results;
                this.numResults = data.results.length;
                this.moreButton.style.display = 'block'; // Show more button if results are returned
            } else {
                this.searchResults.innerHTML = 'No more results.';
                this.moreButton.style.display = 'none';
            }
        })
        .catch(error => {
            this.searchResults.innerHTML = 'Error performing search. Please try again.';
            console.error(error);
        })
        .finally(() => {
            this.classList.remove('searching');
            this.spinner.style.display = 'none';
            this.searchButton.style.display = 'inline';
            this.classList.remove('searching');
            this.searchInput.disabled = false;            
        });
    }

    get endpoint() {
        return this.getAttribute('endpoint') || '/public/search';
    }
}

customElements.define('search-widget', SearchWidget);
