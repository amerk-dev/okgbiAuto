document.addEventListener("DOMContentLoaded", () => {
    // Получаем все кнопки и секции
    const buttons = document.querySelectorAll(".style-btn-pages");
    const sections = document.querySelectorAll(".section");

    // Функция для обновления состояния кнопок и секций
    function updateActiveButton(targetId) {
        // Удаление активного класс у всех кнопок
        buttons.forEach(button => {
            button.classList.remove("active");
        });

        // Скрытие все секции
        sections.forEach(section => {
            section.classList.add("hidden");
        });

        // Активация нажатой кнопки
        const activeButton = document.querySelector(`[data-target="${targetId}"]`);
        if (activeButton) {
            activeButton.classList.add("active");
        }

        // Показ соответствующий секции
        const activeSection = document.getElementById(targetId);
        if (activeSection) {
            activeSection.classList.remove("hidden");
        }
    }

    // Обработчики событий для кнопок
    buttons.forEach(button => {
        button.addEventListener("click", () => {
            const targetId = button.getAttribute("data-target"); // Получаем ID целевой секции
            updateActiveButton(targetId);
        });
    });

    $('#ordersAndRemaindersStat').click(function() {
        updateActiveButton('ordersAndRemaindersSection')
    })

    // Инициализация: активируем первую кнопку по умолчанию
    const defaultButton = document.querySelector(".style-btn-pages.active");
    if (defaultButton) {
        const defaultTargetId = defaultButton.getAttribute("data-target");
        updateActiveButton(defaultTargetId);
    }
});