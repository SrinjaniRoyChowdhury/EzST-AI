const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const tokenStorage = {
    get: () => localStorage.getItem('access_token'),
    set: (token) => localStorage.setItem('access_token', token),
    clear: () => localStorage.removeItem('access_token'),
};

async function request(method, path, body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = tokenStorage.get();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);

    const res = await fetch(`${BASE_URL}${path}`, options);

    if (res.status === 401) {
        tokenStorage.clear();
        throw new Error('Unauthorised');
    }

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
}

const api = {
    signUp: (payload) => request('POST', '/auth/signup', payload),
    signIn: (payload) => request('POST', '/auth/signin', payload),
    signOut: () => request('POST', '/auth/signout'),
    getMe: () => request('GET', '/auth/me'),
    get: (path) => request('GET', path),
    post: (path, body) => request('POST', path, body),
};

export default api;