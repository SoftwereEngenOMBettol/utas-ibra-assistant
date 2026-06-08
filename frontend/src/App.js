// frontend/src/App.js

import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import LoginScreen from "./pages/LoginPage";
import AdminLoginPage from "./pages/AdminLoginPage";
import ChatPage from "./pages/ChatPage";
import AdminDashboard from "./pages/AdminDashboard";
import AdminChatbotManager from "./pages/AdminChatbotManager";  
import AdminProtectedRoute from "./pages/AdminProtectedRoute";
import "./App.css";

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginScreen />} />
        <Route path="/admin/login" element={<AdminLoginPage />} />

        {/* Student Chat Route */}
        <Route path="/chat" element={<ChatPage />} />

        {/* Admin Protected Routes */}
        <Route
          path="/admin/dashboard"
          element={
            <AdminProtectedRoute>
              <AdminDashboard />
            </AdminProtectedRoute>
          }
        />
        <Route 
          path="/admin/chatbot-manager" 
          element={
            <AdminProtectedRoute>
              <AdminChatbotManager />
            </AdminProtectedRoute>
          } 
        />

        {/* Redirects */}
        <Route path="/admin" element={<Navigate to="/admin/login" />} />
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </Router>
  );
}

export default App;