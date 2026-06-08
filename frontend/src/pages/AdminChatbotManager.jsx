// frontend/src/pages/AdminChatbotManager.jsx

import React, { useState, useEffect } from "react";
import axios from "axios";
import { 
  FaRobot, FaPlus, FaTrash, FaEdit, FaSave, FaTimes, 
  FaSpinner, FaCheckCircle, FaExclamationTriangle, FaSearch,
  FaChartLine, FaCalendarAlt, FaUserGraduate, FaBook,
  FaLink, FaEnvelope, FaPhone, FaGlobe, FaKey, FaFileAlt,
  FaTrophy, FaBriefcase, FaShieldAlt, FaComment, FaLanguage
} from "react-icons/fa";
import { MdCategory, MdAutoAwesome, MdDelete, MdRefresh } from "react-icons/md";
import "./AdminChatbotManager.css";

const API_URL = "http://localhost:8000";

const AdminChatbotManager = () => {
  const [activeTab, setActiveTab] = useState("categories");
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState([]);
  const [faqs, setFaqs] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [notification, setNotification] = useState({ show: false, message: "", type: "" });
  const [searchTerm, setSearchTerm] = useState("");
  
  // Category form
  const [categoryForm, setCategoryForm] = useState({
    name_ar: "",
    name_en: "",
    description_ar: "",
    description_en: ""
  });
  const [editingCategory, setEditingCategory] = useState(null);
  
  // FAQ form
  const [faqForm, setFaqForm] = useState({
    question_ar: "",
    question_en: "",
    answer_ar: "",
    answer_en: "",
    category: "",
    category_id: null
  });
  const [editingFaq, setEditingFaq] = useState(null);
  
  // Conversation form
  const [convForm, setConvForm] = useState({
    type: "greeting",
    language: "en",
    text: ""
  });
  
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
    fetchCategories();
    fetchFaqs();
    fetchConversations();
  }, []);
  
  const fetchCategories = async () => {
    try {
      const config = getAuthConfig();
      const response = await axios.get(`${API_URL}/api/admin/categories`, config);
      setCategories(response.data);
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  };
  
  const fetchFaqs = async () => {
    try {
      const config = getAuthConfig();
      const response = await axios.get(`${API_URL}/api/admin/fqa`, config);
      setFaqs(response.data);
    } catch (error) {
      console.error("Error fetching FAQs:", error);
    }
  };
  
  const fetchConversations = async () => {
    try {
      const config = getAuthConfig();
      const response = await axios.get(`${API_URL}/api/admin/conversations`, config);
      setConversations(response.data);
    } catch (error) {
      console.error("Error fetching conversations:", error);
    }
  };
  
  const showNotification = (message, type) => {
    setNotification({ show: true, message, type });
    setTimeout(() => setNotification({ show: false, message: "", type: "" }), 3000);
  };
  
  // Category CRUD
  const handleCategorySubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const config = getAuthConfig();
      
      if (editingCategory) {
        await axios.put(`${API_URL}/api/admin/categories/${editingCategory.id}`, categoryForm, config);
        showNotification("Category updated successfully!", "success");
      } else {
        await axios.post(`${API_URL}/api/admin/categories`, categoryForm, config);
        showNotification("Category created successfully!", "success");
      }
      
      resetCategoryForm();
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
  
  const resetCategoryForm = () => {
    setCategoryForm({ name_ar: "", name_en: "", description_ar: "", description_en: "" });
    setEditingCategory(null);
  };
  
  // FAQ CRUD
  const handleFaqSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const config = getAuthConfig();
      
      if (editingFaq) {
        await axios.put(`${API_URL}/api/admin/fqa/${editingFaq.id}`, faqForm, config);
        showNotification("FAQ updated successfully!", "success");
      } else {
        await axios.post(`${API_URL}/api/admin/fqa/manual`, faqForm, config);
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
    setFaqForm({
      question_ar: faq.question_ar || "",
      question_en: faq.question_en || "",
      answer_ar: faq.answer_ar || "",
      answer_en: faq.answer_en || "",
      category: faq.category || "",
      category_id: faq.category_id || null
    });
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
    setFaqForm({
      question_ar: "",
      question_en: "",
      answer_ar: "",
      answer_en: "",
      category: "",
      category_id: null
    });
    setEditingFaq(null);
  };
  
  // Filter FAQs based on search
  const filteredFaqs = faqs.filter(faq => 
    faq.question_en?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    faq.question_ar?.includes(searchTerm) ||
    faq.answer_en?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    faq.category?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  // Group FAQs by category
  const faqsByCategory = filteredFaqs.reduce((acc, faq) => {
    const cat = faq.category || "Uncategorized";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(faq);
    return acc;
  }, {});
  
  return (
    <div className="admin-chatbot-manager">
      {/* Notification */}
      {notification.show && (
        <div className={`notification ${notification.type}`}>
          {notification.type === "success" ? <FaCheckCircle /> : <FaExclamationTriangle />}
          <span>{notification.message}</span>
        </div>
      )}
      
      <div className="manager-header">
        <h1>
          <FaRobot className="header-icon" />
          Chatbot Content Manager
        </h1>
        <p>Manage all chatbot responses - Categories, FAQs, and Conversations</p>
      </div>
      
      <div className="manager-tabs">
        <button 
          className={`tab-btn ${activeTab === "categories" ? "active" : ""}`}
          onClick={() => setActiveTab("categories")}
        >
          <MdCategory /> Categories ({categories.length})
        </button>
        <button 
          className={`tab-btn ${activeTab === "faqs" ? "active" : ""}`}
          onClick={() => setActiveTab("faqs")}
        >
          <FaBook /> FAQs ({faqs.length})
        </button>
        <button 
          className={`tab-btn ${activeTab === "conversations" ? "active" : ""}`}
          onClick={() => setActiveTab("conversations")}
        >
          <FaComment /> Conversations
        </button>
      </div>
      
      {/* Categories Tab */}
      {activeTab === "categories" && (
        <div className="manager-content">
          <div className="form-section">
            <h2>
              {editingCategory ? <FaEdit /> : <FaPlus />}
              {editingCategory ? "Edit Category" : "Add New Category"}
            </h2>
            <form onSubmit={handleCategorySubmit} className="category-form">
              <div className="form-row">
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
              </div>
              <div className="form-row">
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
              </div>
              <div className="form-actions">
                {editingCategory && (
                  <button type="button" className="btn-secondary" onClick={resetCategoryForm}>
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
          
          <div className="list-section">
            <h2>All Categories</h2>
            <div className="categories-grid">
              {categories.map(cat => (
                <div key={cat.id} className="category-card">
                  <div className="category-header">
                    <h3>{cat.name_en}</h3>
                    <div className="category-actions">
                      <button onClick={() => handleEditCategory(cat)} className="edit-btn">
                        <FaEdit />
                      </button>
                      <button onClick={() => handleDeleteCategory(cat.id)} className="delete-btn">
                        <FaTrash />
                      </button>
                    </div>
                  </div>
                  {cat.name_ar && <p className="category-ar">{cat.name_ar}</p>}
                  {cat.description_en && <p className="category-desc">{cat.description_en}</p>}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* FAQs Tab */}
      {activeTab === "faqs" && (
        <div className="manager-content">
          <div className="form-section">
            <h2>
              {editingFaq ? <FaEdit /> : <FaPlus />}
              {editingFaq ? "Edit FAQ" : "Add New FAQ"}
            </h2>
            <form onSubmit={handleFaqSubmit} className="faq-form">
              <div className="form-group">
                <label>Question (English) *</label>
                <input
                  type="text"
                  value={faqForm.question_en}
                  onChange={(e) => setFaqForm({...faqForm, question_en: e.target.value})}
                  placeholder="Enter question in English"
                  required
                />
              </div>
              <div className="form-group">
                <label>Question (Arabic)</label>
                <input
                  type="text"
                  value={faqForm.question_ar}
                  onChange={(e) => setFaqForm({...faqForm, question_ar: e.target.value})}
                  placeholder="السؤال بالعربية"
                  dir="rtl"
                />
              </div>
              <div className="form-group">
                <label>Answer (English) *</label>
                <textarea
                  value={faqForm.answer_en}
                  onChange={(e) => setFaqForm({...faqForm, answer_en: e.target.value})}
                  placeholder="Enter detailed answer in English"
                  rows="4"
                  required
                />
              </div>
              <div className="form-group">
                <label>Answer (Arabic)</label>
                <textarea
                  value={faqForm.answer_ar}
                  onChange={(e) => setFaqForm({...faqForm, answer_ar: e.target.value})}
                  placeholder="الإجابة بالعربية"
                  rows="4"
                  dir="rtl"
                />
              </div>
              <div className="form-group">
                <label>Category</label>
                <select
                  value={faqForm.category}
                  onChange={(e) => setFaqForm({...faqForm, category: e.target.value})}
                >
                  <option value="">Select category...</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.name_en}>
                      {cat.name_en} - {cat.name_ar}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-actions">
                {editingFaq && (
                  <button type="button" className="btn-secondary" onClick={resetFaqForm}>
                    <FaTimes /> Cancel
                  </button>
                )}
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? <FaSpinner className="spinner" /> : (editingFaq ? <FaSave /> : <FaPlus />)}
                  {editingFaq ? "Update FAQ" : "Add FAQ"}
                </button>
              </div>
            </form>
          </div>
          
          <div className="list-section">
            <h2>All FAQs</h2>
            <div className="search-bar">
              <FaSearch />
              <input
                type="text"
                placeholder="Search FAQs by question or answer..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            
            <div className="faqs-by-category">
              {Object.entries(faqsByCategory).map(([category, categoryFaqs]) => (
                <div key={category} className="faq-category-group">
                  <h3 className="category-title">
                    <MdCategory /> {category}
                    <span className="faq-count">{categoryFaqs.length} FAQs</span>
                  </h3>
                  <div className="faq-list">
                    {categoryFaqs.map(faq => (
                      <div key={faq.id} className="faq-item">
                        <div className="faq-question">
                          <strong>Q:</strong> {faq.question_en}
                          {faq.question_ar && (
                            <span className="arabic-question"> | {faq.question_ar}</span>
                          )}
                        </div>
                        <div className="faq-answer">
                          <strong>A:</strong> {faq.answer_en?.substring(0, 150)}...
                          {faq.answer_ar && (
                            <div className="arabic-answer">{faq.answer_ar?.substring(0, 150)}...</div>
                          )}
                        </div>
                        <div className="faq-actions">
                          <button onClick={() => handleEditFaq(faq)} className="edit-btn">
                            <FaEdit /> Edit
                          </button>
                          <button onClick={() => handleDeleteFaq(faq.id)} className="delete-btn">
                            <FaTrash /> Delete
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Quick Reference Guide */}
      <div className="quick-reference">
        <h3><FaRobot /> Quick Reference - What Students Can Ask:</h3>
        <div className="reference-grid">
          <div className="ref-card"><FaChartLine /> GPA & Grades</div>
          <div className="ref-card"><FaCalendarAlt /> Schedule/Timetable</div>
          <div className="ref-card"><FaUserGraduate /> Attendance</div>
          <div className="ref-card"><FaBook /> Course Registration</div>
          <div className="ref-card"><FaLink /> CIMS Portal Access</div>
          <div className="ref-card"><FaEnvelope /> Advisor Contact</div>
          <div className="ref-card"><FaFileAlt /> Transcript</div>
          <div className="ref-card"><FaKey /> Password Reset</div>
          <div className="ref-card"><FaTrophy /> Scholarships</div>
          <div className="ref-card"><FaBriefcase /> Internships/Jobs</div>
          <div className="ref-card"><FaShieldAlt /> Emergency Contacts</div>
          <div className="ref-card"><FaLanguage /> Bilingual Support</div>
        </div>
      </div>
    </div>
  );
};

export default AdminChatbotManager;