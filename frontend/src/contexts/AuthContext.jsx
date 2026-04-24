/**
 * Authentication Context for SARAI
 * 
 * Manages user authentication state and provides login/logout functions
 */
import React, { createContext, useContext, useState, useEffect } from 'react';
import { jwtDecode } from 'jwt-decode';
import axios from 'axios';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    const storedToken = sessionStorage.getItem('token');
    const storedUser = sessionStorage.getItem('user');

    if (storedToken && storedUser) {
      try {
        // Verify token is not expired
        const decoded = jwtDecode(storedToken);
        const currentTime = Date.now() / 1000;

        if (decoded.exp > currentTime) {
          setToken(storedToken);
          setUser(JSON.parse(storedUser));
        } else {
          // Token expired, clear storage
          sessionStorage.removeItem('token');
          sessionStorage.removeItem('user');
        }
      } catch (error) {
        console.error('Error parsing stored auth:', error);
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('user');
      }
    }

    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
      const response = await axios.post(`${API}/auth/login`, {
        email,
        password
      });

      const { access_token, user: userData } = response.data;

      // Store in state
      setToken(access_token);
      setUser(userData);

      // Store in sessionStorage (cleared on tab/window close)
      sessionStorage.setItem('token', access_token);
      sessionStorage.setItem('user', JSON.stringify(userData));

      return { success: true, user: userData };
    } catch (error) {
      console.error('Login error:', error);
      const message = error.response?.data?.detail || 'Login failed. Please check your credentials.';
      return { success: false, error: message };
    }
  };

  const logout = () => {
    // Clear state
    setToken(null);
    setUser(null);

    // Clear sessionStorage
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');

    // Redirect to login
    window.location.href = '/login';
  };

  const isAuthenticated = () => {
    return !!token && !!user;
  };

  const hasRole = (roles) => {
    if (!user) return false;
    if (Array.isArray(roles)) {
      return roles.includes(user.role);
    }
    return user.role === roles;
  };

  const isAdmin = () => hasRole('admin');
  const isStaff = () => hasRole(['admin', 'staff']);

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    isAuthenticated,
    hasRole,
    isAdmin,
    isStaff
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
