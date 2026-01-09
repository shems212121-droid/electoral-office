// PWA Install Prompt Handler
// Handles the PWA installation experience

let deferredPrompt;
let installButton;

// Listen for the beforeinstallprompt event
window.addEventListener('beforeinstallprompt', (e) => {
    console.log('[PWA] Install prompt triggered');

    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();

    // Stash the event so it can be triggered later
    deferredPrompt = e;

    // Show install button/banner if it exists
    showInstallPromotion();
});

// Function to show install promotion
function showInstallPromotion() {
    // Create install button if it doesn't exist
    if (!installButton) {
        createInstallBanner();
    }

    if (installButton) {
        installButton.style.display = 'block';
    }
}

// Create install banner
function createInstallBanner() {
    const banner = document.createElement('div');
    banner.id = 'pwa-install-banner';
    banner.className = 'pwa-install-banner';
    banner.innerHTML = `
        <div class="pwa-install-content">
            <div class="pwa-install-icon">
                <i class="fas fa-download"></i>
            </div>
            <div class="pwa-install-text">
                <strong>ثبّت التطبيق!</strong>
                <p>احصل على تجربة أفضل عبر تثبيت التطبيق على جهازك</p>
            </div>
            <div class="pwa-install-actions">
                <button id="pwa-install-btn" class="btn btn-primary btn-sm">
                    <i class="fas fa-plus"></i> تثبيت
                </button>
                <button id="pwa-dismiss-btn" class="btn btn-secondary btn-sm">
                    <i class="fas fa-times"></i> إغلاق
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(banner);

    installButton = document.getElementById('pwa-install-btn');
    const dismissButton = document.getElementById('pwa-dismiss-btn');

    // Install button click handler
    installButton.addEventListener('click', async () => {
        console.log('[PWA] Install button clicked');

        if (!deferredPrompt) {
            console.log('[PWA] No deferred prompt available');
            return;
        }

        // Show the install prompt
        deferredPrompt.prompt();

        // Wait for the user to respond to the prompt
        const { outcome } = await deferredPrompt.userChoice;
        console.log(`[PWA] User response: ${outcome}`);

        if (outcome === 'accepted') {
            console.log('[PWA] User accepted the install');
            // Hide the banner
            banner.style.display = 'none';
        }

        // Clear the deferred prompt
        deferredPrompt = null;
    });

    // Dismiss button click handler
    dismissButton.addEventListener('click', () => {
        banner.style.display = 'none';
        // Save dismissal in localStorage
        localStorage.setItem('pwa-install-dismissed', Date.now());
    });

    // Check if user previously dismissed
    const dismissed = localStorage.getItem('pwa-install-dismissed');
    if (dismissed) {
        const daysSinceDismissal = (Date.now() - parseInt(dismissed)) / (1000 * 60 * 60 * 24);
        // Show again after 7 days
        if (daysSinceDismissal < 7) {
            banner.style.display = 'none';
        }
    }
}

// Listen for successful installation
window.addEventListener('appinstalled', (e) => {
    console.log('[PWA] App installed successfully');

    // Hide the install banner
    if (installButton) {
        installButton.parentElement.parentElement.parentElement.style.display = 'none';
    }

    // Clear the deferred prompt
    deferredPrompt = null;

    // Optional: Show success message
    showInstallSuccessMessage();
});

// Show success message
function showInstallSuccessMessage() {
    const message = document.createElement('div');
    message.className = 'alert alert-success pwa-success-message';
    message.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <strong>تم التثبيت بنجاح!</strong>
        يمكنك الآن استخدام التطبيق من الشاشة الرئيسية.
    `;
    message.style.cssText = `
        position: fixed;
        top: 80px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 10000;
        min-width: 300px;
        text-align: center;
        animation: slideDown 0.3s ease-out;
    `;

    document.body.appendChild(message);

    // Remove after 5 seconds
    setTimeout(() => {
        message.style.animation = 'slideUp 0.3s ease-out';
        setTimeout(() => message.remove(), 300);
    }, 5000);
}

// Check if app is already installed
function isAppInstalled() {
    // Check if running in standalone mode
    return window.matchMedia('(display-mode: standalone)').matches ||
        window.navigator.standalone ||
        document.referrer.includes('android-app://');
}

// Register service worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/service-worker.js')
            .then(registration => {
                console.log('[PWA] Service Worker registered successfully:', registration.scope);

                // Check for updates periodically
                setInterval(() => {
                    registration.update();
                }, 60000); // Check every minute

                // Handle updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;

                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // New service worker available
                            showUpdateNotification(newWorker);
                        }
                    });
                });
            })
            .catch(err => {
                console.log('[PWA] Service Worker registration failed:', err);
            });
    });
}

// Show update notification
function showUpdateNotification(newWorker) {
    const notification = document.createElement('div');
    notification.className = 'alert alert-info pwa-update-notification';
    notification.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <i class="fas fa-sync"></i>
                <strong>تحديث متوفر!</strong>
                <p style="margin: 5px 0 0;">توجد نسخة جديدة من التطبيق</p>
            </div>
            <button id="pwa-update-btn" class="btn btn-primary btn-sm">
                <i class="fas fa-redo"></i> تحديث الآن
            </button>
        </div>
    `;
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 10000;
        min-width: 350px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    `;

    document.body.appendChild(notification);

    document.getElementById('pwa-update-btn').addEventListener('click', () => {
        // Tell service worker to skip waiting
        newWorker.postMessage({ action: 'skipWaiting' });

        // Reload the page
        window.location.reload();
    });
}

// Handle online/offline status
window.addEventListener('online', () => {
    console.log('[PWA] App is online');
    showStatusMessage('متصل بالإنترنت', 'success');
});

window.addEventListener('offline', () => {
    console.log('[PWA] App is offline');
    showStatusMessage('غير متصل - وضع Offline', 'warning');
});

// Show status message
function showStatusMessage(message, type) {
    const statusMsg = document.createElement('div');
    statusMsg.className = `alert alert-${type} pwa-status-message`;
    statusMsg.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'wifi' : 'wifi-slash'}"></i>
        ${message}
    `;
    statusMsg.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 10000;
        min-width: 200px;
        animation: slideInRight 0.3s ease-out;
    `;

    document.body.appendChild(statusMsg);

    setTimeout(() => {
        statusMsg.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => statusMsg.remove(), 300);
    }, 3000);
}
