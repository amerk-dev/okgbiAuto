import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { getMaterials, getTrackSettings, updateMaterials, updateTrackSettings } from '../services/api';
import 'react-day-picker/dist/style.css';
import { DayPicker } from 'react-day-picker';

const CostParams = () => {
  const [materials, setMaterials] = useState([]);
  const [trackSettings, setTrackSettings] = useState({
    reconfigurationCost: 0,
    trackLength: 0,
    trackCount: 0,
    tracksInWork: 0,
    tailLength: 0,
  });
  const [weekendDays, setWeekendDays] = useState(new Set(['Понедельник']));
  const [selectedHolidayDates, setSelectedHolidayDates] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [materialsData, trackSettingsData] = await Promise.all([
          getMaterials(),
          getTrackSettings()
        ]);

        setMaterials(materialsData);
        setTrackSettings(trackSettingsData);

        // Update weekend days from fetched data
        if (trackSettingsData.weekendDays && trackSettingsData.weekendDays.length > 0) {
          setWeekendDays(new Set(trackSettingsData.weekendDays));
        }

        // Update holiday dates from fetched data
        if (trackSettingsData.holidayDates && trackSettingsData.holidayDates.length > 0) {
          const holidayDates = trackSettingsData.holidayDates.map(dateStr => new Date(dateStr));
          setSelectedHolidayDates(holidayDates);
        }

        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Handle material price change
  const handleMaterialPriceChange = (id, newPrice) => {
    setMaterials(materials.map(material =>
      material.id === id ? { ...material, price: newPrice } : material
    ));
  };

  // Handle track settings change
  const handleTrackSettingChange = (setting, value) => {
    setTrackSettings({
      ...trackSettings,
      [setting]: value
    });
  };

  // Toggle weekend day
  const toggleWeekendDay = (day) => {
    const newSet = new Set(weekendDays);
    if (newSet.has(day)) {
      newSet.delete(day);
    } else {
      newSet.add(day);
    }
    setWeekendDays(newSet);
  };

  // Handle holiday date selection
  const handleHolidayDateSelect = (date) => {
    const newDates = [...selectedHolidayDates];
    const index = newDates.findIndex(d =>
      d.getFullYear() === date.getFullYear() &&
      d.getMonth() === date.getMonth() &&
      d.getDate() === date.getDate()
    );

    if (index !== -1) {
      newDates.splice(index, 1);
    } else {
      newDates.push(date);
    }
    setSelectedHolidayDates(newDates);
  };

  // Save changes
  const handleSaveChanges = async () => {
    try {
      const savingIndicator = document.getElementById('saving-indicator');
      if (savingIndicator) {
        savingIndicator.classList.remove('hidden');
      }

      await Promise.all([
        updateMaterials(materials),
        updateTrackSettings({
          ...trackSettings,
          weekendDays: Array.from(weekendDays),
          holidayDates: selectedHolidayDates.map(d => d.toISOString().split('T')[0]),
        })
      ]);

      alert('Изменения успешно сохранены');
    } catch (error) {
      console.error('Error saving changes:', error);
      alert('Ошибка при сохранении изменений.');
    } finally {
      const savingIndicator = document.getElementById('saving-indicator');
      if (savingIndicator) {
        savingIndicator.classList.add('hidden');
      }
    }
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-xl font-bold text-gray-800 mb-6">Параметры стоимости производства</h1>

      <div className="flex gap-8">
        {/* Material Prices */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center mb-4">
            <span className="text-blue-600 mr-2"><svg width="26" height="26" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M13 24.375C6.7275 24.375 1.625 19.2725 1.625 13C1.625 6.7275 6.7275 1.625 13 1.625C19.2725 1.625 24.375 6.7275 24.375 13C24.375 19.2725 19.2725 24.375 13 24.375ZM13 3.25C7.62125 3.25 3.25 7.62125 3.25 13C3.25 18.3787 7.62125 22.75 13 22.75C18.3787 22.75 22.75 18.3787 22.75 13C22.75 7.62125 18.3787 3.25 13 3.25Z" fill="#1E2536"/>
<path d="M10.5625 21.125C10.1075 21.125 9.75 20.7675 9.75 20.3125V14.625H7.3125C6.8575 14.625 6.5 14.2675 6.5 13.8125C6.5 13.3575 6.8575 13 7.3125 13H9.75V7.3125C9.75 6.8575 10.1075 6.5 10.5625 6.5H15.4375C16.5149 6.5 17.5483 6.92801 18.3101 7.68988C19.072 8.45175 19.5 9.48506 19.5 10.5625C19.5 11.6399 19.072 12.6733 18.3101 13.4351C17.5483 14.197 16.5149 14.625 15.4375 14.625H11.375V20.3125C11.375 20.7675 11.0175 21.125 10.5625 21.125ZM11.375 13H15.4375C16.7863 13 17.875 11.9113 17.875 10.5625C17.875 9.21375 16.7863 8.125 15.4375 8.125H11.375V13Z" fill="#1E2536"/>
<path d="M15.4375 17.875H7.3125C6.8575 17.875 6.5 17.5175 6.5 17.0625C6.5 16.6075 6.8575 16.25 7.3125 16.25H15.4375C15.8925 16.25 16.25 16.6075 16.25 17.0625C16.25 17.5175 15.8925 17.875 15.4375 17.875Z" fill="#1E2536"/>
</svg>
</span>
            <h3 className="text-lg font-medium text-gray-900">Цены на материал</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Материал</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ед. измерения</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Стоимость</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {materials.map((material) => (
                  <tr key={material.id}>
                    <td className="px-3 py-3 text-sm font-medium text-gray-900">{material.name}</td>
                    <td className="px-3 py-3 text-sm text-gray-500">{material.unit}</td>
                    <td className="px-3 py-3 text-sm">
                      <div className="relative flex items-center">
                        <input
                          type="number"
                          className="w-full px-2 py-1 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                          value={material.price}
                          onChange={(e) => handleMaterialPriceChange(material.id, parseInt(e.target.value, 10) || 0)}
                        />
                        <button
                          onClick={() => handleMaterialPriceChange(material.id, material.price + 100)}
                          className="ml-1 text-xs text-blue-600 hover:text-blue-800"
                        >
                          ↑
                        </button>
                        <button
                          onClick={() => handleMaterialPriceChange(material.id, material.price - 100)}
                          className="ml-1 text-xs text-red-600 hover:text-red-800"
                        >
                          ↓
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Track Settings with Flex Layout */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 flex flex-col h-full">
          <div className="flex items-center mb-4">
            <span className="text-blue-600 mr-2"><svg width="18" height="23" viewBox="0 0 18 23" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M2.16667 1.75008C2.16667 1.46276 2.05253 1.18721 1.84937 0.984049C1.6462 0.780885 1.37065 0.666748 1.08333 0.666748C0.796016 0.666748 0.520466 0.780885 0.317301 0.984049C0.114137 1.18721 0 1.46276 0 1.75008V21.2501C0 21.5374 0.114137 21.8129 0.317301 22.0161C0.520466 22.2193 0.796016 22.3334 1.08333 22.3334C1.37065 22.3334 1.6462 22.2193 1.84937 22.0161C2.05253 21.8129 2.16667 21.5374 2.16667 21.2501V1.75008ZM17.3333 1.75008C17.3333 1.46276 17.2192 1.18721 17.016 0.984049C16.8129 0.780885 16.5373 0.666748 16.25 0.666748C15.9627 0.666748 15.6871 0.780885 15.484 0.984049C15.2808 1.18721 15.1667 1.46276 15.1667 1.75008V21.2501C15.1667 21.5374 15.2808 21.8129 15.484 22.0161C15.6871 22.2193 15.9627 22.3334 16.25 22.3334C16.5373 22.3334 16.8129 22.2193 17.016 22.0161C17.2192 21.8129 17.3333 21.5374 17.3333 21.2501V1.75008ZM9.75 1.75008C9.75 1.46276 9.63586 1.18721 9.4327 0.984049C9.22954 0.780885 8.95399 0.666748 8.66667 0.666748C8.37935 0.666748 8.1038 0.780885 7.90063 0.984049C7.69747 1.18721 7.58333 1.46276 7.58333 1.75008V5.00008C7.58333 5.2874 7.69747 5.56295 7.90063 5.76611C8.1038 5.96928 8.37935 6.08341 8.66667 6.08341C8.95399 6.08341 9.22954 5.96928 9.4327 5.76611C9.63586 5.56295 9.75 5.2874 9.75 5.00008V1.75008ZM7.58333 13.1251C7.58333 13.4124 7.69747 13.6879 7.90063 13.8911C8.1038 14.0943 8.37935 14.2084 8.66667 14.2084C8.95399 14.2084 9.22954 14.0943 9.4327 13.8911C9.63586 13.6879 9.75 13.4124 9.75 13.1251V9.87508C9.75 9.58776 9.63586 9.31221 9.4327 9.10905C9.22954 8.90588 8.95399 8.79175 8.66667 8.79175C8.37935 8.79175 8.1038 8.90588 7.90063 9.10905C7.69747 9.31221 7.58333 9.58776 7.58333 9.87508V13.1251ZM7.58333 18.0001C7.58333 17.7128 7.69747 17.4372 7.90063 17.234C8.1038 17.0309 8.37935 16.9167 8.66667 16.9167C8.95399 16.9167 9.22954 17.0309 9.4327 17.234C9.63586 17.4372 9.75 17.7128 9.75 18.0001V21.2501C9.75 21.5374 9.63586 21.8129 9.4327 22.0161C9.22954 22.2193 8.95399 22.3334 8.66667 22.3334C8.37935 22.3334 8.1038 22.2193 7.90063 22.0161C7.69747 21.8129 7.58333 21.5374 7.58333 21.2501V18.0001Z" fill="#1E2536"/>
</svg>
</span>
            <h3 className="text-lg font-medium text-gray-900">Настройка дорожек</h3>
          </div>

          <div className="flex space-y-4 flex-grow">
            {/* Track settings inputs */}
            <div className="grid grid-cols-1 gap-4 p-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Стоимость переналадки</label>
                <input
                  type="number"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                  value={trackSettings.reconfigurationCost}
                  onChange={(e) => handleTrackSettingChange('reconfigurationCost', parseInt(e.target.value, 10) || 0)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Длина дорожки</label>
                <input
                  type="number"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                  value={trackSettings.trackLength}
                  onChange={(e) => handleTrackSettingChange('trackLength', parseInt(e.target.value, 10) || 0)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Дорожек ВСЕГО</label>
                <input
                  type="number"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                  value={trackSettings.trackCount}
                  onChange={(e) => handleTrackSettingChange('trackCount', parseInt(e.target.value, 10) || 0)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Дорожек В РАБОТЕ</label>
                <input
                  type="number"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                  value={trackSettings.tracksInWork}
                  onChange={(e) => handleTrackSettingChange('tracksInWork', parseInt(e.target.value, 10) || 0)}
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Длина хвоста</label>
                <input
                  type="number"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
                  value={trackSettings.tailLength}
                  onChange={(e) => handleTrackSettingChange('tailLength', parseInt(e.target.value, 10) || 0)}
                />
              </div>
            </div>

            {/* Weekend days */}
            <div className="px-5">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Настройка выходных</h4>
              <div className="grid grid-cols-1 gap-2">
                {['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'].map((day) => (
                  <label key={day} className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={weekendDays.has(day)}
                      onChange={() => toggleWeekendDay(day)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">{day}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Holiday calendar with multiple selection */}
            <div className="flex-grow px-5">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Выбрать выходной день</h4>
              <div className="border border-gray-300 rounded-md p-2 max-h-64 overflow-auto">
                <DayPicker
                  mode="multiple"
                  selected={selectedHolidayDates}
                  onSelect={setSelectedHolidayDates}
                  showOutsideDays
                  locale="ru"
                  firstDayOfWeek={1}
                  classNames={{
                    selected: 'bg-blue-500 text-white',
                    today: 'text-blue-600 font-bold'
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="mt-8 flex justify-end">
        <button
          className="inline-flex items-center px-6 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          onClick={handleSaveChanges}
        >
          <FontAwesomeIcon icon="save" className="mr-2" /> Сохранить и продолжить
        </button>
      </div>

      {/* Saving indicator */}
      <div id="saving-indicator" className="hidden mt-4 text-sm text-gray-500">
        <div className="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-blue-600 mr-2"></div>
        <span>Сохранение...</span>
      </div>
    </div>
  );
};

export default CostParams;
