/**
 * Offline UI Helper Functions
 * مساعدات واجهة المستخدم للعمل Offline
 */

// Update online/offline status indicator
function updateOnlineStatus() {
    const indicator = document.getElementById('onlineIndicator');
    const text = document.getElementById('syncText');

    if (navigator.onLine) {
        indicator.style.color = '#4CAF50';
        text.textContent = 'متصل';
    } else {
        indicator.style.color = '#F44336';
        text.textContent = 'غير متصل';
    }
}

// Listen to online/offline events
window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);
window.addEventListener('load', updateOnlineStatus);

// Sync button handler
async function sync() {
    const button = event.target;
    button.disabled = true;
    button.textContent = 'جاري المزامنة...';

    try {
        const result = await syncManager.fullSync();

        if (result.success) {
            showNotification('success', result.message);
            console.log('Upload:', result.upload);
            console.log('Download:', result.download);
        } else {
            showNotification('error', result.message);
        }
    } catch (error) {
        showNotification('error', 'فشلت المزامنة: ' + error.message);
    } finally {
        button.disabled = false;
        button.textContent = 'مزامنة الآن';
    }
}

// Export database
async function exportDB() {
    try {
        await syncManager.exportDatabase();
        showNotification('success', 'تم تصدير قاعدة البيانات');
    } catch (error) {
        showNotification('error', 'فشل التصدير: ' + error.message);
    }
}

// Import database
document.getElementById('importFile')?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
        const result = await syncManager.importDatabase(file);
        showNotification('success', result.message);
        location.reload(); // Reload to show new data
    } catch (error) {
        showNotification('error', error.message);
    }
});

// Show notification
function showNotification(type, message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        ${message}
    `;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#4CAF50' : '#F44336'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Update statistics display
async function updateStats() {
    const stats = await localDB.getStats();
    const statsDiv = document.getElementById('stats');

    if (statsDiv) {
        statsDiv.innerHTML = `
            <div class="stats-grid">
                <div class="stat-item">
                    <i class="fas fa-users"></i>
                    <div class="stat-number">${stats.voters}</div>
                    <div class="stat-label">ناخب</div>
                </div>
                <div class="stat-item">
                    <i class="fas fa-user-tie"></i>
                    <div class="stat-number">${stats.candidates}</div>
                    <div class="stat-label">مرشح</div>
                </div>
                <div class="stat-item">
                    <i class="fas fa-anchor"></i>
                    <div class="stat-number">${stats.anchors}</div>
                    <div class="stat-label">مرتكز</div>
                </div>
                <div class="stat-item">
                    <i class="fas fa-handshake"></i>
                    <div class="stat-number">${stats.introducers}</div>
                    <div class="stat-label">معرف</div>
                </div>
                <div class="stat-item">
                    <i class="fas fa-sync-alt"></i>
                    <div class="stat-number">${stats.pendingSync}</div>
                    <div class="stat-label">معلق</div>
                </div>
            </div>
        `;
    }
}

// Voter form handler
document.getElementById('voterForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);

    try {
        const id = await localDB.add('voters', data);
        showNotification('success', 'تمت إضافة الناخب بنجاح');
        e.target.reset();
        await loadVoters(); // Reload list
        await updateStats(); // Update stats
    } catch (error) {
        showNotification('error', 'فشلت الإضافة: ' + error.message);
    }
});

// Load and display voters
async function loadVoters() {
    const votersList = document.getElementById('votersList');
    if (!votersList) return;

    const voters = await localDB.getAll('voters');

    if (voters.length === 0) {
        votersList.innerHTML = '<p class="text-muted text-center">لا توجد بيانات</p>';
        return;
    }

    votersList.innerHTML = voters.map(voter => `
        <div class="voter-card">
            <div class="voter-info">
                <strong>${voter.full_name}</strong>
                <small>${voter.voter_number}</small>
            </div>
            <div class="voter-meta">
                <span class="badge bg-${getClassificationColor(voter.classification)}">
                    ${getClassificationLabel(voter.classification)}
                </span>
                <span>${voter.phone || '-'}</span>
            </div>
            <div class="voter-actions">
                <button onclick="editVoter(${voter.id})" class="btn btn-sm btn-primary">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="deleteVoter(${voter.id})" class="btn btn-sm btn-danger">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// Delete voter
async function deleteVoter(id) {
    if (!confirm('هل أنت متأكد من حذف هذا الناخب؟')) return;

    try {
        await localDB.delete('voters', id);
        showNotification('success', 'تم الحذف بنجاح');
        await loadVoters();
        await updateStats();
    } catch (error) {
        showNotification('error', 'فشل الحذف: ' + error.message);
    }
}

// Helper functions
function getClassificationColor(classification) {
    const colors = {
        'supporter': 'success',
        'neutral': 'warning',
        'opponent': 'danger',
        '': 'secondary'
    };
    return colors[classification] || 'secondary';
}

function getClassificationLabel(classification) {
    const labels = {
        'supporter': 'مؤيد',
        'neutral': 'محايد',
        'opponent': 'معارض',
        '': 'غير محدد'
    };
    return labels[classification] || 'غير محدد';
}

// Initialize on load
window.addEventListener('localdb-ready', async () => {
    console.log('✅ Offline UI ready');
    await loadVoters();
    await updateStats();
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .voter-card {
        background: white;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }
    
    .stat-item {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
`;
document.head.appendChild(style);
