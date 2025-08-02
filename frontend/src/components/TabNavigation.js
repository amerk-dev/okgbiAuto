import React from 'react';

const TabNavigation = ({ activeTab, setActiveTab }) => {
  const tabs = [
    {
      id: 'track-availability',
      label: 'Доступность дорожек'
    },
    {
      id: 'orders',
      label: 'Остатки и заказы'
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
    <div className="border-b border-gray-200">
      <nav className="-mb-px flex space-x-8">
        {tabs.map(tab => (
          <a
            key={tab.id}
            href="#"
            data-tab={tab.id}
            className={`
              whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
              ${activeTab === tab.id 
                ? 'border-blue-500 text-blue-600' 
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
            `}
            onClick={(e) => {
              e.preventDefault();
              handleTabClick(tab.id);
            }}
          >
            {tab.label}
          </a>
        ))}
      </nav>
    </div>
  );
};

export default TabNavigation;