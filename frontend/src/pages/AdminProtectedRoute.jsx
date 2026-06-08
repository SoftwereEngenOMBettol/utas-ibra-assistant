// frontend/src/components/AdminProtectedRoute.jsx

import React from "react";
import { Navigate } from "react-router-dom";

const AdminProtectedRoute = ({ children }) => {
  // Read directly from localStorage
  const token = localStorage.getItem("token");
  const isAdmin = localStorage.getItem("is_admin");

  console.log("🔒 Admin Route Check:", { 
    hasToken: !!token, 
    tokenValue: token ? token.substring(0, 30) + "..." : null,
    isAdminValue: isAdmin,
    isAdminBoolean: isAdmin === "true"
  });

  // Check if admin is logged in
  if (!token) {
    console.log("❌ No token found, redirecting to admin login");
    return <Navigate to="/admin/login" replace />;
  }

  if (isAdmin !== "true") {
    console.log("❌ User is not admin (is_admin =", isAdmin, "), redirecting to admin login");
    return <Navigate to="/admin/login" replace />;
  }

  console.log("✅ Admin access granted, rendering protected component");
  return children;
};

export default AdminProtectedRoute;