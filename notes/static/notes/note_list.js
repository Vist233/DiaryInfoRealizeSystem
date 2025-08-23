/* Quick create via API with enhanced UX */
(function () {
  const form = document.getElementById('qc-form');
  const input = document.getElementById('qc-title');
  const button = form?.querySelector('button[type="submit"]');
  
  if (!form || !input || !button) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = (input.value || '').trim();
    if (!title) { 
      input.focus(); 
      return; 
    }
    
    // Show loading state
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Creating...';
    
    try {
      const res = await fetch('/api/notes/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title })
      });
      
      if (!res.ok) {
        const error = await res.text();
        showNotification('Create failed: ' + error, 'error');
        return;
      }
      
      showNotification('Note created successfully!', 'success');
      input.value = '';
      
      // Small delay before reload to show notification
      setTimeout(() => {
        location.href = '/';
      }, 1000);
      
    } catch (e) {
      showNotification('Network error. Please try again.', 'error');
    } finally {
      button.disabled = false;
      button.textContent = originalText;
    }
  });

  function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 16px;
      border-radius: 8px;
      color: white;
      font-weight: 500;
      z-index: 1000;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      transform: translateX(100%);
      transition: transform 0.3s ease;
    `;
    
    if (type === 'success') {
      notification.style.background = 'var(--ok)';
    } else if (type === 'error') {
      notification.style.background = 'var(--danger)';
    } else {
      notification.style.background = 'var(--link)';
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
      notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 3000);
  }
})();

