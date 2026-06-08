import toast from 'react-hot-toast';

class NotificationService {
  constructor() {
    this.isGrowlAvailable = true;
  }

  showSuccess(message, title = 'Success') {
    toast.success(message, {
      duration: 3000,
      icon: '✅',
      style: {
        background: '#10b981',
        color: '#fff',
      },
    });
  }

  showError(message, title = 'Error') {
    toast.error(message, {
      duration: 4000,
      icon: '❌',
      style: {
        background: '#ef4444',
        color: '#fff',
      },
    });
  }

  showWarning(message, title = 'Warning') {
    toast(message, {
      duration: 5000,
      icon: '⚠️',
      style: {
        background: '#f59e0b',
        color: '#fff',
      },
    });
  }

  showInfo(message, title = 'Info') {
    toast(message, {
      duration: 3000,
      icon: 'ℹ️',
      style: {
        background: '#3b82f6',
        color: '#fff',
      },
    });
  }

  showNotice(message, title = 'Notice') {
    toast(message, {
      duration: 2000,
      icon: '📢',
      style: {
        background: '#1800ad',
        color: '#fff',
      },
    });
  }

  showLoginSuccess(studentName) {
    toast.success(`Welcome back, ${studentName}! 👋`, {
      duration: 3000,
      icon: '🎉',
    });
  }

  showLoginError() {
    toast.error('Invalid student ID or password', {
      duration: 4000,
      icon: '🔐',
    });
  }

  showChatResponse(response) {
    // Don't show for long responses
    if (response.length > 100) return;
    toast(response, {
      duration: 3000,
      icon: '🤖',
      style: {
        background: '#1800ad',
        color: '#fff',
      },
    });
  }

  showPDFDownload(studentId, filename) {
    toast.success(`PDF downloaded: ${filename}`, {
      duration: 3000,
      icon: '📄',
    });
  }

  showPDFError(message) {
    toast.error(message || 'Failed to download PDF', {
      duration: 4000,
      icon: '❌',
    });
  }

  showUnansweredLogged() {
    toast('Question saved for learning! 🙏', {
      duration: 3000,
      icon: '📝',
      style: {
        background: '#f59e0b',
        color: '#fff',
      },
    });
  }

  showAdminLoginSuccess() {
    toast.success('Welcome, Administrator!', {
      duration: 3000,
      icon: '👨‍💼',
    });
  }

  showFAQAdded() {
    toast.success('FAQ added successfully!', {
      duration: 3000,
      icon: '✅',
    });
  }

  showFAQUpdated() {
    toast.success('FAQ updated successfully!', {
      duration: 3000,
      icon: '✏️',
    });
  }

  showFAQDeleted() {
    toast.success('FAQ deleted successfully!', {
      duration: 3000,
      icon: '🗑️',
    });
  }

  showStudentAdded() {
    toast.success('Student added successfully!', {
      duration: 3000,
      icon: '👨‍🎓',
    });
  }

  showStaffAdded() {
    toast.success('Staff member added successfully!', {
      duration: 3000,
      icon: '👨‍💼',
    });
  }

  showPasswordReset() {
    toast.success('Password reset successfully!', {
      duration: 3000,
      icon: '🔑',
    });
  }
}

export default new NotificationService();