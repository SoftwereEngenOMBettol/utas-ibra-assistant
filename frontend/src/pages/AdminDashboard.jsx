// frontend/src/pages/AdminDashboard.jsx

import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./AdminDashboard.css";
import logo from '../assets/utas-logo.png';

const API_URL = "http://localhost:8000";

const AdminDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [stats, setStats] = useState({
    totalStudents: 0,
    totalFAQs: 0,
    totalQueries: 0,
    unansweredQuestions: 0,
  });
  
  // Data states
  const [students, setStudents] = useState([]);
  const [faqs, setFaqs] = useState([]);
  const [unansweredQuestions, setUnansweredQuestions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [error, setError] = useState(null);
  
  // Modal states
  const [showAIModal, setShowAIModal] = useState(false);
  const [showManualModal, setShowManualModal] = useState(false);
  const [showAnswerModal, setShowAnswerModal] = useState(false);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [generatedFAQs, setGeneratedFAQs] = useState([]);
  const [showPreview, setShowPreview] = useState(false);
  
  // Form states
  const [aiInputType, setAiInputType] = useState("pdf");
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfFileName, setPdfFileName] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [htmlContent, setHtmlContent] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  
  const [manualFAQ, setManualFAQ] = useState({
    question_ar: "",
    question_en: "",
    answer_ar: "",
    answer_en: "",
    category: "",
  });
  
  const [newCategory, setNewCategory] = useState({ 
    name_ar: "", 
    name_en: "", 
    description: "" 
  });
  
  const [answerData, setAnswerData] = useState({ 
    answer_ar: "", 
    answer_en: "" 
  });
  
  const navigate = useNavigate();

  // Helper to get auth config
  const getAuthConfig = () => {
    const token = localStorage.getItem("token");
    return {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    };
  };

  // Check admin status on mount
  useEffect(() => {
    const token = localStorage.getItem("token");
    const isAdmin = localStorage.getItem("is_admin");

    if (!token || isAdmin !== "true") {
      navigate("/admin/login");
      return;
    }

    fetchDashboardData();
    fetchCategories();
  }, [navigate]);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const config = getAuthConfig();

      const [usageRes, studentsRes, faqsRes, unansweredRes] = await Promise.all([
        axios.get(`${API_URL}/api/admin/usage`, config),
        axios.get(`${API_URL}/api/admin/students`, config),
        axios.get(`${API_URL}/api/admin/fqa`, config),
        axios.get(`${API_URL}/api/admin/fqa/pending`, config),
      ]);

      setStats({
        totalStudents: studentsRes.data?.length || 0,
        totalFAQs: faqsRes.data?.length || 0,
        totalQueries: usageRes.data?.today?.total_queries || 0,
        unansweredQuestions: unansweredRes.data?.length || 0,
      });

      setStudents(studentsRes.data || []);
      setFaqs(faqsRes.data || []);
      setUnansweredQuestions(unansweredRes.data || []);
      
    } catch (err) {
      console.error("Error fetching data:", err);
      if (err.response?.status === 401) {
        localStorage.clear();
        navigate("/admin/login");
      } else {
        setError(err.response?.data?.detail || "Failed to load data");
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const config = getAuthConfig();
      const response = await axios.get(`${API_URL}/api/admin/categories`, config);
      setCategories(response.data || []);
    } catch (err) {
      console.error("Error fetching categories:", err);
      setCategories([
        { id: 1, name_ar: "عام", name_en: "General" },
        { id: 2, name_ar: "التسجيل", name_en: "Registration" },
        { id: 3, name_ar: "المعدل", name_en: "GPA" },
        { id: 4, name_ar: "الجدول", name_en: "Schedule" },
      ]);
    }
  };

  // AI Generation Handlers
  const handleAIGenerate = async () => {
    if (aiInputType === "pdf" && !pdfFile) {
      alert("Please select a PDF file");
      return;
    }
    if (aiInputType === "url" && !urlInput) {
      alert("Please enter a website URL");
      return;
    }
    if (aiInputType === "html" && !htmlContent) {
      alert("Please paste HTML/CSS content");
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const formData = new FormData();
      formData.append("category", selectedCategory || "General");
      
      let response;
      
      if (aiInputType === "pdf" && pdfFile) {
        formData.append("file", pdfFile);
        response = await axios.post(`${API_URL}/api/admin/fqa/upload-pdf`, formData, {
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "multipart/form-data" },
        });
      } else if (aiInputType === "url" && urlInput) {
        formData.append("url", urlInput);
        response = await axios.post(`${API_URL}/api/admin/fqa/from-url`, formData, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } else if (aiInputType === "html" && htmlContent) {
        formData.append("content", htmlContent);
        formData.append("content_type", "html_css");
        response = await axios.post(`${API_URL}/api/admin/fqa/generate-from-content`, formData, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }
      
      setGeneratedFAQs(response.data.faqs || []);
      setShowPreview(true);
      setShowAIModal(false);
      
      // Reset AI form
      setPdfFile(null);
      setPdfFileName("");
      setUrlInput("");
      setHtmlContent("");
      setSelectedCategory("");
      
      alert(`✅ Successfully generated ${response.data.faqs?.length || 0} FAQs!`);
      fetchDashboardData();
    } catch (err) {
      console.error("AI Generation failed:", err);
      alert("❌ Error generating FAQs. Please check your API key and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleManualAdd = async () => {
    if (!manualFAQ.question_en || !manualFAQ.answer_en) {
      alert("Please fill in question and answer in English");
      return;
    }
    
    setLoading(true);
    try {
      const config = getAuthConfig();
      await axios.post(`${API_URL}/api/admin/fqa/manual`, manualFAQ, config);
      setShowManualModal(false);
      setManualFAQ({ 
        question_ar: "", 
        question_en: "", 
        answer_ar: "", 
        answer_en: "", 
        category: "" 
      });
      fetchDashboardData();
      alert("✅ FAQ added successfully!");
    } catch (err) {
      console.error("Failed to add FAQ:", err);
      alert("❌ Error adding FAQ");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFAQ = async (id) => {
    if (window.confirm("Are you sure you want to delete this FAQ?")) {
      setLoading(true);
      try {
        const config = getAuthConfig();
        await axios.delete(`${API_URL}/api/admin/fqa/${id}`, config);
        fetchDashboardData();
        alert("✅ FAQ deleted successfully!");
      } catch (err) {
        console.error("Failed to delete FAQ:", err);
        alert("❌ Error deleting FAQ");
      } finally {
        setLoading(false);
      }
    }
  };

  const handleAnswerQuestion = async () => {
    if (!selectedQuestion) return;
    if (!answerData.answer_en) {
      alert("Please provide an answer in English");
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const formData = new FormData();
      formData.append("answer_ar", answerData.answer_ar);
      formData.append("answer_en", answerData.answer_en);
      
      await axios.post(`${API_URL}/api/admin/fqa/answer-pending/${selectedQuestion.id}`, formData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      setShowAnswerModal(false);
      setSelectedQuestion(null);
      setAnswerData({ answer_ar: "", answer_en: "" });
      fetchDashboardData();
      alert("✅ Question answered and added to FAQ database!");
    } catch (err) {
      console.error("Failed to answer question:", err);
      alert("❌ Error answering question");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCategory = async () => {
    if (!newCategory.name_en) {
      alert("Please enter category name");
      return;
    }
    setLoading(true);
    try {
      const config = getAuthConfig();
      await axios.post(`${API_URL}/api/admin/categories`, newCategory, config);
      setShowCategoryModal(false);
      setNewCategory({ name_ar: "", name_en: "", description: "" });
      fetchCategories();
      alert("✅ Category created successfully!");
    } catch (err) {
      console.error("Failed to create category:", err);
      alert("❌ Error creating category");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate("/admin/login");
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      {/* Sidebar */}
      <div className="dashboard-sidebar">
        <div className="sidebar-logo">
          <h2>UTAS Admin</h2>
          <p>Ibra Branch</p>
        </div>
        <nav className="sidebar-nav">
          <button 
            className={`nav-item ${activeTab === "dashboard" ? "active" : ""}`} 
            onClick={() => setActiveTab("dashboard")}
          >
            <span className="nav-icon">📊</span>
            <span>Dashboard</span>
          </button>
          <button 
            className={`nav-item ${activeTab === "faqs" ? "active" : ""}`} 
            onClick={() => setActiveTab("faqs")}
          >
            <span className="nav-icon">📚</span>
            <span>FAQ Manager</span>
          </button>
          <button 
            className={`nav-item ${activeTab === "unanswered" ? "active" : ""}`} 
            onClick={() => setActiveTab("unanswered")}
          >
            <span className="nav-icon">❓</span>
            <span>Unanswered</span>
          </button>
          <button 
            className={`nav-item ${activeTab === "students" ? "active" : ""}`} 
            onClick={() => setActiveTab("students")}
          >
            <span className="nav-icon">👥</span>
            <span>Students</span>
          </button>
          <button 
            className={`nav-item ${activeTab === "categories" ? "active" : ""}`} 
            onClick={() => setActiveTab("categories")}
          >
            <span className="nav-icon">🏷️</span>
            <span>Categories</span>
          </button>
        </nav>
        <button onClick={handleLogout} className="logout-btn">
          <span className="nav-icon">🚪</span>
          <span>Logout</span>
        </button>
      </div>

      {/* Main Content */}
      <div className="dashboard-main">
        <div className="dashboard-header">
          <h1>
            {activeTab === "dashboard" && "Dashboard"}
            {activeTab === "faqs" && "FAQ Manager"}
            {activeTab === "unanswered" && "Unanswered Questions"}
            {activeTab === "students" && "Students Management"}
            {activeTab === "categories" && "Categories"}
          </h1>
          <div className="admin-info">
            <span>👋 {localStorage.getItem("studentName") || "Admin"}</span>
          </div>
        </div>

        {/* ==================== DASHBOARD TAB ==================== */}
        {activeTab === "dashboard" && (
          <>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon blue">👥</div>
                <div className="stat-info">
                  <h3>{stats.totalStudents}</h3>
                  <p>Total Students</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon green">📚</div>
                <div className="stat-info">
                  <h3>{stats.totalFAQs}</h3>
                  <p>Total FAQs</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon purple">💬</div>
                <div className="stat-info">
                  <h3>{stats.totalQueries}</h3>
                  <p>Today's Queries</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon orange">❓</div>
                <div className="stat-info">
                  <h3>{stats.unansweredQuestions}</h3>
                  <p>Unanswered</p>
                </div>
              </div>
            </div>

            <div className="recent-section">
              <h2>Quick Actions</h2>
              <div className="quick-actions-grid">
                <button className="quick-action-btn" onClick={() => setShowAIModal(true)}>
                  🤖 AI Generate FAQs
                </button>
                <button className="quick-action-btn" onClick={() => setShowManualModal(true)}>
                  ✍️ Manual Add FAQ
                </button>
                <button className="quick-action-btn" onClick={() => setActiveTab("unanswered")}>
                  ❓ Answer Questions
                </button>
                <button className="quick-action-btn" onClick={() => setActiveTab("categories")}>
                  🏷️ Manage Categories
                </button>
              </div>
            </div>

            <div className="recent-section">
              <h2>Recent Unanswered Questions</h2>
              {unansweredQuestions.length === 0 ? (
                <div className="no-data">🎉 No unanswered questions! All caught up.</div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Student</th>
                      <th>Question</th>
                      <th>Language</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {unansweredQuestions.slice(0, 5).map((q) => (
                      <tr key={q.id}>
                        <td>{q.student_name || q.student_id}</td>
                        <td>{q.question?.substring(0, 80)}...</td>
                        <td>
                          <span className={`lang-badge ${q.language}`}>
                            {q.language === "ar" ? "Arabic" : "English"}
                          </span>
                        </td>
                        <td>
                          <button 
                            className="answer-btn" 
                            onClick={() => { 
                              setSelectedQuestion(q); 
                              setShowAnswerModal(true); 
                            }}
                          >
                            Answer
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}

        {/* ==================== FAQ MANAGER TAB ==================== */}
        {activeTab === "faqs" && (
  <>
    {/* ✅ AI COMPLETE UPLOAD SECTION - ADD THIS HERE */}
    <div className="ai-upload-section">
      <h3>🤖 AI Complete Content Upload</h3>
      <p>Upload any document (PDF, URL, or HTML) and Gemini AI will automatically extract ALL categories and FAQs!</p>
      
      <div className="ai-upload-options">
        {/* PDF Upload */}
        <div className="upload-option">
          <div className="upload-icon">📄</div>
          <h4>Upload PDF</h4>
          <input 
            type="file" 
            accept=".pdf" 
            onChange={async (e) => {
              const file = e.target.files[0];
              if (!file) return;
              
              const formData = new FormData();
              formData.append('file', file);
              
              setLoading(true);
              try {
                const token = localStorage.getItem('token');
                const response = await axios.post(`${API_URL}/api/admin/fqa/upload-pdf-complete`, formData, {
                  headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' }
                });
                alert(`✅ ${response.data.message}`);
                fetchDashboardData();
                fetchCategories();
              } catch (err) {
                alert('❌ Error processing PDF: ' + (err.response?.data?.detail || err.message));
              } finally {
                setLoading(false);
              }
            }}
          />
          <p className="upload-hint">Upload PDF - Auto extract categories & FAQs</p>
        </div>
        
        {/* URL Input */}
        <div className="upload-option">
          <div className="upload-icon">🔗</div>
          <h4>Website URL</h4>
          <input 
            type="url" 
            id="urlInput"
            placeholder="https://example.com/page"
            className="url-input-field"
          />
          <button 
            className="btn-primary"
            onClick={async () => {
              const url = document.getElementById('urlInput').value;
              if (!url) {
                alert('Please enter a URL');
                return;
              }
              
              const formData = new FormData();
              formData.append('url', url);
              
              setLoading(true);
              try {
                const token = localStorage.getItem('token');
                const response = await axios.post(`${API_URL}/api/admin/fqa/from-url-complete`, formData, {
                  headers: { Authorization: `Bearer ${token}` }
                });
                alert(`✅ ${response.data.message}`);
                fetchDashboardData();
                fetchCategories();
              } catch (err) {
                alert('❌ Error processing URL: ' + (err.response?.data?.detail || err.message));
              } finally {
                setLoading(false);
              }
            }}
          >
            Extract from URL
          </button>
        </div>
        
        {/* HTML/CSS Input */}
        <div className="upload-option">
          <div className="upload-icon">💻</div>
          <h4>HTML/CSS Content</h4>
          <textarea 
            id="htmlContent"
            rows="5"
            placeholder="Paste your HTML/CSS content here..."
            className="html-textarea"
          ></textarea>
          <button 
            className="btn-primary"
            onClick={async () => {
              const htmlContent = document.getElementById('htmlContent').value;
              if (!htmlContent) {
                alert('Please paste HTML/CSS content');
                return;
              }
              
              const formData = new FormData();
              formData.append('html_content', htmlContent);
              
              setLoading(true);
              try {
                const token = localStorage.getItem('token');
                const response = await axios.post(`${API_URL}/api/admin/fqa/from-html-complete`, formData, {
                  headers: { Authorization: `Bearer ${token}` }
                });
                alert(`✅ ${response.data.message}`);
                fetchDashboardData();
                fetchCategories();
              } catch (err) {
                alert('❌ Error processing HTML: ' + (err.response?.data?.detail || err.message));
              } finally {
                setLoading(false);
              }
            }}
          >
            Extract from HTML
          </button>
        </div>
      </div>
    </div>

    {/* Action Bar - Keep this after AI section */}
    <div className="action-bar">
      <button className="btn-primary" onClick={() => setShowManualModal(true)}>✍️ Add Manual FAQ</button>
      <button className="btn-refresh" onClick={fetchDashboardData}>🔄 Refresh</button>
    </div>

    {/* FAQs Table */}
    <div className="recent-section">
      <h2>All FAQs ({faqs.length})</h2>
              {faqs.length === 0 ? (
                <div className="no-data">📚 No FAQs found. Click "AI Generate" to create some!</div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Question (EN)</th>
                      <th>Question (AR)</th>
                      <th>Category</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {faqs.map((faq) => (
                      <tr key={faq.id}>
                        <td>{faq.id}</td>
                        <td>{faq.question_en?.substring(0, 60)}...</td>
                        <td>{faq.question_ar?.substring(0, 60)}...</td>
                        <td>
                          <span className="category-badge">{faq.category || "General"}</span>
                        </td>
                        <td>
                          <button className="delete-btn" onClick={() => handleDeleteFAQ(faq.id)}>
                            🗑️ Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}

        {/* ==================== UNANSWERED TAB ==================== */}
        {activeTab === "unanswered" && (
          <div className="recent-section">
            <h2>Pending Questions ({unansweredQuestions.length})</h2>
            {unansweredQuestions.length === 0 ? (
              <div className="no-data">🎉 No pending questions! All questions have been answered.</div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Question</th>
                    <th>Language</th>
                    <th>Date</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {unansweredQuestions.map((q) => (
                    <tr key={q.id}>
                      <td>
                        <strong>{q.student_name}</strong><br/>
                        <small>{q.student_id}</small>
                      </td>
                      <td style={{ maxWidth: "400px" }}>{q.question}</td>
                      <td>
                        <span className={`lang-badge ${q.language}`}>
                          {q.language === "ar" ? "Arabic" : "English"}
                        </span>
                      </td>
                      <td>{new Date(q.asked_at).toLocaleString()}</td>
                      <td>
                        <button 
                          className="answer-btn" 
                          onClick={() => { 
                            setSelectedQuestion(q); 
                            setShowAnswerModal(true); 
                          }}
                        >
                          Answer & Add to FAQ
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ==================== STUDENTS TAB ==================== */}
        {activeTab === "students" && (
          <div className="recent-section">
            <h2>All Students ({students.length})</h2>
            {students.length === 0 ? (
              <div className="no-data">👥 No students found</div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Student ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Department</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((student) => (
                    <tr key={student.student_id}>
                      <td>{student.student_id}</td>
                      <td>{student.name}</td>
                      <td>{student.email}</td>
                      <td>{student.department}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ==================== CATEGORIES TAB ==================== */}
        {activeTab === "categories" && (
          <>
            <div className="action-bar">
              <button className="btn-primary" onClick={() => setShowCategoryModal(true)}>
                ➕ Add Category
              </button>
              <button className="btn-refresh" onClick={fetchCategories}>
                🔄 Refresh
              </button>
            </div>
            <div className="recent-section">
              <h2>Categories ({categories.length})</h2>
              <div className="categories-grid">
                {categories.map((cat) => (
                  <div key={cat.id} className="category-card">
                    <div className="category-icon">📁</div>
                    <h3>{cat.name_en}</h3>
                    <p className="category-ar">{cat.name_ar}</p>
                    <p className="category-desc">{cat.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      {/* ==================== AI GENERATE MODAL ==================== */}
      {showAIModal && (
        <div className="modal-overlay" onClick={() => setShowAIModal(false)}>
          <div className="modal-content large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>🤖 AI Auto-Generate FAQs with Gemini</h2>
              <button className="modal-close" onClick={() => setShowAIModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="ai-type-selector">
                <button 
                  className={`ai-type-btn ${aiInputType === "pdf" ? "active" : ""}`} 
                  onClick={() => setAiInputType("pdf")}
                >
                  📄 PDF Document
                </button>
                <button 
                  className={`ai-type-btn ${aiInputType === "url" ? "active" : ""}`} 
                  onClick={() => setAiInputType("url")}
                >
                  🔗 Website URL
                </button>
                <button 
                  className={`ai-type-btn ${aiInputType === "html" ? "active" : ""}`} 
                  onClick={() => setAiInputType("html")}
                >
                  💻 HTML/CSS Content
                </button>
              </div>

              {aiInputType === "pdf" && (
                <div className="form-group">
                  <label>Upload PDF File</label>
                  <input 
                    type="file" 
                    accept=".pdf" 
                    onChange={(e) => {
                      setPdfFile(e.target.files[0]);
                      setPdfFileName(e.target.files[0]?.name || "");
                    }} 
                  />
                  {pdfFileName && <small style={{ color: "#48bb78", marginTop: "5px", display: "block" }}>✅ Selected: {pdfFileName}</small>}
                </div>
              )}

              {aiInputType === "url" && (
                <div className="form-group">
                  <label>Website URL</label>
                  <input 
                    type="url" 
                    placeholder="https://example.com/page" 
                    value={urlInput} 
                    onChange={(e) => setUrlInput(e.target.value)} 
                  />
                </div>
              )}

              {aiInputType === "html" && (
                <div className="form-group">
                  <label>HTML/CSS Content</label>
                  <textarea 
                    rows="8" 
                    placeholder="Paste your HTML/CSS content here..." 
                    value={htmlContent} 
                    onChange={(e) => setHtmlContent(e.target.value)}
                  ></textarea>
                </div>
              )}

              <div className="form-group">
                <label>Category (Optional)</label>
                <input 
                  type="text" 
                  placeholder="e.g., Registration, Exams, GPA" 
                  value={selectedCategory} 
                  onChange={(e) => setSelectedCategory(e.target.value)} 
                />
              </div>

              <div className="info-box">
                <p>🤖 Gemini AI will analyze your content and automatically extract questions and answers in <strong>BOTH Arabic and English</strong>!</p>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowAIModal(false)}>Cancel</button>
              <button className="btn-primary" onClick={handleAIGenerate}>Generate FAQs with AI</button>
            </div>
          </div>
        </div>
      )}

      {/* ==================== MANUAL FAQ MODAL ==================== */}
      {showManualModal && (
        <div className="modal-overlay" onClick={() => setShowManualModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>✍️ Add FAQ Manually</h2>
              <button className="modal-close" onClick={() => setShowManualModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Question (English) <span className="required">*</span></label>
                <input 
                  type="text" 
                  value={manualFAQ.question_en} 
                  onChange={(e) => setManualFAQ({...manualFAQ, question_en: e.target.value})} 
                  placeholder="Enter question in English" 
                />
              </div>
              <div className="form-group">
                <label>Question (Arabic)</label>
                <input 
                  type="text" 
                  dir="rtl"
                  value={manualFAQ.question_ar} 
                  onChange={(e) => setManualFAQ({...manualFAQ, question_ar: e.target.value})} 
                  placeholder="السؤال بالعربية" 
                />
              </div>
              <div className="form-group">
                <label>Answer (English) <span className="required">*</span></label>
                <textarea 
                  rows="4" 
                  value={manualFAQ.answer_en} 
                  onChange={(e) => setManualFAQ({...manualFAQ, answer_en: e.target.value})} 
                  placeholder="Enter answer in English"
                ></textarea>
              </div>
              <div className="form-group">
                <label>Answer (Arabic)</label>
                <textarea 
                  rows="4" 
                  dir="rtl"
                  value={manualFAQ.answer_ar} 
                  onChange={(e) => setManualFAQ({...manualFAQ, answer_ar: e.target.value})} 
                  placeholder="الإجابة بالعربية"
                ></textarea>
              </div>
              <div className="form-group">
                <label>Category</label>
                <input 
                  type="text" 
                  value={manualFAQ.category} 
                  onChange={(e) => setManualFAQ({...manualFAQ, category: e.target.value})} 
                  placeholder="e.g., Registration, GPA" 
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowManualModal(false)}>Cancel</button>
              <button className="btn-primary" onClick={handleManualAdd}>Save FAQ</button>
            </div>
          </div>
        </div>
      )}

      {/* ==================== ANSWER QUESTION MODAL ==================== */}
      {showAnswerModal && selectedQuestion && (
        <div className="modal-overlay" onClick={() => setShowAnswerModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>❓ Answer Student Question</h2>
              <button className="modal-close" onClick={() => setShowAnswerModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="question-box">
                <strong>Student Question:</strong>
                <p>{selectedQuestion.question}</p>
                <span className={`lang-badge ${selectedQuestion.language}`}>
                  {selectedQuestion.language === "ar" ? "Arabic" : "English"}
                </span>
              </div>
              <div className="form-group">
                <label>Answer (Arabic)</label>
                <textarea 
                  rows="4" 
                  dir="rtl"
                  value={answerData.answer_ar} 
                  onChange={(e) => setAnswerData({...answerData, answer_ar: e.target.value})} 
                  placeholder="اكتب الإجابة بالعربية..."
                ></textarea>
              </div>
              <div className="form-group">
                <label>Answer (English) <span className="required">*</span></label>
                <textarea 
                  rows="4" 
                  value={answerData.answer_en} 
                  onChange={(e) => setAnswerData({...answerData, answer_en: e.target.value})} 
                  placeholder="Write answer in English..."
                ></textarea>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowAnswerModal(false)}>Cancel</button>
              <button className="btn-primary" onClick={handleAnswerQuestion}>Answer & Add to FAQ</button>
            </div>
          </div>
        </div>
      )}

      {/* ==================== PREVIEW MODAL ==================== */}
      {showPreview && generatedFAQs.length > 0 && (
        <div className="modal-overlay" onClick={() => setShowPreview(false)}>
          <div className="modal-content xlarge" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>✅ Generated FAQs Preview</h2>
              <button className="modal-close" onClick={() => setShowPreview(false)}>×</button>
            </div>
            <div className="modal-body">
              {generatedFAQs.map((faq, idx) => (
                <div key={idx} className="generated-faq-card">
                  <h3>FAQ #{idx + 1}</h3>
                  <div className="faq-preview">
                    <div className="faq-column">
                      <strong>🇸🇦 Arabic:</strong>
                      <p><strong>Q:</strong> {faq.question_ar}</p>
                      <p><strong>A:</strong> {faq.answer_ar}</p>
                    </div>
                    <div className="faq-column">
                      <strong>🇬🇧 English:</strong>
                      <p><strong>Q:</strong> {faq.question_en}</p>
                      <p><strong>A:</strong> {faq.answer_en}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="modal-footer">
              <button className="btn-primary" onClick={() => { 
                setShowPreview(false); 
                fetchDashboardData(); 
              }}>
                ✅ All FAQs Saved to Database
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;