// frontend/src/pages/FQAManager.jsx

import React, { useState, useEffect } from "react";
import axios from "axios";
import { 
  FaRobot, FaPlus, FaTrash, FaFilePdf, FaGlobe, FaCode, 
  FaUpload, FaSave, FaTimes, FaSpinner, FaCheckCircle, 
  FaExclamationTriangle, FaUniversity, FaChartLine, FaCalendarAlt,
  FaCalendarPlus, FaQuestionCircle, FaDownload, FaEye, FaEdit,
  FaSearch, FaLink, FaEnvelope, FaPhone, FaKey, FaFileAlt,
  FaTrophy, FaBriefcase, FaShieldAlt, FaComment, FaLanguage,
  FaBook, FaUserGraduate, FaCalendarCheck, FaFilter
} from "react-icons/fa";
import { MdAutoAwesome, MdCategory, MdLanguage, MdDelete, MdRefresh, MdDateRange } from "react-icons/md";
import "./FQAManager.css";

const API_URL = "http://localhost:8000";

const FQAManager = () => {
  const [activeMainTab, setActiveMainTab] = useState("faqs");
  const [activeSubTab, setActiveSubTab] = useState("manual");
  const [loading, setLoading] = useState(false);
  const [faqs, setFaqs] = useState([]);
  const [categories, setCategories] = useState([]);
  const [notification, setNotification] = useState({ show: false, message: "", type: "" });
  const [searchTerm, setSearchTerm] = useState("");
  
  // Filter states
  const [filterYear, setFilterYear] = useState("");
  const [filterSemester, setFilterSemester] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [showFilters, setShowFilters] = useState(false);
  
  // Academic years and semesters
  const academicYears = [
    "2023-2024",
    "2024-2025", 
    "2025-2026",
    "2026-2027"
  ];
  
  const semesters = [
    { value: "Fall", label_en: "Fall Semester", label_ar: "الفصل الأول" },
    { value: "Spring", label_en: "Spring Semester", label_ar: "الفصل الثاني" },
    { value: "Summer", label_en: "Summer Semester", label_ar: "الفصل الصيفي" }
  ];
  
  // Manual FAQ form with date fields
  const [manualFaq, setManualFaq] = useState({
    question_en: "",
    question_ar: "",
    answer_en: "",
    answer_ar: "",
    category: "",
    valid_from: "",
    valid_until: "",
    academic_year: "",
    semester: "",
    is_active: true
  });
  const [editingFaq, setEditingFaq] = useState(null);
  
  // Category form
  const [categoryForm, setCategoryForm] = useState({
    name_ar: "",
    name_en: "",
    description_ar: "",
    description_en: ""
  });
  const [editingCategory, setEditingCategory] = useState(null);
  
  // AI Generation states
  const [pdfFile, setPdfFile] = useState(null);
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [htmlContent, setHtmlContent] = useState("");
  const [processingStatus, setProcessingStatus] = useState("");
  
  // Get auth config
  const getAuthConfig = () => {
    const token = localStorage.getItem("token");
    return {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    };
  };
  
  // Load data
  useEffect(() => {
    fetchFaqs();
    fetchCategories();
  }, []);
  
  const fetchFaqs = async () => {
    try {
      const config = getAuthConfig();
      let url = `${API_URL}/api/admin/fqa`;
      
      // Add filters if selected
      const params = new URLSearchParams();
      if (filterYear) params.append("academic_year", filterYear);
      if (filterSemester) params.append("semester", filterSemester);
      if (params.toString()) url += `?${params.toString()}`;
      
      const response = await axios.get(url, config);
      setFaqs(response.data);
    } catch (error) {
      console.error("Error fetching FAQs:", error);
      if (error.response?.status === 401) {
        showNotification("Session expired. Please login again.", "error");
      }
    }
  };
  
  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/admin/categories`);
      setCategories(response.data);
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  };
  
  const showNotification = (message, type) => {
    setNotification({ show: true, message, type });
    setTimeout(() => setNotification({ show: false, message: "", type: "" }), 5000);
  };
  
  // Apply filters
  useEffect(() => {
    fetchFaqs();
  }, [filterYear, filterSemester, filterStatus]);
  
  // ==================== FAQ CRUD ====================
  const handleManualSubmit = async (e) => {
    e.preventDefault();
    
    if (!manualFaq.question_en || !manualFaq.answer_en) {
      showNotification("Please fill in English question and answer", "error");
      return;
    }
    
    setLoading(true);
    
    try {
      const config = getAuthConfig();
      
      // Prepare data with dates
      const faqData = {
        ...manualFaq,
        valid_from: manualFaq.valid_from || null,
        valid_until: manualFaq.valid_until || null,
        academic_year: manualFaq.academic_year || null,
        semester: manualFaq.semester || null,
        is_active: manualFaq.is_active
      };
      
      if (editingFaq) {
        await axios.put(`${API_URL}/api/admin/fqa/${editingFaq.id}`, faqData, config);
        showNotification("FAQ updated successfully!", "success");
        setEditingFaq(null);
      } else {
        await axios.post(`${API_URL}/api/admin/fqa/manual`, faqData, config);
        showNotification("FAQ added successfully!", "success");
      }
      
      resetFaqForm();
      fetchFaqs();
      
    } catch (error) {
      console.error("Error saving FAQ:", error);
      showNotification(error.response?.data?.detail || "Failed to save FAQ", "error");
    } finally {
      setLoading(false);
    }
  };
  
  const handleEditFaq = (faq) => {
    setEditingFaq(faq);
    setManualFaq({
      question_en: faq.question_en || "",
      question_ar: faq.question_ar || "",
      answer_en: faq.answer_en || "",
      answer_ar: faq.answer_ar || "",
      category: faq.category || "",
      valid_from: faq.valid_from ? faq.valid_from.split('T')[0] : "",
      valid_until: faq.valid_until ? faq.valid_until.split('T')[0] : "",
      academic_year: faq.academic_year || "",
      semester: faq.semester || "",
      is_active: faq.is_active !== undefined ? faq.is_active : true
    });
    setActiveSubTab("manual");
  };
  
  const handleDeleteFaq = async (id) => {
    if (!window.confirm("Are you sure you want to delete this FAQ?")) return;
    
    try {
      const config = getAuthConfig();
      await axios.delete(`${API_URL}/api/admin/fqa/${id}`, config);
      showNotification("FAQ deleted successfully!", "success");
      fetchFaqs();
    } catch (error) {
      console.error("Error deleting FAQ:", error);
      showNotification("Failed to delete FAQ", "error");
    }
  };
  
  const resetFaqForm = () => {
    setManualFaq({
      question_en: "",
      question_ar: "",
      answer_en: "",
      answer_ar: "",
      category: "",
      valid_from: "",
      valid_until: "",
      academic_year: "",
      semester: "",
      is_active: true
    });
    setEditingFaq(null);
  };
  
  // ==================== CATEGORY CRUD ====================
  const handleCategorySubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const config = getAuthConfig();
      
      if (editingCategory) {
        await axios.put(`${API_URL}/api/admin/categories/${editingCategory.id}`, categoryForm, config);
        showNotification("Category updated successfully!", "success");
        setEditingCategory(null);
      } else {
        await axios.post(`${API_URL}/api/admin/categories`, categoryForm, config);
        showNotification("Category created successfully!", "success");
      }
      
      setCategoryForm({ name_ar: "", name_en: "", description_ar: "", description_en: "" });
      fetchCategories();
      
    } catch (error) {
      console.error("Error saving category:", error);
      showNotification(error.response?.data?.detail || "Failed to save category", "error");
    } finally {
      setLoading(false);
    }
  };
  
  const handleEditCategory = (category) => {
    setEditingCategory(category);
    setCategoryForm({
      name_ar: category.name_ar || "",
      name_en: category.name_en || "",
      description_ar: category.description_ar || "",
      description_en: category.description_en || ""
    });
  };
  
  const handleDeleteCategory = async (id) => {
    if (!window.confirm("Are you sure? This will also delete all FAQs in this category.")) return;
    
    try {
      const config = getAuthConfig();
      await axios.delete(`${API_URL}/api/admin/categories/${id}`, config);
      showNotification("Category deleted successfully!", "success");
      fetchCategories();
      fetchFaqs();
    } catch (error) {
      console.error("Error deleting category:", error);
      showNotification("Failed to delete category", "error");
    }
  };
  
  // ==================== AI GENERATION ====================
  const handlePdfUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || file.type !== "application/pdf") {
      showNotification("Please select a valid PDF file", "error");
      return;
    }
    
    setPdfFile(file);
    setLoading(true);
    setProcessingStatus("Uploading and processing PDF with Gemini AI...");
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(
        `${API_URL}/api/admin/fqa/upload-pdf-complete`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "multipart/form-data"
          }
        }
      );
      
      showNotification(response.data.message, "success");
      fetchFaqs();
      fetchCategories();
      setPdfFile(null);
      e.target.value = "";
      
    } catch (error) {
      console.error("Error processing PDF:", error);
      showNotification(error.response?.data?.detail || "Failed to process PDF", "error");
    } finally {
      setLoading(false);
      setProcessingStatus("");
    }
  };
  
 const handleUrlSubmit = async () => {
  if (!websiteUrl) {
    showNotification("Please enter a website URL", "error");
    return;
  }
  
  // Validate URL format
  const urlPattern = /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/;
  if (!urlPattern.test(websiteUrl)) {
    showNotification("Please enter a valid URL (e.g., https://example.com)", "error");
    return;
  }
  
  setLoading(true);
  setProcessingStatus("Analyzing website content with Gemini AI...");
  
  const formData = new FormData();
  formData.append("url", websiteUrl);
  
  try {
    const token = localStorage.getItem("token");
    console.log("🚀 Sending URL request:", websiteUrl);
    
    const response = await axios.post(
      `${API_URL}/api/admin/fqa/from-url-complete`,
      formData,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data"
        },
        timeout: 60000 // 60 second timeout
      }
    );
    
    console.log("✅ URL response:", response.data);
    showNotification(response.data.message, "success");
    fetchFaqs();
    fetchCategories();
    setWebsiteUrl("");
    
  } catch (error) {
    console.error("❌ Error processing URL:", error);
    
    // Detailed error handling
    let errorMessage = "Failed to process URL";
    
    if (error.code === 'ECONNABORTED') {
      errorMessage = "Request timed out. The website might be slow or unreachable.";
    } else if (error.response) {
      // Server responded with error
      console.error("Response data:", error.response.data);
      errorMessage = error.response.data?.detail || `Server error: ${error.response.status}`;
    } else if (error.request) {
      // Request was made but no response
      errorMessage = "No response from server. Please check if the backend is running.";
    } else {
      errorMessage = error.message || "Failed to process URL";
    }
    
    showNotification(errorMessage, "error");
  } finally {
    setLoading(false);
    setProcessingStatus("");
  }
};
  
  const handleHtmlSubmit = async () => {
    if (!htmlContent) {
      showNotification("Please paste HTML/CSS content", "error");
      return;
    }
    
    setLoading(true);
    setProcessingStatus("Analyzing HTML content with Gemini AI...");
    
    const formData = new FormData();
    formData.append("html_content", htmlContent);
    
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(
        `${API_URL}/api/admin/fqa/from-html-complete`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "multipart/form-data"
          }
        }
      );
      
      showNotification(response.data.message, "success");
      fetchFaqs();
      fetchCategories();
      setHtmlContent("");
      
    } catch (error) {
      console.error("Error processing HTML:", error);
      showNotification(error.response?.data?.detail || "Failed to process HTML", "error");
    } finally {
      setLoading(false);
      setProcessingStatus("");
    }
  };
  
  // Filter FAQs based on search and status
  const filteredFaqs = faqs.filter(faq => {
    const matchesSearch = 
      faq.question_en?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      faq.question_ar?.includes(searchTerm) ||
      faq.answer_en?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      faq.category?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filterStatus === "all" || 
      (filterStatus === "active" && faq.is_active) ||
      (filterStatus === "inactive" && !faq.is_active);
    
    return matchesSearch && matchesStatus;
  });
  
  // Group FAQs by category
  const faqsByCategory = filteredFaqs.reduce((acc, faq) => {
    const cat = faq.category || "Uncategorized";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(faq);
    return acc;
  }, {});
  
  // Get icon for category
  const getCategoryIcon = (categoryName) => {
    const icons = {
      'General': <FaUniversity />,
      'Registration': <FaCalendarPlus />,
      'GPA': <FaChartLine />,
      'Schedule': <FaCalendarAlt />,
      'Exams': <FaBook />,
      'Advisor': <FaUserGraduate />
    };
    return icons[categoryName] || <FaQuestionCircle />;
  };
  
  // Check if FAQ is currently valid
  const isValidFAQ = (faq) => {
    if (!faq.is_active) return false;
    const today = new Date();
    if (faq.valid_from && new Date(faq.valid_from) > today) return false;
    if (faq.valid_until && new Date(faq.valid_until) < today) return false;
    return true;
  };
  
  return (
    <div className="fqa-manager">
      {/* Notification */}
      {notification.show && (
        <div className={`notification ${notification.type}`}>
          {notification.type === "success" ? <FaCheckCircle /> : <FaExclamationTriangle />}
          <span>{notification.message}</span>
        </div>
      )}
      
      {/* Processing Status Modal */}
      {loading && (
        <div className="processing-modal">
          <div className="processing-content">
            <FaSpinner className="spinner-large" />
            <h3>🤖 Gemini AI is Analyzing</h3>
            <p>{processingStatus}</p>
            <div className="progress-bar">
              <div className="progress-fill"></div>
            </div>
            <small>This may take a few moments...</small>
          </div>
        </div>
      )}
      
      <div className="fqa-header">
        <h1>
          <FaRobot className="header-icon" />
          Chatbot Content Management System
        </h1>
        <p>Manage FAQs with Academic Year & Semester Tracking | Gemini AI Powered Extraction</p>
      </div>
      
      {/* Main Tabs */}
      <div className="main-tabs">
        <button 
          className={`main-tab-btn ${activeMainTab === "faqs" ? "active" : ""}`}
          onClick={() => setActiveMainTab("faqs")}
        >
          <FaBook /> FAQs Management ({faqs.length})
        </button>
        <button 
          className={`main-tab-btn ${activeMainTab === "categories" ? "active" : ""}`}
          onClick={() => setActiveMainTab("categories")}
        >
          <MdCategory /> Categories ({categories.length})
        </button>
      </div>
      
      {/* FAQs Management Tab */}
      {activeMainTab === "faqs" && (
        <div className="fqa-container">
          {/* Left Panel - Add FAQ */}
          <div className="fqa-left-panel">
            <div className="panel-tabs">
              <button 
                className={`tab-btn ${activeSubTab === "manual" ? "active" : ""}`}
                onClick={() => {
                  setActiveSubTab("manual");
                  resetFaqForm();
                }}
              >
                <FaPlus /> Manual Entry
              </button>
              <button 
                className={`tab-btn ${activeSubTab === "pdf" ? "active" : ""}`}
                onClick={() => setActiveSubTab("pdf")}
              >
                <FaFilePdf /> AI: PDF
              </button>
              <button 
                className={`tab-btn ${activeSubTab === "url" ? "active" : ""}`}
                onClick={() => setActiveSubTab("url")}
              >
                <FaGlobe /> AI: Website
              </button>
              <button 
                className={`tab-btn ${activeSubTab === "html" ? "active" : ""}`}
                onClick={() => setActiveSubTab("html")}
              >
                <FaCode /> AI: HTML/CSS
              </button>
            </div>
            
            <div className="panel-content">
              {/* Manual Add Form with Date Fields */}
              {activeSubTab === "manual" && (
                <form onSubmit={handleManualSubmit} className="manual-form">
                  <h2>
                    {editingFaq ? <FaEdit /> : <FaPlus />}
                    {editingFaq ? "Edit FAQ" : "Add FAQ Manually"}
                  </h2>
                  
                  <div className="form-group">
                    <label>Question (English) *</label>
                    <input
                      type="text"
                      value={manualFaq.question_en}
                      onChange={(e) => setManualFaq({...manualFaq, question_en: e.target.value})}
                      placeholder="Enter question in English"
                      required
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Question (Arabic)</label>
                    <input
                      type="text"
                      value={manualFaq.question_ar}
                      onChange={(e) => setManualFaq({...manualFaq, question_ar: e.target.value})}
                      placeholder="السؤال بالعربية"
                      dir="rtl"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Answer (English) *</label>
                    <textarea
                      value={manualFaq.answer_en}
                      onChange={(e) => setManualFaq({...manualFaq, answer_en: e.target.value})}
                      placeholder="Enter answer in English"
                      rows="4"
                      required
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Answer (Arabic)</label>
                    <textarea
                      value={manualFaq.answer_ar}
                      onChange={(e) => setManualFaq({...manualFaq, answer_ar: e.target.value})}
                      placeholder="الإجابة بالعربية"
                      rows="4"
                      dir="rtl"
                    />
                  </div>
                  
                  <div className="form-row">
                    <div className="form-group">
                      <label>
                        <MdCategory /> Category
                      </label>
                      <select
                        value={manualFaq.category}
                        onChange={(e) => setManualFaq({...manualFaq, category: e.target.value})}
                      >
                        <option value="">Select category...</option>
                        {categories.map(cat => (
                          <option key={cat.id} value={cat.name_en}>
                            {cat.name_en} - {cat.name_ar}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    <div className="form-group">
                      <label>
                        <FaCalendarAlt /> Academic Year
                      </label>
                      <select
                        value={manualFaq.academic_year}
                        onChange={(e) => setManualFaq({...manualFaq, academic_year: e.target.value})}
                      >
                        <option value="">Select academic year...</option>
                        {academicYears.map(year => (
                          <option key={year} value={year}>{year}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  
                  <div className="form-row">
                    <div className="form-group">
                      <label>
                        <FaCalendarCheck /> Semester
                      </label>
                      <select
                        value={manualFaq.semester}
                        onChange={(e) => setManualFaq({...manualFaq, semester: e.target.value})}
                      >
                        <option value="">Select semester...</option>
                        {semesters.map(sem => (
                          <option key={sem.value} value={sem.value}>
                            {sem.label_en} - {sem.label_ar}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    <div className="form-group">
                      <label>
                        <FaCheckCircle /> Status
                      </label>
                      <select
                        value={manualFaq.is_active}
                        onChange={(e) => setManualFaq({...manualFaq, is_active: e.target.value === "true"})}
                      >
                        <option value="true">Active</option>
                        <option value="false">Inactive</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="form-row">
                    <div className="form-group">
                      <label>
                        <MdDateRange /> Valid From Date
                      </label>
                      <input
                        type="date"
                        value={manualFaq.valid_from}
                        onChange={(e) => setManualFaq({...manualFaq, valid_from: e.target.value})}
                      />
                    </div>
                    
                    <div className="form-group">
                      <label>
                        <MdDateRange /> Valid Until Date
                      </label>
                      <input
                        type="date"
                        value={manualFaq.valid_until}
                        onChange={(e) => setManualFaq({...manualFaq, valid_until: e.target.value})}
                      />
                    </div>
                  </div>
                  
                  <div className="form-actions">
                    {editingFaq && (
                      <button type="button" className="btn-secondary" onClick={resetFaqForm}>
                        <FaTimes /> Cancel Edit
                      </button>
                    )}
                    <button type="button" className="btn-secondary" onClick={resetFaqForm}>
                      <FaTimes /> Clear
                    </button>
                    <button type="submit" className="btn-primary" disabled={loading}>
                      {loading ? <FaSpinner className="spinner" /> : <FaSave />}
                      {editingFaq ? "Update FAQ" : "Save FAQ"}
                    </button>
                  </div>
                </form>
              )}
              
              {/* PDF Upload with AI */}
              {activeSubTab === "pdf" && (
                <div className="ai-generate-form">
                  <div className="ai-badge">
                    <MdAutoAwesome /> Powered by Gemini AI
                  </div>
                  
                  <h2><FaFilePdf /> AI Auto-Generate FAQs with Gemini</h2>
                  
                  <div className="upload-area">
                    <FaFilePdf className="upload-icon" />
                    <p>Upload PDF Document</p>
                    <p className="upload-hint">Gemini will automatically extract categories and Q&A</p>
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={handlePdfUpload}
                      style={{ display: "none" }}
                      id="pdf-upload"
                      disabled={loading}
                    />
                    <label htmlFor="pdf-upload" className="upload-btn" style={{ opacity: loading ? 0.6 : 1 }}>
                      <FaUpload /> Choose File
                    </label>
                    {pdfFile && <span className="file-name">{pdfFile.name}</span>}
                  </div>
                  
                  <div className="info-box">
                    <MdAutoAwesome />
                    <div>
                      <strong>Gemini AI will:</strong>
                      <ul>
                        <li>📚 Extract ALL main categories from the PDF</li>
                        <li>❓ Generate comprehensive FAQs for each category</li>
                        <li>🌐 Create bilingual content (Arabic & English)</li>
                        <li>🔍 Include keywords for better search</li>
                        <li>💾 Automatically save to database</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Website URL with AI */}
              {activeSubTab === "url" && (
                <div className="ai-generate-form">
                  <div className="ai-badge">
                    <MdAutoAwesome /> Powered by Gemini AI
                  </div>
                  
                  <h2><FaGlobe /> AI Auto-Generate FAQs from Website</h2>
                  
                  <div className="form-group">
                    <label>Website URL</label>
                    <input
                      type="url"
                      value={websiteUrl}
                      onChange={(e) => setWebsiteUrl(e.target.value)}
                      placeholder="https://example.com/university-page"
                      disabled={loading}
                    />
                  </div>
                  
                  <div className="info-box">
                    <MdAutoAwesome />
                    <div>
                      <strong>Gemini AI will analyze:</strong>
                      <ul>
                        <li>🌐 Website content and structure</li>
                        <li>📑 Headings and important sections</li>
                        <li>❓ Extract relevant Q&A pairs</li>
                        <li>🌍 Generate bilingual FAQs</li>
                        <li>📂 Organize into categories</li>
                      </ul>
                    </div>
                  </div>
                  
                  <div className="form-actions">
                    <button type="button" className="btn-secondary" onClick={() => setWebsiteUrl("")}>
                      <FaTimes /> Clear
                    </button>
                    <button 
                      type="button" 
                      className="btn-primary"
                      onClick={handleUrlSubmit}
                      disabled={!websiteUrl || loading}
                    >
                      {loading ? <FaSpinner className="spinner" /> : <MdAutoAwesome />}
                      {loading ? "Processing..." : "Generate FAQs with AI"}
                    </button>
                  </div>
                </div>
              )}
              
              {/* HTML/CSS Content with AI */}
              {activeSubTab === "html" && (
                <div className="ai-generate-form">
                  <div className="ai-badge">
                    <MdAutoAwesome /> Powered by Gemini AI
                  </div>
                  
                  <h2><FaCode /> AI Auto-Generate from HTML/CSS</h2>
                  
                  <div className="form-group">
                    <label>HTML/CSS Content</label>
                    <textarea
                      value={htmlContent}
                      onChange={(e) => setHtmlContent(e.target.value)}
                      placeholder="Paste your HTML/CSS content here..."
                      rows="8"
                      disabled={loading}
                    />
                  </div>
                  
                  <div className="info-box">
                    <MdAutoAwesome />
                    <div>
                      <strong>Gemini AI will extract:</strong>
                      <ul>
                        <li>📄 Text content from HTML structure</li>
                        <li>🏷️ Categories from headings</li>
                        <li>❓ Questions and answers from content</li>
                        <li>🌐 Bilingual FAQ generation</li>
                      </ul>
                    </div>
                  </div>
                  
                  <div className="form-actions">
                    <button type="button" className="btn-secondary" onClick={() => setHtmlContent("")}>
                      <FaTimes /> Clear
                    </button>
                    <button 
                      type="button" 
                      className="btn-primary"
                      onClick={handleHtmlSubmit}
                      disabled={!htmlContent || loading}
                    >
                      {loading ? <FaSpinner className="spinner" /> : <MdAutoAwesome />}
                      {loading ? "Processing..." : "Generate FAQs with AI"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* Right Panel - FAQ List */}
          <div className="fqa-right-panel">
            <div className="panel-header">
              <h2>
                📚 FAQ Database
                <span className="faq-count">{filteredFaqs.length} FAQs</span>
              </h2>
              <div className="panel-actions">
                <button 
                  className="filter-toggle-btn" 
                  onClick={() => setShowFilters(!showFilters)}
                  title="Toggle Filters"
                >
                  <FaFilter /> Filters
                </button>
                <div className="search-bar-small">
                  <FaSearch />
                  <input
                    type="text"
                    placeholder="Search FAQs..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <button className="refresh-btn" onClick={fetchFaqs} title="Refresh">
                  <MdRefresh /> Refresh
                </button>
              </div>
            </div>
            
            {/* Filter Bar */}
            {showFilters && (
              <div className="filter-bar">
                <div className="filter-group">
                  <label>Academic Year</label>
                  <select value={filterYear} onChange={(e) => setFilterYear(e.target.value)}>
                    <option value="">All Years</option>
                    {academicYears.map(year => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                </div>
                
                <div className="filter-group">
                  <label>Semester</label>
                  <select value={filterSemester} onChange={(e) => setFilterSemester(e.target.value)}>
                    <option value="">All Semesters</option>
                    {semesters.map(sem => (
                      <option key={sem.value} value={sem.value}>{sem.label_en}</option>
                    ))}
                  </select>
                </div>
                
                <div className="filter-group">
                  <label>Status</label>
                  <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
                    <option value="all">All</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
                
                <button 
                  className="clear-filters-btn"
                  onClick={() => {
                    setFilterYear("");
                    setFilterSemester("");
                    setFilterStatus("all");
                  }}
                >
                  Clear Filters
                </button>
              </div>
            )}
            
            <div className="faq-list">
              {filteredFaqs.length === 0 ? (
                <div className="empty-state">
                  <FaRobot />
                  <h3>No FAQs Found</h3>
                  <p>Add your first FAQ using the form on the left,</p>
                  <p>or adjust your filters to see more results!</p>
                </div>
              ) : (
                Object.entries(faqsByCategory).map(([category, categoryFaqs]) => (
                  <div key={category} className="faq-category-group">
                    <h3 className="category-title">
                      {getCategoryIcon(category)} {category}
                      <span className="faq-count">{categoryFaqs.length}</span>
                    </h3>
                    {categoryFaqs.map((faq) => (
                      <div key={faq.id} className={`faq-card ${!isValidFAQ(faq) ? 'inactive-faq' : ''}`}>
                        <div className="faq-header">
                          <div className="faq-question">
                            <div className="question-en">
                              <strong>Q:</strong> {faq.question_en}
                            </div>
                            {faq.question_ar && (
                              <div className="question-ar" dir="rtl">
                                <strong>س:</strong> {faq.question_ar}
                              </div>
                            )}
                          </div>
                          <div className="faq-card-actions">
                            <button 
                              className="edit-faq-btn"
                              onClick={() => handleEditFaq(faq)}
                              title="Edit FAQ"
                            >
                              <FaEdit />
                            </button>
                            <button 
                              className="delete-faq-btn"
                              onClick={() => handleDeleteFaq(faq.id)}
                              title="Delete FAQ"
                            >
                              <FaTrash />
                            </button>
                          </div>
                        </div>
                        
                        <div className="faq-answer">
                          <div className="answer-en">
                            <strong>A:</strong> {faq.answer_en}
                          </div>
                          {faq.answer_ar && (
                            <div className="answer-ar" dir="rtl">
                              <strong>ج:</strong> {faq.answer_ar}
                            </div>
                          )}
                        </div>
                        
                        {/* Date and Academic Information */}
                        <div className="faq-meta">
                          {(faq.academic_year || faq.semester) && (
                            <div className="academic-info">
                              <FaCalendarAlt />
                              <span>
                                {faq.academic_year && `AY: ${faq.academic_year}`}
                                {faq.academic_year && faq.semester && " | "}
                                {faq.semester && `Sem: ${faq.semester}`}
                              </span>
                            </div>
                          )}
                          
                          {(faq.valid_from || faq.valid_until) && (
                            <div className="validity-info">
                              <MdDateRange />
                              <span>
                                {faq.valid_from && `From: ${new Date(faq.valid_from).toLocaleDateString()}`}
                                {faq.valid_from && faq.valid_until && " "}
                                {faq.valid_until && `To: ${new Date(faq.valid_until).toLocaleDateString()}`}
                                {!faq.valid_from && !faq.valid_until && "Always valid"}
                              </span>
                            </div>
                          )}
                          
                          <div className="status-badge">
                            <span className={isValidFAQ(faq) ? "active" : "inactive"}>
                              {isValidFAQ(faq) ? "Active" : faq.is_active ? "Expired" : "Inactive"}
                            </span>
                          </div>
                        </div>
                        
                        {faq.source_type && (
                          <div className="faq-source">
                            <small>Source: {faq.source_type}</small>
                            <small> • Created: {new Date(faq.created_at).toLocaleDateString()}</small>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Categories Management Tab */}
      {activeMainTab === "categories" && (
        <div className="categories-container">
          <div className="categories-left-panel">
            <div className="form-section">
              <h2>
                {editingCategory ? <FaEdit /> : <FaPlus />}
                {editingCategory ? "Edit Category" : "Add New Category"}
              </h2>
              <form onSubmit={handleCategorySubmit} className="category-form">
                <div className="form-group">
                  <label>Name (English)</label>
                  <input
                    type="text"
                    value={categoryForm.name_en}
                    onChange={(e) => setCategoryForm({...categoryForm, name_en: e.target.value})}
                    placeholder="e.g., Registration, GPA, Exams"
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label>Name (Arabic)</label>
                  <input
                    type="text"
                    value={categoryForm.name_ar}
                    onChange={(e) => setCategoryForm({...categoryForm, name_ar: e.target.value})}
                    placeholder="مثال: التسجيل، المعدل، الامتحانات"
                    dir="rtl"
                  />
                </div>
                
                <div className="form-group">
                  <label>Description (English)</label>
                  <textarea
                    value={categoryForm.description_en}
                    onChange={(e) => setCategoryForm({...categoryForm, description_en: e.target.value})}
                    placeholder="Describe what this category covers"
                    rows="2"
                  />
                </div>
                
                <div className="form-group">
                  <label>Description (Arabic)</label>
                  <textarea
                    value={categoryForm.description_ar}
                    onChange={(e) => setCategoryForm({...categoryForm, description_ar: e.target.value})}
                    placeholder="وصف ما تغطيه هذه الفئة"
                    rows="2"
                    dir="rtl"
                  />
                </div>
                
                <div className="form-actions">
                  {editingCategory && (
                    <button type="button" className="btn-secondary" onClick={() => {
                      setEditingCategory(null);
                      setCategoryForm({ name_ar: "", name_en: "", description_ar: "", description_en: "" });
                    }}>
                      <FaTimes /> Cancel
                    </button>
                  )}
                  <button type="submit" className="btn-primary" disabled={loading}>
                    {loading ? <FaSpinner className="spinner" /> : (editingCategory ? <FaSave /> : <FaPlus />)}
                    {editingCategory ? "Update Category" : "Create Category"}
                  </button>
                </div>
              </form>
            </div>
          </div>
          
          <div className="categories-right-panel">
            <div className="panel-header">
              <h2>
                <MdCategory /> All Categories
                <span className="faq-count">{categories.length} Categories</span>
              </h2>
              <button className="refresh-btn" onClick={fetchCategories}>
                <MdRefresh /> Refresh
              </button>
            </div>
            
            <div className="categories-grid">
              {categories.map(cat => (
                <div key={cat.id} className="category-card">
                  <div className="category-header">
                    <h3>{getCategoryIcon(cat.name_en)} {cat.name_en}</h3>
                    <div className="category-actions">
                      <button onClick={() => handleEditCategory(cat)} className="edit-btn" title="Edit">
                        <FaEdit />
                      </button>
                      <button onClick={() => handleDeleteCategory(cat.id)} className="delete-btn" title="Delete">
                        <FaTrash />
                      </button>
                    </div>
                  </div>
                  {cat.name_ar && <p className="category-ar">{cat.name_ar}</p>}
                  {cat.description_en && <p className="category-desc">{cat.description_en}</p>}
                  {cat.description_ar && <p className="category-desc-ar" dir="rtl">{cat.description_ar}</p>}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Quick Reference Guide */}
      <div className="quick-reference">
        <h3><FaRobot /> What Students Can Ask The Chatbot:</h3>
        <div className="reference-grid">
          <div className="ref-card"><FaChartLine /> GPA & Grades</div>
          <div className="ref-card"><FaCalendarAlt /> Schedule/Timetable</div>
          <div className="ref-card"><FaUserGraduate /> Attendance</div>
          <div className="ref-card"><FaBook /> Course Registration</div>
          <div className="ref-card"><FaLink /> CIMS Portal</div>
          <div className="ref-card"><FaEnvelope /> Advisor Contact</div>
          <div className="ref-card"><FaFileAlt /> Transcript</div>
          <div className="ref-card"><FaKey /> Password Reset</div>
          <div className="ref-card"><FaTrophy /> Scholarships</div>
          <div className="ref-card"><FaBriefcase /> Internships</div>
          <div className="ref-card"><FaShieldAlt /> Emergency</div>
          <div className="ref-card"><FaLanguage /> Bilingual Support</div>
        </div>
      </div>
    </div>
  );
};

export default FQAManager;