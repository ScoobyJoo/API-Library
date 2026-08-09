const categorySelect = document.getElementById('category');
const form = document.getElementById('add-book-form');
const status = document.getElementById('add-book-status');

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value ?? '';
    return div.innerHTML;
}

async function loadCategories() {
    const response = await fetch('/api/categories');
    const categories = await response.json();
    categorySelect.innerHTML = categories
        .map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`)
        .join('');
}

async function addBook(event) {
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

    const response = await fetch('/api/books', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (!response.ok) {
        status.textContent = `Error: ${data.error}`;
        return;
    }

    status.textContent = `Added "${data.title}" (id ${data.id})`;
    form.reset();
}

form.addEventListener('submit', addBook);
loadCategories();