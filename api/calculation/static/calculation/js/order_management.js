// Функции для работы с заказами и плитами
function deleteOrder(orderId) {
    if (!confirm('Вы действительно хотите удалить этот заказ?')) {
        return;
    }
    
    fetch(`/delete-order/${orderId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Скрываем строку заказа в основной таблице
            const orderRow = document.querySelector(`.order-row[data-id="${orderId}"]`);
            if (orderRow) {
                orderRow.style.display = 'none';
            }
            
            // Обновляем страницу для отображения в таблице удаленных заказов
            window.location.reload();
        } else {
            alert('Ошибка при удалении заказа');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при удалении заказа');
    });
}

function restoreOrder(orderId) {
    if (!confirm('Вы действительно хотите восстановить этот заказ?')) {
        return;
    }
    
    fetch(`/restore-order/${orderId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Скрываем строку заказа в таблице удаленных заказов
            const orderRow = document.querySelector(`.deleted-order-row[data-id="${orderId}"]`);
            if (orderRow) {
                orderRow.style.display = 'none';
            }
            
            // Обновляем страницу для отображения в основной таблице
            window.location.reload();
        } else {
            alert('Ошибка при восстановлении заказа');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при восстановлении заказа');
    });
}

function deletePlate(plateType, plateId) {
    if (!confirm('Вы действительно хотите удалить эту плиту?')) {
        return;
    }
    
    fetch(`/delete-plate/${plateType}/${plateId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Обновляем страницу
            window.location.reload();
        } else {
            alert('Ошибка при удалении плиты');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при удалении плиты');
    });
}

function restorePlate(plateType, plateId) {
    if (!confirm('Вы действительно хотите восстановить эту плиту?')) {
        return;
    }
    
    fetch(`/restore-plate/${plateType}/${plateId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Обновляем страницу
            window.location.reload();
        } else {
            alert('Ошибка при восстановлении плиты');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при восстановлении плиты');
    });
}

// Сортировка таблицы
function sortTable(table, column, asc) {
    const dirModifier = asc ? 1 : -1;
    const tBody = table.tBodies[0];
    const rows = Array.from(tBody.querySelectorAll('tr'));
    
    // Сортируем строки
    const sortedRows = rows.sort((a, b) => {
        const aColValue = a.querySelector(`td:nth-child(${column + 1})`).getAttribute('data-value') || 
                         a.querySelector(`td:nth-child(${column + 1})`).textContent.trim();
        const bColValue = b.querySelector(`td:nth-child(${column + 1})`).getAttribute('data-value') || 
                         b.querySelector(`td:nth-child(${column + 1})`).textContent.trim();
        
        // Проверяем, являются ли значения числами
        const aValue = isNaN(aColValue) ? aColValue : parseFloat(aColValue);
        const bValue = isNaN(bColValue) ? bColValue : parseFloat(bColValue);
        
        return aValue > bValue ? (1 * dirModifier) : (-1 * dirModifier);
    });
    
    // Удаляем все существующие строки из таблицы
    while (tBody.firstChild) {
        tBody.removeChild(tBody.firstChild);
    }
    
    // Добавляем отсортированные строки
    tBody.append(...sortedRows);
    
    // Запоминаем текущую сортировку
    table.querySelectorAll('th').forEach(th => th.classList.remove('th-sort-asc', 'th-sort-desc'));
    table.querySelector(`th:nth-child(${column + 1})`).classList.toggle('th-sort-asc', asc);
    table.querySelector(`th:nth-child(${column + 1})`).classList.toggle('th-sort-desc', !asc);
}

// Фильтрация по контрагенту
function filterOrdersByContractor(contractorName) {
    const orderRows = document.querySelectorAll('.order-row');
    orderRows.forEach(row => {
        const rowContractor = row.getAttribute('data-contractor');
        if (!contractorName || rowContractor === contractorName) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Обработчики для кнопок удаления/восстановления заказов
    document.querySelectorAll('.delete-order-btn').forEach(button => {
        button.addEventListener('click', function() {
            const orderId = this.getAttribute('data-id');
            deleteOrder(orderId);
        });
    });
    
    document.querySelectorAll('.restore-order-btn').forEach(button => {
        button.addEventListener('click', function() {
            const orderId = this.getAttribute('data-id');
            restoreOrder(orderId);
        });
    });
    
    // Обработчик для кнопки показа/скрытия удаленных заказов
    const showDeletedOrdersBtn = document.getElementById('showDeletedOrders');
    if (showDeletedOrdersBtn) {
        showDeletedOrdersBtn.addEventListener('click', function() {
            const deletedOrdersContainer = document.getElementById('deletedOrdersContainer');
            if (deletedOrdersContainer.style.display === 'none') {
                deletedOrdersContainer.style.display = 'block';
                this.textContent = 'Скрыть удаленные';
            } else {
                deletedOrdersContainer.style.display = 'none';
                this.textContent = 'Показать удаленные';
            }
        });
    }
    
    // Обработчик для фильтра по контрагенту
    const contractorFilter = document.getElementById('orderFilterContractor');
    if (contractorFilter) {
        contractorFilter.addEventListener('change', function() {
            filterOrdersByContractor(this.value);
        });
    }
    
    // Обработчики для сортировки таблиц
    document.querySelectorAll('.sortable').forEach(headerCell => {
        headerCell.addEventListener('click', function() {
            const table = this.closest('table');
            const headerIndex = Array.prototype.indexOf.call(this.parentElement.children, this);
            const currentIsAscending = this.classList.contains('th-sort-asc');
            
            sortTable(table, headerIndex, !currentIsAscending);
        });
    });
});