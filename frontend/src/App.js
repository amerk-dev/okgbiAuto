import React, { useState, useEffect } from 'react';
import { library } from '@fortawesome/fontawesome-svg-core';
import { 
  faRoad, faCubes, faPercentage, faCog, faPrint, faCalculator, 
  faFileExport, faSearch, faFilter, faTrashAlt, faPlus, faSort, 
  faEdit, faTags, faBoxOpen, faExclamationTriangle, faSave, faInfoCircle,
  faMoneyBillWave, faCalendarCheck, faChevronDown, faChevronUp, faExchangeAlt,
  faHandPaper, faWrench, faLineChart
} from '@fortawesome/free-solid-svg-icons';
import { getDashboardStats, startCalculation } from './services/api';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

import Header from './components/Header';
import TabNavigation from './components/TabNavigation';
import TrackAvailability from './components/TrackAvailability';
import Orders from './components/Orders';
import CostParams from './components/CostParams';

// Add all icons to the library
library.add(
  faRoad, faCubes, faWrench, faLineChart, faPercentage, faCog, faPrint, faCalculator,
  faFileExport, faSearch, faFilter, faTrashAlt, faPlus, faSort, 
  faEdit, faTags, faBoxOpen, faExclamationTriangle, faSave, faInfoCircle,
  faMoneyBillWave, faCalendarCheck, faChevronDown, faChevronUp, faExchangeAlt,
  faHandPaper
);

function App() {
  const [activeTab, setActiveTab] = useState('track-availability');
  const [stats, setStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);

  // Fetch dashboard stats from API
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getDashboardStats();
        setStats(data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching dashboard stats:', error);
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  // Handle action button clicks
  const handleAction = async (actionId) => {
    // Action ID 1 is the "Calculate" button
    if (actionId === 1) {
      try {
        setCalculating(true);
        const result = await startCalculation();
        console.log("Calculation started successfully:", result);

        // Refresh the dashboard stats after calculation
        const data = await getDashboardStats();
        setStats(data);
      } catch (error) {
        console.error("Error during calculation:", error);
        alert("Ошибка при запуске расчета. Пожалуйста, попробуйте снова.");
      } finally {
        setCalculating(false);
      }
    }
  };

  // Action buttons for the header
  const actions = [
    {
      id: 1,
      label: 'Рассчитать',
      icon: 'calculator',
      color: 'green'
    },
    {
      id: 2,
      label: 'Выгрузить в 1С',
      icon: 'file-export',
      color: 'indigo'
    }
  ];

  return (
    <div className="px-10 pb-4" style={{backgroundColor: "#F8FAFD"}}>
      <Header 
        title="ПАНЕЛЬ УПРАВЛЕНИЯ"
        stats={stats}
        actions={actions}
        loading={loading || calculating}
        onAction={handleAction}
      />

      <div className="mx-auto rounded-xl shadow-sm p-6 space-y-6 mt-4">
        <TabNavigation 
          activeTab={activeTab}
          setActiveTab={setActiveTab}
        />

        <div>
          {activeTab === 'track-availability' && <TrackAvailability calculating={calculating} />}
          {activeTab === 'orders' && <Orders />}
          {activeTab === 'cost-params' && <CostParams />}
        </div>
      </div>
    </div>
  );
}

export default App;
