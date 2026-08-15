const loginSection = document.getElementById('login-section');
const loginForm = document.getElementById('login-form');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const loginStatus = document.getElementById('login-status');
const showRegisterLink = document.getElementById('show-register');

const registerSection = document.getElementById('register-section');
const registerForm = document.getElementById('register-form');
const regFirstNameInput = document.getElementById('reg-first-name');
const regLastNameInput = document.getElementById('reg-last-name');
const regEmailInput = document.getElementById('reg-email');
const regPasswordInput = document.getElementById('reg-password');
const registerStatus = document.getElementById('register-status');
const showLoginLink = document.getElementById('show-login');

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

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: emailInput.value,
                password: passwordInput.value,
            }),
        });
        const data = await response.json();

        if (!response.ok) {
            loginStatus.textContent = data.error || 'Invalid email or password.';
            return;
        }

        loginForm.reset();
        await enterApp(data);
    } catch (err) {
        loginStatus.textContent = 'Something went wrong. Please try again.';
    }
}

// Function to handle new account registration
async function registerCustomer(event) {
    event.preventDefault();
    registerStatus.textContent = '';

    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                first_name: regFirstNameInput.value,
                last_name: regLastNameInput.value,
                email: regEmailInput.value,
                password: regPasswordInput.value,
            }),
        });
        const data = await response.json();

        if (!response.ok) {
            registerStatus.textContent = data.error || 'Could not create an account.';
            return;
        }

        registerForm.reset();
        await enterApp(data);
    } catch (err) {
        registerStatus.textContent = 'Something went wrong. Please try again.';
    }
}

// Function to enter the main application after successful login or registration
async function enterApp(customer) {
    currentCustomer = customer;
    loginSection.hidden = true;
    registerSection.hidden = true;
    appContent.hidden = false;
    welcomeMessage.textContent = `Logged in as ${customer.first_name} ${customer.last_name}`;

    await loadCategories();
    await loadBooks();
    await loadMyLoans();
}

// Function to handle user logout
async function logout() {
    status.textContent = '';
    loginStatus.textContent = '';

    try {
        await fetch('/api/auth/logout', { method: 'POST' });
    } catch (err) {
        loginStatus.textContent = 'Something went wrong. Please try again.';
    }

    currentCustomer = null;
    appContent.hidden = true;
    registerSection.hidden = true;
    loginSection.hidden = false;
}

// Restores an existing session without re-prompting for credentials
async function restoreSession() {
    try {
        const response = await fetch('/api/auth/me');
        if (response.ok) {
            await enterApp(await response.json());
        }
    } catch (err) {
        loginStatus.textContent = 'Something went wrong. Please try again.';
    }
}

// Function to load categories
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const categories = await response.json();
        categoriesById = Object.fromEntries(categories.map(c => [c.id, c.name]));
    } catch (err) {
        status.textContent = 'Something went wrong. Please try again.';
    }
}

// Function to load books
async function loadBooks() {
    try {
        const response = await fetch('/api/books');
        books = await response.json();
        renderBooksTable();
    } catch (err) {
        status.textContent = 'Something went wrong. Please try again.';
    }
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

    try {
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
    } catch (err) {
        status.textContent = 'Something went wrong. Please try again.';
    }
}

// Function to handle the checkout of a book to the current user
async function checkoutBook(bookId) {
    status.textContent = '';
    if (!currentCustomer) {
        status.textContent = 'Log in before checking out a book.';
        return;
    }

    try {
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
    } catch (err) {
        status.textContent = 'Something went wrong. Please try again.';
    }
}

// Function to handle the return of a loan by its ID
async function returnLoan(loanId) {
    status.textContent = '';

    try {
        const response = await fetch(`/api/loans/${loanId}/return`, { method: 'POST' });
        const data = await response.json();

        if (!response.ok) {
            status.textContent = `Error: ${data.error}`;
            return;
        }

        status.textContent = 'Book returned.';
        await loadBooks();
        await loadMyLoans();
    } catch (err) {
        status.textContent = 'Something went wrong. Please try again.';
    }
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

// Event listeners for login, registration, and logout
loginForm.addEventListener('submit', login);
registerForm.addEventListener('submit', registerCustomer);
logoutBtn.addEventListener('click', logout);

showRegisterLink.addEventListener('click', (event) => {
    event.preventDefault();
    loginSection.hidden = true;
    registerSection.hidden = false;
});

showLoginLink.addEventListener('click', (event) => {
    event.preventDefault();
    registerSection.hidden = true;
    loginSection.hidden = false;
});

restoreSession();
