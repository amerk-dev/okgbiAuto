import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import axios from 'axios';

const Algorithm = () => {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedTrack, setExpandedTrack] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      setError('Пожалуйста, выберите файл для загрузки.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setExpandedTrack(null);

    const formData = new FormData();
    formData.append('demo_file', file);

    try {
      const response = await axios.post(process.env.REACT_APP_API_URL + '/api/algorithm/demo/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.result) {
        setResult(response.data.result);
      } else if (response.data.error) {
        setError(response.data.error);
      }

      // Scroll to result
      const resultElement = document.getElementById('result-container');
      if (resultElement) {
        resultElement.scrollIntoView({ behavior: 'smooth' });
      }
    } catch (error) {
      console.error('Error submitting file:', error);
      setError(error.response?.data?.error || 'Произошла ошибка при обработке файла. Пожалуйста, попробуйте снова.');
    } finally {
      setLoading(false);
    }
  };

  const toggleTrackExpand = (trackId) => {
    if (expandedTrack === trackId) {
      setExpandedTrack(null);
    } else {
      setExpandedTrack(trackId);
    }
  };

  return (
    <div className="mx-auto rounded-xl shadow-sm p-6 space-y-6 mt-4 bg-white">
      <div className="max-w-8xl mx-auto">
        <h1 className="text-2xl font-bold text-blue-700 mb-6">Алгоритм расчета производственного плана</h1>

        {/* Algorithm Description Section */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-blue-700 mb-4">Описание алгоритма</h2>
          <p className="text-gray-700 mb-4">
            Алгоритм расчета производственного плана оптимизирует размещение плит на дорожках с учетом нескольких ключевых факторов:
          </p>

          <div className="ml-5 mb-3 relative pl-5 text-gray-700">
            <div className="absolute left-0 top-1.5 w-2 h-2 rounded-full bg-blue-700"></div>
            <strong>1. Использование готовых плит:</strong> Алгоритм сначала проверяет наличие готовых плит, которые могут быть использованы для выполнения заказов.
          </div>

          <div className="ml-5 mb-3 relative pl-5 text-gray-700">
            <div className="absolute left-0 top-1.5 w-2 h-2 rounded-full bg-blue-700"></div>
            <strong>2. Приоритет заказчиков:</strong> Плиты для дорожек с назначенными заказчиками размещаются в первую очередь.
          </div>

          <div className="ml-5 mb-3 relative pl-5 text-gray-700">
            <div className="absolute left-0 top-1.5 w-2 h-2 rounded-full bg-blue-700"></div>
            <strong>3. Соблюдение сроков:</strong> Плиты с дедлайнами имеют приоритет над плитами без дедлайнов.
          </div>

          <div className="ml-5 mb-3 relative pl-5 text-gray-700">
            <div className="absolute left-0 top-1.5 w-2 h-2 rounded-full bg-blue-700"></div>
            <strong>4. Оптимизация размеров:</strong> Плиты группируются по размерам для минимизации переналадок оборудования.
          </div>

          <div className="ml-5 mb-3 relative pl-5 text-gray-700">
            <div className="absolute left-0 top-1.5 w-2 h-2 rounded-full bg-blue-700"></div>
            <strong>5. Максимальное использование дорожек:</strong> Алгоритм стремится максимально заполнить каждую дорожку.
          </div>

          <h3 className="text-lg font-bold text-blue-700 mt-6 mb-4">Как работает алгоритм</h3>

          <div className="ml-5 mb-3 relative pl-5 text-gray-700">
            <div className="absolute left-0 top-1.5 w-2 h-2 rounded-full bg-blue-700"></div>
            <strong>Подготовительный этап:</strong> 
            <ul className="list-disc ml-8 mt-2">
              <li>Создание пустых дорожек для планирования</li>
              <li>Проверка наличия готовых плит и их использование для заказов</li>
              <li>Обработка дорожек с назначенными заказчиками</li>
            </ul>
          </div>

          <div className="ml-5 mb-3 relative pl-5 text-gray-700">
            <div className="absolute left-0 top-1.5 w-2 h-2 rounded-full bg-blue-700"></div>
            <strong>Основной алгоритм размещения:</strong>
            <ul className="list-disc ml-8 mt-2">
              <li>Разделение плит на группы с дедлайнами и без дедлайнов</li>
              <li>Сортировка плит с дедлайнами по дате, ширине и высоте</li>
              <li>Сортировка плит без дедлайнов по ширине и высоте</li>
              <li>Последовательное размещение плит на дорожках с учетом их размеров и свободного места</li>
              <li>Приоритетное размещение плит с одинаковыми размерами на одной дорожке</li>
            </ul>
          </div>

          <div className="ml-5 mb-3 relative pl-5 text-gray-700">
            <div className="absolute left-0 top-1.5 w-2 h-2 rounded-full bg-blue-700"></div>
            <strong>Постобработка и оптимизация:</strong>
            <ul className="list-disc ml-8 mt-2">
              <li>Перераспределение плит для минимизации переналадок между дорожками</li>
              <li>Оптимизация размещения плит с учетом дедлайнов и производственного лага</li>
              <li>Перемещение дорожек с критическими дедлайнами на более ранние даты</li>
              <li>Заполнение оставшихся свободных мест на дорожках</li>
            </ul>
          </div>

          <div className="ml-5 mb-3 relative pl-5 text-gray-700">
            <div className="absolute left-0 top-1.5 w-2 h-2 rounded-full bg-blue-700"></div>
            <strong>Результат работы алгоритма:</strong> После завершения работы алгоритма, назначения плит сохраняются 
            непосредственно в базе данных:
            <ul className="list-disc ml-8 mt-2">
              <li>Поле track в модели Plate указывает, на какой дорожке размещена плита</li>
              <li>Поле day в модели Track показывает дату производства</li>
              <li>Система учитывает производственный лаг для соблюдения дедлайнов</li>
            </ul>
          </div>
        </div>

        {/* Algorithm Demo Section */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-blue-700 mb-4">Демонстрация алгоритма</h2>
          <p className="text-gray-700 mb-4">
            Вы можете загрузить файл с данными о заказах для демонстрации работы алгоритма. Система обработает данные 
            и покажет результат расчета производственного плана.
          </p>

          <div className="bg-gray-100 p-6 rounded-lg">
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block font-bold mb-2" htmlFor="demoFile">
                  Загрузите файл с данными (формат JSON):
                </label>
                <input 
                  className="w-full p-2 border border-gray-300 rounded" 
                  type="file" 
                  id="demoFile" 
                  accept=".json"
                  onChange={handleFileChange}
                />
              </div>

              <div className="mb-4">
                <a 
                  href="/static/calculation/demo/example.json"
                  download 
                  className="text-blue-700 hover:underline inline-flex items-center"
                >
                  <FontAwesomeIcon icon="download" className="mr-2" />
                  Скачать пример файла
                </a>
              </div>

              {error && (
                <div className="mb-4 text-red-600">
                  {error}
                </div>
              )}

              <button 
                type="submit" 
                className="bg-blue-700 text-white px-4 py-2 rounded hover:bg-blue-800 transition-colors"
                disabled={loading}
              >
                {loading ? 'Обработка...' : 'Запустить демонстрацию'}
              </button>
            </form>
          </div>

          {result && (
            <div id="result-container" className="mt-8 p-6 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-bold text-blue-700 mb-4">Результат расчета:</h3>

              <div className="overflow-x-auto">
                <div className="grid grid-cols-[150px_repeat(5,1fr)] gap-1 bg-gray-200 border border-gray-200 rounded-lg overflow-hidden text-xs font-medium">
                  {/* Header */}
                  <div className="p-2 bg-gray-50 text-gray-800 font-semibold flex items-center justify-center">Дорожки</div>

                  {/* Column Headers - First 5 days */}
                  {result[0].days.slice(0, 5).map((day, dayIndex) => {
                    let dateText = day.date;
                    if (day.date === 'today') dateText = 'Сегодня';
                    else if (day.date === 'tomorrow') dateText = 'Завтра';

                    return (
                      <div key={`header-${day.date}`} className="p-2 text-center bg-white">
                        <p>{dateText}</p>
                        {day.total_overendering_wire_kg !== 0 && (
                          <span className="flex items-center justify-center gap-1 text-red-600">
                            {day.total_overendering_wire_kg && `${day.total_overendering_wire_kg.toFixed(2)}КГ`}
                          </span>
                        )}
                      </div>
                    );
                  })}

                  {/* Track Rows */}
                  {result.map(track => (
                    <React.Fragment key={track.id}>
                      {/* Track Name */}
                      <div className={`p-2 bg-white font-semibold text-gray-600 flex flex-col items-center justify-center ${track.contractor ? 'border-2 border-blue-300 border-r-0' : ''}`}>
                        <div>{track.name}</div>
                        {track.contractor && (
                          <div className="mt-1 text-xs text-blue-600">{track.contractor}</div>
                        )}
                      </div>

                      {/* Track Days - First 5 days */}
                      {track.days.slice(0, 5).map((day, dayIndex) => {
                        // Determine cell styling based on status
                        let cellClass = "p-2 text-gray-400 bg-white flex items-center justify-center";
                        let cellContent = "ПУСТО";

                        if (day.reconfiguration) {
                          // Reconfiguration day
                          cellClass = "p-2 text-center text-gray-600 flex items-center justify-center font-semibold bg-[#EFF6FF]";
                          cellContent = "ВЫХОДНОЙ";
                        } else if (day.size || day.concrete || day.wireTop || day.wireBottom || day.occupied) {
                          // Day with content
                          if (day.status === 'overdue') {
                            // Delayed
                            cellClass = "p-2 relative bg-[#FFE4E4]";
                            cellContent = (
                              <>
                                <p className="flex items-center gap-1 text-red-600 font-semibold">
                                  <FontAwesomeIcon icon="exclamation-triangle" className="text-red-600" />
                                  Задержка
                                </p>
                                <div className="mt-1 space-y-0.5 text-gray-700">
                                  {day.deadline ? <p style={{color: "#1420A0"}}>До {day.deadline}</p> : <p style={{color: "#1420A0"}}>Без дедлайна</p>}
                                  <p>{day.size || 'Нет размера'}</p>
                                  <p>{day.concrete || 'Нет бетона'}</p>
                                  <p>↑{day.wireTop || '?'} ↓{day.wireBottom || '?'}</p>
                                  <p>Занято: {day.occupied || "0"}мм</p>
                                </div>
                                <p className="text-blue-600 font-bold mt-2 pt-2 border-t border-red-200">{day.price || ""}</p>
                              </>
                            );
                          } else {
                            // In progress
                            cellClass = "p-2 relative bg-[#E9FFF9]";
                            cellContent = (
                              <>
                                <p className="flex items-center gap-1 text-green-600 font-semibold">
                                  <span className="w-2 h-2 bg-green-600 rounded-full"></span>В работе
                                </p>
                                <div className="mt-1 space-y-0.5 text-gray-700">
                                  {day.deadline ? <p style={{color: "#1420A0"}}>До {day.deadline}</p> : <p style={{color: "#1420A0"}}>Без дедлайна</p>}
                                  <p>{day.size || 'Нет размера'}</p>
                                  <p>{day.concrete || 'Нет бетона'}</p>
                                  <p>↑{day.wireTop || '?'} ↓{day.wireBottom || '?'}</p>
                                  <p>Занято: {day.occupied || "0"}мм</p>
                                </div>
                                <p className="text-blue-600 font-bold mt-2 pt-2 border-t border-green-200">{day.price || ""}</p>
                              </>
                            );
                          }
                        }

                        return (
                          <div 
                            key={`${track.id}-${day.date}`}
                            className={`${cellClass} ${track.contractor ? 'border-2 border-blue-300 border-l-0' + (dayIndex === 4 ? '' : ' border-r-0') : ''}`}
                            onClick={() => toggleTrackExpand(`${track.id}-${dayIndex}`)}
                          >
                            {cellContent}
                            {day.orders && day.orders.length > 0 && (
                              <div className="absolute bottom-1 right-1">
                                <FontAwesomeIcon icon="info-circle" className="text-blue-500" title={`Заказы: ${day.orders.join(', ')}`} />
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </React.Fragment>
                  ))}
                </div>

                {/* Expanded Track Details */}
                {expandedTrack && (
                  <div className="mt-4 p-4 bg-white border border-gray-300 rounded-lg">
                    <h4 className="font-bold mb-2">Плиты на дорожке:</h4>
                    <table className="min-w-full border border-gray-300">
                      <thead>
                        <tr className="bg-gray-100">
                          <th className="py-1 px-2 border-b text-left">Название</th>
                          <th className="py-1 px-2 border-b text-left">Размеры</th>
                          <th className="py-1 px-2 border-b text-left">Бетон</th>
                          <th className="py-1 px-2 border-b text-left">Проволока</th>
                          <th className="py-1 px-2 border-b text-left">Заказ</th>
                          <th className="py-1 px-2 border-b text-left">Дедлайн</th>
                          <th className="py-1 px-2 border-b text-left">Заказчик</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(() => {
                          const [trackId, dayIndex] = expandedTrack.split('-');
                          const track = result.find(t => t.id === trackId);
                          const day = track ? track.days[dayIndex] : null;

                          if (day && day.slabs && day.slabs.length > 0) {
                            return day.slabs.map(slab => (
                              <tr key={slab.id} className="border-b">
                                <td className="py-1 px-2">{slab.name}</td>
                                <td className="py-1 px-2">{`${slab.length}x${slab.width}x${slab.height}`}</td>
                                <td className="py-1 px-2">{slab.concrete_class}</td>
                                <td className="py-1 px-2">{`${slab.wire_top}/${slab.wire_bottom}`}</td>
                                <td className="py-1 px-2">{slab.order_number}</td>
                                <td className="py-1 px-2">{slab.deadline_date}</td>
                                <td className="py-1 px-2">{slab.customer}</td>
                              </tr>
                            ));
                          } else {
                            return (
                              <tr>
                                <td colSpan="7" className="py-2 px-2 text-center text-gray-500">
                                  Нет данных о плитах для этой дорожки
                                </td>
                              </tr>
                            );
                          }
                        })()}
                      </tbody>
                    </table>
                    <button 
                      className="mt-4 px-3 py-1 bg-gray-200 rounded-md hover:bg-gray-300 text-sm"
                      onClick={() => setExpandedTrack(null)}
                    >
                      Скрыть детали
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <a href="/" className="text-blue-700 hover:underline inline-flex items-center">
          <FontAwesomeIcon icon="arrow-left" className="mr-2" />
          Вернуться на главную
        </a>
      </div>
    </div>
  );
};

export default Algorithm;
