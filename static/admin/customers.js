const form = document.getElementById('add-customer-form');
const status = document.getElementById('customer-status');
const customerIdField = document.getElementById('customer-id');
const formHeading = document.getElementById('form-heading');
const submitBtn = document.getElementById('form-submit-btn');
const cancelBtn = document.getElementById('cancel-edit-btn');
const customersTableBody = document.getElementById('customers-table-body');

let customers = [];

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value ?? '';
    return div.innerHTML;
}

async function loadCustomers() {
    const response = await fetch('/api/customers');
    customers = await response.json();
    renderCustomersTable();
}

function renderCustomersTable() {
    customersTableBody.innerHTML = customers.map(customer => `
        <tr>
            <td>${escapeHtml(customer.first_name)}</td>
            <td>${escapeHtml(customer.last_name)}</td>
            <td>${escapeHtml(customer.email)}</td>
            <td>${escapeHtml(customer.phone)}</td>
            <td>${escapeHtml(customer.membership_date)}</td>
            <td>
                <button type="button" data-edit="${customer.id}">Edit</button>
                <button type="button" data-delete="${customer.id}">Delete</button>
            </td>
        </tr>
    `).join('');
}

function startEdit(customer) {
    customerIdField.value = customer.id;
    document.getElementById('first_name').value = customer.first_name;
    document.getElementById('last_name').value = customer.last_name;
    document.getElementById('email').value = customer.email;
    document.getElementById('phone').value = customer.phone ?? '';
    document.getElementById('membership_date').value = customer.membership_date ?? '';

    formHeading.textContent = 'Edit Customer';
    submitBtn.textContent = 'Update Customer';
    cancelBtn.style.display = 'inline-block';
    status.textContent = '';
}

function resetForm() {
    form.reset();
    customerIdField.value = '';
    formHeading.textContent = 'Create a New Customer';
    submitBtn.textContent = 'Add Customer';
    cancelBtn.style.display = 'none';
}

async function submitCustomer(event) {
    event.preventDefault();
    status.textContent = '';

    const payload = {
        first_name: document.getElementById('first_name').value,
        last_name: document.getElementById('last_name').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value || null,
        membership_date: document.getElementById('membership_date').value || null,
    };

    const editingId = customerIdField.value;
    const url = editingId ? `/api/customers/${editingId}` : '/api/customers';
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
        ? `Updated ${data.first_name} ${data.last_name} (id ${data.id})`
        : `Added ${data.first_name} ${data.last_name} (id ${data.id})`;
    resetForm();
    loadCustomers();
}

async function deleteCustomer(customerId) {
    status.textContent = '';

    const response = await fetch(`/api/customers/${customerId}`, { method: 'DELETE' });

    if (!response.ok) {
        const data = await response.json();
        status.textContent = `Error: ${data.error}`;
        return;
    }

    if (customerIdField.value === String(customerId)) {
        resetForm();
    }
    status.textContent = `Deleted customer ${customerId}`;
    loadCustomers();
}

customersTableBody.addEventListener('click', (event) => {
    const editId = event.target.dataset.edit;
    const deleteId = event.target.dataset.delete;

    if (editId) {
        const customer = customers.find(c => c.id === Number(editId));
        if (customer) startEdit(customer);
    } else if (deleteId) {
        deleteCustomer(Number(deleteId));
    }
});

form.addEventListener('submit', submitCustomer);
cancelBtn.addEventListener('click', resetForm);

loadCustomers();