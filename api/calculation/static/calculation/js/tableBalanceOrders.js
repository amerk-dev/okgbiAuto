// Соотношение столбцов и переменных в массиве данных
const headerToKeyMap = {
    "Номер заказа": "orderNumber",
    "Наименование": "name",
    "Длина, мм": "length",
    "Ширина, мм": "width",
    "Высота, мм": "height",
    "Класс бетона": "concreteClass",
    "Проболока верх, шт": "topWires",
    "Проболока низ, шт": "bottomWires",
    "Количество, шт": "quantity",
    "Дедлайн по заказу": "deadline",
};
const remaindersHeaderToKeyMap = {
    "Наименование": "name",
    "Длина, мм": "length",
    "Ширина, мм": "width",
    "Высота, мм": "height",
    "Нагрузка": "load", 
    "Класс бетона": "concreteClass",
    "Проволока верх, шт": "wiresTop",
    "Проволока низ, шт": "bottomWires",
    "Количество, шт": "quantity",
};

// Функция для создания таблицы
function createTable(data, headers, headerToKeyMap) {
    const table = document.createElement("table");
    table.classList.add("custom-table");

    // Создание заголовока таблицы
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    headerRow.classList.add("position-text");

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
        row.classList.add("position-text");

        // Определения ячейки в зависимости от типа данных
        const cells = headers.map(header => item[headerToKeyMap[header]] || "");
        
        cells.forEach(cellText => {
            const td = document.createElement("td");
            td.textContent = cellText || ""; // Если значение пустое, ставим ""
            row.appendChild(td);
        });

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    return table;
}
// Данные для заказов
const ordersData = [
    { orderNumber: "Заказ 123", name: "ПБ 60-12", length: 6000, width: 1200, height: 220, concreteClass: "В25", topWires: 4, bottomWires: 12, quantity: 10, deadline: "25.07.2024"},
    { orderNumber: "Заказ 124", name: "ПБ 72-15", length: 7200, width: 1500, height: 220, concreteClass: "В30", topWires: 5, bottomWires: 14, quantity: 8, deadline: "26.07.2024" },
    { orderNumber: "Заказ 125", name: "ПБ 48-10", length: 4800, width: 1000, height: 220, concreteClass: "В25", topWires: 4, bottomWires: 10, quantity: 15, deadline: "26.07.2024" },
    { orderNumber: "Заказ 125", name: "ПБ 54-12", length: 5400, width: 1200, height: 220, concreteClass: "В25", topWires: 4, bottomWires: 12, quantity: 12, deadline: "27.07.2024" },
    { orderNumber: "Заказ 126", name: "ПБ 60-15", length: 6000, width: 1500, height: 220, concreteClass: "В30", topWires: 5, bottomWires: 12, quantity: 6, deadline: "27.07.2024" },
    { orderNumber: "Заказ 126", name: "ПБ 72-10", length: 7200, width: 1000, height: 220, concreteClass: "В30", topWires: 5, bottomWires: 14, quantity: 20, deadline: "28.07.2024" },
    { orderNumber: "Заказ 126", name: "ПБ 89-12", length: 8900, width: 1200, height: 220, concreteClass: "В30", topWires: 6, bottomWires: 15, quantity: 5, deadline: "29.07.2024" },
];

// Данные для остатков
const remaindersData = [
    { name: "ПБ 60-12", length: 6000, width: 1200, height: 220, load: 8, concreteClass: "В25", wiresTop: 4, bottomWires: 12, quantity: 10 },
    { name: "ПБ 72-15", length: 7200, width: 1500, height: 220, load: 6, concreteClass: "В30", wiresTop: 5, bottomWires: 14 ,quantity: 14 },
    { name: "ПБ 48-10", length: 4800, width: 1000, height: 220, load: 12, concreteClass: "В25", wiresTop: 4, bottomWires: 10 ,quantity: 15 },
    { name: "ПБ 54-12", length: 5400, width: 1200, height: 220, load: 16, concreteClass: "В25", wiresTop: 4, bottomWires: 12 ,quantity: 12 },
];

// Загаловки столбцов таблицы
const ordersHeaders = ["Номер заказа", "Наименование", "Длина, мм", "Ширина, мм", "Высота, мм", "Класс бетона", "Проболока верх, шт", "Проболока низ, шт","Количество, шт","Дедлайн по заказу"];
const remaindersHeaders = ["Наименование", "Длина, мм", "Ширина, мм", "Высота, мм", "Нагрузка", "Класс бетона", "Проволока верх, шт", "Проволока низ, шт","Количество, шт"];

// Генерация таблицы заказов
const ordersTable = createTable(ordersData, ordersHeaders, headerToKeyMap);
document.getElementById("ordersTableContainer").appendChild(ordersTable);
// Генерация таблицы остатков
const remaindersTable = createTable(remaindersData, remaindersHeaders, remaindersHeaderToKeyMap);
document.getElementById("remaindersTableContainer").appendChild(remaindersTable);