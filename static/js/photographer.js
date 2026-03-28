// Approve individual photo
async function approvePhoto(photoId) {
    try {
        const response = await fetch(`/photo/${photoId}/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            // Update UI
            const photoCard = document.getElementById(`photo-${photoId}`);
            const actionsDiv = photoCard.querySelector('.photo-actions');
            actionsDiv.innerHTML = `
                <span class="badge badge-success">Approved ✓</span>
                <button onclick="unapprovePhoto(${photoId})" class="btn btn-small btn-secondary">Unapprove</button>
            `;
            
            // Show success message
            showNotification('Photo approved successfully!', 'success');
        }
    } catch (error) {
        console.error('Error approving photo:', error);
        showNotification('Error approving photo', 'error');
    }
}

// Unapprove individual photo
async function unapprovePhoto(photoId) {
    try {
        const response = await fetch(`/photo/${photoId}/unapprove`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            // Update UI
            const photoCard = document.getElementById(`photo-${photoId}`);
            const actionsDiv = photoCard.querySelector('.photo-actions');
            actionsDiv.innerHTML = `
                <span class="badge badge-warning">Pending</span>
                <button onclick="approvePhoto(${photoId})" class="btn btn-small btn-success">Approve</button>
            `;
            
            // Show success message
            showNotification('Photo unapproved', 'success');
        }
    } catch (error) {
        console.error('Error unapproving photo:', error);
        showNotification('Error unapproving photo', 'error');
    }
}

// Show notification
function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '1000';
    notification.style.maxWidth = '300px';
    notification.style.animation = 'slideIn 0.3s ease-out';
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// File upload preview
const fileInput = document.getElementById('photos');
if (fileInput) {
    const label = document.querySelector('.file-upload-label');
    const originalText = label.textContent;
    
    fileInput.addEventListener('change', (e) => {
        const files = e.target.files;
        if (files.length > 0) {
            label.textContent = `${files.length} file${files.length > 1 ? 's' : ''} selected`;
        } else {
            label.textContent = originalText;
        }
    });
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
