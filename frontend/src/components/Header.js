import React, { useState, useRef, useEffect } from 'react';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import { printTrackPlan, printTrackPlanShort } from '../services/api';


const icons = {
	'road': <svg className="text-blue-600 mr-2 w-6 h-6" width="26" height="26" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">\n' +
		'<path d="M6.49992 3.25008C6.49992 2.96276 6.38578 2.68721 6.18262 2.48405C5.97945 2.28088 5.7039 2.16675 5.41659 2.16675C5.12927 2.16675 4.85372 2.28088 4.65055 2.48405C4.44739 2.68721 4.33325 2.96276 4.33325 3.25008V22.7501C4.33325 23.0374 4.44739 23.3129 4.65055 23.5161C4.85372 23.7193 5.12927 23.8334 5.41659 23.8334C5.7039 23.8334 5.97945 23.7193 6.18262 23.5161C6.38578 23.3129 6.49992 23.0374 6.49992 22.7501V3.25008ZM21.6666 3.25008C21.6666 2.96276 21.5525 2.68721 21.3493 2.48405C21.1461 2.28088 20.8706 2.16675 20.5833 2.16675C20.2959 2.16675 20.0204 2.28088 19.8172 2.48405C19.6141 2.68721 19.4999 2.96276 19.4999 3.25008V22.7501C19.4999 23.0374 19.6141 23.3129 19.8172 23.5161C20.0204 23.7193 20.2959 23.8334 20.5833 23.8334C20.8706 23.8334 21.1461 23.7193 21.3493 23.5161C21.5525 23.3129 21.6666 23.0374 21.6666 22.7501V3.25008ZM14.0833 3.25008C14.0833 2.96276 13.9691 2.68721 13.766 2.48405C13.5628 2.28088 13.2872 2.16675 12.9999 2.16675C12.7126 2.16675 12.4371 2.28088 12.2339 2.48405C12.0307 2.68721 11.9166 2.96276 11.9166 3.25008V6.50008C11.9166 6.7874 12.0307 7.06295 12.2339 7.26611C12.4371 7.46928 12.7126 7.58341 12.9999 7.58341C13.2872 7.58341 13.5628 7.46928 13.766 7.26611C13.9691 7.06295 14.0833 6.7874 14.0833 6.50008V3.25008ZM11.9166 14.6251C11.9166 14.9124 12.0307 15.1879 12.2339 15.3911C12.4371 15.5943 12.7126 15.7084 12.9999 15.7084C13.2872 15.7084 13.5628 15.5943 13.766 15.3911C13.9691 15.1879 14.0833 14.9124 14.0833 14.6251V11.3751C14.0833 11.0878 13.9691 10.8122 13.766 10.609C13.5628 10.4059 13.2872 10.2917 12.9999 10.2917C12.7126 10.2917 12.4371 10.4059 12.2339 10.609C12.0307 10.8122 11.9166 11.0878 11.9166 11.3751V14.6251ZM11.9166 19.5001C11.9166 19.2128 12.0307 18.9372 12.2339 18.734C12.4371 18.5309 12.7126 18.4167 12.9999 18.4167C13.2872 18.4167 13.5628 18.5309 13.766 18.734C13.9691 18.9372 14.0833 19.2128 14.0833 19.5001V22.7501C14.0833 23.0374 13.9691 23.3129 13.766 23.5161C13.5628 23.7193 13.2872 23.8334 12.9999 23.8334C12.7126 23.8334 12.4371 23.7193 12.2339 23.5161C12.0307 23.3129 11.9166 23.0374 11.9166 22.7501V19.5001Z" fill="#235FEB"/>\n' +
		'</svg>,
	'cube': <svg className="text-blue-600 mr-2 w-6 h-6" width="26" height="26" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">\n' +
		'<path fill-rule="evenodd" clip-rule="evenodd" d="M13.9912 4.875L23.3188 7.36125L24.375 8.125V19.0775L23.7738 19.8575L13.8125 22.6038L3.835 19.8575L3.25 19.0775V8.125L4.24125 7.36125L13.5525 4.875H13.9912ZM13.845 6.5L7.345 8.125L8.23875 8.45L13.8125 9.9125L18.6875 8.59625L20.2312 8.125L13.845 6.5ZM4.875 18.46L13 20.6862V11.375L4.875 9.1975V18.46ZM14.625 11.375V20.6862L22.75 18.46V9.14875L19.4675 10.0474V14.2188L17.8425 14.6413V10.4926L14.625 11.375Z" fill="#235FEB"/>\n' +
		'</svg>,
	'percentage': <svg className="text-blue-600 mr-2 w-6 h-6" width="26" height="26" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">\n' +
		'<path d="M16.25 19.4999C16.25 19.7872 16.1359 20.0628 15.9327 20.266C15.7295 20.4691 15.454 20.5833 15.1667 20.5833L10.8333 20.5833C10.546 20.5833 10.2705 20.4691 10.0673 20.266C9.86414 20.0628 9.75 19.7872 9.75 19.4999L9.75 12.9999L16.25 12.9999L16.25 19.4999Z" fill="#235FEB"/>\n' +
		'<path fill-rule="evenodd" clip-rule="evenodd" d="M6.5 6.49992L6.5 20.5833C6.5 21.4452 6.84241 22.2719 7.4519 22.8813C8.0614 23.4908 8.88805 23.8333 9.75 23.8333L16.25 23.8333C17.112 23.8333 17.9386 23.4908 18.5481 22.8813C19.1576 22.2719 19.5 21.4452 19.5 20.5833L19.5 6.49992C19.5 5.63797 19.1576 4.81131 18.5481 4.20182C17.9386 3.59233 17.112 3.24992 16.25 3.24992C16.25 2.9626 16.1359 2.68705 15.9327 2.48389C15.7295 2.28072 15.454 2.16659 15.1667 2.16659L10.8333 2.16659C10.546 2.16659 10.2705 2.28072 10.0673 2.48389C9.86414 2.68705 9.75 2.9626 9.75 3.24992C8.88805 3.24992 8.0614 3.59233 7.4519 4.20182C6.84241 4.81132 6.5 5.63797 6.5 6.49992ZM8.66667 6.49992L8.66667 20.5833C8.66667 20.8706 8.7808 21.1461 8.98397 21.3493C9.18713 21.5524 9.46268 21.6666 9.75 21.6666L16.25 21.6666C16.5373 21.6666 16.8129 21.5524 17.016 21.3493C17.2192 21.1461 17.3333 20.8706 17.3333 20.5833L17.3333 6.49992C17.3333 6.2126 17.2192 5.93705 17.016 5.73389C16.8129 5.53072 16.5373 5.41659 16.25 5.41659L9.75 5.41659C9.46268 5.41659 9.18713 5.53072 8.98397 5.73389C8.7808 5.93705 8.66667 6.2126 8.66667 6.49992Z" fill="#235FEB"/>\n' +
		'</svg>,
	'wrench': <svg className="text-blue-600 mr-2 w-6 h-6" width="26" height="26" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">\n' +
		'<path d="M11.5701 3.94928C11.709 3.69034 11.9155 3.47391 12.1676 3.32304C12.4198 3.17216 12.7082 3.09249 13.002 3.09249C13.2958 3.09249 13.5842 3.17216 13.8364 3.32304C14.0885 3.47391 14.295 3.69034 14.434 3.94928L16.592 7.97018L15.2582 7.52558C15.0139 7.44779 14.7488 7.46934 14.5203 7.58555C14.2918 7.70175 14.1183 7.90327 14.0373 8.14648C13.9563 8.38969 13.9743 8.65503 14.0875 8.88504C14.2006 9.11506 14.3998 9.29125 14.642 9.37548L18.542 10.6755C18.6757 10.72 18.8175 10.7351 18.9576 10.7195C19.0977 10.704 19.2328 10.6583 19.3535 10.5855C19.4743 10.5127 19.5778 10.4146 19.6569 10.2979C19.7361 10.1813 19.789 10.0489 19.8121 9.90978L20.4621 6.00978C20.483 5.88345 20.479 5.75422 20.45 5.62947C20.4211 5.50471 20.3678 5.38689 20.2934 5.28271C20.2189 5.17853 20.1246 5.09004 20.0159 5.0223C19.9072 4.95455 19.7863 4.90888 19.66 4.88788C19.5336 4.86688 19.4044 4.87097 19.2796 4.89991C19.1549 4.92886 19.0371 4.98209 18.9329 5.05658C18.8287 5.13106 18.7402 5.22533 18.6725 5.33401C18.6047 5.44269 18.559 5.56365 18.5381 5.68998L18.3119 7.04978L16.1513 3.02628C14.8045 0.514678 11.2022 0.514678 9.85405 3.02628L7.59725 7.22788C7.48081 7.45506 7.45811 7.71885 7.53404 7.96259C7.60997 8.20632 7.77847 8.41055 8.00333 8.53141C8.2282 8.65227 8.49149 8.68011 8.73667 8.60896C8.98184 8.53781 9.18932 8.37334 9.31455 8.15088L11.5701 3.94928ZM22.0221 18.0829L19.5378 13.4549C19.4742 13.3419 19.4337 13.2174 19.4188 13.0886C19.4039 12.9598 19.4149 12.8294 19.451 12.7049C19.4872 12.5803 19.5478 12.4643 19.6293 12.3635C19.7108 12.2627 19.8116 12.1792 19.9258 12.1178C20.04 12.0564 20.1653 12.0184 20.2943 12.006C20.4234 11.9937 20.5536 12.0072 20.6774 12.0457C20.8011 12.0843 20.916 12.1471 21.0152 12.2306C21.1144 12.3141 21.1959 12.4165 21.2551 12.5319L23.7407 17.1599C25.0186 19.5415 23.2935 22.4249 20.5908 22.4249H16.007L16.9417 23.3609C17.0347 23.4509 17.109 23.5585 17.16 23.6775C17.211 23.7964 17.2379 23.9244 17.2389 24.0539C17.24 24.1833 17.2153 24.3117 17.1662 24.4315C17.1171 24.5513 17.0447 24.6601 16.9531 24.7516C16.8615 24.8431 16.7526 24.9155 16.6327 24.9644C16.5129 25.0134 16.3845 25.038 16.255 25.0368C16.1256 25.0356 15.9977 25.0087 15.8787 24.9575C15.7598 24.9064 15.6522 24.832 15.5624 24.7389L12.9624 22.1389C12.7798 21.9561 12.6772 21.7083 12.6772 21.4499C12.6772 21.1915 12.7798 20.9437 12.9624 20.7609L15.5624 18.1609C15.6516 18.0651 15.7593 17.9883 15.8789 17.935C15.9985 17.8817 16.1276 17.853 16.2585 17.8507C16.3894 17.8484 16.5194 17.8725 16.6408 17.9215C16.7622 17.9706 16.8725 18.0435 16.9651 18.1361C17.0577 18.2287 17.1307 18.339 17.1797 18.4604C17.2287 18.5818 17.2528 18.7118 17.2505 18.8428C17.2482 18.9737 17.2196 19.1028 17.1663 19.2224C17.113 19.342 17.0361 19.4496 16.9404 19.5389L16.0044 20.4749H20.5908C20.8714 20.4744 21.1471 20.4013 21.3911 20.2627C21.635 20.124 21.8389 19.9246 21.9829 19.6837C22.1269 19.4428 22.2061 19.1688 22.2127 18.8883C22.2193 18.6077 22.1532 18.3303 22.0208 18.0829M9.42505 20.4749C9.68364 20.4749 9.93163 20.5776 10.1145 20.7604C10.2973 20.9433 10.4001 21.1913 10.4001 21.4499C10.4001 21.7085 10.2973 21.9565 10.1145 22.1393C9.93163 22.3222 9.68364 22.4249 9.42505 22.4249H5.41325C2.70925 22.4249 0.985451 19.5415 2.26335 17.1599L4.66445 12.6892L2.90945 13.2742C2.78691 13.3195 2.6565 13.3397 2.52599 13.3337C2.39547 13.3276 2.2675 13.2954 2.14969 13.2389C2.03187 13.1824 1.92661 13.1028 1.84015 13.0049C1.7537 12.9069 1.68782 12.7926 1.64642 12.6686C1.60502 12.5447 1.58896 12.4137 1.59918 12.2835C1.6094 12.1532 1.64569 12.0263 1.70591 11.9104C1.76613 11.7944 1.84903 11.6918 1.94971 11.6085C2.05038 11.5252 2.16677 11.463 2.29195 11.4256L6.19195 10.1243C6.31342 10.0837 6.44168 10.0675 6.56942 10.0765C6.69717 10.0855 6.82188 10.1196 6.93644 10.1768C7.05101 10.234 7.15317 10.3133 7.23711 10.41C7.32105 10.5067 7.38512 10.619 7.42565 10.7405L8.72565 14.6418C8.76808 14.7637 8.78586 14.8929 8.77796 15.0218C8.77006 15.1507 8.73663 15.2767 8.67963 15.3926C8.62262 15.5084 8.54317 15.6118 8.44589 15.6967C8.3486 15.7816 8.23542 15.8464 8.11291 15.8872C7.9904 15.928 7.86101 15.944 7.73224 15.9344C7.60347 15.9248 7.4779 15.8897 7.3628 15.8312C7.2477 15.7727 7.14538 15.6919 7.06177 15.5934C6.97816 15.495 6.91493 15.381 6.87575 15.258L6.34795 13.6759L3.98195 18.0829C3.84945 18.3304 3.78332 18.608 3.79001 18.8886C3.7967 19.1692 3.87598 19.4434 4.02012 19.6843C4.16426 19.9252 4.36835 20.1246 4.6125 20.2632C4.85665 20.4017 5.13253 20.4747 5.41325 20.4749H9.42505Z" fill="#235FEB"/>\n' +
		'</svg>,
	'money-bill-wave': <svg className="text-blue-600 mr-2 w-6 h-6" width="26" height="26" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">\n' +
		'<path d="M13 24.375C6.7275 24.375 1.625 19.2725 1.625 13C1.625 6.7275 6.7275 1.625 13 1.625C19.2725 1.625 24.375 6.7275 24.375 13C24.375 19.2725 19.2725 24.375 13 24.375ZM13 3.25C7.62125 3.25 3.25 7.62125 3.25 13C3.25 18.3787 7.62125 22.75 13 22.75C18.3787 22.75 22.75 18.3787 22.75 13C22.75 7.62125 18.3787 3.25 13 3.25Z" fill="#235FEB"/>\n' +
		'<path d="M10.5625 21.125C10.1075 21.125 9.75 20.7675 9.75 20.3125V14.625H7.3125C6.8575 14.625 6.5 14.2675 6.5 13.8125C6.5 13.3575 6.8575 13 7.3125 13H9.75V7.3125C9.75 6.8575 10.1075 6.5 10.5625 6.5H15.4375C16.5149 6.5 17.5483 6.92801 18.3101 7.68988C19.072 8.45175 19.5 9.48506 19.5 10.5625C19.5 11.6399 19.072 12.6733 18.3101 13.4351C17.5483 14.197 16.5149 14.625 15.4375 14.625H11.375V20.3125C11.375 20.7675 11.0175 21.125 10.5625 21.125ZM11.375 13H15.4375C16.7863 13 17.875 11.9113 17.875 10.5625C17.875 9.21375 16.7863 8.125 15.4375 8.125H11.375V13Z" fill="#235FEB"/>\n' +
		'<path d="M15.4375 17.875H7.3125C6.8575 17.875 6.5 17.5175 6.5 17.0625C6.5 16.6075 6.8575 16.25 7.3125 16.25H15.4375C15.8925 16.25 16.25 16.6075 16.25 17.0625C16.25 17.5175 15.8925 17.875 15.4375 17.875Z" fill="#235FEB"/>\n' +
		'</svg>,
	'calendar-check': <svg className="text-blue-600 mr-2 w-6 h-6" width="26" height="26" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">\n' +
		'<path d="M4.3335 9.75V20.5833C4.3335 21.158 4.56177 21.7091 4.9681 22.1154C5.37443 22.5217 5.92553 22.75 6.50016 22.75H19.5002C20.0748 22.75 20.6259 22.5217 21.0322 22.1154C21.4386 21.7091 21.6668 21.158 21.6668 20.5833V9.75M4.3335 9.75V7.58333C4.3335 7.0087 4.56177 6.4576 4.9681 6.05127C5.37443 5.64494 5.92553 5.41667 6.50016 5.41667H8.66683M4.3335 9.75H21.6668M21.6668 9.75V7.58333C21.6668 7.0087 21.4386 6.4576 21.0322 6.05127C20.6259 5.64494 20.0748 5.41667 19.5002 5.41667H17.3335M8.66683 5.41667H17.3335M8.66683 5.41667V3.25M17.3335 5.41667V3.25" stroke="#235FEB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>\n' +
		'</svg>,
}



const Header = ({title, stats, actions, loading = false, loadingMessage = "Загрузка статистики...", onAction}) => {
	// State for date input
	const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
	// State for print dropdown
	const [isPrintDropdownOpen, setIsPrintDropdownOpen] = useState(false);
	const printDropdownRef = useRef(null);

	// Close dropdown when clicking outside
	useEffect(() => {
		function handleClickOutside(event) {
			if (printDropdownRef.current && !printDropdownRef.current.contains(event.target)) {
				setIsPrintDropdownOpen(false);
			}
		}

		document.addEventListener("mousedown", handleClickOutside);
		return () => {
			document.removeEventListener("mousedown", handleClickOutside);
		};
	}, []);

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
            <input 
              type="date" 
              className="border border-gray-300 rounded-md px-3 py-1.5 text-sm text-gray-500" 
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
            />
            <div className="relative" ref={printDropdownRef}>
              <button 
                className="flex items-center gap-2 px-4 py-2 text-sm border border-gray-300 rounded-md text-gray-600 hover:bg-gray-50"
                onClick={() => setIsPrintDropdownOpen(!isPrintDropdownOpen)}
              >
                <FontAwesomeIcon icon="print" className="w-5 h-5" />
                <span>Печать</span>
                <FontAwesomeIcon icon={isPrintDropdownOpen ? "chevron-up" : "chevron-down"} className="w-3 h-3 ml-1" />
              </button>

              {isPrintDropdownOpen && (
                <div className="absolute right-0 mt-1 w-40 bg-white border border-gray-300 rounded-md shadow-lg z-10">
                  <button 
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                    onClick={() => {
                      printTrackPlan(selectedDate);
                      setIsPrintDropdownOpen(false);
                    }}
                  >
                    <FontAwesomeIcon icon="file-alt" className="w-4 h-4 mr-2" />
                    Отчет
                  </button>
                  <button 
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                    onClick={() => {
                      printTrackPlanShort(selectedDate);
                      setIsPrintDropdownOpen(false);
                    }}
                  >
                    <FontAwesomeIcon icon="users" className="w-4 h-4 mr-2" />
                    Для рабочих
                  </button>
                </div>
              )}
            </div>
            <a 
              href="/algorithm" 
              className="flex items-center gap-2 px-4 py-2 text-sm border border-gray-300 rounded-md text-gray-600 hover:bg-gray-50"
            >
              <FontAwesomeIcon icon="info-circle" className="w-5 h-5" />
              <span>Алгоритм</span>
            </a>
          </div>
        </header>
      </div>

      <div style={{display: 'flex', justifyContent: 'space-between', width: '100%'}}>
      {/* Stats - Block 2 */}
		  {loading ? (
			  <div className="bg-white rounded-xl shadow-sm p-6 text-center py-10">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">{loadingMessage}</p>
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
                    {icons[stat.icon] ? icons[stat.icon] : <FontAwesomeIcon icon={stat.icon} className="text-blue-600 mr-2 w-6 h-6" />}
						{stat.title}:
                    <span className={stat.highlight ? "text-red-600 font-semibold ml-1" : "ml-1"}>
                      <span className="font-semibold ml-1">{stat.value}</span>
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
                    {icons[stat.icon] ? icons[stat.icon] : <FontAwesomeIcon icon={stat.icon} className="text-blue-600 mr-2 w-6 h-6" />}
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
                    {icons[stat.icon] ? icons[stat.icon] : <FontAwesomeIcon icon={stat.icon} className="text-blue-600 mr-2 w-6 h-6" />}
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
					{icons[stat.icon] ? icons[stat.icon] : <FontAwesomeIcon icon={stat.icon} className="text-blue-600 mr-2 w-6 h-6" />}
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
