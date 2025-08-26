import React, {useEffect, useState, useRef} from 'react';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import { 
  getTracks, getContractors, updateTrackContractor, moveSlab, swapTracks, 
  startCalculation, getTrackSlabs, updateSlab, deleteSlab, transferSlabs,
  printTrackPlan
} from '../services/api';

const TrackAvailability = ({calculating}) => {
 const [showModal, setShowModal] = useState(false);
	const [showRecalculateModal, setShowRecalculateModal] = useState(false);
	const [showCellModal, setShowCellModal] = useState(false);
	const [selectedReconfiguration, setSelectedReconfiguration] = useState(null);
	const [selectedCell, setSelectedCell] = useState(null);
	const [pendingContractorChange, setPendingContractorChange] = useState(null);
	const [contractors, setContractors] = useState([]);
	const [tracks, setTracks] = useState([]);
	const [loading, setLoading] = useState(true);
	const [selectedSlabs, setSelectedSlabs] = useState([]);
	const [showEditModal, setShowEditModal] = useState(false);
	const [showDeleteModal, setShowDeleteModal] = useState(false);
	const [showTransferModal, setShowTransferModal] = useState(false);
	const [editingSlab, setEditingSlab] = useState(null);
	const [transferDate, setTransferDate] = useState('');
	const [transferTrackId, setTransferTrackId] = useState('');
 const [isSubmitting, setIsSubmitting] = useState(false);
 const [dayOffset, setDayOffset] = useState(0);
 const [searchTerm, setSearchTerm] = useState('');
	const [searchResults, setSearchResults] = useState([]);
	const [showSearchResults, setShowSearchResults] = useState(false);
	const [sortColumn, setSortColumn] = useState(null);
	const [sortDirection, setSortDirection] = useState('asc');

	// Refs for edit form
	const nameRef = useRef(null);
	const lengthRef = useRef(null);
	const concreteClassRef = useRef(null);
	const wireTopRef = useRef(null);
	const wireBottomRef = useRef(null);

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
				setLoading(true)
				// Call API to swap tracks
				await swapTracks(draggedTrackDay.id, targetDay.id);

				// After swapping tracks on the backend, refresh the data
				try {
					const tracksData = await getTracks();
					setTracks(tracksData);
					console.log(`Swapped track ${draggedTrackId} with track ${targetTrackId}`);
				} catch (error) {
					console.error('Error refreshing tracks after swap:', error);
				} finally {
					setLoading(false)
				}
			} else {
				setLoading(true)
				// Call API to move slab
				await moveSlab(draggedItem.id, targetTrackId, targetDay.date);

				// Refresh the tracks data from the backend
				try {
					const tracksData = await getTracks();
					setTracks(tracksData);
					console.log(`Moved slab ${draggedItem.id} to track ${targetTrackId}`);
					return; // Exit early as we've updated the tracks data
				} catch (error) {
					console.error('Error refreshing tracks after move:', error);
					// Fall back to manual state update if the API call fails
				} finally {
					setLoading(false)
				}

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
		const term = e.target.value.toLowerCase();
		setSearchTerm(term);

		if (!term.trim()) {
			setSearchResults([]);
			setShowSearchResults(false);
			return;
		}

		// Collect all searchable items from tracks
		const results = [];

		tracks.forEach(track => {
			track.days.forEach(day => {
				// Skip empty days
				if (!day.orders && !day.plates && !day.size) return;

				// Check if any order number matches
				const orderMatch = day.orders && day.orders.some(order => 
					order.toString().toLowerCase().includes(term)
				);

				// Check if any plate name matches
				const plateMatch = day.plates && day.plates.some(plate => 
					plate.toString().toLowerCase().includes(term)
				);

				// Check if size matches
				const sizeMatch = day.size && day.size.toString().toLowerCase().includes(term);

				if (orderMatch || plateMatch || sizeMatch) {
					// Add this day to results if not already added
					const existingResult = results.find(r => 
						r.trackId === track.id && r.dayId === day.id
					);

					if (!existingResult) {
						results.push({
							trackId: track.id,
							trackName: track.name,
							dayId: day.id,
							date: day.date === 'today' ? 'Сегодня' : 
								day.date === 'tomorrow' ? 'Завтра' : day.date,
							matchType: orderMatch ? 'order' : (plateMatch ? 'plate' : 'size'),
							matchValue: orderMatch ? day.orders.find(order => 
									order.toString().toLowerCase().includes(term)
								) : (plateMatch ? day.plates.find(plate => 
									plate.toString().toLowerCase().includes(term)
								) : day.size)
						});
					}
				}
			});
		});

		setSearchResults(results);
		setShowSearchResults(results.length > 0);
	};

	// Check if a cell matches the search criteria
	const cellMatchesSearch = (track, day) => {
		if (!searchTerm.trim()) return true;

		// Skip empty days
		if (!day.orders && !day.plates && !day.size) return false;

		// Check if any order number matches
		const orderMatch = day.orders && day.orders.some(order => 
			order.toString().toLowerCase().includes(searchTerm.toLowerCase())
		);

		// Check if any plate name matches
		const plateMatch = day.plates && day.plates.some(plate => 
			plate.toString().toLowerCase().includes(searchTerm.toLowerCase())
		);

		// Check if size matches
		const sizeMatch = day.size && day.size.toString().toLowerCase().includes(searchTerm.toLowerCase());

		return orderMatch || plateMatch || sizeMatch;
	};

	// Handle search result click
	const handleSearchResultClick = (result) => {
		// Find the track and day indices
		const trackIndex = tracks.findIndex(t => t.id === result.trackId);
		if (trackIndex === -1) return;

		const track = tracks[trackIndex];
		const dayIndex = track.days.findIndex(d => d.id === result.dayId);
		if (dayIndex === -1) return;

		// Calculate the new dayOffset to show this day
		const newOffset = Math.max(0, dayIndex - 2); // Center the day if possible
		setDayOffset(newOffset);

		// Clear search
		setSearchTerm('');
		setSearchResults([]);
		setShowSearchResults(false);

		// Optionally, highlight the cell or open the cell modal
		const day = track.days[dayIndex];
		handleCellClick(track, day);
	};

	// Handle opening the reconfiguration modal
	const handleOpenReconfigurationModal = (trackId, dayIndex) => {
		const track = tracks.find(t => t.id === trackId);
		const day = track.days[dayIndex];

		// Get all tracks for this day to collect all unique width/height combinations
		const dayTracks = tracks.map(t => t.days[dayIndex]).filter(d => d && (d.width || d.height));

		// Create reconfiguration data from unique width/height combinations
		let reconfigData = [];

		if (dayTracks.length > 0) {
			// Set to store unique width/height combinations
			const uniqueCombinations = new Set();

			// Collect all unique width/height combinations
			dayTracks.forEach(dayTrack => {
				if (dayTrack.width && dayTrack.height) {
					uniqueCombinations.add(`${dayTrack.width}|${dayTrack.height}`);
				}
			});

			// Convert to array of objects
			reconfigData = Array.from(uniqueCombinations).map((combo, index) => {
				const [width, height] = combo.split('|');
				return {
					type: index === 0 ? `Начало дня` : `Переналадка ${index}`,
					width: width,
					height: height
				};
			});
		}

		// If no reconfiguration data was found, use default message
		if (reconfigData.length === 0) {
			reconfigData = [{type: 'Нет данных о переналадке', width: '-', height: '-'}];
		}

		setSelectedReconfiguration({
			trackName: track.name,
			date: day.date === 'today' ? 'Сегодня' : 
				day.date === 'tomorrow' ? 'Завтра' : day.date,
			data: reconfigData
		});
		setShowModal(true);
	};

	// Handle closing the reconfiguration modal
	const handleCloseModal = () => {
		setShowModal(false);
		setSelectedReconfiguration(null);
	};

	// Handle cell click to open cell details modal
	const handleCellClick = async (track, day) => {
		// Only open modal for cells with content
		if (day.width || day.number) {
			// Set initial cell data
			setSelectedCell({
				trackId: day.id,
				trackName: track.name,
				date: day.date === 'today' ? 'Сегодня' : 
					day.date === 'tomorrow' ? 'Завтра' : day.date,
				status: day.status,
				width: day.width,
				height: day.height,
				concrete: day.concrete,
				wireTop: day.wireTop,
				wireBottom: day.wireBottom,
				deadline: day.deadline,
				price: day.price,
				occupied: day.occupied,
				free: day.free,
				slabs: [],
				loading: true
			});

			// Show modal immediately with loading state
			setShowCellModal(true);

			// Fetch slabs data for this track
			try {
				const slabsData = await getTrackSlabs(day.id);
				// Update selectedCell with slabs data
				setSelectedCell(prevState => ({
					...prevState,
					slabs: slabsData,
					loading: false
				}));
			} catch (error) {
				console.error('Error fetching slabs data:', error);
				// Update selectedCell to show error state
				setSelectedCell(prevState => ({
					...prevState,
					slabs: [],
					loading: false,
					error: 'Ошибка при загрузке данных о плитах'
				}));
			}
		}
	};

	// Handle closing the cell details modal
	const handleCloseCellModal = () => {
		setShowCellModal(false);
		setSelectedCell(null);
		setSelectedSlabs([]);
	};

	// Handle edit form submission
	const handleEditSubmit = async () => {
		if (!editingSlab || !editingSlab.id) {
			alert('Ошибка: Не удалось определить ID плиты');
			return;
		}

		setIsSubmitting(true);

		try {
			const updatedData = {
				name: nameRef.current.value,
				length: parseFloat(lengthRef.current.value),
				concrete_class: concreteClassRef.current.value,
				wire_top: wireTopRef.current.value,
				wire_bottom: wireBottomRef.current.value
			};

			await updateSlab(editingSlab.id, updatedData);

			// Refresh the slabs data
			if (selectedCell && selectedCell.trackId) {
				const slabsData = await getTrackSlabs(selectedCell.trackId);
				setSelectedCell(prevState => ({
					...prevState,
					slabs: slabsData
				}));
			}

			// Close the modal
			setShowEditModal(false);
			setEditingSlab(null);

			// Show success message
			alert('Плита успешно обновлена');

			// Refresh the tracks data
			const tracksData = await getTracks();
			setTracks(tracksData);
		} catch (error) {
			console.error('Error updating slab:', error);
			alert(`Ошибка при обновлении плиты: ${error.message}`);
		} finally {
			setIsSubmitting(false);
		}
	};

	// Handle delete confirmation
	const handleDeleteConfirm = async () => {
		if (selectedSlabs.length === 0) {
			alert('Пожалуйста, выберите плиты для удаления');
			return;
		}

		setIsSubmitting(true);

		try {
			// Delete each selected slab
			for (const slabId of selectedSlabs) {
				await deleteSlab(slabId);
			}

			// Refresh the slabs data
			if (selectedCell && selectedCell.trackId) {
				const slabsData = await getTrackSlabs(selectedCell.trackId);
				setSelectedCell(prevState => ({
					...prevState,
					slabs: slabsData
				}));
			}

			// Close the modal
			setShowDeleteModal(false);
			setSelectedSlabs([]);

			// Show success message
			alert('Плиты успешно удалены');

			// Refresh the tracks data
			const tracksData = await getTracks();
			setTracks(tracksData);
		} catch (error) {
			console.error('Error deleting slabs:', error);
			alert(`Ошибка при удалении плит: ${error.message}`);
		} finally {
			setIsSubmitting(false);
		}
	};

	// Handle transfer form submission
	const handleTransferSubmit = async () => {
		if (selectedSlabs.length === 0) {
			alert('Пожалуйста, выберите плиты для переноса');
			return;
		}

		if (!transferTrackId) {
			alert('Пожалуйста, выберите дорожку для переноса');
			return;
		}

		if (!transferDate) {
			alert('Пожалуйста, выберите дату для переноса');
			return;
		}

		setIsSubmitting(true);

		try {
			await transferSlabs(selectedSlabs, transferTrackId, transferDate);

			// Refresh the slabs data
			if (selectedCell && selectedCell.trackId) {
				const slabsData = await getTrackSlabs(selectedCell.trackId);
				setSelectedCell(prevState => ({
					...prevState,
					slabs: slabsData
				}));
			}

			// Close the modal
			setShowTransferModal(false);
			setSelectedSlabs([]);
			setTransferDate('');
			setTransferTrackId('');

			// Show success message
			alert('Плиты успешно перенесены');

			// Refresh the tracks data
			const tracksData = await getTracks();
			setTracks(tracksData);
		} catch (error) {
			console.error('Error transferring slabs:', error);
			alert(`Ошибка при переносе плит: ${error.message}`);
		} finally {
			setIsSubmitting(false);
		}
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

		// Close the modal and reset the pending change
		setShowRecalculateModal(false);
		setPendingContractorChange(null);
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

 // Function to handle scrolling left (previous day)
  const handleScrollLeft = () => {
    if (dayOffset > 0) {
      setDayOffset(dayOffset - 1);
    }
  };

  // Function to handle scrolling right (next day)
  const handleScrollRight = () => {
    // Check if there are more days to show
    if (tracks.length > 0 && tracks[0].days.length > dayOffset + 5) {
      setDayOffset(dayOffset + 1);
    }
  };

 return (
    <div id="track-availability">
      {!(loading || calculating) && (
        <div className="flex justify-between mb-2 gap-2">
          {/* Search component */}
          <div className="relative">
            <div className="flex items-center">
              <input
                type="text"
                placeholder="Поиск по заказам, плитам, размерам..."
                className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-64"
                value={searchTerm}
                onChange={handleSearch}
                onFocus={() => searchResults.length > 0 && setShowSearchResults(true)}
                onBlur={() => setTimeout(() => setShowSearchResults(false), 200)}
              />
            </div>

            {/* Search results dropdown */}
            {showSearchResults && (
              <div className="absolute z-10 mt-1 w-full bg-white shadow-lg rounded-md border border-gray-300 max-h-60 overflow-y-auto">
                {searchResults.map((result, index) => (
                  <div 
                    key={`${result.trackId}-${result.dayId}-${index}`}
                    className="px-3 py-2 hover:bg-gray-100 cursor-pointer border-b border-gray-200 last:border-b-0"
                    onMouseDown={() => handleSearchResultClick(result)}
                  >
                    <div className="flex items-center">
                      <span className="font-medium text-gray-800">{result.trackName}</span>
                      <span className="mx-2 text-gray-400">|</span>
                      <span className="text-gray-600">{result.date}</span>
                    </div>
                    <div className="mt-1 text-sm">
                      {result.matchType === 'order' && (
                        <span className="text-blue-600">Заказ: {result.matchValue}</span>
                      )}
                      {result.matchType === 'plate' && (
                        <span className="text-green-600">Плита: {result.matchValue}</span>
                      )}
                      {result.matchType === 'size' && (
                        <span className="text-purple-600">Размер: {result.matchValue}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Navigation buttons */}
          <div className="flex gap-2">
            <button 
              className="px-3 py-1 bg-gray-200 rounded-md hover:bg-gray-300 flex items-center justify-center"
              onClick={handleScrollLeft}
            >
              <svg width="26" height="27" viewBox="0 0 26 27" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 13.5L14.5 2M3 13.5L14.5 25M3 13.5H26" stroke="#727579" stroke-width="3"/>
              </svg>
            </button>
            <button 
              className="px-3 py-1 bg-gray-200 rounded-md hover:bg-gray-300 flex items-center justify-center"
              onClick={handleScrollRight}
            >
              <svg width="26" height="27" viewBox="0 0 26 27" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M23 13.5L11.5 2M23 13.5L11.5 25M23 13.5H0" stroke="#727579" stroke-width="3"/>
              </svg>
            </button>
          </div>
        </div>
      )}
      {(loading || calculating) ? (
        <div className="bg-white shadow rounded-lg overflow-hidden mb-4">
          <div className="p-10 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600">Загрузка данных о дорожках и плитах...</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-[150px_repeat(5,1fr)] gap-1 bg-gray-200 border border-gray-200 rounded-lg overflow-hidden text-xs font-medium responsive-table">
          {/* Header */}
          <div className="p-2 bg-gray-50 text-gray-800 font-semibold flex items-center justify-center">Дорожки</div>

          {/* Column Headers */}
          {tracks.length > 0 && tracks[0].days.slice(dayOffset, dayOffset + 5).map((day, dayIndex) => {
            let dateText = '';
            if (day.date === 'today') dateText = 'Сегодня';
            else if (day.date === 'tomorrow') dateText = 'Завтра';
            else dateText = day.date;

            // Check if any track has overrun on this day
            const hasOverrun = tracks.some(track => {
              const trackDay = track.days[dayIndex];
              return trackDay && trackDay.status === 'overdue';
            });

            return (
              <div key={`header-${day.date}`} className="p-2 text-center bg-white">
                <p>{dateText}</p>
                {day.total_overendering_wire_kg !== 0 && (
                  <span className="flex items-center justify-center gap-1 text-red-600">
                    {hasOverrun && <FontAwesomeIcon icon="exclamation-triangle" className="text-red-600" />}
                    {day.total_overendering_wire_kg && `${day.total_overendering_wire_kg.toFixed(2)}КГ`}
                    <FontAwesomeIcon 
                      icon="info-circle" 
                      className="ml-1 text-blue-500 cursor-pointer" 
                      onClick={(e) => {
                        e.stopPropagation();
                        // Find the track index for the first track (just to get the day data)
                        const trackIndex = 0;
                        // Get the day index from the current iteration
                        const dayIdx = dayOffset + dayIndex;
                        // Open the reconfiguration modal for this day
                        handleOpenReconfigurationModal(tracks[trackIndex].id, dayIdx);
                      }}
                      title="Показать переналадки"
                    />
                  </span>
                )}
              </div>
            );
          })}

          {/* Track Rows */}
          {tracks.map(track => (
            <React.Fragment key={track.id}>
              {/* Track Name and Contractor Dropdown */}
              <div className={`p-2 bg-white font-semibold text-gray-600 flex flex-col items-center justify-center ${track.contractor ? 'border-2 border-blue-300 border-r-0' : ''}`}>
                <div>{track.name}</div>
                <select 
                  className="mt-1 p-1 text-xs border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-full"
                  value={track.contractor || ''}
                  onChange={(e) => handleContractorChange(track.id, e.target.value)}
                >
                  <option value="">Выберите контрагента</option>
                  {contractors.map((contractor, index) => (
                    <option key={index} value={contractor}>
                      {contractor}
                    </option>
                  ))}
                </select>
              </div>

              {/* Track Days */}
              {track.days.slice(dayOffset, dayOffset + 5).map((day, dayIndex) => {
                // Determine cell styling based on status
                let cellClass = "p-2 text-gray-400 bg-white flex items-center justify-center";
                let cellContent = "ПУСТО";

                if (day.reconfiguration) {
                  // Reconfiguration day
                  cellClass = "p-2 text-center text-gray-600 flex items-center justify-center font-semibold bg-[#EFF6FF]";
                  cellContent = "ВЫХОДНОЙ";
                } else if (day.width || day.number) {
                  // Day with content
                  if (day.status === 'booked') {
                    // In progress
                    cellClass = "p-2 relative bg-[#E9FFF9]";
                    cellContent = (
                      <>
                        <p className="flex items-center gap-1 text-green-600 font-semibold">
                          <span className="w-2 h-2 bg-green-600 rounded-full"></span>В работе
                          {day.is_manual && <FontAwesomeIcon icon="hand-paper" className="ml-1 text-green-600" />}
                        </p>
                        <div className="mt-1 space-y-0.5 text-gray-700">
                          {day.deadline ? <p style={{color: "#1420A0"}}>До {day.deadline}</p> : <p style={{color: "#1420A0"}}>Без дедлайна</p>}
                          <p>{Number.parseFloat(day.width)}×{Number.parseFloat(day.height)}</p>
                          <p>{day.concrete}</p>
                          <p>↑{day.wireTop} ↓{day.wireBottom}</p>
                          <p>Занято: {day.occupied || "0"}мм</p>
                        </div>
                        <p className="text-blue-600 font-bold mt-2 pt-2 border-t border-green-200">{day.price}</p>
                      </>
                    );
                  } else if (day.status === 'overdue') {
                    // Delayed
                    cellClass = "p-2 relative bg-[#FFE4E4]";
                    cellContent = (
                      <>
                        <p className="flex items-center gap-1 text-red-600 font-semibold">
                          <FontAwesomeIcon icon="exclamation-triangle" className="text-red-600" />
                          Задержка
                          {day.is_manual && <FontAwesomeIcon icon="hand-paper" className="ml-1 text-red-600" />}
                        </p>
                        <div className="mt-1 space-y-0.5 text-gray-700">
						  {day.deadline ? <p style={{color: "#1420A0"}}>До {day.deadline}</p> : <p style={{color: "#1420A0"}}>Без дедлайна</p>}
							<p>{Number.parseFloat(day.width)}×{Number.parseFloat(day.height)}</p>
							<p>{day.concrete}</p>
							<p>↑{day.wireTop } ↓{day.wireBottom}</p>
							<p>Занято: {day.occupied || "0"}мм</p>
                        </div>
                        <p className="text-blue-600 font-bold mt-2 pt-2 border-t border-red-200">{day.price || "32,22 КГ"}</p>
                      </>
                    );
                  }
                }

                // Determine if cell should be faded based on search term
                const shouldFade = searchTerm.trim() !== '' && !cellMatchesSearch(track, day);
                const opacityStyle = shouldFade ? { opacity: 0.3 } : {};

                return (
                  <div 
                    key={`${track.id}-${day.date}`}
                    className={`${cellClass} ${track.contractor ? 'border-2 border-blue-300 border-l-0' + (dayIndex === 4 ? '' : ' border-r-0') : ''}`}
                    style={opacityStyle}
                    data-date={day.date}
                    data-track={track.id}
                    onClick={() => handleCellClick(track, day)}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleDrop(e, track.id, dayIndex)}
                  >
                    {typeof cellContent === 'string' ? cellContent : (
                      <div 
                        className="w-full cursor-grab"
                        draggable={day.width || day.number ? true : false}
                        onDragStart={(e) => handleDragStart(track.id, dayIndex, 0, day)}
                      >
                        {cellContent}
                      </div>
                    )}
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
      )}

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

			{/* Cell Details Modal */}
			{showCellModal && selectedCell && (
				<div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
          <div className="relative mx-auto p-5 border max-w-12xl shadow-lg rounded-xl bg-white" style={{maxHeight: "95vh"}}>
            {/* Close button (X) in the top-right corner */}
            <button
              onClick={handleCloseCellModal}
              className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <div className="mt-5">
              {/* Modal header with required information */}
              <div className="border-b pb-3 mb-4">
                <div className="flex justify-between items-center">
					<div className="flex gap-4" style={{alignItems: "center"}}>
						<h3 className="text-lg leading-6 font-medium text-gray-900">
							{selectedCell.trackName && selectedCell.trackName.includes('Дорожка')
							  ? selectedCell.trackName
							  : `Дорожка ${selectedCell.trackId || ''}`}
					  	</h3>
						<span className="text-sm text-gray-500">{selectedCell.width}x{selectedCell.height}</span>
						<span className={`px-2 py-1 rounded-md text-xs font-medium ${
						  selectedCell.status === 'overdue' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
						}`}>
						  {selectedCell.status === 'overdue' ? 'Просрочено' : 'В работе'}
						</span>
						<span className="text-sm text-gray-500">{selectedCell.date}</span>
					</div>

                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-blue-600">Стоимость {selectedCell.price}</span>
                    <button 
                      className="flex items-center gap-1 px-3 py-1 text-sm border border-gray-500 rounded-md text-white bg-gray-600 hover:bg-gray-700"
                      onClick={() => {
                        // Get the date from the selected cell
                        const cellDate = selectedCell.date;

                        // Parse the date string based on its format
                        let formattedDate;
                        if (cellDate === 'Сегодня') {
                          // If the date is "Today", use today's date
                          formattedDate = new Date().toISOString().split('T')[0];
                        } else if (cellDate === 'Завтра') {
                          // If the date is "Tomorrow", use tomorrow's date
                          const tomorrow = new Date();
                          tomorrow.setDate(tomorrow.getDate() + 1);
                          formattedDate = tomorrow.toISOString().split('T')[0];
                        } else {
                          // Try to parse the date in DD.MM.YYYY format
                          const parts = cellDate.split('.');
                          if (parts.length === 3) {
                            // Convert DD.MM.YYYY to YYYY-MM-DD
                            formattedDate = `${parts[2]}-${parts[1]}-${parts[0]}`;
                          } else {
                            // Fallback to current date if parsing fails
                            formattedDate = new Date().toISOString().split('T')[0];
                          }
                        }

                        // Call the print function with the date and track ID
                        printTrackPlan(formattedDate, selectedCell.trackId);
                      }}
                    >
					  <FontAwesomeIcon icon="print" className="w-4 h-4" />
					  <span>Печать</span>
					</button>
                  </div>
                </div>
              </div>

              {/* Slabs Table */}
              <div className="px-4">
                {selectedCell.loading ? (
                  <div className="text-center py-4">
                    <div className="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-600 mb-2"></div>
                    <p className="text-sm text-gray-600">Загрузка данных о плитах...</p>
                  </div>
                ) : selectedCell.error ? (
                  <div className="text-center py-4 text-red-600">
                    <p>{selectedCell.error}</p>
                  </div>
                ) : selectedCell.slabs && selectedCell.slabs.length > 0 ? (
                  <div className="overflow-x-auto overflow-y-scroll" style={{maxHeight: "55vh"}}>
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            <input 
                              type="checkbox" 
                              className="form-checkbox h-4 w-4 text-blue-600 transition duration-150 ease-in-out"
                              onChange={(e) => {
                                if (e.target.checked) {
                                  // Select all slabs
                                  setSelectedSlabs(selectedCell.slabs.map(slab => slab.id));
                                } else {
                                  // Deselect all slabs
                                  setSelectedSlabs([]);
                                }
                              }}
                              checked={selectedSlabs.length > 0 && selectedSlabs.length === selectedCell.slabs.length}
                            />
                          </th>
                          <th 
                            scope="col" 
                            className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            onClick={() => {
                              if (sortColumn === 'customer') {
                                setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
                              } else {
                                setSortColumn('customer');
                                setSortDirection('asc');
                              }
                            }}
                          >
                            Заказчик
                            {sortColumn === 'customer' && (
                              <span className="ml-1">
                                {sortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </th>
                          <th 
                            scope="col" 
                            className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            onClick={() => {
                              if (sortColumn === 'deadline') {
                                setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
                              } else {
                                setSortColumn('deadline');
                                setSortDirection('asc');
                              }
                            }}
                          >
                            Дата дедлайна
                            {sortColumn === 'deadline' && (
                              <span className="ml-1">
                                {sortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </th>
                          <th 
                            scope="col" 
                            className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            onClick={() => {
                              if (sortColumn === 'order') {
                                setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
                              } else {
                                setSortColumn('order');
                                setSortDirection('asc');
                              }
                            }}
                          >
                            Номер заказа
                            {sortColumn === 'order' && (
                              <span className="ml-1">
                                {sortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </th>
                          <th 
                            scope="col" 
                            className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            onClick={() => {
                              if (sortColumn === 'name') {
                                setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
                              } else {
                                setSortColumn('name');
                                setSortDirection('asc');
                              }
                            }}
                          >
                            Название
                            {sortColumn === 'name' && (
                              <span className="ml-1">
                                {sortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </th>
                          <th 
                            scope="col" 
                            className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            onClick={() => {
                              if (sortColumn === 'length') {
                                setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
                              } else {
                                setSortColumn('length');
                                setSortDirection('asc');
                              }
                            }}
                          >
                            Длина
                            {sortColumn === 'length' && (
                              <span className="ml-1">
                                {sortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </th>
                          <th 
                            scope="col" 
                            className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            onClick={() => {
                              if (sortColumn === 'capacity') {
                                setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
                              } else {
                                setSortColumn('capacity');
                                setSortDirection('asc');
                              }
                            }}
                          >
                            Нагрузка
                            {sortColumn === 'capacity' && (
                              <span className="ml-1">
                                {sortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </th>
                          <th 
                            scope="col" 
                            className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            onClick={() => {
                              if (sortColumn === 'concrete_class') {
                                setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
                              } else {
                                setSortColumn('concrete_class');
                                setSortDirection('asc');
                              }
                            }}
                          >
                            Класс бетона
                            {sortColumn === 'concrete_class' && (
                              <span className="ml-1">
                                {sortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </th>
                          <th 
                            scope="col" 
                            className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            onClick={() => {
                              if (sortColumn === 'wire_top') {
                                setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
                              } else {
                                setSortColumn('wire_top');
                                setSortDirection('asc');
                              }
                            }}
                          >
                            Проволока верх
                            {sortColumn === 'wire_top' && (
                              <span className="ml-1">
                                {sortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </th>
                          <th 
                            scope="col" 
                            className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            onClick={() => {
                              if (sortColumn === 'wire_bottom') {
                                setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
                              } else {
                                setSortColumn('wire_bottom');
                                setSortDirection('asc');
                              }
                            }}
                          >
                            Проволока низ
                            {sortColumn === 'wire_bottom' && (
                              <span className="ml-1">
                                {sortDirection === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {selectedCell.slabs
                          .slice()
                          .sort((a, b) => {
                            if (!sortColumn) return 0;

                            let valueA, valueB;

                            switch(sortColumn) {
                              case 'customer':
                                valueA = a.customer || '';
                                valueB = b.customer || '';
                                break;
                              case 'deadline':
                                // Convert date strings to Date objects for comparison
                                valueA = a.deadline ? new Date(a.deadline.split('.').reverse().join('-')) : new Date(0);
                                valueB = b.deadline ? new Date(b.deadline.split('.').reverse().join('-')) : new Date(0);
                                break;
                              case 'order':
                                valueA = a.order || '';
                                valueB = b.order || '';
                                break;
                              case 'name':
                                valueA = a.clean_name || '';
                                valueB = b.clean_name || '';
                                break;
                              case 'length':
                                valueA = parseFloat(a.length) || 0;
                                valueB = parseFloat(b.length) || 0;
                                break;
                              case 'capacity':
                                valueA = parseFloat(a.capacity) || 0;
                                valueB = parseFloat(b.capacity) || 0;
                                break;
                              case 'concrete_class':
                                valueA = a.concrete_class || '';
                                valueB = b.concrete_class || '';
                                break;
                              case 'wire_top':
                                valueA = a.wire_top || '';
                                valueB = b.wire_top || '';
                                break;
                              case 'wire_bottom':
                                valueA = a.wire_bottom || '';
                                valueB = b.wire_bottom || '';
                                break;
                              default:
                                return 0;
                            }

                            // For string comparison
                            if (typeof valueA === 'string' && typeof valueB === 'string') {
                              return sortDirection === 'asc' 
                                ? valueA.localeCompare(valueB) 
                                : valueB.localeCompare(valueA);
                            }

                            // For number or date comparison
                            return sortDirection === 'asc' 
                              ? valueA - valueB 
                              : valueB - valueA;
                          })
                          .map((slab, index) => {
                            const slabId = slab.id;
                            const isSelected = selectedSlabs.includes(slabId);

                          return (
                            <tr key={index} className={isSelected ? "bg-blue-50" : ""}>
                              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                                <input 
                                  type="checkbox" 
                                  className="form-checkbox h-4 w-4 text-blue-600 transition duration-150 ease-in-out"
                                  checked={isSelected}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setSelectedSlabs([...selectedSlabs, slabId]);
                                    } else {
                                      setSelectedSlabs(selectedSlabs.filter(id => id !== slabId));
                                    }
                                  }}
                                />
                              </td>
                              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{slab.customer}</td>
                              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{slab.deadline_date}</td>
                              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{slab.order_number}</td>
                              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{slab.name}</td>
                              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{slab.length}</td>
                              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{slab.load}</td>
                              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{slab.concrete_class}</td>
                              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{slab.wire_top}</td>
                              <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">{slab.wire_bottom}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    <p>Нет данных о плитах на этой дорожке</p>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end mt-4 px-4 gap-2 border-t pt-4">
                <button 
                  className="flex items-center gap-1 px-3 py-1 text-sm border border-blue-500 rounded-md text-white bg-blue-600 hover:bg-blue-700"
                  onClick={() => {
                    // Check if exactly one slab is selected
                    if (selectedSlabs.length === 1) {
                      // Find the selected slab
                      const selectedSlab = selectedCell.slabs.find(slab => {
                        const slabId = slab.id;
                        return slabId === selectedSlabs[0];
                      });

                      if (selectedSlab) {
                        setEditingSlab(selectedSlab);
                        setShowEditModal(true);
                      }
                    } else {
                      alert('Пожалуйста, выберите одну плиту для редактирования');
                    }
                  }}
                >
                  <FontAwesomeIcon icon="edit" className="w-4 h-4" />
                  <span>Изменить</span>
                </button>
                <button 
                  className="flex items-center gap-1 px-3 py-1 text-sm border border-red-500 rounded-md text-white bg-red-600 hover:bg-red-700"
                  onClick={() => {
                    // Check if at least one slab is selected
                    if (selectedSlabs.length > 0) {
                      setShowDeleteModal(true);
                    } else {
                      alert('Пожалуйста, выберите плиты для удаления');
                    }
                  }}
                >
                  <FontAwesomeIcon icon="trash-alt" className="w-4 h-4" />
                  <span>Удалить</span>
                </button>
                <button 
                  className="flex items-center gap-1 px-3 py-1 text-sm border border-green-500 rounded-md text-white bg-green-600 hover:bg-green-700"
                  onClick={() => {
                    // Check if at least one slab is selected
                    if (selectedSlabs.length > 0) {
                      setShowTransferModal(true);
                    } else {
                      alert('Пожалуйста, выберите плиты для переноса');
                    }
                  }}
                >
                  <FontAwesomeIcon icon="exchange-alt" className="w-4 h-4" />
                  <span>Перенос</span>
                </button>
              </div>

            </div>
          </div>
        </div>
			)}

      {/* Transfer Modal */}
      {showTransferModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
          <div className="relative mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Перенос плит на другую дорожку
              </h3>
              <div className="mt-2 px-4 py-3">
                <p className="text-sm text-gray-500 mb-4">
                  Выбрано плит: <span className="font-semibold">{selectedSlabs.length}</span>
                </p>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Выберите дату
                  </label>
                  <input 
                    type="date" 
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    value={transferDate}
                    onChange={(e) => setTransferDate(e.target.value)}
                    required
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Выберите дорожку
                  </label>
                  <select 
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    value={transferTrackId}
                    onChange={(e) => setTransferTrackId(e.target.value)}
                    required
                  >
                    <option value="">Выберите дорожку</option>
                    {tracks.map(track => (
                      <option key={track.id} value={track.position}>
                        {track.name} {track.contractor ? `(${track.contractor})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-4">
                <button
                  onClick={() => setShowTransferModal(false)}
                  className="px-4 py-2 bg-gray-300 text-gray-800 text-base font-medium rounded-md shadow-sm hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300"
                  disabled={isSubmitting}
                >
                  Отмена
                </button>
                <button
                  onClick={handleTransferSubmit}
                  className="px-4 py-2 bg-green-600 text-white text-base font-medium rounded-md shadow-sm hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-300"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Перенос...' : 'Перенести'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
          <div className="relative mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
            <div className="mt-3 text-center">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Подтверждение удаления
              </h3>
              <div className="mt-2 px-4 py-3">
                <p className="text-sm text-gray-500 mb-4">
                  Вы уверены, что хотите удалить выбранные плиты ({selectedSlabs.length} шт.)?
                </p>
                <p className="text-sm text-red-500 mb-4">
                  Это действие нельзя отменить.
                </p>
              </div>
              <div className="flex justify-center gap-3 mt-4">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="px-4 py-2 bg-gray-300 text-gray-800 text-base font-medium rounded-md shadow-sm hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300"
                  disabled={isSubmitting}
                >
                  Отмена
                </button>
                <button
                  onClick={handleDeleteConfirm}
                  className="px-4 py-2 bg-red-600 text-white text-base font-medium rounded-md shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-300"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Удаление...' : 'Удалить'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Slab Modal */}
      {showEditModal && editingSlab && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
          <div className="relative mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Редактирование плиты
              </h3>
              <div className="mt-2 px-4 py-3">
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Название
                  </label>
                  <input 
                    type="text" 
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    defaultValue={editingSlab.name}
                    ref={nameRef}
                    required
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Длина
                  </label>
                  <input 
                    type="number" 
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    defaultValue={editingSlab.length}
                    ref={lengthRef}
                    required
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Класс бетона
                  </label>
                  <input 
                    type="text" 
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    defaultValue={editingSlab.concrete_class}
                    ref={concreteClassRef}
                    required
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Проволока верх
                  </label>
                  <input 
                    type="text" 
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    defaultValue={editingSlab.wire_top}
                    ref={wireTopRef}
                    required
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Проволока низ
                  </label>
                  <input 
                    type="text" 
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    defaultValue={editingSlab.wire_bottom}
                    ref={wireBottomRef}
                    required
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-4">
                <button
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingSlab(null);
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-800 text-base font-medium rounded-md shadow-sm hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300"
                  disabled={isSubmitting}
                >
                  Отмена
                </button>
                <button
                  onClick={handleEditSubmit}
                  className="px-4 py-2 bg-blue-600 text-white text-base font-medium rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Сохранение...' : 'Сохранить'}
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
