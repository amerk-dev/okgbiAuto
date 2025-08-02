import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { getMaterials, getTrackSettings, updateMaterials, updateTrackSettings } from '../services/api';

const CostParams = () => {
  const [materials, setMaterials] = useState([]);
  const [trackSettings, setTrackSettings] = useState({
    reconfigurationCost: 0,
    trackLength: 0,
    trackCount: 0
  });
  const [loading, setLoading] = useState(true);

  // Fetch materials and track settings data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [materialsData, trackSettingsData] = await Promise.all([
          getMaterials(),
          getTrackSettings()
        ]);

        setMaterials(materialsData);
        setTrackSettings(trackSettingsData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleMaterialPriceChange = (id, newPrice) => {
    setMaterials(materials.map(material => 
      material.id === id ? { ...material, price: newPrice } : material
    ));
  };

  const handleTrackSettingChange = (setting, value) => {
    setTrackSettings({
      ...trackSettings,
      [setting]: value
    });
  };

  const handleSaveChanges = async () => {
    try {
      // Show saving indicator
      const savingIndicator = document.getElementById('saving-indicator');
      if (savingIndicator) {
        savingIndicator.classList.remove('hidden');
      }

      // Call API to update materials and track settings
      await Promise.all([
        updateMaterials(materials),
        updateTrackSettings(trackSettings)
      ]);

      // Show success message
      alert('Изменения успешно сохранены');
    } catch (error) {
      console.error('Error saving changes:', error);
      alert('Ошибка при сохранении изменений. Пожалуйста, попробуйте снова.');
    } finally {
      // Hide saving indicator
      const savingIndicator = document.getElementById('saving-indicator');
      if (savingIndicator) {
        savingIndicator.classList.add('hidden');
      }
    }
  };

  return (
    <div id="cost-params">
      {loading && (
        <div className="bg-white shadow rounded-lg overflow-hidden mb-4">
          <div className="p-10 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600">Загрузка параметров стоимости...</p>
          </div>
        </div>
      )}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Параметры стоимости производства
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Настройка цен на материалы и параметров дорожек
          </p>
        </div>

        <div className="px-4 py-5 sm:p-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {/* Material Prices */}
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-4">
                <FontAwesomeIcon icon="tags" className="mr-2" /> Цены на материалы
              </h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Материал
                      </th>
                      <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ед. изм.
                      </th>
                      <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Цена (₽)
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {materials.map(material => (
                      <tr key={material.id}>
                        <td className="px-3 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {material.name}
                        </td>
                        <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                          {material.unit}
                        </td>
                        <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                          <input 
                            type="number" 
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm" 
                            value={material.price}
                            onChange={(e) => handleMaterialPriceChange(material.id, parseInt(e.target.value, 10) || 0)}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Track Settings */}
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-4">
                <FontAwesomeIcon icon="road" className="mr-2" /> Параметры дорожек
              </h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Стоимость переналадки (₽)
                  </label>
                  <input 
                    type="number" 
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm" 
                    value={trackSettings.reconfigurationCost}
                    onChange={(e) => handleTrackSettingChange('reconfigurationCost', parseInt(e.target.value, 10) || 0)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Длина дорожки (мм)
                  </label>
                  <input 
                    type="number" 
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm" 
                    value={trackSettings.trackLength}
                    onChange={(e) => handleTrackSettingChange('trackLength', parseInt(e.target.value, 10) || 0)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Количество дорожек
                  </label>
                  <input 
                    type="number" 
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm" 
                    value={trackSettings.trackCount}
                    onChange={(e) => handleTrackSettingChange('trackCount', parseInt(e.target.value, 10) || 0)}
                  />
                </div>
              </div>

              <div className="mt-6 flex items-center">
                <button 
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  onClick={handleSaveChanges}
                >
                  <FontAwesomeIcon icon="save" className="mr-2" /> Сохранить изменения
                </button>
                <div id="saving-indicator" className="ml-4 hidden">
                  <div className="inline-block animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-blue-600 mr-2"></div>
                  <span className="text-sm text-gray-600">Сохранение...</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CostParams;
