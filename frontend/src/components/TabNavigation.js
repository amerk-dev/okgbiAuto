import React from 'react';

const TabNavigation = ({ activeTab, setActiveTab }) => {
  const tabs = [
    {
      id: 'track-availability',
      label: 'Дорожки'
    },
    {
      id: 'orders',
      label: 'Заказы'
    },
    {
      id: 'inventory',
      label: 'Остатки'
    },
    {
      id: 'cost-params',
      label: 'Параметры стоимости'
    }
  ];

  const handleTabClick = (tabId) => {
    setActiveTab(tabId);
  };

  return (
    <nav className="flex gap-6 border-b border-gray-200 text-sm">
      {tabs.map(tab => (
        <button
          key={tab.id}
          className={`
            ${activeTab === tab.id 
              ? 'font-semibold text-blue-600 border-b-2 border-blue-600 pb-2' 
              : 'text-gray-500 pb-2 hover:text-blue-600'}
          `}
          onClick={() => handleTabClick(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
};

export default TabNavigation;
