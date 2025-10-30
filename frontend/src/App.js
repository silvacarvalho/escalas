import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import '@/App.css';

// Pages
import Login from '@/pages/Login';
import Dashboard from '@/pages/Dashboard';
import Districts from '@/pages/Districts';
import Churches from '@/pages/Churches';
import Users from '@/pages/Users';
import Schedules from '@/pages/Schedules';
import ScheduleCreate from '@/pages/ScheduleCreate';
import ScheduleCalendar from '@/pages/ScheduleCalendar';
import ScheduleConfirm from '@/pages/ScheduleConfirm';
import Evaluate from '@/pages/Evaluate';
import Profile from '@/pages/Profile';
import Analytics from '@/pages/Analytics';
import Notifications from '@/pages/Notifications';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Axios interceptor for auth token
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor de resposta global para normalizar payloads de erro de API
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    try {
      const apiDetail = error?.response?.data?.detail;
      let normalized = null;
      if (typeof apiDetail === 'string') {
        normalized = apiDetail;
      } else if (Array.isArray(apiDetail)) {
        normalized = apiDetail.map(d => d.msg || JSON.stringify(d)).join('; ');
      } else if (apiDetail && typeof apiDetail === 'object') {
        normalized = apiDetail.msg || JSON.stringify(apiDetail);
      }
      if (normalized) {
        // Sobrescreva tanto `error.message` quanto `response.data.detail` para que os chamadores recebam uma string.
        error.message = normalized;
        if (error.response && error.response.data) {
          error.response.data.detail = normalized;
        }
      }
    } catch (e) {
      // ignore normalization errors
    }
    return Promise.reject(error);
  }
);

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/evaluate/:scheduleItemId" element={<Evaluate />} />
          
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/districts"
            element={
              <PrivateRoute>
                <Districts />
              </PrivateRoute>
            }
          />
          <Route
            path="/churches"
            element={
              <PrivateRoute>
                <Churches />
              </PrivateRoute>
            }
          />
          <Route
            path="/users"
            element={
              <PrivateRoute>
                <Users />
              </PrivateRoute>
            }
          />
          <Route
            path="/schedules"
            element={
              <PrivateRoute>
                <Schedules />
              </PrivateRoute>
            }
          />
          <Route
            path="/schedules/create"
            element={
              <PrivateRoute>
                <ScheduleCreate />
              </PrivateRoute>
            }
          />
          <Route
            path="/schedules/:scheduleId/calendar"
            element={
              <PrivateRoute>
                <ScheduleCalendar />
              </PrivateRoute>
            }
          />
          <Route
            path="/schedule/confirm/:itemId"
            element={
              <PrivateRoute>
                <ScheduleConfirm />
              </PrivateRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <Profile />
              </PrivateRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <PrivateRoute>
                <Analytics />
              </PrivateRoute>
            }
          />
          <Route
            path="/notifications"
            element={
              <PrivateRoute>
                <Notifications />
              </PrivateRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
