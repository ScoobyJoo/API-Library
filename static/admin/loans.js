const checkoutForm = document.getElementById('checkout-form');
const bookSelect = document.getElementById('book');
const customerSelect = document.getElementById('customer');
const status = document.getElementById('loan-status');
const statusFilter = document.getElementById('status-filter');
const loansTableBody = document.getElementById('loans-table-body');

let booksById = {};
let customersById = {};

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value ?? '';
    return div.innerHTML;
}

async function loadBooks() {
    const response = await fetch('/api/books');
    const books = await response.json();
    booksById = Object.fromEntries(books.map(b => [b.id, b]));
    bookSelect.innerHTML = books
        .map(b => `<option value="${b.id}">${escapeHtml(b.title)} (${b.available_copies} available)</option>`)
        .join('');
}

async function loadCustomers() {
    const response = await fetch('/api/customers');
    const customers = await response.json();
    customersById = Object.fromEntries(customers.map(c => [c.id, c]));
    customerSelect.innerHTML = customers
        .map(c => `<option value="${c.id}">${escapeHtml(c.first_name)} ${escapeHtml(c.last_name)}</option>`)
        .join('');
}

async function loadLoans() {
    const params = statusFilter.value ? `?status=${encodeURIComponent(statusFilter.value)}` : '';
    const response = await fetch(`/api/loans${params}`);
    const loans = await response.json();
    renderLoansTable(loans);
}

function renderLoansTable(loans) {
    loansTableBody.innerHTML = loans.map(loan => {
        const book = booksById[loan.book_id];
        const customer = customersById[loan.customer_id];
        const bookLabel = book ? escapeHtml(book.title) : `book ${loan.book_id}`;
        const customerLabel = customer ? `${escapeHtml(customer.first_name)} ${escapeHtml(customer.last_name)}` : `customer ${loan.customer_id}`;

        return `
            <tr>
                <td>${bookLabel}</td>
                <td>${customerLabel}</td>
                <td>${escapeHtml(loan.checkout_date)}</td>
                <td>${escapeHtml(loan.due_date)}</td>
                <td>${escapeHtml(loan.return_date) || ''}</td>
                <td>${escapeHtml(loan.status)}</td>
                <td>
                    ${loan.status !== 'returned' ? `<button type="button" data-return="${loan.id}">Return</button>` : ''}
                </td>
            </tr>
        `;
    }).join('');
}

async function checkoutBook(event) {
    event.preventDefault();
    status.textContent = '';

    const payload = {
        book_id: Number(bookSelect.value),
        customer_id: Number(customerSelect.value),
    };

    const response = await fetch('/api/loans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (!response.ok) {
        status.textContent = `Error: ${data.error}`;
        return;
    }

    status.textContent = `Checked out book ${data.book_id} to customer ${data.customer_id} (loan id ${data.id})`;
    await loadBooks();
    await loadLoans();
}

async function returnLoan(loanId) {
    status.textContent = '';

    const response = await fetch(`/api/loans/${loanId}/return`, { method: 'POST' });
    const data = await response.json();

    if (!response.ok) {
        status.textContent = `Error: ${data.error}`;
        return;
    }

    status.textContent = `Loan ${loanId} marked as returned`;
    await loadBooks();
    await loadLoans();
}

loansTableBody.addEventListener('click', (event) => {
    const returnId = event.target.dataset.return;
    if (returnId) {
        returnLoan(Number(returnId));
    }
});

checkoutForm.addEventListener('submit', checkoutBook);
statusFilter.addEventListener('change', loadLoans);

Promise.all([loadBooks(), loadCustomers()]).then(loadLoans);