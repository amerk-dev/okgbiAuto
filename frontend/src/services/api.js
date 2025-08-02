// API service for communicating with the backend
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
      headers: {
        'Content-Type': 'application/json',
      },
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
      headers: {
        'Content-Type': 'application/json',
      },
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
      headers: {
        'Content-Type': 'application/json',
      },
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

export const deleteOrder = async (orderId) => {
  try {
    const response = await fetch(`${API_URL}/api/orders/${orderId}/`, {
      method: 'DELETE',
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
      headers: {
        'Content-Type': 'application/json',
      },
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
      headers: {
        'Content-Type': 'application/json',
      },
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
      headers: {
        'Content-Type': 'application/json',
      },
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
