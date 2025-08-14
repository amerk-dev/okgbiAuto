import React, {useEffect, useState} from 'react';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import { getTracks, getContractors, updateTrackContractor, moveSlab, swapTracks, startCalculation } from '../services/api';

const TrackAvailability = ({calculating}) => {
 const [showModal, setShowModal] = useState(false);
	const [showRecalculateModal, setShowRecalculateModal] = useState(false);
	const [selectedReconfiguration, setSelectedReconfiguration] = useState(null);
	const [pendingContractorChange, setPendingContractorChange] = useState(null);
	const [contractors, setContractors] = useState([]);
	const [tracks, setTracks] = useState([]);
	const [loading, setLoading] = useState(true);

	// Fetch tracks and contractors data from API
	useEffect(() => {
		const fetchData = async () => {
			try {
				const [tracksData, contractorsData] = await Promise.all([
					getTracks(),
					getContractors()
				]);
				setTracks(tracksData);
				setContractors(contractorsData);
				setLoading(false);
			} catch (error) {
				console.error('Error fetching data:', error);
				setLoading(false);
			}
		};

		fetchData();
	}, [calculating]);

	const [draggedItem, setDraggedItem] = useState(null);
	const [draggedTrackId, setDraggedTrackId] = useState(null);
	const [draggedDayIndex, setDraggedDayIndex] = useState(null);
	const [draggedSlabIndex, setDraggedSlabIndex] = useState(null);
	const [autoScrollInterval, setAutoScrollInterval] = useState(null);
	const [isDragging, setIsDragging] = useState(false);
// Auto-scroll function
	const startAutoScroll = (e) => {
		if (autoScrollInterval) {
			clearInterval(autoScrollInterval);
		}

		const scrollContainer = document.querySelector('.responsive-table');
		if (!scrollContainer) return;

		const scrollThreshold = 50;
		const scrollSpeedLeft = 3;    // Уменьшена скорость
		const scrollSpeedRight = 3;   // Уменьшена скорость и сделана одинаковой
		const scrollSpeedVertical = 3;

		// Проверяем, что e определен, прежде чем обращаться к его свойствам
		if (!e) {
			return; // Выходим из функции, если e не определен
		}

		let currentMouseX = e.clientX;
		let currentMouseY = e.clientY;

		// Сохраняем ссылку на функцию обновления позиции мыши в глобальной переменной
		// для возможности удаления обработчика позже
		window.currentUpdateMousePosition = (e) => {
			currentMouseX = e.clientX;
			currentMouseY = e.clientY;
		};

		document.addEventListener('mousemove', window.currentUpdateMousePosition);

		const interval = setInterval(() => {
			const containerRect = scrollContainer.getBoundingClientRect();

			// Расстояния от краев контейнера
			const distanceFromLeft = currentMouseX - containerRect.left;
			const distanceFromRight = containerRect.right - currentMouseX;
			const distanceFromTop = currentMouseY - containerRect.top;
			const distanceFromBottom = containerRect.bottom - currentMouseY;

			// Расстояния от краев экрана
			const distanceFromScreenLeft = currentMouseX;
			const distanceFromScreenRight = window.innerWidth - currentMouseX;
			const distanceFromScreenTop = currentMouseY;
			const distanceFromScreenBottom = window.innerHeight - currentMouseY;

			const screenEdgeThreshold = 20;

			// Горизонтальный скролл - исправлены условия
			if ((distanceFromLeft < scrollThreshold || distanceFromScreenLeft < screenEdgeThreshold) &&
				scrollContainer.scrollLeft > 0) {
				// Проверяем, что мы действительно у левого края
				if (distanceFromLeft < scrollThreshold || distanceFromScreenLeft < screenEdgeThreshold) {
					scrollContainer.scrollLeft -= scrollSpeedLeft;
				}
			} else if ((distanceFromRight < scrollThreshold || distanceFromScreenRight < screenEdgeThreshold) &&
				scrollContainer.scrollLeft < scrollContainer.scrollWidth - scrollContainer.clientWidth) {
				// Добавлена проверка на максимальный скролл вправо
				scrollContainer.scrollLeft += scrollSpeedRight;
			}

			// Вертикальный скролл - исправлены условия
			if ((distanceFromTop < scrollThreshold || distanceFromScreenTop < screenEdgeThreshold) &&
				scrollContainer.scrollTop > 0) {
				scrollContainer.scrollTop -= scrollSpeedVertical;
			} else if ((distanceFromBottom < scrollThreshold || distanceFromScreenBottom < screenEdgeThreshold) &&
				scrollContainer.scrollTop < scrollContainer.scrollHeight - scrollContainer.clientHeight) {
				// Добавлена проверка на максимальный скролл вниз
				scrollContainer.scrollTop += scrollSpeedVertical;
			}
		}, 50); // Увеличен интервал для более плавного скролла

		setAutoScrollInterval(interval);

		return () => {
			if (window.currentUpdateMousePosition) {
				document.removeEventListener('mousemove', window.currentUpdateMousePosition);
				delete window.currentUpdateMousePosition;
			}
		};
	};

// Stop auto-scrolling
	const stopAutoScroll = () => {
		if (autoScrollInterval) {
			clearInterval(autoScrollInterval);
			setAutoScrollInterval(null);

			// Удаляем правильные обработчики событий
			document.removeEventListener('mousemove', handleGlobalDragOver);

			// Удаляем обработчик обновления позиции мыши через глобальную ссылку
			if (window.currentUpdateMousePosition) {
				document.removeEventListener('mousemove', window.currentUpdateMousePosition);
				delete window.currentUpdateMousePosition;
			}

			// Принудительная остановка скролла
			const scrollContainer = document.querySelector('.responsive-table');
			if (scrollContainer) {
				// Более надежная остановка скролла
				scrollContainer.style.scrollBehavior = 'auto'; // Отключаем плавный скролл

				const currentScrollLeft = scrollContainer.scrollLeft;
				const currentScrollTop = scrollContainer.scrollTop;

				scrollContainer.scrollLeft = currentScrollLeft;
				scrollContainer.scrollTop = currentScrollTop;

				// Восстанавливаем плавный скролл через небольшую задержку
				setTimeout(() => {
					scrollContainer.style.scrollBehavior = '';
				}, 100);
			}
		}
	};

// Улучшенный обработчик drag start
	const handleDragStart = (trackId, dayIndex, slabIndex, slab) => {
		// If slab is not provided, use the day object directly
		// This handles the case where the backend returns data directly on the day object
		if (!slab) {
			const track = tracks.find(t => t.id === trackId);
			if (track && track.days[dayIndex]) {
				slab = track.days[dayIndex];
			}
		}

		setDraggedItem(slab);
		setDraggedTrackId(trackId);
		setDraggedDayIndex(dayIndex);
		setDraggedSlabIndex(slabIndex);
		setIsDragging(true);

		// Добавляем обработчики событий
		const handleMouseMove = (e) => {
			// Запускаем автоскролл при движении мыши во время драга
			if (isDragging) {
				startAutoScroll(e);
			}
		};

		document.addEventListener('mousemove', handleMouseMove);
		document.addEventListener('dragend', handleGlobalDragEnd);

		// Очистка обработчиков
		const cleanup = () => {
			document.removeEventListener('mousemove', handleMouseMove);
			document.removeEventListener('dragend', handleGlobalDragEnd);
		};

		// Сохраняем cleanup функцию для последующего использования
		window.dragCleanup = cleanup;
	};

// Улучшенный обработчик завершения драга
	const handleGlobalDragEnd = () => {
		setIsDragging(false);
		stopAutoScroll();

		// Выполняем дополнительную очистку
		if (window.dragCleanup) {
			window.dragCleanup();
			delete window.dragCleanup;
		}
	};

	// Handle global drag over for auto-scrolling
	const handleGlobalDragOver = (e) => {
		if (!isDragging) return;

		const scrollContainer = document.querySelector('.responsive-table');
		if (!scrollContainer) return;

		const containerRect = scrollContainer.getBoundingClientRect();
		const scrollThreshold = 60; // Increased threshold to make it easier to trigger scrolling

		// Extended bounds to make scrolling more responsive
		// Add a buffer around the container to detect mouse position even slightly outside
		const buffer = 20; // pixels

		// Check if mouse is near the edge of the container with extended bounds
		// For horizontal edges, check if mouse is within the vertical bounds of the container (with buffer)
		const isWithinVerticalBounds = e.clientY >= (containerRect.top - buffer) && e.clientY <= (containerRect.bottom + buffer);
		// For vertical edges, check if mouse is within the horizontal bounds of the container (with buffer)
		const isWithinHorizontalBounds = e.clientX >= (containerRect.left - buffer) && e.clientX <= (containerRect.right + buffer);

		// Check each edge with appropriate bounds checking
		const isNearLeftEdge = isWithinVerticalBounds && Math.abs(e.clientX - containerRect.left) < scrollThreshold;
		const isNearRightEdge = isWithinVerticalBounds && Math.abs(containerRect.right - e.clientX) < scrollThreshold;
		const isNearTopEdge = isWithinHorizontalBounds && Math.abs(e.clientY - containerRect.top) < scrollThreshold;
		const isNearBottomEdge = isWithinHorizontalBounds && Math.abs(containerRect.bottom - e.clientY) < scrollThreshold;

		// Debug information to help troubleshoot scrolling issues
		// console.log(`Left: ${isNearLeftEdge}, Right: ${isNearRightEdge}, Top: ${isNearTopEdge}, Bottom: ${isNearBottomEdge}`);

		// Start auto-scroll if near any edge
		// Check if cursor is near any edge of the screen as well
		const screenEdgeThreshold = 20; // pixels from screen edge
		const isNearScreenLeftEdge = e.clientX < screenEdgeThreshold;
		const isNearScreenRightEdge = window.innerWidth - e.clientX < screenEdgeThreshold;
		const isNearScreenTopEdge = e.clientY < screenEdgeThreshold;
		const isNearScreenBottomEdge = window.innerHeight - e.clientY < screenEdgeThreshold;

		if (isNearLeftEdge || isNearRightEdge || isNearTopEdge || isNearBottomEdge ||
			isNearScreenLeftEdge || isNearScreenRightEdge || isNearScreenTopEdge || isNearScreenBottomEdge) {
			startAutoScroll(e);
		} else {
			stopAutoScroll();
		}
	};

	// Handle global drag end cleanup
	const cleanupDragListeners = () => {
		setIsDragging(false);
		stopAutoScroll();
		document.removeEventListener('mousemove', handleGlobalDragOver);
		document.removeEventListener('dragend', cleanupDragListeners);

		// Also remove the updateMousePosition listener using our global reference
		if (window.currentUpdateMousePosition) {
			document.removeEventListener('mousemove', window.currentUpdateMousePosition);
			delete window.currentUpdateMousePosition;
		}
	};

	// Handle drag over
	const handleDragOver = (e) => {
		e.preventDefault();
		e.currentTarget.classList.add('highlight');
		handleGlobalDragOver(e);
	};

	// Handle drag leave
	const handleDragLeave = (e) => {
		e.currentTarget.classList.remove('highlight');
	};

	// Handle drop
	const handleDrop = async (e, targetTrackId, targetDayIndex) => {
		e.preventDefault();
		e.currentTarget.classList.remove('highlight');

		// Ensure all auto-scrolling is stopped
		stopAutoScroll();
		setIsDragging(false);

		// Remove all event listeners
		document.removeEventListener('mousemove', handleGlobalDragOver);
		document.removeEventListener('dragend', cleanupDragListeners);

		// Remove the updateMousePosition listener using our global reference
		if (window.currentUpdateMousePosition) {
			document.removeEventListener('mousemove', window.currentUpdateMousePosition);
			delete window.currentUpdateMousePosition;
		}

		// For extra safety, remove listeners from window as well
		if (typeof window !== 'undefined') {
			window.removeEventListener('mousemove', handleGlobalDragOver);
		}

		// Force scroll to stop immediately
		const scrollContainer = document.querySelector('.responsive-table');
		if (scrollContainer) {
			// Save current scroll position
			const currentScrollLeft = scrollContainer.scrollLeft;
			const currentScrollTop = scrollContainer.scrollTop;

			// Set the same position to stop any momentum scrolling
			scrollContainer.scrollLeft = currentScrollLeft;
			scrollContainer.scrollTop = currentScrollTop;

			// Add a class to temporarily disable smooth scrolling
			scrollContainer.classList.add('no-smooth-scroll');

			// Apply a second time after a short delay to ensure it takes effect
			setTimeout(() => {
				scrollContainer.scrollLeft = currentScrollLeft;
				scrollContainer.scrollTop = currentScrollTop;
			}, 50);

			// Apply a third time after another delay for extra assurance
			setTimeout(() => {
				scrollContainer.scrollLeft = currentScrollLeft;
				scrollContainer.scrollTop = currentScrollTop;
			}, 150);

			// Remove the class after a longer delay
			setTimeout(() => {
				scrollContainer.classList.remove('no-smooth-scroll');
			}, 350);
		}

		if (!draggedItem) return;

		try {
			// Get the target day date
			const targetTrack = tracks.find(track => track.id === targetTrackId);
			const targetDay = targetTrack.days[targetDayIndex];

			const draggedTrack = tracks.find(track => track.id === draggedTrackId);
			const draggedTrackDay = draggedTrack.days[draggedDayIndex];

			// Check if we're swapping tracks or moving a slab
			const isSwappingTracks = draggedTrackDay.id !== targetDay.id;

			if (isSwappingTracks) {
				// Call API to swap tracks
				await swapTracks(draggedTrackDay.id, targetDay.id);

				// After swapping tracks on the backend, refresh the data
				try {
					const tracksData = await getTracks();
					setTracks(tracksData);
					console.log(`Swapped track ${draggedTrackId} with track ${targetTrackId}`);
				} catch (error) {
					console.error('Error refreshing tracks after swap:', error);
				}
			} else {
				// Call API to move slab
				await moveSlab(draggedItem.id, targetTrackId, targetDay.date);

				// Create a deep copy of the tracks state
				const newTracks = JSON.parse(JSON.stringify(tracks));

				// Remove the slab from its original position
				const originalTrack = newTracks.find(track => track.id === draggedTrackId);
				const originalDay = originalTrack.days[draggedDayIndex];

				// Handle both data structures (with slabs array or direct properties)
				if (originalDay.slabs && originalDay.slabs.length > 0) {
					// If using the slabs array structure
					const [removedSlab] = originalDay.slabs.splice(draggedSlabIndex, 1);

					// Add the slab to the new position
					const targetTrackInState = newTracks.find(track => track.id === targetTrackId);
					const targetDayInState = targetTrackInState.days[targetDayIndex];

					// Initialize slabs array if it doesn't exist
					if (!targetDayInState.slabs) {
						targetDayInState.slabs = [];
					}

					// Check if the target day already has slabs
					if (targetDayInState.slabs.length > 0) {
						// Perform a swap - take the first slab from target and move it to original position
						const [targetSlab] = targetDayInState.slabs.splice(0, 1);
						originalDay.slabs.push(targetSlab);

						// Add the dragged slab to the target day
						targetDayInState.slabs.push(removedSlab);

						console.log(`Swapped slab ${removedSlab.id} with slab ${targetSlab.id}`);
					} else {
						// If target is empty, just add the dragged slab
						targetDayInState.slabs.push(removedSlab);
					}
				} else {
					// If using direct properties structure
					// Store the original day's properties
					const originalProperties = { ...originalDay };

					// Get the target day
					const targetTrackInState = newTracks.find(track => track.id === targetTrackId);
					const targetDayInState = targetTrackInState.days[targetDayIndex];

					// Store the target day's properties
					const targetProperties = { ...targetDayInState };

					// Check if the target day has properties (is occupied)
					const isTargetOccupied = targetDayInState.width || targetDayInState.number;

					if (isTargetOccupied) {
						// Swap properties between original and target days
						// Clear original day properties
						Object.keys(originalDay).forEach(key => {
							if (!['date', 'reconfiguration', 'reconfigurationData'].includes(key)) {
								delete originalDay[key];
							}
						});

						// Copy target properties to original day
						Object.keys(targetProperties).forEach(key => {
							if (!['date', 'reconfiguration', 'reconfigurationData'].includes(key)) {
								originalDay[key] = targetProperties[key];
							}
						});

						// Clear target day properties
						Object.keys(targetDayInState).forEach(key => {
							if (!['date', 'reconfiguration', 'reconfigurationData'].includes(key)) {
								delete targetDayInState[key];
							}
						});

						// Copy original properties to target day
						Object.keys(originalProperties).forEach(key => {
							if (!['date', 'reconfiguration', 'reconfigurationData'].includes(key)) {
								targetDayInState[key] = originalProperties[key];
							}
						});

						console.log(`Swapped properties between days`);
					} else {
						// If target is empty, just copy properties
						Object.keys(originalProperties).forEach(key => {
							if (!['date', 'reconfiguration', 'reconfigurationData'].includes(key)) {
								targetDayInState[key] = originalProperties[key];
								delete originalDay[key];
							}
						});
					}
				}

				// Update the state
				setTracks(newTracks);
			}
		} catch (error) {
			console.error('Error moving slab or swapping tracks:', error);
			alert('Ошибка при перемещении. Пожалуйста, попробуйте снова.');
		} finally {
			// Reset dragged item state
			setDraggedItem(null);
			setDraggedTrackId(null);
			setDraggedDayIndex(null);
			setDraggedSlabIndex(null);
		}
	};

	// Handle search
	const handleSearch = (e) => {
		const searchTerm = e.target.value.toLowerCase();
		console.log(`Searching for: ${searchTerm}`);
		// In a real app, you would filter the tracks/slabs based on the search term
	};

	// Handle opening the reconfiguration modal
	const handleOpenReconfigurationModal = (trackId, dayIndex) => {
		const track = tracks.find(t => t.id === trackId);
		const day = track.days[dayIndex];

		// If the day has reconfiguration data, use it; otherwise, use an empty array
		const reconfigData = (day.reconfiguration && day.reconfigurationData)
			? day.reconfigurationData
			: [{type: 'Нет данных о переналадке', width: '-', height: '-'}];

		setSelectedReconfiguration({
			trackName: track.name,
			date: day.date,
			data: reconfigData
		});
		setShowModal(true);
	};

	// Handle closing the reconfiguration modal
	const handleCloseModal = () => {
		setShowModal(false);
		setSelectedReconfiguration(null);
	};

	// Handle contractor assignment
	const handleContractorChange = (trackId, contractorName) => {
		// Get the current track
		const track = tracks.find(t => t.id === trackId);

		// Show the modal for all contractor changes, including initial assignment
		setPendingContractorChange({ trackId, contractorName });
		setShowRecalculateModal(true);
	};

	// Apply the contractor change after confirmation
	const applyContractorChange = async (trackId, contractorName) => {
		try {
			// Call API to update track contractor
			await updateTrackContractor(trackId, contractorName);

			// Update local state
			const newTracks = tracks.map(track => {
				if (track.id === trackId) {
					return { ...track, contractor: contractorName };
				}
				return track;
			});
			setTracks(newTracks);
		} catch (error) {
			console.error('Error updating track contractor:', error);
			// Show error message to user
			alert('Ошибка при обновлении контрагента. Пожалуйста, попробуйте снова.');
		}
	};

	// Handle recalculation confirmation with calculation
	const handleRecalculateWithCalc = async () => {
		// Apply the pending change with calculation
		if (pendingContractorChange) {
			applyContractorChange(
				pendingContractorChange.trackId, 
				pendingContractorChange.contractorName
			);

			// Trigger calculation using the new API endpoint
			try {
				setLoading(true);
				const result = await startCalculation();
				console.log("Calculation started successfully:", result);

				// Refresh the tracks data after calculation
				const tracksData = await getTracks();
				setTracks(tracksData);
			} catch (error) {
				console.error("Error during calculation:", error);
				alert("Ошибка при запуске расчета. Пожалуйста, попробуйте снова.");
			} finally {
				setLoading(false);
			}
		}

		// Close the modal and reset the pending change
		setShowRecalculateModal(false);
		setPendingContractorChange(null);
	};

	// Handle recalculation confirmation without calculation
	const handleRecalculateWithoutCalc = () => {
		// Apply the pending change without calculation
		if (pendingContractorChange) {
			applyContractorChange(
				pendingContractorChange.trackId, 
				pendingContractorChange.contractorName
			);
			console.log("Applying change without calculation");
		}
		// Close the modal and reset the pending change
		setShowRecalculateModal(false);
		setPendingContractorChange(null);
	};

	// Handle recalculation cancellation
	const handleRecalculateCancel = () => {
		// Close the modal without applying the change
		setShowRecalculateModal(false);
		setPendingContractorChange(null);
	};

	// Add CSS for no-smooth-scroll class
	useEffect(() => {
		// Create a style element
		const styleElement = document.createElement('style');
		styleElement.textContent = `
      .no-smooth-scroll {
        scroll-behavior: auto !important;
        -webkit-overflow-scrolling: auto !important;
      }
    `;
		document.head.appendChild(styleElement);

		// Clean up on component unmount
		return () => {
			document.head.removeChild(styleElement);
		};
	}, []);

	return (
		<div id="track-availability">
      {(loading || calculating) ? (
        <div className="bg-white shadow rounded-lg overflow-hidden mb-4">
          <div className="p-10 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600">Загрузка данных о дорожках и плитах...</p>
          </div>
        </div>
      )
		  :
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Планирование по дорожкам
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Перетаскивайте плиты между ячейками для изменения расписания
              </p>
            </div>
            <div className="mt-4 md:mt-0 relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <FontAwesomeIcon icon="search" className="text-gray-400" />
              </div>
              <input
				  id="search"
				  type="text"
				  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
				  placeholder="Поиск заказа..."
				  onChange={handleSearch}
			  />
            </div>
          </div>
        </div>

        <div className="overflow-x-auto responsive-table" style={{maxWidth: '100%', overflowX: 'auto'}}>
          <table className="divide-y divide-gray-200 border-collapse border border-gray-200 text-2xs"
				 style={{tableLayout: 'fixed', width: '1400px'}}>
            <thead className="bg-gray-50">
              <tr>
                <th scope="col"
					className="w-48 px-2 py-4 text-center text-2xs font-medium text-gray-500 uppercase tracking-wider border border-gray-200 sticky left-0 bg-gray-50 z-10">
                  <div>Дорожка</div>
                </th>
				  {tracks.map((track, trackIndex) => (
					  track.days.map((day, dayIndex) => {
						  // Only render the header once for each date (for the first track)
						  if (trackIndex === 0) {
							  let dateText = '';
							  if (day.date === 'today') dateText = 'Сегодня';
							  else if (day.date === 'tomorrow') dateText = 'Завтра';
							  else dateText = day.date;

							  // Find if any track has reconfiguration on this day
							  const hasReconfiguration = tracks.some(t => t.days[dayIndex]?.reconfiguration);

							  return (
								  <th key={`header-${day.date}`}
									  scope="col"
									  className="w-44 px-1 py-1 text-left text-2xs font-medium text-gray-500 uppercase tracking-wider border border-gray-200">
                          <div className="flex justify-between items-center">
                            <span>{dateText}</span>
                            {day.kpi !== undefined && (
                              <span className="text-blue-600 font-medium" title="KPI показатель">
                                KPI: {day.kpi}
                              </span>
                            )}
                          </div>
                          <button
							  onClick={() => {
								  // Use the first track's ID for all days
								  handleOpenReconfigurationModal(tracks[0].id, dayIndex);
							  }}
							  className="text-2xs text-yellow-600 font-medium mt-0.5 hover:text-yellow-800 focus:outline-none block"
							  style={{fontSize: '0.55rem'}}
						  >
                            <FontAwesomeIcon icon="info-circle" className="mr-0.5" /> Переналадка
                          </button>
                        </th>
							  );
						  }
						  return null;
					  })
				  ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tracks.map(track => (
				  <tr key={track.id}>
                  <td className={`w-48 px-2 py-4 text-center text-2xs font-medium text-gray-900 border border-gray-200 sticky left-0 z-10 ${track.contractor ? 'bg-blue-50' : 'bg-white'}`}>
                    <div>{track.name}</div>
                    <div className="mt-2">
                      <select
                        className="w-full text-2xs p-1 border border-gray-300 rounded"
                        value={track.contractor}
                        onChange={(e) => handleContractorChange(track.id, e.target.value)}
                      >
                        <option value="">Выберите контрагента</option>
                        {contractors.map((contractor, index) => (
                          <option key={index} value={contractor}>{contractor}</option>
                        ))}
                      </select>
                      {track.contractor && (
                        <div className="mt-1 text-2xs text-blue-600 font-semibold p-1 bg-blue-100 rounded border border-blue-200">
                          Выделено для:<br/>{track.contractor}
                        </div>
                      )}
                    </div>
                  </td>
					  {track.days.map((day, dayIndex) => (
						  <td
							  key={`${track.id}-${day.date}`}
							  className={`w-44 px-1 py-1 dropzone border ${track.contractor ? 'border-blue-300' : 'border-gray-200'} ${track.contractor ? 'bg-blue-50' : ''}`}
							  data-date={day.date}
							  data-track={track.id}
							  onDragOver={handleDragOver}
							  onDragLeave={handleDragLeave}
							  onDrop={(e) => handleDrop(e, track.id, dayIndex)}
						  >
                      {day.reconfiguration ? (
						  <>
                          <div className="text-2xs text-gray-500">Переналадка</div>
                        </>
					  ) : (
						  <>
                          {day.width || day.number ? (
                              <div
                                className={`drag-item p-0.5 mb-0.5 rounded border ${
                                  day.status === 'booked'
                                    ? 'border-green-200 bg-green-50'
                                    : 'border-red-200 bg-red-50'
                                }`}
                                draggable={true}
                                onDragStart={(e) => handleDragStart(track.id, dayIndex, 0, day)}
                              >
                                <div className="flex items-center">
                                  <span className={`status-indicator status-${day.status}`}></span>
                                  <span className="text-2xs font-medium">{day.status === 'overdue' ? 'Просрочено' : ''}</span>
                                </div>
                                <div className="text-2xs mt-0.5 grid grid-cols-2 gap-0.5">
                                  <div className="font-semibold">Размер:</div><div>{Number.parseFloat(day.width)}×{Number.parseFloat(day.height)}</div>
                                  <div className="font-semibold">Проволока:</div><div><span>↑ {day.wireTop}</span> <span>↓ {day.wireBottom}</span></div>
                                  <div className="font-semibold">Бетон:</div><div>{day.concrete}</div>
                                  <div className="font-semibold">Занято:</div><div>{Number.parseFloat(day.occupied)} мм</div>
                                  <div className="font-semibold">Свободно:</div><div>{Number.parseFloat(day.free)} мм</div>
                                  <div className="font-semibold">Стоимость:</div><div className="font-medium text-blue-600">{day.price}</div>
                                  <div className="font-semibold">Дедлайн:</div><div>{day.deadline}</div>
                                </div>
                              </div>
                          ) : (
                              <div className="text-center py-1 text-gray-500 text-2xs">Пусто</div>
                          )}
                        </>
					  )}
                    </td>
					  ))}
                </tr>
			  ))}
            </tbody>
          </table>
        </div>
      </div>
	  }

			{/* Reconfiguration Modal */}
			{showModal && selectedReconfiguration && (
				<div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
          <div className="relative mx-auto p-5 border max-w-lg shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Информация о переналадке
              </h3>
              <div className="mt-2 px-4 py-3">
                <p className="text-sm text-gray-500 mb-2">
                  {selectedReconfiguration.trackName}, {selectedReconfiguration.date === 'today' ? 'Сегодня' :
					selectedReconfiguration.date === 'tomorrow' ? 'Завтра' : selectedReconfiguration.date}
                </p>
                <div className="mt-4 text-left overflow-x-auto">
                  <table className="w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col"
							className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Этап</th>
                        <th scope="col"
							className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ширина</th>
                        <th scope="col"
							className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Высота</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {selectedReconfiguration.data.map((item, index) => (
						  <tr key={index}>
                          <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{item.type}</td>
                          <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{item.width}</td>
                          <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">{item.height}</td>
                        </tr>
					  ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div className="items-center px-4 py-3">
                <button
					onClick={handleCloseModal}
					className="px-4 py-2 bg-blue-500 text-white text-base font-medium rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
				>
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </div>
			)}

			{/* Recalculation Confirmation Modal */}
			{showRecalculateModal && pendingContractorChange && (
				<div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
          <div className="relative mx-auto p-5 border max-w-lg shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Подтверждение перерасчета
              </h3>
              <div className="mt-2 px-4 py-3">
                <p className="text-sm text-gray-500 mb-4">
                  В связи с изменением контрагента необходимо произвести перерасчет. Продолжить?
                </p>
              </div>
              <div className="items-center px-4 py-3 flex justify-center space-x-4">
                <button
					onClick={handleRecalculateCancel}
					className="px-4 py-2 bg-gray-300 text-gray-800 text-base font-medium rounded-md shadow-sm hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300"
				>
                  Отмена
                </button>
                <button
					onClick={handleRecalculateWithoutCalc}
					className="px-4 py-2 bg-yellow-500 text-white text-base font-medium rounded-md shadow-sm hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-300"
				>
                  Без Расчета
                </button>
                <button
					onClick={handleRecalculateWithCalc}
					className="px-4 py-2 bg-blue-500 text-white text-base font-medium rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
				>
                  Расчитать
                </button>
              </div>
            </div>
          </div>
        </div>
			)}
    </div>
	);
};

export default TrackAvailability;
