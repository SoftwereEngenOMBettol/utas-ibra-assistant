// frontend/src/pages/ChatPage.jsx

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './ChatPage.css';
import logo from '../assets/utas-logo.png';

const API_URL = 'http://localhost:8000';

const ChatPage = ({ user, onLogout }) => {
  const [messages, setMessages] = useState([]);
  const [showWelcome, setShowWelcome] = useState(true);
  const [hasSentFirstMessage, setHasSentFirstMessage] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState(localStorage.getItem('preferredLanguage') || 'en');
  const [showFQA, setShowFQA] = useState(false);
  const [fqaList, setFqaList] = useState([]);
  const [showFeedback, setShowFeedback] = useState(false);
  const [rating, setRating] = useState(0);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [showLanguageWarning, setShowLanguageWarning] = useState(false);
  const [error, setError] = useState(null);
  
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();

  const sessionToken = localStorage.getItem('session_token');
  const studentId = localStorage.getItem('studentId');
  const studentName = localStorage.getItem('studentName');

  const quickQuestions = language === 'ar' ? [
    'ما هو معدلي التراكمي؟',
    'كيفية التسجيل في المواد؟',
    'آخر يوم للإضافة والحذف؟',
    'الدخول إلى نظام CIMS',
    'التواصل مع المرشد الأكاديمي',
    'تحميل جدول المحاضرات',
    'تحميل تقرير الحضور'
  ] : [
    'What is my GPA?',
    'How to register for courses?',
    'Add/Drop deadline?',
    'Access CIMS',
    'Contact my advisor',
    'Download my timetable',
    'Download attendance report'
  ];

  // Check if text contains Arabic
  const containsArabic = (text) => {
    const arabicRegex = /[\u0600-\u06FF]/;
    return arabicRegex.test(text);
  };

  // Check if text contains English
  const containsEnglish = (text) => {
    const englishRegex = /[a-zA-Z]/;
    return englishRegex.test(text);
  };

  // ==================== PDF DOWNLOAD HANDLER ====================
  const handleDownloadPDF = (pdfData, filename) => {
    try {
      console.log('📄 Downloading PDF:', filename);
      console.log('PDF Data length:', pdfData?.length);
      
      if (!pdfData) {
        console.error('No PDF data received');
        alert('No PDF data received');
        return;
      }
      
      // Convert base64 to blob
      const byteCharacters = atob(pdfData);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/pdf' });
      
      // Create download link
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      console.log('✅ PDF downloaded successfully:', filename);
      alert(`PDF downloaded: ${filename}`);
      
    } catch (error) {
      console.error('PDF download error:', error);
      alert('Failed to download PDF. Please try again.');
    }
  };

  // Save messages to localStorage
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('chat_messages', JSON.stringify(messages));
    }
  }, [messages]);

  // Load saved messages
  useEffect(() => {
    const savedMessages = localStorage.getItem('chat_messages');
    if (savedMessages) {
      try {
        const parsedMessages = JSON.parse(savedMessages);
        setMessages(parsedMessages);
        if (parsedMessages.length > 0) {
          setShowWelcome(false);
          setHasSentFirstMessage(true);
        }
      } catch (e) {
        console.error('Error loading saved messages:', e);
      }
    }
  }, []);

  useEffect(() => {
    document.dir = language === 'ar' ? 'rtl' : 'ltr';
    document.body.className = language === 'ar' ? 'arabic-mode' : 'english-mode';
    loadFQA();
  }, [language]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadFQA = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/admin/fqa/public`);
      setFqaList(response.data);
    } catch (err) {
      console.error('Failed to load FQA:', err);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    // Hide welcome message on first message
    if (!hasSentFirstMessage && showWelcome) {
      setShowWelcome(false);
      setHasSentFirstMessage(true);
    }

    // Language validation
    if (language === 'ar' && containsEnglish(inputMessage) && !containsArabic(inputMessage)) {
      setShowLanguageWarning(true);
      setTimeout(() => setShowLanguageWarning(false), 5000);
      return;
    }

    if (language === 'en' && containsArabic(inputMessage)) {
      setShowLanguageWarning(true);
      setTimeout(() => setShowLanguageWarning(false), 5000);
      return;
    }

    const userMessage = {
      id: messages.length + 1,
      text: inputMessage,
      sender: 'user',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputMessage;
    setInputMessage('');
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      
      const response = await axios.post(`${API_URL}/api/chat`, {
        student_id: studentId,
        session_token: sessionToken,
        message: currentInput,
        language: language
      }, {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = response.data;
      const hasPDF = data.pdf_data && data.filename;
      
      const botMessage = {
        id: messages.length + 2,
        text: data.answer,
        sender: 'bot',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        fromFaq: data.from_faq,
        intent: data.intent,
        pdf_data: data.pdf_data,
        filename: data.filename,
        isPdfResponse: hasPDF,
        isHtml: data.answer && (data.answer.includes('<div') || data.answer.includes('<table'))
      };

      setMessages(prev => [...prev, botMessage]);

      // Auto-download PDF if present
      if (hasPDF) {
        console.log('📄 PDF detected, downloading...');
        setTimeout(() => {
          handleDownloadPDF(data.pdf_data, data.filename);
        }, 500);
      }

    } catch (error) {
      console.error('Error:', error);
      
      let errorMessage = language === 'ar' 
        ? 'عذراً، حدث خطأ. الرجاء المحاولة مرة أخرى.'
        : "Sorry, I'm having trouble connecting. Please try again.";
      
      setMessages(prev => [...prev, {
        id: messages.length + 2,
        text: errorMessage,
        sender: 'bot',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);

    } finally {
      setLoading(false);
    }
  };

  const handleSuggestedQuestion = (question) => {
    setInputMessage(question);
    setTimeout(() => {
      sendMessage();
    }, 100);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !loading) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleLogout = () => {
    setShowFeedback(true);
  };

  const submitFeedback = async () => {
    if (rating === 0) {
      alert(language === 'ar' ? 'الرجاء اختيار تقييم' : 'Please select a rating');
      return;
    }
    
    try {
      if (rating > 0) {
        await axios.post(`${API_URL}/api/feedback`, {
          student_id: studentId,
          rating: rating,
          comment: feedbackComment
        });
      }
      
      await axios.post(`${API_URL}/api/logout`, null, {
        params: { session_token: sessionToken }
      });
      
      localStorage.removeItem('chat_messages');
      localStorage.clear();
      navigate('/login');
    } catch (err) {
      console.error('Feedback submission failed:', err);
      localStorage.clear();
      navigate('/login');
    }
  };

  const toggleLanguage = () => {
    const newLang = language === 'ar' ? 'en' : 'ar';
    setLanguage(newLang);
    localStorage.setItem('preferredLanguage', newLang);
  };

  const clearChatHistory = () => {
    if (window.confirm(language === 'ar' ? 'هل تريد مسح سجل المحادثة؟' : 'Clear chat history?')) {
      setMessages([]);
      setShowWelcome(true);
      setHasSentFirstMessage(false);
      localStorage.removeItem('chat_messages');
    }
  };

  const getStudentName = () => {
    if (studentName) {
      return studentName.split(' ')[0];
    }
    return language === 'ar' ? 'الطالب' : 'Student';
  };

  return (
    <div className={`chat-container ${language === 'ar' ? 'rtl-mode' : 'ltr-mode'}`} dir={language === 'ar' ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className={`chat-header ${language === 'ar' ? 'rtl-mode' : 'ltr-mode'}`}>
  <div className="logo-container">
    <div className="university-logo">
      <img 
        src={logo} 
        alt="UTAS Logo" 
        className="logo-image"
      />
    </div>
  </div>
  <div className="header-buttons">
    <button onClick={clearChatHistory} className="clear-btn" title={language === 'ar' ? 'مسح المحادثة' : 'Clear chat'}>
      <i className="fas fa-trash-alt"></i>
    </button>
    <button onClick={() => setShowFQA(true)} className="faq-btn">
      <i className="fas fa-question-circle"></i>
      {language === 'ar' ? 'الأسئلة الشائعة' : 'FAQ'}
    </button>
    <button onClick={toggleLanguage} className="lang-switch-btn">
      <i className="fas fa-language"></i>
      {language === 'ar' ? 'English' : 'العربية'}
    </button>
    <button onClick={handleLogout} className="logout-btn">
      <i className="fas fa-sign-out-alt"></i>
      {language === 'ar' ? 'تسجيل الخروج' : 'Logout'}
    </button>
  </div>
</div>

      <div className="main-content">
        {/* Language Warning */}
        {showLanguageWarning && (
          <div className="language-warning">
            <i className="fas fa-exclamation-triangle"></i>
            <div className="warning-text">
              <strong>{language === 'ar' ? 'تحذير:' : 'Warning:'}</strong>
              {language === 'ar' ? ' الرجاء استخدام اللغة العربية فقط' : ' Please use English only'}
            </div>
            <button className="warning-close" onClick={() => setShowLanguageWarning(false)}>
              <i className="fas fa-times"></i>
            </button>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="error-message">
            <i className="fas fa-exclamation-circle"></i>
            <span>{error}</span>
            <button onClick={() => setError(null)} className="error-close">
              <i className="fas fa-times"></i>
            </button>
          </div>
        )}

        <div className="messages-area">
          {messages.map((msg) => (
            <div key={msg.id} className={`message-wrapper ${msg.sender}`}>
              <div className={`message ${msg.sender}`}>
                <div className={`avatar ${msg.sender === 'bot' ? 'bot-avatar' : 'user-avatar'}`}>
                  <i className={`fas ${msg.sender === 'bot' ? 'fa-robot' : 'fa-user'}`}></i>
                </div>
                <div className="message-content">
                  <div className="message-bubble">
                    {msg.sender === 'bot' && msg.isHtml ? (
                      <div className="html-content" dangerouslySetInnerHTML={{ __html: msg.text }} />
                    ) : (
                      msg.text.split('\n').map((line, i) => (
                        <React.Fragment key={i}>
                          {line}
                          {i < msg.text.split('\n').length - 1 && <br />}
                        </React.Fragment>
                      ))
                    )}
                  </div>
                  
                  {/* PDF Download Button */}
                  {msg.sender === 'bot' && msg.pdf_data && (
                    <button 
                      onClick={() => handleDownloadPDF(msg.pdf_data, msg.filename)}
                      className="download-pdf-btn"
                    >
                      <i className="fas fa-download"></i>
                      {language === 'ar' ? 'تحميل PDF' : 'Download PDF'}
                    </button>
                  )}
                  
                  <div className="message-time">{msg.time}</div>
                </div>
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="message-wrapper bot">
              <div className="message bot">
                <div className="avatar bot-avatar">
                  <i className="fas fa-robot"></i>
                </div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Welcome Message */}
        {showWelcome && messages.length === 0 && !loading && !hasSentFirstMessage && (
          <div className="welcome-container">
            <div className="welcome-content">
              <div className="welcome-icon">
                <i className="fas fa-robot"></i>
              </div>
              <h2 className="welcome-title">
                {language === 'ar' 
                  ? `مرحباً ${getStudentName()}، أنا مساعد جامعة التقنية`
                  : `Hi ${getStudentName()}, I'm your UTAS Assistant`}
              </h2>
              <p className="welcome-subtitle">
                {language === 'ar' 
                  ? 'يمكنني مساعدتك في المعدل، الجدول، التسجيل، وأكثر. ماذا تريد أن تعرف؟'
                  : 'I can help you with GPA, schedules, registration, and more. What would you like to know?'}
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="bottom-section">
        <div className="suggested-questions">
          {quickQuestions.map((q, index) => (
            <button
              key={index}
              className="suggested-question-btn"
              onClick={() => handleSuggestedQuestion(q)}
              disabled={loading}
            >
              {q}
            </button>
          ))}
        </div>

        <div className="input-container">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={language === 'ar' ? 'اكتب سؤالك هنا...' : 'Type your message here...'}
            className="chat-input"
            disabled={loading}
          />
          <button 
            onClick={sendMessage} 
            className="send-button"
            disabled={loading || !inputMessage.trim()}
          >
            {loading ? (
              <i className="fas fa-spinner fa-spin"></i>
            ) : (
              <i className="fas fa-paper-plane"></i>
            )}
          </button>
        </div>
      </div>

      {/* FAQ Modal */}
      {showFQA && (
        <div className="modal-overlay" onClick={() => setShowFQA(false)}>
          <div className="modal-content faq-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3><i className="fas fa-question-circle"></i> {language === 'ar' ? 'الأسئلة الشائعة' : 'Frequently Asked Questions'}</h3>
              <button className="modal-close" onClick={() => setShowFQA(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="faq-cards-grid">
                {fqaList.map((fqa, idx) => (
                  <div 
                    key={idx} 
                    className="faq-card"
                    onClick={() => {
                      setInputMessage(language === 'ar' ? fqa.question_ar : fqa.question_en);
                      setShowFQA(false);
                      setTimeout(() => {
                        sendMessage();
                      }, 100);
                    }}
                  >
                    <div className="faq-card-icon">
                      <i className="fas fa-question"></i>
                    </div>
                    <div className="faq-card-content">
                      <div className="faq-card-question">
                        {language === 'ar' ? fqa.question_ar : fqa.question_en}
                      </div>
                      <div className="faq-card-category">
                        <i className="fas fa-tag"></i>
                        {fqa.category || 'General'}
                      </div>
                    </div>
                    <div className="faq-card-arrow">
                      <i className="fas fa-chevron-right"></i>
                    </div>
                  </div>
                ))}
              </div>
              {fqaList.length === 0 && (
                <div className="no-data">
                  <i className="fas fa-inbox"></i>
                  <p>{language === 'ar' ? 'لا توجد أسئلة شائعة' : 'No FAQs available'}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Feedback Modal */}
      {showFeedback && (
        <div className="modal-overlay" onClick={() => setShowFeedback(false)}>
          <div className="modal-content feedback-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3><i className="fas fa-star"></i> {language === 'ar' ? 'قيم تجربتك' : 'Rate Your Experience'}</h3>
              <button className="modal-close" onClick={() => setShowFeedback(false)}>×</button>
            </div>
            <div className="modal-body text-center">
              <div className="rating-stars">
                {[1, 2, 3, 4, 5].map(star => (
                  <i 
                    key={star}
                    className={`fas fa-star ${star <= rating ? 'active' : ''}`}
                    onClick={() => setRating(star)}
                  ></i>
                ))}
              </div>
              {rating === 0 && (
                <div className="feedback-error">{language === 'ar' ? 'الرجاء اختيار تقييم' : 'Please select a rating'}</div>
              )}
              <textarea
                placeholder={language === 'ar' ? 'تعليقك (اختياري)...' : 'Your feedback (optional)...'}
                value={feedbackComment}
                onChange={(e) => setFeedbackComment(e.target.value)}
                rows="3"
              />
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowFeedback(false)}>
                {language === 'ar' ? 'إلغاء' : 'Cancel'}
              </button>
              <button className="btn-primary" onClick={submitFeedback}>
                <i className="fas fa-paper-plane"></i>
                {language === 'ar' ? 'إرسال' : 'Submit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatPage;