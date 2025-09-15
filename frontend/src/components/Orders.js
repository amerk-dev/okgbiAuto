import React, { useState, useEffect, useMemo } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { getOrders, deleteOrder, getContractors, getDeletedOrders, restoreOrder } from '../services/api';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [contractors, setContractors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewingDeleted, setViewingDeleted] = useState(false);

  // Состояние для сортировки
  const [sortConfig, setSortConfig] = useState({
    key: 'deadline',
    direction: 'asc'
  });

  // Fetch orders and contractors data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [ordersData, contractorsData] = await Promise.all([
          viewingDeleted ? getDeletedOrders() : getOrders(),
          getContractors()
        ]);
        setOrders(ordersData);
        setContractors(contractorsData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, [viewingDeleted]);

  const [selectedCustomer, setSelectedCustomer] = useState([]);
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedConcrete, setSelectedConcrete] = useState([]);
  const [selectedWidths, setSelectedWidths] = useState([]);
  const [selectedLengths, setSelectedLengths] = useState([]);
  const [selectedHeights, setSelectedHeights] = useState([]);
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Функция для сортировки
  const requestSort = (key) => {
    let direction = 'asc';
    let newKey = key;

    if (sortConfig.key === key) {
      if (sortConfig.direction === 'asc') {
        direction = 'desc';
      } else if (sortConfig.direction === 'desc') {
        // Третье нажатие - сброс сортировки
        newKey = null;
        direction = 'asc';
      }
    }

    setSortConfig({ key: newKey, direction });
  };

  // Мемоизированные уникальные значения для фильтров
  const { uniqueConcreteClasses, uniqueWidths, uniqueLengths, uniqueHeights, uniqueCustomers } = useMemo(() => {
    return {
      uniqueConcreteClasses: [...new Set(orders.map(order => order.concrete))].sort(),
      uniqueWidths: [...new Set(orders.map(order => order.width))].sort((a, b) => a - b),
      uniqueLengths: [...new Set(orders.map(order => order.length))].sort((a, b) => a - b),
      uniqueHeights: [...new Set(orders.map(order => order.height))].sort((a, b) => a - b),
      uniqueCustomers: [...new Set(orders.map(order => order.customer))]
    };
  }, [orders]);

  // Очистка фильтров при изменении данных
  useEffect(() => {
    // Убираем выбранные значения, которых больше нет в данных
    setSelectedConcrete(prev => prev.filter(c => uniqueConcreteClasses.includes(c)));
    setSelectedWidths(prev => prev.filter(w => uniqueWidths.includes(w)));
    setSelectedLengths(prev => prev.filter(l => uniqueLengths.includes(l)));
    setSelectedHeights(prev => prev.filter(h => uniqueHeights.includes(h)));

    // Для статуса мы теперь используем фиксированные значения, поэтому не нужно проверять
    // Проверяем только контрагентов - удаляем тех, которых больше нет в данных
    if (selectedCustomer.length > 0) {
      setSelectedCustomer(selectedCustomer.filter(customer => uniqueCustomers.includes(customer)));
    }
  }, [orders, uniqueConcreteClasses, uniqueWidths, uniqueLengths, uniqueHeights, uniqueCustomers]);

  const handleConcreteChange = (concrete) => {
    setSelectedConcrete(prev =>
      prev.includes(concrete)
        ? prev.filter(c => c !== concrete)
        : [...prev, concrete]
    );
  };

  const handleWidthChange = (width) => {
    setSelectedWidths(prev =>
      prev.includes(width)
        ? prev.filter(w => w !== width)
        : [...prev, width]
    );
  };

  const handleLengthChange = (length) => {
    setSelectedLengths(prev =>
      prev.includes(length)
        ? prev.filter(l => l !== length)
        : [...prev, length]
    );
  };

  const handleHeightChange = (height) => {
    setSelectedHeights(prev =>
      prev.includes(height)
        ? prev.filter(h => h !== height)
        : [...prev, height]
    );
  };

  // Filter orders based on selected filters
  const filteredOrders = orders.filter(order => {
    // Filter by customer
    if (selectedCustomer.length > 0 && !selectedCustomer.includes(order.customer)) {
      return false;
    }

    // Filter by status
    if (selectedStatus === 'overdue' && !order.status) {
      return false;
    }
    if (selectedStatus === 'not_overdue' && order.status) {
      return false;
    }

    // Filter by concrete class
    if (selectedConcrete.length > 0 && !selectedConcrete.includes(order.concrete)) {
      return false;
    }

    // Filter by width
    if (selectedWidths.length > 0 && !selectedWidths.includes(order.width)) {
      return false;
    }

    // Filter by length
    if (selectedLengths.length > 0 && !selectedLengths.includes(order.length)) {
      return false;
    }

    // Filter by height
    if (selectedHeights.length > 0 && !selectedHeights.includes(order.height)) {
      return false;
    }

    return true;
  });

  // Функция для парсинга даты
  const parseDate = (dateString) => {
    if (!dateString || dateString === '-') return null;
    // Предполагаем формат DD.MM.YYYY
    const parts = dateString.split('.');
    if (parts.length === 3) {
      return new Date(parts[2], parts[1] - 1, parts[0]);
    }
    return new Date(dateString);
  };

  // Сортировка отфильтрованных заказов
  const sortedOrders = useMemo(() => {
    const sortableItems = [...filteredOrders];
    if (sortConfig.key) {
      sortableItems.sort((a, b) => {
        // Получаем значения для сравнения
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];

        // Обработка специальных случаев
        if (sortConfig.key === 'number') {
          // Сортировка по номеру заказа (убираем #)
          aValue = parseInt(aValue.replace('#', '')) || 0;
          bValue = parseInt(bValue.replace('#', '')) || 0;
        }

        // Обработка дат
        if (sortConfig.key === 'deadline' || sortConfig.key === 'completeDate') {
          if (sortConfig.key === 'completeDate' && (aValue === '-' || !aValue)) aValue = null;
          if (sortConfig.key === 'completeDate' && (bValue === '-' || !bValue)) bValue = null;

          const aDate = parseDate(aValue);
          const bDate = parseDate(bValue);

          if (aDate === null && bDate === null) return 0;
          if (aDate === null) return 1;
          if (bDate === null) return -1;

          aValue = aDate;
          bValue = bDate;
        }

        // Обработка null/undefined значений
        if (aValue == null) aValue = '';
        if (bValue == null) bValue = '';

        // Сравнение
        if (aValue instanceof Date && bValue instanceof Date) {
          // Сравнение дат
          if (aValue < bValue) {
            return sortConfig.direction === 'asc' ? -1 : 1;
          }
          if (aValue > bValue) {
            return sortConfig.direction === 'asc' ? 1 : -1;
          }
          return 0;
        } else if (typeof aValue === 'string' && typeof bValue === 'string') {
          aValue = aValue.toLowerCase();
          bValue = bValue.toLowerCase();
        }

        if (aValue < bValue) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [filteredOrders, sortConfig]);

  const handleEditOrder = (orderId) => {
    console.log(`Editing order: ${orderId}`);
    // In a real app, you would open an edit form or modal
  };

  const handleDeleteOrder = async (orderId, plateName) => {
    if (window.confirm(`Вы уверены, что хотите удалить заказ ${orderId}?`)) {
      try {
        await deleteOrder(orderId, plateName);
        // Remove the deleted order from the state
        setOrders(orders.filter(order => order.id !== orderId));
      } catch (error) {
        console.error('Error deleting order:', error);
        alert('Ошибка при удалении заказа. Пожалуйста, попробуйте снова.');
      }
    }
  };

  const handleRestoreOrder = async (orderId, plateName) => {
    if (window.confirm(`Вы уверены, что хотите восстановить заказ ${orderId}?`)) {
      try {
        await restoreOrder(orderId, plateName);
        // Remove the restored order from the state
        setOrders(orders.filter(order => order.id !== orderId));
      } catch (error) {
        console.error('Error restoring order:', error);
        alert('Ошибка при восстановлении заказа. Пожалуйста, попробуйте снова.');
      }
    }
  };

  const handleNewOrder = () => {
    console.log('Creating new order');
    // In a real app, you would open a form or modal to create a new order
  };

  const handleViewDeleted = () => {
    setViewingDeleted(!viewingDeleted);
  };

  const resetFilters = () => {
    setSelectedCustomer([]);
    setSelectedStatus('');
    setSelectedConcrete([]);
    setSelectedWidths([]);
    setSelectedLengths([]);
    setSelectedHeights([]);
  };

  const hasActiveFilters = selectedCustomer.length > 0 || selectedStatus ||
    selectedConcrete.length > 0 || selectedWidths.length > 0 ||
    selectedLengths.length > 0 || selectedHeights.length > 0;

  // Функция для получения иконки сортировки
  const getSortIcon = (columnKey) => {
    if (sortConfig.key === columnKey) {
      return sortConfig.direction === 'asc' ? 'sort-up' : 'sort-down';
    }
    return 'sort';
  };

  return (
    <div id="orders">
      {loading && (
        <div className="bg-white shadow rounded-lg overflow-hidden mb-4">
          <div className="p-10 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600">Загрузка данных о заказах...</p>
          </div>
        </div>
      )}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            {viewingDeleted ? 'Удаленные заказы' : 'Управление заказами'}
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {viewingDeleted ? 'Список удаленных заказов' : 'Список всех заказов'}
          </p>
        </div>

        <div className="px-4 py-5 sm:p-6">
          <div className="flex justify-between items-center mb-4">
            <div className="flex space-x-2">
              <button
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                onClick={() => setIsFilterOpen(!isFilterOpen)}
              >
                <FontAwesomeIcon icon="filter" className="mr-2" />
                Фильтры
                <FontAwesomeIcon icon={isFilterOpen ? "chevron-up" : "chevron-down"} className="ml-2" />
              </button>

              {hasActiveFilters && (
                <button
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  onClick={resetFilters}
                >
                  Сбросить
                </button>
              )}
            </div>

            <button
              className={`inline-flex items-center px-3 py-2 border shadow-sm text-sm leading-4 font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                viewingDeleted 
                  ? 'border-blue-500 text-blue-700 bg-blue-50 hover:bg-blue-100' 
                  : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
              }`}
              onClick={handleViewDeleted}
            >
              <FontAwesomeIcon icon={viewingDeleted ? "arrow-left" : "trash-alt"} className="mr-2" />
              {viewingDeleted ? 'Вернуться к активным' : 'Удаленные'}
            </button>
          </div>

          {/* Filter Panel */}
          <div
            className={`filter-panel bg-gray-50 rounded-lg shadow mb-4 transition-all duration-300 ease-in-out overflow-hidden ${
              isFilterOpen 
                ? 'max-h-[600px] opacity-100 p-4 border border-gray-200' 
                : 'max-h-0 opacity-0 p-0 m-0 border-0 pointer-events-none'
            }`}
          >
            <div className="grid grid-cols-1 md:grid-cols-6 gap-4 w-full">
              {/* Customer Filter with Tags */}
              <div className="col-span-1 bg-white p-3 rounded-lg shadow">
                <label htmlFor="customer-filter" className="block text-sm font-medium text-gray-700 mb-1">
                  Выбор контрагентов
                </label>
                <select
                  id="customer-filter"
                  className="block w-full pl-3 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  value=""
                  onChange={(e) => {
                    if (e.target.value && !selectedCustomer.includes(e.target.value)) {
                      setSelectedCustomer([...selectedCustomer, e.target.value]);
                    }
                  }}
                >
                  <option value="">Выберите контрагента</option>
                  {contractors
                    .filter(contractor => !selectedCustomer.includes(contractor))
                    .map((contractor, index) => (
                      <option key={index} value={contractor}>
                        {contractor}
                      </option>
                    ))}
                </select>

                {selectedCustomer.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {selectedCustomer.map((customer, index) => (
                      <span key={index} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {customer}
                        <button
                          onClick={() => setSelectedCustomer(selectedCustomer.filter(c => c !== customer))}
                          className="ml-1 text-blue-600 hover:text-blue-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Status Filter */}
              <div className="bg-white p-3 rounded-lg shadow">
                <label className="block text-sm font-medium text-gray-700 mb-1">Статус</label>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      checked={selectedStatus === ''}
                      onChange={() => setSelectedStatus('')}
                      className="border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Все</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      checked={selectedStatus === 'overdue'}
                      onChange={() => setSelectedStatus('overdue')}
                      className="border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Просрочен</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      checked={selectedStatus === 'not_overdue'}
                      onChange={() => setSelectedStatus('not_overdue')}
                      className="border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Не просрочен</span>
                  </label>
                </div>
              </div>

              {/* Concrete Class Filter */}
              <div className="bg-white p-3 rounded-lg shadow">
                <label className="block text-sm font-medium text-gray-700 mb-1">Класс бетона</label>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {uniqueConcreteClasses && uniqueConcreteClasses.length > 0 && uniqueConcreteClasses.map(concrete => (
                    <label key={concrete} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedConcrete.includes(concrete)}
                        onChange={() => handleConcreteChange(concrete)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">{concrete}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Width Filter */}
              <div className="bg-white p-3 rounded-lg shadow">
                <label className="block text-sm font-medium text-gray-700 mb-1">Ширина, мм</label>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {uniqueWidths && uniqueWidths.length > 0 && uniqueWidths.map(width => (
                    <label key={width} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedWidths.includes(width)}
                        onChange={() => handleWidthChange(width)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">{width}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Length Filter */}
              <div className="bg-white p-3 rounded-lg shadow">
                <label className="block text-sm font-medium text-gray-700 mb-1">Длина, мм</label>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {uniqueLengths && uniqueLengths.length > 0 && uniqueLengths.map(length => (
                    <label key={length} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedLengths.includes(length)}
                        onChange={() => handleLengthChange(length)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">{length}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Height Filter */}
              <div className="bg-white p-3 rounded-lg shadow">
                <label className="block text-sm font-medium text-gray-700 mb-1">Высота, мм</label>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {uniqueHeights && uniqueHeights.length > 0 && uniqueHeights.map(height => (
                    <label key={height} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedHeights.includes(height)}
                        onChange={() => handleHeightChange(height)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">{height}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Orders Table */}
          <div className="overflow-x-auto responsive-table" style={{width: "100%"}}>
            <table className="min-w-full divide-y divide-gray-200" style={{width: "100%", fontSize: "0.75rem"}}>
              <thead className="bg-gray-50">
                <tr>
                  <th
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    style={{ fontSize: "0.7rem" }}
                    onClick={() => requestSort('deadline')}
                  >
                    <div className="flex items-center">
                      <span>Дата отгрузки</span>
                      <FontAwesomeIcon icon={getSortIcon('deadline')} className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    style={{ fontSize: "0.7rem" }}
                    onClick={() => requestSort('completeDate')}
                  >
                    <div className="flex items-center">
                      <span>Дата изготовления</span>
                      <FontAwesomeIcon icon={getSortIcon('completeDate')} className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    style={{ fontSize: "0.7rem" }}
                    onClick={() => requestSort('number')}
                  >
                    <div className="flex items-center">
                      <span>№ заказа</span>
                      <FontAwesomeIcon icon={getSortIcon('number')} className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    style={{ fontSize: "0.7rem" }}
                    onClick={() => requestSort('customer')}
                  >
                    <div className="flex items-center">
                      <span>Контрагент</span>
                      <FontAwesomeIcon icon={getSortIcon('customer')} className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    style={{ fontSize: "0.7rem" }}
                    onClick={() => requestSort('name')}
                  >
                    <div className="flex items-center">
                      <span>Наименование</span>
                      <FontAwesomeIcon icon={getSortIcon('name')} className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    style={{ fontSize: "0.7rem" }}
                    onClick={() => requestSort('length')}
                  >
                    <div className="flex items-center">
                      <span>Длина, мм</span>
                      <FontAwesomeIcon icon={getSortIcon('length')} className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    style={{ fontSize: "0.7rem" }}
                    onClick={() => requestSort('width')}
                  >
                    <div className="flex items-center">
                      <span>Ширина, мм</span>
                      <FontAwesomeIcon icon={getSortIcon('width')} className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    style={{ fontSize: "0.7rem" }}
                    onClick={() => requestSort('height')}
                  >
                    <div className="flex items-center">
                      <span>Высота, мм</span>
                      <FontAwesomeIcon icon={getSortIcon('height')} className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    style={{ fontSize: "0.7rem" }}
                    onClick={() => requestSort('capacity')}
                  >
                    <div className="flex items-center">
                      <span>Нагрузка</span>
                      <FontAwesomeIcon icon={getSortIcon('capacity')} className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    style={{ fontSize: "0.7rem" }}
                    onClick={() => requestSort('concrete')}
                  >
                    <div className="flex items-center">
                      <span>Класс бетона</span>
                      <FontAwesomeIcon icon={getSortIcon('concrete')} className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    style={{ fontSize: "0.7rem" }}
                    onClick={() => requestSort('wireTop')}
                  >
                    <div className="flex items-center">
                      <span>Проволока верх, шт</span>
                      <FontAwesomeIcon icon={getSortIcon('wireTop')} className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    style={{ fontSize: "0.7rem" }}
                    onClick={() => requestSort('wireBottom')}
                  >
                    <div className="flex items-center">
                      <span>Проволока низ, шт</span>
                      <FontAwesomeIcon icon={getSortIcon('wireBottom')} className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    style={{ fontSize: "0.7rem" }}
                    onClick={() => requestSort('slabCount')}
                  >
                    <div className="flex items-center">
                      <span>Кол-во плит</span>
                      <FontAwesomeIcon icon={getSortIcon('slabCount')} className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider" style={{ fontSize: "0.7rem" }}>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedOrders.map((order, index) => (
                  <tr key={index} className={order.status ? 'bg-red-50' : ''}>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">
                      {order.deadline}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">
                      {order.completeDate || '-'}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs font-medium text-gray-900">
                      #{order.number}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">
                      {order.customer}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">
                      {order.name}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">
                      {order.length}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">
                      {order.width}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">
                      {order.height}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">
                      {order.capacity}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">
                      {order.concrete}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">
                      {order.wireTop}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">
                      {order.wireBottom}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">
                      {order.slabCount}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-xs font-medium">
                      {viewingDeleted ? (
                        <button
                          className="text-green-600 hover:text-green-900"
                          onClick={() => handleRestoreOrder(order.id, order.raw_name)}
                        >
                          <FontAwesomeIcon icon="undo" />
                        </button>
                      ) : (
                        <button
                          className="text-red-600 hover:text-red-900"
                          onClick={() => handleDeleteOrder(order.id, order.raw_name)}
                        >
                          <FontAwesomeIcon icon="trash-alt" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Orders;
