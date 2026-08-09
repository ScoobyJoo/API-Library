const categorySelect = document.getElementById('category');
const form = document.getElementById('add-book-form');
const status = document.getElementById('add-book-status');
const bookIdField = document.getElementById('book-id');
const formHeading = document.getElementById('form-heading');
const submitBtn = document.getElementById('form-submit-btn');
const cancelBtn = document.getElementById('cancel-edit-btn');
const booksTableBody = document.getElementById('books-table-body');

let categoriesById = {};
let books = [];

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value ?? '';
    return div.innerHTML;
}

async function loadCategories() {
    const response = await fetch('/api/categories');
    const categories = await response.json();
    categoriesById = Object.fromEntries(categories.map(c => [c.id, c.name]));
    categorySelect.innerHTML = categories
        .map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`)
        .join('');
}

async function loadBooks() {
    const response = await fetch('/api/books');
    books = await response.json();
    renderBooksTable();
}

function renderBooksTable() {
    booksTableBody.innerHTML = books.map(book => `
        <tr>
            <td>${escapeHtml(book.title)}</td>
            <td>${escapeHtml(book.author)}</td>
            <td>${escapeHtml(book.isbn)}</td>
            <td>${escapeHtml(categoriesById[book.category_id] ?? book.category_id)}</td>
            <td>${book.total_copies}</td>
            <td>${book.available_copies}</td>
            <td>${book.published_year ?? ''}</td>
            <td>
                <button type="button" data-edit="${book.id}">Edit</button>
                <button type="button" data-delete="${book.id}">Delete</button>
            </td>
        </tr>
    `).join('');
}

function startEdit(book) {
    bookIdField.value = book.id;
    document.getElementById('title').value = book.title;
    document.getElementById('author').value = book.author;
    document.getElementById('isbn').value = book.isbn;
    categorySelect.value = book.category_id;
    document.getElementById('total_copies').value = book.total_copies;
    document.getElementById('published_year').value = book.published_year ?? '';

    formHeading.textContent = 'Edit Book';
    submitBtn.textContent = 'Update Book';
    cancelBtn.style.display = 'inline-block';
    status.textContent = '';
}

function resetForm() {
    form.reset();
    bookIdField.value = '';
    formHeading.textContent = 'Create a New Book';
    submitBtn.textContent = 'Add Book';
    cancelBtn.style.display = 'none';
}

async function submitBook(event) {
    event.preventDefault();
    status.textContent = '';

    const payload = {
        title: document.getElementById('title').value,
        author: document.getElementById('author').value,
        isbn: document.getElementById('isbn').value,
        category_id: Number(categorySelect.value),
        total_copies: Number(document.getElementById('total_copies').value),
        published_year: document.getElementById('published_year').value
            ? Number(document.getElementById('published_year').value)
            : null,
    };

    const editingId = bookIdField.value;
    const url = editingId ? `/api/books/${editingId}` : '/api/books';
    const method = editingId ? 'PATCH' : 'POST';

    const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (!response.ok) {
        status.textContent = `Error: ${data.error}`;
        return;
    }

    status.textContent = editingId
        ? `Updated "${data.title}" (id ${data.id})`
        : `Added "${data.title}" (id ${data.id})`;
    resetForm();
    loadBooks();
}

async function deleteBook(bookId) {
    status.textContent = '';

    const response = await fetch(`/api/books/${bookId}`, { method: 'DELETE' });

    if (!response.ok) {
        const data = await response.json();
        status.textContent = `Error: ${data.error}`;
        return;
    }

    if (bookIdField.value === String(bookId)) {
        resetForm();
    }
    status.textContent = `Deleted book ${bookId}`;
    loadBooks();
}

booksTableBody.addEventListener('click', (event) => {
    const editId = event.target.dataset.edit;
    const deleteId = event.target.dataset.delete;

    if (editId) {
        const book = books.find(b => b.id === Number(editId));
        if (book) startEdit(book);
    } else if (deleteId) {
        deleteBook(Number(deleteId));
    }
});

form.addEventListener('submit', submitBook);
cancelBtn.addEventListener('click', resetForm);

loadCategories().then(loadBooks);