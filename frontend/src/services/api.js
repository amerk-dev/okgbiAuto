// API service for communicating with the backend
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Function to get CSRF token from cookies
const getCsrfToken = () => {
  const name = 'csrftoken=';
  const decodedCookie = decodeURIComponent(document.cookie);
  const cookieArray = decodedCookie.split(';');

  for (let i = 0; i < cookieArray.length; i++) {
    let cookie = cookieArray[i].trim();
    if (cookie.indexOf(name) === 0) {
      return cookie.substring(name.length, cookie.length);
    }
  }
  return '';
};

// Headers for non-GET requests with CSRF token
const getHeaders = () => {
  const headers = {
    'Content-Type': 'application/json',
  };

  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers['X-CSRFToken'] = csrfToken;
  }

  return headers;
};

// Tracks API
export const getTracks = async () => {
  try {
    const response = await fetch(`${API_URL}/api/tracks/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching tracks:', error);
    throw error;
  }
};

export const getContractors = async () => {
  try {
    const response = await fetch(`${API_URL}/api/contractors/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching contractors:', error);
    throw error;
  }
};

export const updateTrackContractor = async (trackId, contractor) => {
  try {
    const response = await fetch(`${API_URL}/api/tracks/${trackId}/contractor/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ contractor }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error updating track contractor:', error);
    throw error;
  }
};

export const moveSlab = async (slabId, targetTrackId, targetDay) => {
  try {
    const response = await fetch(`${API_URL}/api/tracks/move-slab/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ slabId, targetTrackId, targetDay }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error moving slab:', error);
    throw error;
  }
};

export const swapTracks = async (track1Id, track2Id) => {
  try {
    // Note: This uses the same endpoint as moveSlab but with different parameters
    // The backend MoveTrackView handles both slab movement and track swapping
    const response = await fetch(`${API_URL}/api/tracks/swap/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ track1Id, track2Id }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error swapping tracks:', error);
    throw error;
  }
};

export const getTrackSlabs = async (trackId) => {
  try {
    const response = await fetch(`${API_URL}/api/tracks/${trackId}/slabs/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching track slabs:', error);
    throw error;
  }
};

export const updateSlab = async (slabId, slabData) => {
  try {
    const response = await fetch(`${API_URL}/api/plates/${slabId}/`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(slabData),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error updating slab:', error);
    throw error;
  }
};

export const deleteSlab = async (slabId) => {
  try {
    const response = await fetch(`${API_URL}/api/plates/${slabId}/`, {
      method: 'DELETE',
      headers: getHeaders(),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error deleting slab:', error);
    throw error;
  }
};

export const transferSlabs = async (slabIds, targetTrackPosition, targetDate) => {
  try {
    const response = await fetch(`${API_URL}/api/tracks/transfer-slabs/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ slabIds, targetTrackPosition, targetDate }),
    });

    if (!response.ok) {
      // Special handling for 400 Bad Request responses
      if (response.status === 400) {
        // Parse the response body to get the detailed error message
        const errorData = await response.json();
        // The Django REST framework typically returns error details in the 'detail' field
        const errorMessage = errorData.detail || JSON.stringify(errorData);
        throw new Error(errorMessage);
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error transferring slabs:', error);
    throw error;
  }
};

// Orders API
export const getOrders = async () => {
  try {
    const response = await fetch(`${API_URL}/api/orders/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching orders:', error);
    throw error;
  }
};

export const getDeletedOrders = async () => {
  try {
    const response = await fetch(`${API_URL}/api/orders/deleted/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching deleted orders:', error);
    throw error;
  }
};

export const getStock = async () => {
  try {
    const response = await fetch(`${API_URL}/api/stock/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching stock:', error);
    throw error;
  }
};

export const deleteOrder = async (orderId, plateName) => {
  try {
    const response = await fetch(`${API_URL}/api/orders/${orderId}/`, {
      method: 'DELETE',
      headers: getHeaders(),
      body: JSON.stringify({ plateName }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error deleting order:', error);
    throw error;
  }
};

export const restoreOrder = async (orderId, plateName) => {
  try {
    const response = await fetch(`${API_URL}/api/orders/${orderId}/restore/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ plateName }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error restoring order:', error);
    throw error;
  }
};

// Materials and Settings API
export const getMaterials = async () => {
  try {
    const response = await fetch(`${API_URL}/api/materials/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching materials:', error);
    throw error;
  }
};

export const getTrackSettings = async () => {
  try {
    const response = await fetch(`${API_URL}/api/track-settings/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching track settings:', error);
    throw error;
  }
};

export const updateMaterials = async (materials) => {
  try {
    const response = await fetch(`${API_URL}/api/materials/update/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ materials }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error updating materials:', error);
    throw error;
  }
};

export const updateTrackSettings = async (settings) => {
  try {
    const response = await fetch(`${API_URL}/api/track-settings/update/`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(settings),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error updating track settings:', error);
    throw error;
  }
};

// Dashboard API
export const getDashboardStats = async () => {
  try {
    const response = await fetch(`${API_URL}/api/dashboard/`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching dashboard stats:', error);
    throw error;
  }
};

// Calculation API
export const startCalculation = async () => {
  try {
    const response = await fetch(`${API_URL}/api/calculate/`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error starting calculation:', error);
    throw error;
  }
};

export const startResetCalculation = async () => {
  try {
    const response = await fetch(`${API_URL}/api/reset-calculate/`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error starting reset calculation:', error);
    throw error;
  }
};

export const getCalculationStatus = async (taskId) => {
  try {
    const url = taskId 
      ? `${API_URL}/api/calculation-status/${taskId}/` 
      : `${API_URL}/api/calculation-status/`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error getting calculation status:', error);
    throw error;
  }
};

// Print API
export const printTrackPlan = (date, trackId) => {
  // Construct the URL with query parameters
  let url = `${API_URL}/api/print/?date=${date}`;
  if (trackId) {
    url += `&track_id=${trackId}`;
  }

  // Open the URL in a new window/tab
  window.open(url, '_blank');
};

// Print Short API (for workers)
export const printTrackPlanShort = (date, trackId) => {
  // Construct the URL with query parameters
  let url = `${API_URL}/api/print-short/?date=${date}`;
  if (trackId) {
    url += `&track_id=${trackId}`;
  }

  // Open the URL in a new window/tab
  window.open(url, '_blank');
};

// Export to 1C API
export const exportTo1C = async () => {
  try {
    const response = await fetch(`${API_URL}/api/export-1c/`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error exporting to 1C:', error);
    throw error;
  }
};
