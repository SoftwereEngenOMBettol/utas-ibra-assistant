import React from 'react';

const MarkdownRenderer = ({ content }) => {
  // Handle bullet points
  if (content.includes('•') || content.includes('\n- ')) {
    const lines = content.split('\n').filter(line => line.trim());
    const bulletPoints = lines.filter(line => line.trim().startsWith('•') || line.trim().startsWith('-'));
    
    if (bulletPoints.length > 0) {
      return (
        <ul style={{ margin: '10px 0', paddingLeft: '20px', listStyleType: 'disc' }}>
          {bulletPoints.map((item, i) => (
            <li key={i} style={{ marginBottom: '5px', lineHeight: '1.6' }}>
              {item.replace(/^[•-]\s*/, '')}
            </li>
          ))}
        </ul>
      );
    }
  }

  // Handle numbered lists
  if (content.match(/^\d+\./m)) {
    const lines = content.split('\n').filter(line => line.trim());
    const numbered = lines.filter(line => line.match(/^\d+\./));
    
    if (numbered.length > 0) {
      return (
        <ol style={{ margin: '10px 0', paddingLeft: '20px' }}>
          {numbered.map((item, i) => (
            <li key={i} style={{ marginBottom: '5px', lineHeight: '1.6' }}>
              {item.replace(/^\d+\.\s*/, '')}
            </li>
          ))}
        </ol>
      );
    }
  }

  // Handle tables
  if (content.includes('|') && content.includes('---')) {
    const lines = content.split('\n');
    const tableLines = lines.filter(line => line.includes('|') && line.trim());
    
    if (tableLines.length >= 2) {
      const headers = tableLines[0].split('|')
        .filter(cell => cell.trim())
        .map(cell => cell.trim());
      
      const dataRows = [];
      for (let i = 2; i < tableLines.length; i++) {
        if (tableLines[i].includes('|')) {
          const cells = tableLines[i].split('|')
            .filter(cell => cell.trim())
            .map(cell => cell.trim());
          if (cells.length > 0) {
            dataRows.push(cells);
          }
        }
      }
      
      return (
        <table style={{ 
          width: '100%', 
          borderCollapse: 'collapse',
          margin: '15px 0',
          fontSize: '14px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <thead>
            <tr>
              {headers.map((header, i) => (
                <th key={i} style={{ 
                  padding: '12px 10px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  border: '1px solid #ddd',
                  textAlign: 'left',
                  fontWeight: '600'
                }}>
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dataRows.map((row, i) => (
              <tr key={i} style={{ background: i % 2 === 0 ? '#ffffff' : '#f8f9fa' }}>
                {row.map((cell, j) => (
                  <td key={j} style={{ padding: '10px', border: '1px solid #ddd' }}>
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
    }
  }

  // Handle sections with headers
  if (content.includes('**')) {
    const parts = content.split(/(\*\*[^*]+\*\*)/g);
    return (
      <div>
        {parts.map((part, i) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return <h4 key={i} style={{ margin: '15px 0 10px', color: '#333' }}>{part.slice(2, -2)}</h4>;
          } else if (part.trim()) {
            return <p key={i} style={{ margin: '10px 0', lineHeight: '1.6' }}>{part}</p>;
          }
          return null;
        })}
      </div>
    );
  }

  // Default: render as paragraphs
  return content.split('\n\n').map((paragraph, i) => (
    <p key={i} style={{ margin: '10px 0', lineHeight: '1.6' }}>{paragraph}</p>
  ));
};

export default MarkdownRenderer;