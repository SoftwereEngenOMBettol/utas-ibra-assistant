// frontend/src/pages/AdminLoginPage.jsx

import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./AdminLoginPage.css";

const API_URL = "http://localhost:8000";

const AdminLoginPage = () => {
  const [studentId, setStudentId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      console.log("🔐 Attempting admin login...");
      
      const response = await axios.post(`${API_URL}/api/login`, {
        student_id: studentId,
        password: password,
        language: "en",
      });

      console.log("✅ Login response:", response.data);

      const token = response.data.token; // Use 'token' not 'session_token'
      const user = response.data.student;
      
      console.log("Token received:", token ? "Yes" : "No");
      console.log("User:", user);
      
      if (!token || !user) {
        setError("Invalid response from server");
        setLoading(false);
        return;
      }

      // Check if user is admin
      if (user.is_admin !== true) {
        setError("This account does not have admin privileges");
        setLoading(false);
        return;
      }

      // Clear any old data
      localStorage.clear();

      // Save admin data with standard keys
      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(user));
      localStorage.setItem("is_admin", "true");
      localStorage.setItem("studentId", user.student_id);
      localStorage.setItem("studentName", user.name);

      console.log("💾 Data saved to localStorage:");
      console.log("   token:", token.substring(0, 50) + "...");
      console.log("   is_admin:", localStorage.getItem("is_admin"));
      console.log("   user:", user.name);
      
      // Navigate to dashboard
      navigate("/admin/dashboard");
      
    } catch (err) {
      console.error("❌ Login error:", err);
      const errorMsg = err.response?.data?.detail || "Login failed. Please check your credentials.";
      setError(errorMsg);
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-container">
      <div className="admin-login-box">
        <div className="university-header">
          <h1 className="arabic-title">جامعة التقنية والعلوم التطبيقية</h1>
          <h2 className="english-title">University of Technology and Applied Sciences</h2>
          <div className="branch">Ibra Branch</div>
        </div>

        <h2 className="admin-login-title">Admin Login</h2>

        {error && <div className="admin-error-message">⚠️ {error}</div>}

        <form onSubmit={handleSubmit} className="admin-login-form">
          <div className="admin-form-group">
            <label>Student ID</label>
            <input
              type="text"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              placeholder="Enter admin student ID"
              required
              disabled={loading}
              autoComplete="off"
            />
          </div>

          <div className="admin-form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter admin password"
              required
              disabled={loading}
            />
          </div>

          <button type="submit" className="admin-login-btn" disabled={loading}>
            {loading ? <span className="admin-loading-spinner"></span> : "Login"}
          </button>
        </form>

        <div className="admin-login-footer">
          <p>Use: admin3 / admin123</p>
        </div>
      </div>
    </div>
  );
};

export default AdminLoginPage;