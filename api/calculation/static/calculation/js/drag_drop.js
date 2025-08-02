// Функционал перетаскивания плит между дорожками
document.addEventListener('DOMContentLoaded', function() {
    // Находим все ячейки с плитами
    const plateCells = document.querySelectorAll('#dynamicTable tbody td');
    
    // Добавляем атрибуты для drag-and-drop
    plateCells.forEach(cell => {
        // Проверяем, содержит ли ячейка информацию о плите
        if (cell.querySelector('.position-info') && cell.querySelector('.position-info').textContent.trim() !== '') {
            cell.setAttribute('draggable', 'true');
            cell.classList.add('draggable-plate');
            
            // Добавляем обработчики событий для drag-and-drop
            cell.addEventListener('dragstart', handleDragStart);
            cell.addEventListener('dragend', handleDragEnd);
        }
        
        // Добавляем обработчики для всех ячеек (чтобы можно было перетаскивать в любую ячейку)
        cell.addEventListener('dragover', handleDragOver);
        cell.addEventListener('dragenter', handleDragEnter);
        cell.addEventListener('dragleave', handleDragLeave);
        cell.addEventListener('drop', handleDrop);
    });
    
    // Переменная для хранения перетаскиваемого элемента
    let draggedCell = null;
    
    // Обработчик начала перетаскивания
    function handleDragStart(e) {
        this.style.opacity = '0.4';
        draggedCell = this;
        
        // Сохраняем информацию о плите и её позиции
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', this.innerHTML);
        e.dataTransfer.setData('sourceRow', this.parentNode.rowIndex);
        e.dataTransfer.setData('sourceCol', Array.from(this.parentNode.children).indexOf(this));
    }
    
    // Обработчик окончания перетаскивания
    function handleDragEnd(e) {
        this.style.opacity = '1';
        
        // Сбрасываем стили для всех ячеек
        plateCells.forEach(cell => {
            cell.classList.remove('over');
        });
    }
    
    // Обработчик перетаскивания над ячейкой
    function handleDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault(); // Позволяет сделать drop
        }
        
        e.dataTransfer.dropEffect = 'move';
        return false;
    }
    
    // Обработчик входа в ячейку при перетаскивании
    function handleDragEnter(e) {
        this.classList.add('over');
    }
    
    // Обработчик выхода из ячейки при перетаскивании
    function handleDragLeave(e) {
        this.classList.remove('over');
    }
    
    // Обработчик сброса (drop)
    function handleDrop(e) {
        if (e.stopPropagation) {
            e.stopPropagation(); // Останавливаем всплытие события
        }
        
        // Проверяем, что перетаскивание происходит не на тот же элемент
        if (draggedCell !== this) {
            // Получаем информацию о позиции источника и цели
            const sourceRow = parseInt(e.dataTransfer.getData('sourceRow'));
            const sourceCol = parseInt(e.dataTransfer.getData('sourceCol'));
            const targetRow = this.parentNode.rowIndex;
            const targetCol = Array.from(this.parentNode.children).indexOf(this);
            
            // Проверяем, что целевая ячейка не содержит плиту
            if (!this.querySelector('.position-info') || this.querySelector('.position-info').textContent.trim() === '') {
                // Отправляем запрос на сервер для обновления позиции плиты
                movePlate(sourceRow, sourceCol, targetRow, targetCol);
            } else {
                alert('Невозможно переместить плиту в ячейку, которая уже содержит плиту');
            }
        }
        
        return false;
    }
    
    // Функция для отправки запроса на сервер
    function movePlate(sourceRow, sourceCol, targetRow, targetCol) {
        // Получаем CSRF токен
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Отправляем запрос на сервер
        fetch('/move-plate/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                sourceRow: sourceRow,
                sourceCol: sourceCol,
                targetRow: targetRow,
                targetCol: targetCol
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Обновляем страницу для отображения изменений
                window.location.reload();
            } else {
                alert('Ошибка при перемещении плиты: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при перемещении плиты');
        });
    }
});

// Добавляем стили для drag-and-drop
const style = document.createElement('style');
style.textContent = `
    .draggable-plate {
        cursor: move;
    }
    
    .over {
        border: 2px dashed #000;
    }
`;
document.head.appendChild(style);