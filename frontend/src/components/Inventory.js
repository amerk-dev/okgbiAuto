import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { getStock } from '../services/api';

const Inventory = () => {
  const [availableStock, setAvailableStock] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch stock data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        const stockData = await getStock();
        // The updated StockView returns a flat array of stock items
        setAvailableStock(stockData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div id="inventory">
      {loading && (
        <div className="bg-white shadow rounded-lg overflow-hidden mb-4">
          <div className="p-10 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600">Загрузка данных об остатках...</p>
          </div>
        </div>
      )}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Управление остатками
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Список всех доступных остатков
          </p>
        </div>

        <div className="px-4 py-5 sm:p-6">
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
                    <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Заказ
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
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                        {item.order || '-'}
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
  );
};

export default Inventory;
