/**
 * Data Synchronization Manager
 * نظام المزامنة التلقائية للبيانات
 * 
 * يدير تحميل البيانات من السيرفر وتخزينها في IndexedDB
 * والمزامنة التلقائية عند العودة للاتصال
 */

class DataSync {
    constructor() {
        this.syncInProgress = false;
        this.lastSyncTime = null;
        this.syncInterval = 5 * 60 * 1000; // 5 minutes
        this.autoSyncEnabled = true;
        this.init();
    }

    init() {
        // الانتظار حتى يصبح localDB جاهزاً
        window.addEventListener('localdb-ready', () => {
            console.log('[DataSync] LocalDB is ready, starting sync manager');
            this.loadLastSyncTime();
            this.setupEventListeners();

            // بدء المزامنة التلقائية إذا كنا متصلين
            if (navigator.onLine) {
                this.scheduleAutoSync();
            }
        });
    }

    setupEventListeners() {
        // الاستماع لتغييرات حالة الاتصال
        window.addEventListener('online', () => {
            console.log('[DataSync] Connection restored, starting sync...');
            this.showSyncNotification('تم استعادة الاتصال، جاري المزامنة...', 'info');
            this.performFullSync();
        });

        window.addEventListener('offline', () => {
            console.log('[DataSync] Connection lost, switching to offline mode');
            this.showSyncNotification('تم فقدان الاتصال - وضع Offline', 'warning');
        });

        // الاستماع لطلبات المزامنة من Service Worker
        navigator.serviceWorker?.addEventListener('message', (event) => {
            if (event.data.type === 'SYNC_REQUESTED') {
                console.log('[DataSync] Sync requested by service worker');
                this.performFullSync();
            }
        });
    }

    loadLastSyncTime() {
        const stored = localStorage.getItem('lastSyncTime');
        if (stored) {
            this.lastSyncTime = new Date(stored);
            console.log('[DataSync] Last sync:', this.lastSyncTime.toLocaleString('ar-SA'));
        }
    }

    saveLastSyncTime() {
        this.lastSyncTime = new Date();
        localStorage.setItem('lastSyncTime', this.lastSyncTime.toISOString());
    }

    scheduleAutoSync() {
        if (!this.autoSyncEnabled) return;

        // المزامنة الدورية
        setInterval(() => {
            if (navigator.onLine && !this.syncInProgress) {
                console.log('[DataSync] Auto-sync triggered');
                this.performFullSync();
            }
        }, this.syncInterval);
    }

    async performFullSync() {
        if (this.syncInProgress) {
            console.log('[DataSync] Sync already in progress');
            return;
        }

        if (!navigator.onLine) {
            console.log('[DataSync] Cannot sync - offline');
            return;
        }

        this.syncInProgress = true;
        this.showSyncNotification('جاري مزامنة البيانات...', 'info');

        try {
            // 1. مزامنة البيانات المحلية المعلقة إلى السيرفر
            await this.syncPendingChanges();

            // 2. جلب البيانات المحدثة من السيرفر
            await this.fetchUpdatesFromServer();

            this.saveLastSyncTime();
            this.showSyncNotification('تمت المزامنة بنجاح! ✓', 'success');

            // إطلاق حدث المزامنة
            window.dispatchEvent(new CustomEvent('data-sync-complete'));

        } catch (error) {
            console.error('[DataSync] Sync failed:', error);
            this.showSyncNotification('فشلت المزامنة - سيتم إعادة المحاولة', 'error');
        } finally {
            this.syncInProgress = false;
        }
    }

    async syncPendingChanges() {
        console.log('[DataSync] Syncing pending changes to server...');

        const pendingItems = await localDB.getPendingSyncItems();
        console.log(`[DataSync] Found ${pendingItems.length} pending items`);

        for (const item of pendingItems) {
            try {
                await this.syncItemToServer(item);

                // تحديث حالة العنصر إلى synced
                await localDB.update('sync_queue', item.id, { status: 'synced' });

            } catch (error) {
                console.error('[DataSync] Failed to sync item:', item, error);

                // زيادة عدد المحاولات
                await localDB.update('sync_queue', item.id, {
                    retries: item.retries + 1,
                    status: 'error'
                });
            }
        }
    }

    async syncItemToServer(item) {
        // إرسال البيانات للسيرفر حسب نوع العملية
        const endpoint = this.getEndpointForStore(item.storeName);

        if (!endpoint) {
            console.warn('[DataSync] No endpoint configured for:', item.storeName);
            return;
        }

        let response;
        switch (item.action) {
            case 'create':
                response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: JSON.stringify(item.data)
                });
                break;

            case 'update':
                response = await fetch(`${endpoint}${item.recordId}/`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: JSON.stringify(item.data)
                });
                break;

            case 'delete':
                response = await fetch(`${endpoint}${item.recordId}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': this.getCsrfToken()
                    }
                });
                break;
        }

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }

        return await response.json();
    }

    async fetchUpdatesFromServer() {
        console.log('[DataSync] Fetching updates from server...');

        // جلب البيانات الأساسية وتخزينها في IndexedDB
        const endpoints = [
            { store: 'candidates', url: '/api/candidates/' },
            { store: 'parties', url: '/api/parties/' },
            // يمكن إضافة المزيد من endpoints هنا
        ];

        for (const { store, url } of endpoints) {
            try {
                const response = await fetch(url);
                if (!response.ok) continue;

                const data = await response.json();

                // تحديث البيانات في IndexedDB
                for (const item of data) {
                    try {
                        await localDB.add(store, item);
                    } catch (e) {
                        // قد يكون موجوداً مسبقاً، نحاول التحديث
                        if (item.id) {
                            await localDB.update(store, item.id, item);
                        }
                    }
                }

                console.log(`[DataSync] Updated ${data.length} items in ${store}`);
            } catch (error) {
                console.error(`[DataSync] Failed to fetch ${store}:`, error);
            }
        }
    }

    getEndpointForStore(storeName) {
        const endpoints = {
            'voters': '/api/voters/',
            'candidates': '/api/candidates/',
            'anchors': '/api/anchors/',
            'introducers': '/api/introducers/',
            'parties': '/api/parties/'
        };
        return endpoints[storeName];
    }

    getCsrfToken() {
        // الحصول على CSRF token من cookie
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    showSyncNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `sync-notification sync-${type}`;

        const icons = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-sync fa-spin'
        };

        notification.innerHTML = `
            <i class="fas ${icons[type] || icons.info}"></i>
            <span>${message}</span>
        `;

        notification.style.cssText = `
            position: fixed;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#2196F3'};
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            display: flex;
            align-items: center;
            gap: 10px;
            font-family: 'Cairo', sans-serif;
            font-size: 14px;
            animation: slideUp 0.3s ease-out;
        `;

        document.body.appendChild(notification);

        // إزالة بعد 3 ثواني (إلا إذا كانت info - المزامنة جارية)
        if (type !== 'info' || !message.includes('جاري')) {
            setTimeout(() => {
                notification.style.animation = 'slideDown 0.3s ease-out';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        } else {
            // حفظ المرجع لإزالته لاحقاً
            this.activeSyncNotification = notification;
        }
    }

    hideSyncNotification() {
        if (this.activeSyncNotification) {
            this.activeSyncNotification.style.animation = 'slideDown 0.3s ease-out';
            setTimeout(() => this.activeSyncNotification.remove(), 300);
            this.activeSyncNotification = null;
        }
    }

    // دالة لحفظ البيانات محلياً مع إضافتها لطابور المزامنة
    async saveDataOffline(storeName, data, action = 'create') {
        try {
            // حفظ في IndexedDB
            const id = await localDB.add(storeName, data);

            // لا حاجة لإضافة يدوية للـ sync queue، localDB.add يقوم بذلك

            console.log(`[DataSync] Data saved offline in ${storeName}:`, id);

            // إذا كنا متصلين، حاول المزامنة فوراً
            if (navigator.onLine) {
                this.performFullSync();
            }

            return id;
        } catch (error) {
            console.error('[DataSync] Failed to save data offline:', error);
            throw error;
        }
    }

    // الحصول على إحصائيات المزامنة
    async getSyncStats() {
        return {
            lastSync: this.lastSyncTime,
            pending: await localDB.count('sync_queue'),
            dbStats: await localDB.getStats()
        };
    }
}

// إنشاء نسخة عامة
const dataSync = new DataSync();

// إضافة أنماط CSS للرسوم المتحركة
const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translate(-50%, 20px);
        }
        to {
            opacity: 1;
            transform: translate(-50%, 0);
        }
    }

    @keyframes slideDown {
        from {
            opacity: 1;
            transform: translate(-50%, 0);
        }
        to {
            opacity: 0;
            transform: translate(-50%, 20px);
        }
    }

    .sync-notification {
        font-weight: 600;
    }

    .sync-notification i {
        font-size: 1.1em;
    }
`;
document.head.appendChild(style);

// تصدير للاستخدام العام
if (typeof window !== 'undefined') {
    window.dataSync = dataSync;
}

console.log('[DataSync] Manager initialized');
