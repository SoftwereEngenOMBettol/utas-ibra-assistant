// frontend/src/components/Admin/TemplateManager.jsx

const TemplateManager = () => {
  const [template, setTemplate] = useState({
    intent_name: '',
    keywords: '',
    response_html_en: '',
    response_html_ar: '',
    requires_data: false,
    data_tables: []
  });

  const saveTemplate = async () => {
    await axios.post('/api/admin/response-templates', template);
    alert('Template saved! Now Gemini will use this for matching questions');
  };

  return (
    <div className="template-editor">
      <h3>Create Response Template</h3>
      
      <div className="form-group">
        <label>Intent Name (e.g., "gpa_query")</label>
        <input value={template.intent_name} onChange={e => setTemplate({...template, intent_name: e.target.value})} />
      </div>
      
      <div className="form-group">
        <label>Trigger Keywords (comma separated)</label>
        <input placeholder="gpa, معدل, my grades" onChange={e => setTemplate({...template, keywords: e.target.value.split(',')})} />
      </div>
      
      <div className="form-group">
        <label>HTML Response (English)</label>
        <textarea rows="10" value={template.response_html_en} onChange={e => setTemplate({...template, response_html_en: e.target.value})} />
        <small>Use {{placeholders}} for dynamic data like {{gpa_value}}</small>
      </div>
      
      <div className="form-group">
        <label>HTML Response (Arabic)</label>
        <textarea rows="10" value={template.response_html_ar} onChange={e => setTemplate({...template, response_html_ar: e.target.value})} />
      </div>
      
      <div className="form-group">
        <label>Requires Student Data?</label>
        <input type="checkbox" checked={template.requires_data} onChange={e => setTemplate({...template, requires_data: e.target.checked})} />
      </div>
      
      {template.requires_data && (
        <div className="form-group">
          <label>Data Tables Needed</label>
          <select multiple onChange={e => setTemplate({...template, data_tables: Array.from(e.target.selectedOptions, opt => opt.value)})}>
            <option value="student_gpa">GPA Data</option>
            <option value="student_schedule">Schedule Data</option>
            <option value="attendance">Attendance Data</option>
            <option value="students">Student Info</option>
          </select>
        </div>
      )}
      
      <button onClick={saveTemplate}>Save Template</button>
    </div>
  );
};