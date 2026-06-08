import React from 'react';
import { useNavigate } from 'react-router-dom';

const Navigation = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const isAdmin = user?.is_admin === true;
  
  return (
    <nav style={styles.nav}>
      <div style={styles.logo}>
        <h3>UTAS Assistant</h3>
      </div>
      
      <div style={styles.navLinks}>
        {isAdmin && (
          <>
            <button onClick={() => navigate('/admin')} style={styles.navButton}>
              Dashboard
            </button>
            <button onClick={() => navigate('/admin?tab=faq')} style={styles.navButton}>
              FAQ Manager
            </button>
            <button onClick={() => navigate('/admin?tab=students')} style={styles.navButton}>
              Students
            </button>
          </>
        )}
        
        <button onClick={() => navigate('/chat')} style={styles.navButton}>
          Chat
        </button>
        
        <button onClick={onLogout} style={{...styles.navButton, ...styles.logoutButton}}>
          Logout
        </button>
      </div>
    </nav>
  );
};

const styles = {
  nav: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 20px',
    backgroundColor: '#2d3748',
    color: 'white',
  },
  logo: {
    fontSize: '18px',
    fontWeight: 'bold',
  },
  navLinks: {
    display: 'flex',
    gap: '10px',
  },
  navButton: {
    padding: '8px 16px',
    backgroundColor: 'transparent',
    border: '1px solid #4a5568',
    borderRadius: '6px',
    color: 'white',
    cursor: 'pointer',
    transition: 'all 0.3s',
  },
  logoutButton: {
    backgroundColor: '#e53e3e',
    borderColor: '#e53e3e',
  }
};

export default Navigation;