const form = document.getElementById('add-category-form');
const status = document.getElementById('category-status');
const categoryIdField = document.getElementById('category-id');
const formHeading = document.getElementById('form-heading');
const submitBtn = document.getElementById('form-submit-btn');
const cancelBtn = document.getElementById('cancel-edit-btn');
const categoriesTableBody = document.getElementById('categories-table-body');

let categories = [];

// Function to escape HTML special characters 
function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value ?? '';
    return div.innerHTML;
}

// Function to load categories from the API and render them in the table
async function loadCategories() {
    const response = await fetch('/api/categories');
    categories = await response.json();
    renderCategoriesTable();
}

// Function to render the categories table with the current list of categories
function renderCategoriesTable() {
    categoriesTableBody.innerHTML = categories.map(category => `
        <tr>
            <td>${escapeHtml(category.name)}</td>
            <td>${escapeHtml(category.description)}</td>
            <td>
                <button type="button" data-edit="${category.id}">Edit</button>
                <button type="button" data-delete="${category.id}">Delete</button>
            </td>
        </tr>
    `).join('');
}

// Function to start editing a category by populating the form with its data
function startEdit(category) {
    categoryIdField.value = category.id;
    document.getElementById('name').value = category.name;
    document.getElementById('description').value = category.description ?? '';

    formHeading.textContent = 'Edit Category';
    submitBtn.textContent = 'Update Category';
    cancelBtn.style.display = 'inline-block';
    status.textContent = '';
}

// Function to reset the form to its initial state
function resetForm() {
    form.reset();
    categoryIdField.value = '';
    formHeading.textContent = 'Create a New Category';
    submitBtn.textContent = 'Add Category';
    cancelBtn.style.display = 'none';
}

// Function to handle form submission for adding or editing a category
async function submitCategory(event) {
    event.preventDefault();
    status.textContent = '';

    const payload = {
        name: document.getElementById('name').value,
        description: document.getElementById('description').value || null,
    };

    const editingId = categoryIdField.value;
    const url = editingId ? `/api/categories/${editingId}` : '/api/categories';
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
        ? `Updated "${data.name}" (id ${data.id})`
        : `Added "${data.name}" (id ${data.id})`;
    resetForm();
    loadCategories();
}

// Function to delete a category by its ID
async function deleteCategory(categoryId) {
    status.textContent = '';

    const response = await fetch(`/api/categories/${categoryId}`, { method: 'DELETE' });

    if (!response.ok) {
        const data = await response.json();
        status.textContent = `Error: ${data.error}`;
        return;
    }

    if (categoryIdField.value === String(categoryId)) {
        resetForm();
    }
    status.textContent = `Deleted category ${categoryId}`;
    loadCategories();
}

// Function to handle clicks on the categories table for edit and delete actions
categoriesTableBody.addEventListener('click', (event) => {
    const editId = event.target.dataset.edit;
    const deleteId = event.target.dataset.delete;

    if (editId) {
        const category = categories.find(c => c.id === Number(editId));
        if (category) startEdit(category);
    } else if (deleteId) {
        deleteCategory(Number(deleteId));
    }
});

form.addEventListener('submit', submitCategory);
cancelBtn.addEventListener('click', resetForm);

loadCategories();