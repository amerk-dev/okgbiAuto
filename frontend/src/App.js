import React, {useEffect, useState} from 'react';
import {library} from '@fortawesome/fontawesome-svg-core';
import {
	faArrowLeft,
	faBoxOpen,
	faCalculator,
	faCalendarCheck,
	faChevronDown,
	faChevronUp,
	faCog,
	faCubes,
	faDownload,
	faEdit,
	faExchangeAlt,
	faExclamationTriangle,
	faFileExport,
	faFilter,
	faHandPaper,
	faInfoCircle,
	faLineChart,
	faMoneyBillWave,
	faPercentage,
	faPlus,
	faPrint,
	faRoad,
	faSave,
	faSearch,
	faSort,
	faSortDown,
	faSortUp,
	faTags,
	faTrashAlt,
	faUndo,
	faWrench
} from '@fortawesome/free-solid-svg-icons';
import {exportTo1C, getDashboardStats, startCalculation, getCalculationStatus} from './services/api';

import Header from './components/Header';
import TabNavigation from './components/TabNavigation';
import TrackAvailability from './components/TrackAvailability';
import Orders from './components/Orders';
import Inventory from './components/Inventory';
import CostParams from './components/CostParams';
import Algorithm from './components/Algorithm';

// Add all icons to the library
library.add(
	faRoad, faCubes, faUndo, faWrench, faLineChart, faPercentage, faCog, faPrint, faCalculator,
	faFileExport, faSearch, faFilter, faTrashAlt, faPlus, faSort, faSortUp, faSortDown,
	faEdit, faTags, faBoxOpen, faExclamationTriangle, faSave, faInfoCircle,
	faMoneyBillWave, faCalendarCheck, faChevronDown, faChevronUp, faExchangeAlt,
	faHandPaper, faArrowLeft, faDownload
);

function App() {
	const [activeTab, setActiveTab] = useState('track-availability');
	const [stats, setStats] = useState([]);
	const [loading, setLoading] = useState(true);
	const [calculating, setCalculating] = useState(false);
	const [exporting, setExporting] = useState(false);
	const [calculationTaskId, setCalculationTaskId] = useState(null);
	const [calculationProgress, setCalculationProgress] = useState(0);
	const [calculationMessage, setCalculationMessage] = useState('');

	// Check if we're on the algorithm page
	const isAlgorithmPage = window.location.pathname === '/algorithm';

	// Fetch dashboard stats from API
	useEffect(() => {
		const fetchStats = async () => {
			try {
				const data = await getDashboardStats();
				setStats(data);
				setLoading(false);
			}
			catch (error) {
				console.error('Error fetching dashboard stats:', error);
				setLoading(false);
			}
		};

		fetchStats();
	}, []);

	// Poll for calculation status
	useEffect(() => {
		let intervalId;

		if (calculationTaskId && calculating) {
			// Set up polling every 2 seconds
			intervalId = setInterval(async () => {
				try {
					const statusData = await getCalculationStatus(calculationTaskId);
					setCalculationProgress(statusData.progress);
					setCalculationMessage(statusData.message);

					// If calculation is completed or failed, stop polling
					if (statusData.status === 'completed' || statusData.status === 'failed') {
						setCalculating(false);
						clearInterval(intervalId);

						// Refresh the dashboard stats after calculation
						const data = await getDashboardStats();
						setStats(data);

						// Reset task ID after a short delay
						setTimeout(() => {
							setCalculationTaskId(null);
							setCalculationProgress(0);
							setCalculationMessage('');
						}, 3000);
					}
				} catch (error) {
					console.error("Error fetching calculation status:", error);
				}
			}, 2000);
		}

		// Clean up interval on unmount or when calculation is done
		return () => {
			if (intervalId) {
				clearInterval(intervalId);
			}
		};
	}, [calculationTaskId, calculating]);

	// Handle action button clicks
	const handleAction = async (actionId) => {
		// Action ID 1 is the "Calculate" button
		if (actionId === 1) {
			try {
				setCalculating(true);
				setCalculationProgress(0);
				setCalculationMessage('Запуск расчета...');

				const result = await startCalculation();
				console.log("Calculation started successfully:", result);

				// Store the task ID for polling
				if (result.task_id) {
					setCalculationTaskId(result.task_id);
				} else {
					// If no task ID is returned, stop calculating
					setCalculating(false);
					alert("Ошибка при запуске расчета: не получен ID задачи.");
				}
			}
			catch (error) {
				console.error("Error during calculation:", error);
				alert("Ошибка при запуске расчета. Пожалуйста, попробуйте снова.");
				setCalculating(false);
			}
		}
		if (actionId === 2) {
			try {
				setExporting(true);
				const result = await exportTo1C();
				if (result.status === 'success') {
					alert(result.message);
				} else {
					alert(result.message || 'Ошибка при выгрузке в 1С');
				}
			}
			catch (error) {
				console.error('Error exporting to 1C:', error);
				alert('Ошибка при выгрузке в 1С');
			}
			finally {
				setExporting(false);
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
			{isAlgorithmPage ? (
				<Algorithm />
			) : (
				<>
					<Header
						title="ПАНЕЛЬ УПРАВЛЕНИЯ"
						stats={stats}
						actions={actions}
						loading={loading || calculating || exporting}
						loadingMessage={
							exporting ? "Выгрузка в 1С..." : 
							calculating ? (calculationMessage || "Выполняется расчет...") : 
							"Загрузка статистики..."
						}
						calculationProgress={calculating ? calculationProgress : null}
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
							{activeTab === 'inventory' && <Inventory />}
							{activeTab === 'cost-params' && <CostParams />}
						</div>
					</div>
				</>
			)}
		</div>
	);
}

export default App;
