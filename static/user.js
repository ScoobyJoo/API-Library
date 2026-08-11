const loginSection = document.getElementById('login-section');
const loginForm = document.getElementById('login-form');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const loginStatus = document.getElementById('login-status');

const appContent = document.getElementById('app-content');
const welcomeMessage = document.getElementById('welcome-message');
const logoutBtn = document.getElementById('logout-btn');

const searchInput = document.getElementById('book-search');
const booksTableBody = document.getElementById('books-table-body');
const loansTableBody = document.getElementById('loans-table-body');
const status = document.getElementById('status');

let currentCustomer = null;
let books = [];
let categoriesById = {};

// Function to escape HTML special characters
function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value ?? '';
    return div.innerHTML;
}

// Function to handle user login
async function login(event) {
    event.preventDefault();
    loginStatus.textContent = '';

    const username = usernameInput.value.trim().toLowerCase();
    const password = passwordInput.value.trim().toLowerCase();

    // Not real auth
    const response = await fetch('/api/customers');
    const customers = await response.json();
    const match = customers.find(c => {
        const firstName = c.first_name.trim().toLowerCase();
        const lastName = c.last_name.trim().toLowerCase();
        return firstName === username && lastName === password;
    });

    // Invalid login will print error message
    if (!match) {
        loginStatus.textContent = 'Invalid username or password.';
        return;
    }

    currentCustomer = match;
    loginForm.reset();
    loginSection.hidden = true;
    appContent.hidden = false;
    welcomeMessage.textContent = `Logged in as ${match.first_name} ${match.last_name}`;

    await loadCategories();
    await loadBooks();
    await loadMyLoans();
}

// Function to handle user logout
function logout() {
    currentCustomer = null;
    appContent.hidden = true;
    loginSection.hidden = false;
    status.textContent = '';
    loginStatus.textContent = '';
}

// Function to load categories
async function loadCategories() {
    const response = await fetch('/api/categories');
    const categories = await response.json();
    categoriesById = Object.fromEntries(categories.map(c => [c.id, c.name]));
}

// Function to load books
async function loadBooks() {
    const response = await fetch('/api/books');
    books = await response.json();
    renderBooksTable();
}

// Function to render the books table with the current list of books
function renderBooksTable() {
    const term = searchInput.value.trim().toLowerCase();
    const filtered = term
        ? books.filter(b => b.title.toLowerCase().includes(term) || b.author.toLowerCase().includes(term))
        : books;

    booksTableBody.innerHTML = filtered.map(book => `
        <tr>
            <td>${escapeHtml(book.title)}</td>
            <td>${escapeHtml(book.author)}</td>
            <td>${escapeHtml(categoriesById[book.category_id] ?? book.category_id)}</td>
            <td>${book.available_copies} / ${book.total_copies}</td>
            <td>
                <button type="button" data-checkout="${book.id}" ${book.available_copies < 1 ? 'disabled' : ''}>
                    Check Out
                </button>
            </td>
        </tr>
    `).join('');
}

// Function to load the current user's loans and render them in the table
async function loadMyLoans() {
    if (!currentCustomer) {
        loansTableBody.innerHTML = '';
        return;
    }

    const response = await fetch(`/api/loans?customer_id=${encodeURIComponent(currentCustomer.id)}`);
    const loans = await response.json();
    const myLoans = loans.filter(loan => loan.status !== 'returned');
    const booksById = Object.fromEntries(books.map(b => [b.id, b]));

    loansTableBody.innerHTML = myLoans.map(loan => {
        const book = booksById[loan.book_id];
        return `
            <tr>
                <td>${book ? escapeHtml(book.title) : `book ${loan.book_id}`}</td>
                <td>${escapeHtml(loan.checkout_date)}</td>
                <td>${escapeHtml(loan.due_date)}</td>
                <td>${escapeHtml(loan.status)}</td>
                <td><button type="button" data-return="${loan.id}">Return</button></td>
            </tr>
        `;
    }).join('');
}

// Function to handle the checkout of a book to the current user
async function checkoutBook(bookId) {
    status.textContent = '';
    if (!currentCustomer) {
        status.textContent = 'Log in before checking out a book.';
        return;
    }

    const response = await fetch('/api/loans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ book_id: bookId, customer_id: currentCustomer.id }),
    });
    const data = await response.json();

    if (!response.ok) {
        status.textContent = `Error: ${data.error}`;
        return;
    }

    status.textContent = 'Book checked out.';
    await loadBooks();
    await loadMyLoans();
}

// Function to handle the return of a loan by its ID
async function returnLoan(loanId) {
    status.textContent = '';

    const response = await fetch(`/api/loans/${loanId}/return`, { method: 'POST' });
    const data = await response.json();

    if (!response.ok) {
        status.textContent = `Error: ${data.error}`;
        return;
    }

    status.textContent = 'Book returned.';
    await loadBooks();
    await loadMyLoans();
}

// Event listeners for user interactions
booksTableBody.addEventListener('click', (event) => {
    const bookId = event.target.dataset.checkout;
    if (bookId) {
        checkoutBook(Number(bookId));
    }
});

// Event listener for returning books
loansTableBody.addEventListener('click', (event) => {
    const loanId = event.target.dataset.return;
    if (loanId) {
        returnLoan(Number(loanId));
    }
});

// Event listeners for search input
searchInput.addEventListener('input', renderBooksTable);

// Event listeners for login and logout
loginForm.addEventListener('submit', login);
logoutBtn.addEventListener('click', logout);
