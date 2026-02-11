const API_BASE_URL = '/api';

export const fetchTrafficStats = async () => {
    const response = await fetch(`${API_BASE_URL}/traffic/stats`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
};

export const fetchTrafficLogs = async (limit = 50, offset = 0) => {
    const response = await fetch(`${API_BASE_URL}/traffic?limit=${limit}&offset=${offset}`);
    if (!response.ok) throw new Error('Failed to fetch logs');
    return response.json();
};

export const fetchSettings = async () => {
    const response = await fetch(`${API_BASE_URL}/settings`);
    if (!response.ok) throw new Error('Failed to fetch settings');
    return response.json();
};

export const updateSetting = async (name, value) => {
    const response = await fetch(`${API_BASE_URL}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, value }),
    });
    if (!response.ok) throw new Error('Failed to update setting');
    return response.json();
};
