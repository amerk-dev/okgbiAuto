import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

const Header = ({ title, stats, actions, loading = false, onAction }) => {
  // Color mapping from color names to hex codes (Tailwind CSS -600 shades)
  const colorMap = {
    blue: '#2563eb',    // blue-600
    green: '#16a34a',   // green-600
    yellow: '#ca8a04',  // yellow-600
    purple: '#9333ea',  // purple-600
    indigo: '#4f46e5',  // indigo-600
  };
  // Initialize state to track which sections are expanded
  const [expandedSections, setExpandedSections] = useState({
    'Статистика на сегодня': true,
    'Общая статистика': false
  });

  // Toggle section expansion
  const toggleSection = (section) => {
    setExpandedSections({
      ...expandedSections,
      [section]: !expandedSections[section]
    });
  };

  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold leading-tight text-gray-900">
              {title}
            </h1>
          </div>

          <div className="mt-4 flex md:mt-0 md:ml-4 space-x-3">
            {/* Print Block */}
            <div className="relative">
              <input type="date" className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500" />
              <button className="ml-2 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <FontAwesomeIcon icon="print" className="mr-2" /> Печать
              </button>
            </div>
          </div>
        </div>

        {/* Stats */}
        {loading ? (
          <div className="mt-6 text-center py-10">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Загрузка статистики...</p>
          </div>
        ) : (
          /* Group stats by section */
          ['Статистика на сегодня', 'Общая статистика'].map(section => (
            <div key={section} className="mt-6">
              <div 
                className="flex items-center justify-between cursor-pointer" 
                onClick={() => toggleSection(section)}
              >
                <h2 className="text-lg font-medium text-gray-900 mb-3">{section}</h2>
                <FontAwesomeIcon 
                  icon={expandedSections[section] ? 'chevron-up' : 'chevron-down'} 
                  className="text-gray-500"
                />
              </div>
              {expandedSections[section] && (
                <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
                  {stats
                    .filter(stat => stat.section === section)
                    .map(stat => (
                      <div key={stat.id} className="bg-white overflow-hidden shadow rounded-lg">
                        <div className="px-4 py-5 sm:p-6">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 rounded-md p-4" style={{ backgroundColor: colorMap[stat.color] }}>
                              <FontAwesomeIcon icon={stat.icon} className="text-white" size="2x" />
                            </div>
                            <div className="ml-5 w-0 flex-1">
                              <dl>
                                <dt className="text-sm font-medium text-gray-500 truncate">
                                  {stat.title}
                                </dt>
                                <dd>
                                  <div className="text-lg font-medium text-gray-900">
                                    {stat.value}
                                  </div>
                                </dd>
                              </dl>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          ))
        )}

        {/* Action Buttons */}
        <div className="mt-6 flex justify-end space-x-3">
          {actions.map(action => (
            <button 
              key={action.id}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              style={{ 
                backgroundColor: colorMap[action.color],
                // We can't use hover with inline styles, so we'll keep the focus ring styling with classes
              }}
              onClick={() => onAction && onAction(action.id)}
              onMouseOver={(e) => {
                // Darken the color by 10% for hover effect
                const color = colorMap[action.color];
                if (color) {
                  // Convert hex to RGB, darken, then convert back to hex
                  const r = parseInt(color.slice(1, 3), 16);
                  const g = parseInt(color.slice(3, 5), 16);
                  const b = parseInt(color.slice(5, 7), 16);
                  const darkerColor = `#${Math.max(0, Math.floor(r * 0.9)).toString(16).padStart(2, '0')}${Math.max(0, Math.floor(g * 0.9)).toString(16).padStart(2, '0')}${Math.max(0, Math.floor(b * 0.9)).toString(16).padStart(2, '0')}`;
                  e.currentTarget.style.backgroundColor = darkerColor;
                }
              }}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = colorMap[action.color]}
            >
              <FontAwesomeIcon icon={action.icon} className="mr-2" /> {action.label}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
};

export default Header;
