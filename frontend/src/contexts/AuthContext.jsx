import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within AuthProvider');
    return context;
};

export const AuthProvider = ({ children }) => {
    const [state, setState] = useState({
        user: null,
        accessToken: null,
        loading: true,
    });

    // API client with auth interceptor
    const api = axios.create({
        baseURL: 'http://localhost:8000/api', // Your FastAPI URL
        withCredentials: true,
    });

    // Request interceptor - add token
    api.interceptors.request.use((config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    });

    // Response interceptor - handle 401
    api.interceptors.response.use(
        (response) => response,
        async (error) => {
            if (error.response?.status === 401) {
                logout();
            }
            return Promise.reject(error);
        }
    );

    const login = useCallback(async (email, password) => {
        const response = await api.post('/auth/signin', { email, password });
        const { access_token, user_id, email: userEmail } = response.data;

        localStorage.setItem('access_token', access_token);
        setState({ ...state, accessToken: access_token, user: { id: user_id, email: userEmail } });

        // Fetch full profile
        await getProfile();
    }, [state]);

    const signup = useCallback(async (email, password, full_name, role = 'seller') => {
        const response = await api.post('/auth/signup', { email, password, full_name, role });
        const { access_token, user_id, email: userEmail } = response.data;

        localStorage.setItem('access_token', access_token);
        setState({ ...state, accessToken: access_token, user: { id: user_id, email: userEmail } });

        // Fetch full profile
        await getProfile();
    }, [state]);

    const logout = useCallback(() => {
        api.post('/auth/signout').catch(() => { }); // Ignore errors
        localStorage.removeItem('access_token');
        setState({ user: null, accessToken: null, loading: false });
    }, []);

    const getProfile = useCallback(async () => {
        try {
            const response = await api.get('/auth/me');
            setState(prev => ({ ...prev, user: response.data }));
        } catch (error) {
            console.error('Failed to fetch profile:', error);
        }
    }, []);

    const registerBusiness = useCallback(async (data) => {
        const response = await api.post('/auth/register-business', data);
        await getProfile(); // Refresh profile with business_id
        return response.data;
    }, [getProfile]);

    // Check auth on mount
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (token) {
            setState(prev => ({ ...prev, accessToken: token }));
            getProfile().finally(() => {
                setState(prev => ({ ...prev, loading: false }));
            });
        } else {
            setState(prev => ({ ...prev, loading: false }));
        }
    }, []);

    const value = {
        ...state,
        login,
        signup,
        logout,
        getProfile,
        registerBusiness,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};