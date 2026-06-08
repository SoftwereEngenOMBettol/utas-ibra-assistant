import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './LoginPage.css';
import logo from '../assets/utas-logo.png';

const API_URL = 'http://localhost:8000'; // Changed to match your backend port

const LoginPage = ({ onLogin, onLanguageChange }) => {
  const [studentId, setStudentId] = useState('');
  const [password, setPassword] = useState('');
  const [language, setLanguage] = useState('ar'); // Default to Arabic as per design
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Set document direction based on language
    document.dir = language === 'ar' ? 'rtl' : 'ltr';
    document.body.className = language === 'ar' ? 'arabic-mode' : 'english-mode';
    
    // Check if already logged in
    const token = localStorage.getItem('token');
    const savedLanguage = localStorage.getItem('preferredLanguage');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      const lang = savedLanguage || 'en';
      navigate('/chat');
    }
  }, [language, navigate]);

  const handleLanguageToggle = (lang) => {
    setLanguage(lang);
    if (onLanguageChange) {
      onLanguageChange(lang);
    }
    document.dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.body.className = lang === 'ar' ? 'arabic-mode' : 'english-mode';
    localStorage.setItem('preferredLanguage', lang);
  };

const handleSubmit = async (e) => {
  e.preventDefault();
  setIsLoading(true);
  setError('');

  try {
    // ✅ CORRECT URL - matches your backend endpoint
    const response = await axios.post(`${API_URL}/api/login`, {
      student_id: studentId,
      password: password,
      language: language
    });

    console.log('Login response:', response.data);

    if (response.data.session_token) {
      // Save to localStorage
      localStorage.setItem('token', response.data.session_token);
      localStorage.setItem('session_token', response.data.session_token);
      localStorage.setItem('studentId', response.data.student.student_id);
      localStorage.setItem('studentName', response.data.student.name);
      localStorage.setItem('preferredLanguage', language);
      localStorage.setItem('user', JSON.stringify(response.data.student));
      localStorage.setItem('is_admin', response.data.student.is_admin || false);
      
      if (onLogin) {
        onLogin(response.data.student);
      }
      
      // ✅ Redirect based on user role
      if (response.data.student.is_admin === true) {
        // Admin user - go to admin dashboard
        console.log('✅ Admin login detected, redirecting to admin dashboard');
        navigate('/');
      } else {
        // Regular student - go to chat
        console.log('✅ Student login detected, redirecting to chat');
        navigate('/chat');
      }
    } else {
      setError('Invalid response from server');
    }
  } catch (err) {
    console.error('Login error:', err);
    console.error('Error response:', err.response);
    
    let errorMessage = '';
    if (err.response) {
      // Server responded with error status
      errorMessage = err.response.data?.detail || 
                    err.response.data?.error || 
                    (language === 'en' ? 'Invalid student ID or password' : 'رقم الطالب أو كلمة المرور غير صحيحة');
    } else if (err.request) {
      // Request made but no response
      errorMessage = language === 'en' 
        ? 'Cannot connect to server. Please make sure the backend is running on port 8000'
        : 'لا يمكن الاتصال بالخادم. تأكد من تشغيل الخادم الخلفي على المنفذ 8000';
    } else {
      errorMessage = err.message;
    }
    
    setError(errorMessage);
  } finally {
    setIsLoading(false);
  }
};
  const toggleLanguage = (lang) => {
    setLanguage(lang);
    localStorage.setItem('preferredLanguage', lang);
  };

  

  return (
    <div className={`login-container ${language}`} dir={language === 'ar' ? 'rtl' : 'ltr'}>
      <div className="login-background"></div>
      <div className="login-box">
        <div className="login-header">
            <div className="university-logo">
            <img 
              src={logo} 
              alt="UTAS Logo" 
              className="logo-image"
            />
          </div>
          <h1 className="login-title">
            {language === 'en' ? 'UTAS Ibra Assistant' : 'مساعد جامعة التقنية والعلوم'}
          </h1>
          <p className="login-subtitle">
            {language === 'en' ? 'Administration' : 'إدارة'}
          </p>
        </div>
        
        <div className="login-message">
          {language === 'en' ? 'Please login to continue' : 'الرجاء تسجيل الدخول للمتابعة'}
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <div className="input-icon">
            </div>
            <div className="login-message">
          {language === 'en' ? 'Student ID' : 'رقم الطالب'}
        </div>
            <input
              type="text"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              placeholder={language === 'en' ? 'Student ID' : 'رقم الطالب'}
              required
              disabled={isLoading}
              className={error ? 'error' : ''}
            />
          </div>
          
          <div className="input-group">
         <div className="login-message">
          {language === 'en' ? 'Password' : 'كلمة المرور'}
        </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={language === 'en' ? 'Password' : 'كلمة المرور'}
              required
              disabled={isLoading}
              className={error ? 'error' : ''}
            />
          </div>
          
          {error && (
            <div className="error-message">{error}</div>
          )}
          
          <div className="language-selector">
            <button 
              type="button"
              className={`lang-btn ${language === 'en' ? 'active' : ''}`}
              onClick={() => handleLanguageToggle('en')}
              disabled={isLoading}
            >
              English
            </button>
            <button 
              type="button"
              className={`lang-btn ${language === 'ar' ? 'active' : ''}`}
              onClick={() => handleLanguageToggle('ar')}
              disabled={isLoading}
            >
              العربية
            </button>
          </div>
          
          <button 
            type="submit" 
            className="login-btn"
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="loading-spinner"></span>
            ) : (
              language === 'en' ? 'Login' : 'تسجيل الدخول'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;