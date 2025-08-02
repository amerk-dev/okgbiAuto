import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { getOrders, getStock, deleteOrder } from '../services/api';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [usedStock, setUsedStock] = useState([]);
  const [availableStock, setAvailableStock] = useState([]);
  const [unplacedSlabs, setUnplacedSlabs] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch orders and stock data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ordersData, stockData] = await Promise.all([
          getOrders(),
          getStock()
        ]);

        setOrders(ordersData);
        setUsedStock(stockData.usedStock);
        setAvailableStock(stockData.availableStock);
        setUnplacedSlabs(stockData.unplacedSlabs);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedConcrete, setSelectedConcrete] = useState('');
  const [minWidth, setMinWidth] = useState('');
  const [maxWidth, setMaxWidth] = useState('');
  const [minHeight, setMinHeight] = useState('');
  const [maxHeight, setMaxHeight] = useState('');
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Get unique values for filter dropdowns
  const uniqueStatuses = [...new Set(orders.map(order => order.status))];
  const uniqueConcreteClasses = [...new Set(orders.map(order => order.concrete))];

  const handleCustomerFilter = (e) => {
    setSelectedCustomer(e.target.value);
  };

  const handleStatusFilter = (e) => {
    setSelectedStatus(e.target.value);
  };

  const handleConcreteFilter = (e) => {
    setSelectedConcrete(e.target.value);
  };

  const handleMinWidthChange = (e) => {
    setMinWidth(e.target.value);
  };

  const handleMaxWidthChange = (e) => {
    setMaxWidth(e.target.value);
  };

  const handleMinHeightChange = (e) => {
    setMinHeight(e.target.value);
  };

  const handleMaxHeightChange = (e) => {
    setMaxHeight(e.target.value);
  };

  // Filter orders based on selected filters
  const filteredOrders = orders.filter(order => {
    // Filter by customer
    if (selectedCustomer && !order.customer.includes(selectedCustomer)) {
      return false;
    }

    // Filter by status
    if (selectedStatus && order.status !== selectedStatus) {
      return false;
    }

    // Filter by concrete class
    if (selectedConcrete && order.concrete !== selectedConcrete) {
      return false;
    }

    // Filter by width range
    if (minWidth && order.width < parseInt(minWidth)) {
      return false;
    }
    if (maxWidth && order.width > parseInt(maxWidth)) {
      return false;
    }

    // Filter by height range
    if (minHeight && order.height < parseInt(minHeight)) {
      return false;
    }
    if (maxHeight && order.height > parseInt(maxHeight)) {
      return false;
    }

    return true;
  });

  const handleEditOrder = (orderId) => {
    console.log(`Editing order: ${orderId}`);
    // In a real app, you would open an edit form or modal
  };

  const handleDeleteOrder = async (orderId) => {
    if (window.confirm(`Вы уверены, что хотите удалить заказ ${orderId}?`)) {
      try {
        await deleteOrder(orderId);
        // Remove the deleted order from the state
        setOrders(orders.filter(order => order.id !== orderId));
      } catch (error) {
        console.error('Error deleting order:', error);
        alert('Ошибка при удалении заказа. Пожалуйста, попробуйте снова.');
      }
    }
  };

  const handleNewOrder = () => {
    console.log('Creating new order');
    // In a real app, you would open a form or modal to create a new order
  };

  const handleViewDeleted = () => {
    console.log('Viewing deleted orders');
    // In a real app, you would show deleted orders
  };

  return (
    <div id="orders">
      {loading && (
        <div className="bg-white shadow rounded-lg overflow-hidden mb-4">
          <div className="p-10 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600">Загрузка данных о заказах и остатках...</p>
          </div>
        </div>
      )}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Управление заказами и остатками
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Список всех заказов и доступных остатков
          </p>
        </div>

        <div className="px-4 py-5 sm:p-6">
          <div className="flex justify-between items-center mb-4">
            <button 
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              onClick={() => setIsFilterOpen(!isFilterOpen)}
            >
              <FontAwesomeIcon icon="filter" className="mr-2" /> 
              Фильтры
              <FontAwesomeIcon icon={isFilterOpen ? "chevron-up" : "chevron-down"} className="ml-2" />
            </button>

            <button 
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              onClick={handleViewDeleted}
            >
              <FontAwesomeIcon icon="trash-alt" className="mr-2" /> Удаленные
            </button>
          </div>

          {/* Filter Panel */}
          <div 
            className={`filter-panel bg-gray-50 rounded-lg shadow mb-4 transition-all duration-300 ease-in-out overflow-hidden ${
              isFilterOpen 
                ? 'max-h-[500px] opacity-100 p-4 border border-gray-200' 
                : 'max-h-0 opacity-0 p-0 m-0 border-0 pointer-events-none'
            }`}
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full mb-4">
              {/* Customer Filter */}
              <div className="relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FontAwesomeIcon icon="filter" className="text-gray-400" />
                </div>
                <select 
                  id="customer-filter" 
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  value={selectedCustomer}
                  onChange={handleCustomerFilter}
                >
                  <option value="">Все контрагенты</option>
                  <option value="ООО &quot;СтройКомплект&quot;">ООО "СтройКомплект"</option>
                  <option value="ЗАО &quot;МонолитСтрой&quot;">ЗАО "МонолитСтрой"</option>
                  <option value="ИП Петров А.В.">ИП Петров А.В.</option>
                </select>
              </div>

              {/* Status Filter */}
              <div className="relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FontAwesomeIcon icon="filter" className="text-gray-400" />
                </div>
                <select 
                  id="status-filter" 
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  value={selectedStatus}
                  onChange={handleStatusFilter}
                >
                  <option value="">Все статусы</option>
                  {uniqueStatuses.map(status => (
                    <option key={status} value={status}>{status}</option>
                  ))}
                </select>
              </div>

              {/* Concrete Class Filter */}
              <div className="relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FontAwesomeIcon icon="filter" className="text-gray-400" />
                </div>
                <select 
                  id="concrete-filter" 
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  value={selectedConcrete}
                  onChange={handleConcreteFilter}
                >
                  <option value="">Все классы бетона</option>
                  {uniqueConcreteClasses.map(concrete => (
                    <option key={concrete} value={concrete}>{concrete}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Dimension Filters */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
              <div className="flex space-x-2">
                <div className="relative rounded-md shadow-sm flex-1">
                  <input
                    type="number"
                    id="min-width"
                    placeholder="Мин. ширина"
                    className="block w-full pl-3 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    value={minWidth}
                    onChange={handleMinWidthChange}
                  />
                </div>
                <div className="relative rounded-md shadow-sm flex-1">
                  <input
                    type="number"
                    id="max-width"
                    placeholder="Макс. ширина"
                    className="block w-full pl-3 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    value={maxWidth}
                    onChange={handleMaxWidthChange}
                  />
                </div>
              </div>

              <div className="flex space-x-2">
                <div className="relative rounded-md shadow-sm flex-1">
                  <input
                    type="number"
                    id="min-height"
                    placeholder="Мин. высота"
                    className="block w-full pl-3 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    value={minHeight}
                    onChange={handleMinHeightChange}
                  />
                </div>
                <div className="relative rounded-md shadow-sm flex-1">
                  <input
                    type="number"
                    id="max-height"
                    placeholder="Макс. высота"
                    className="block w-full pl-3 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    value={maxHeight}
                    onChange={handleMaxHeightChange}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Orders Table */}
          <div className="overflow-x-auto responsive-table" style={{width: "100%"}}>
            <table className="min-w-full divide-y divide-gray-200" style={{width: "100%", fontSize: "0.9rem"}}>
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
                    <div className="flex items-center">
                      <span>Дата отгрузки</span>
                      <FontAwesomeIcon icon="sort" className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
                    <div className="flex items-center">
                      <span>Дата изготовления</span>
                      <FontAwesomeIcon icon="sort" className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
                    <div className="flex items-center">
                      <span>№ заказа</span>
                      <FontAwesomeIcon icon="sort" className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
                    <div className="flex items-center">
                      <span>Контрагент</span>
                      <FontAwesomeIcon icon="sort" className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
                    <div className="flex items-center">
                      <span>Наименование</span>
                      <FontAwesomeIcon icon="sort" className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
                    <div className="flex items-center">
                      <span>Длина, мм</span>
                      <FontAwesomeIcon icon="sort" className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
                    <div className="flex items-center">
                      <span>Ширина, мм</span>
                      <FontAwesomeIcon icon="sort" className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
                    <div className="flex items-center">
                      <span>Высота, мм</span>
                      <FontAwesomeIcon icon="sort" className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
                    <div className="flex items-center">
                      <span>Нагрузка</span>
                      <FontAwesomeIcon icon="sort" className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
                    <div className="flex items-center">
                      <span>Класс бетона</span>
                      <FontAwesomeIcon icon="sort" className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
                    <div className="flex items-center">
                      <span>Проволока верх, шт</span>
                      <FontAwesomeIcon icon="sort" className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
                    <div className="flex items-center">
                      <span>Проволока низ, шт</span>
                      <FontAwesomeIcon icon="sort" className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
                    <div className="flex items-center">
                      <span>Кол-во плит</span>
                      <FontAwesomeIcon icon="sort" className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100">
                    <div className="flex items-center">
                      <span>Статус</span>
                      <FontAwesomeIcon icon="sort" className="ml-1 text-gray-400" />
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredOrders.map(order => (
                  <tr key={order.id} className={order.status === 'Просрочен' ? 'bg-red-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.deadline}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.completeDate || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #{order.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.customer}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.length}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.width}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.height}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.capacity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.concrete}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.wireTop}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.wireBottom}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.slabCount}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${order.statusClass}`}>
                        {order.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button 
                        className="text-red-600 hover:text-red-900"
                        onClick={() => handleDeleteOrder(order.id)}
                      >
                        <FontAwesomeIcon icon="trash-alt" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Stock Tables */}
          <div className="mt-8 grid grid-cols-1 gap-6">
            {/* Used Stock */}
            <div className="bg-gray-50 p-4 rounded-lg shadow">
              <h4 className="text-lg font-medium text-gray-900 mb-4">
                <FontAwesomeIcon icon="cubes" className="mr-2" /> Использованные остатки
              </h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200" style={{width: "100%"}}>
                  <thead className="bg-gray-100">
                    <tr>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Заказ
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Наименование
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Длина, мм
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ширина, мм
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Высота, мм
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Нагрузка
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Класс бетона
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Проволока верх, шт
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Проволока низ, шт
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Количество, шт
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {usedStock.map(item => (
                      <tr key={item.id}>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          #{item.order}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.name}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.length}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.width}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.height}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.capacity}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.concrete}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.wireTop}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.wireBottom}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Available Stock */}
            <div className="bg-gray-50 p-4 rounded-lg shadow">
              <h4 className="text-lg font-medium text-gray-900 mb-4">
                <FontAwesomeIcon icon="box-open" className="mr-2" /> Доступные остатки
              </h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200" style={{width: "100%"}}>
                  <thead className="bg-gray-100">
                    <tr>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Наименование
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Длина, мм
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ширина, мм
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Высота, мм
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Нагрузка
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Класс бетона
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Проволока верх, шт
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Проволока низ, шт
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Количество, шт
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {availableStock.map(item => (
                      <tr key={item.id}>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.name}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.length}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.width}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.height}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.capacity}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.concrete}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.wireTop}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.wireBottom}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Unplaced Slabs */}
            <div className="bg-gray-50 p-4 rounded-lg shadow">
              <h4 className="text-lg font-medium text-gray-900 mb-4">
                <FontAwesomeIcon icon="exclamation-triangle" className="mr-2" /> Неразмещенные плиты
              </h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200" style={{width: "100%"}}>
                  <thead className="bg-gray-100">
                    <tr>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Наименование
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Длина, мм
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ширина, мм
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Высота, мм
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Нагрузка
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Класс бетона
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Проволока верх, шт
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Проволока низ, шт
                      </th>
                      <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Количество, шт
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {unplacedSlabs.map(item => (
                      <tr key={item.id}>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.name}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.length}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.width}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.height}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.capacity}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.concrete}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.wireTop}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.wireBottom}
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                          {item.count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Orders;
