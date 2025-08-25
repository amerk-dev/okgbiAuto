import React from 'react';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';

const Header = ({title, stats, actions, loading = false, onAction}) => {
	// Color mapping for action buttons
	const colorMap = {
		blue: 'bg-blue-700 hover:bg-blue-800',
		green: 'bg-green-600 hover:bg-green-700',
		yellow: 'bg-yellow-600 hover:bg-yellow-700',
		purple: 'bg-purple-600 hover:bg-purple-700',
		indigo: 'bg-indigo-700 hover:bg-indigo-800',
		orange: 'bg-orange-600 hover:bg-orange-700',
		red: 'bg-red-600 hover:bg-red-700',
	};

	// Filter stats by section
	const todayStats = stats.filter(stat => stat.section === 'Статистика на сегодня');
	const generalStats = stats.filter(stat => stat.section === 'Общая статистика');
	const kpiStats = stats.filter(stat => stat.section === 'KPI расстановки плит');

	return (
		<div className="mx-auto space-y-4 px-10">
      {/* Header with title and date/print - Block 1 */}
			<div className="bg-white rounded-b-xl shadow-sm p-6">
        <header className="flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-700 tracking-wider">{title}</h1>
          <div className="flex items-center gap-4">
            <input type="date" className="border border-gray-300 rounded-md px-3 py-1.5 text-sm text-gray-500" />
            <button className="flex items-center gap-2 px-4 py-2 text-sm border border-gray-300 rounded-md text-gray-600 hover:bg-gray-50">
              <FontAwesomeIcon icon="print" className="w-5 h-5" />
              <span>Печать</span>
            </button>
          </div>
        </header>
      </div>

      <div style={{display: 'flex', justifyContent: 'space-between', width: '100%'}}>
      {/* Stats - Block 2 */}
		  {loading ? (
			  <div className="bg-white rounded-xl shadow-sm p-6 text-center py-10">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Загрузка статистики...</p>
        </div>
		  ) : (
			  <div className="bg-white rounded-xl shadow-sm p-6" style={{width: '80%'}}>
          <div className="flex text-sm" style={{gap: '100px'}}>
            {/* Today's Stats */}
			  <div>
              <h3 className="font-semibold text-gray-800 mb-3">Статистика на сегодня</h3>
              <div className="space-y-2.5 text-gray-600">
                {todayStats.map(stat => (
					<p key={stat.id} className="flex items-center">
                    <FontAwesomeIcon icon={stat.icon} className="text-blue-600 mr-2 w-6 h-6" />
						{stat.title}:
                    <span className={stat.highlight ? "text-red-600 font-semibold ml-1" : "ml-1"}>
                      {stat.value}
                    </span>
                  </p>
				))}
              </div>
            </div>

			  {/* General Stats */}
			  <div>
              <h3 className="font-semibold text-gray-800 mb-3">Общая статистика</h3>
              <div className="space-y-2.5 text-gray-600">
                {generalStats.slice(0, 3).map(stat => (
					<p key={stat.id} className="flex items-center">
                    <FontAwesomeIcon icon={stat.icon} className="text-blue-600 mr-2 w-6 h-6" />
						{stat.title}:
                    <span className="font-semibold ml-1">{stat.value}</span>
                  </p>
				))}
              </div>
            </div>
            <div>
              <h3 className="font-semibold text-white mb-3">Общая статистика</h3>
              <div className="space-y-2.5 text-gray-600">
                {generalStats.slice(3,).map(stat => (
					<p key={stat.id} className="flex items-center">
                    <FontAwesomeIcon icon={stat.icon} className="text-blue-600 mr-2 w-6 h-6" />
						{stat.title}:
                    <span className="font-semibold ml-1">{stat.value}</span>
                  </p>
				))}
              </div>
            </div>
			  <div>
			  <h3 className="font-semibold mb-3">KPI расстановки плит</h3>
			  <div className="space-y-2.5 text-gray-600">
				{kpiStats.slice(0, 3).map(stat => (
					<p key={stat.id} className="flex items-center">
					<FontAwesomeIcon icon={stat.icon} className="text-blue-600 mr-2 w-6 h-6" />
						{stat.title}:
					<span className="font-semibold ml-1">{stat.value}</span>
				  </p>
				))}
			  </div>
			  </div>
          </div>
        </div>
		  )}

		  {/* Action Buttons - Block 3 */}
		  <div className="bg-white rounded-xl shadow-sm p-10 flex justify-end">
        <div className="flex gap-3" style={{flexDirection: 'column'}}>
          {actions.map(action => (
			  <button
				  style={{height: '45px'}}
				  key={action.id}
				  className={`${colorMap[action.color]} text-white px-5 py-2.5 rounded-lg text-sm font-semibold`}
				  onClick={() => onAction && onAction(action.id)}
			  >
              {action.label}
            </button>
		  ))}
        </div>
      </div>
        </div>
    </div>
	);
};

export default Header;
