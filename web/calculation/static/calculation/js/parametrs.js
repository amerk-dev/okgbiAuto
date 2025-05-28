function createTable(data, headers, containerId) {
    // Создание основной элемент таблицы
    const table = document.createElement("table");
    table.classList.add("custom-table");

    // Создание заголовков таблицы
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");


    headers.forEach(headerText => {
        const th = document.createElement("th");
        th.textContent = headerText;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Создание тело таблицы
    const tbody = document.createElement("tbody");

    data.forEach(item => {
        const row = document.createElement("tr");

        // Определение ячейки в зависимости от типа данных
        const cells = Object.values(item);

        cells.forEach(cellText => {
            const td = document.createElement("td");
            td.textContent = cellText || ""; // Если значение пустое, ставим ""
            row.appendChild(td);
        });

        tbody.appendChild(row);
    });

    table.appendChild(tbody);

    // Добавление таблицы в указанный контейнер
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = ""; // Очищаем контейнер перед добавлением новой таблицы
        container.appendChild(table);
    }
}

// Данные для первой таблицы
const priceData = [
    { name: "Бетон В25 М350", price: 5500, unit: "₽ за 1 куб" },
    { name: "Бетон В30 М400", price: 6000, unit: "₽ за 1 куб" },
    { name: "Бетон В35 М450", price: 6500, unit: "₽ за 1 куб" },
    { name: "Бетон В40 М500", price: 7000, unit: "₽ за 1 куб" },
    { name: "Стоимость проволоки", price: 85, unit: "₽ за 1 п.м." },
    { name: "Стоимость одной переналадки", price: 15000, unit: "₽ за 1 раз" },
];

// Данные для второй таблицы
const trackData = [
    { name: "Длина дорожки", value: 85000, unit: "мм" },
];

// Генерируем первую таблицу
const priceHeaders = ["Наименование", "Цена", "Ед.изм."];
createTable(priceData, priceHeaders, "pricesContainer");

// Генерируем вторую таблицу
const trackHeaders = ["", "Размер", "Ед.изм."];
createTable(trackData, trackHeaders, "trackContainer");