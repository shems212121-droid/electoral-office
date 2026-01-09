/**
 * Sync Manager - مدير المزامنة
 * Synchronizes local database with server
 */

class SyncManager {
    constructor(localDB, serverURL = '') {
        this.localDB = localDB;
        this.serverURL = serverURL || window.location.origin;
        this.isSyncing = false;
        this.lastSyncTime = null;
    }

    /**
     * Check if online
     */
    isOnline() {
        return navigator.onLine;
    }

    /**
     * Download data from server to local DB
     */
    async downloadFromServer(forceRefresh = false) {
        if (!this.isOnline()) {
            throw new Error('No internet connection');
        }

        this.isSyncing = true;
        const results = {
            voters: 0,
            candidates: 0,
            anchors: 0,
            introducers: 0,
            parties: 0,
            errors: []
        };

        try {
            // Check last sync
            const lastSync = await this.localDB.get('settings', 'last_sync');
            const lastSyncTime = lastSync ? lastSync.value : null;

            // Download voters
            try {
                const response = await fetch(`${this.serverURL}/api/voters/sync/`, {
                    headers: {
                        'X-Last-Sync': lastSyncTime || ''
                    }
                });

                if (response.ok) {
                    const voters = await response.json();
                    for (const voter of voters) {
                        try {
                            await this.localDB.add('voters', voter);
                            results.voters++;
                        } catch (e) {
                            // Already exists, update instead
                            await this.localDB.update('voters', voter.id, voter);
                        }
                    }
                }
            } catch (error) {
                results.errors.push({ entity: 'voters', error: error.message });
            }

            // Download candidates
            try {
                const response = await fetch(`${this.serverURL}/api/candidates/sync/`);
                if (response.ok) {
                    const candidates = await response.json();
                    for (const candidate of candidates) {
                        try {
                            await this.localDB.add('candidates', candidate);
                            results.candidates++;
                        } catch (e) {
                            await this.localDB.update('candidates', candidate.id, candidate);
                        }
                    }
                }
            } catch (error) {
                results.errors.push({ entity: 'candidates', error: error.message });
            }

            // Download parties
            try {
                const response = await fetch(`${this.serverURL}/api/parties/sync/`);
                if (response.ok) {
                    const parties = await response.json();
                    for (const party of parties) {
                        try {
                            await this.localDB.add('parties', party);
                            results.parties++;
                        } catch (e) {
                            await this.localDB.update('parties', party.id, party);
                        }
                    }
                }
            } catch (error) {
                results.errors.push({ entity: 'parties', error: error.message });
            }

            // Save last sync time
            await this.localDB.db.transaction('settings', 'readwrite')
                .objectStore('settings')
                .put({ key: 'last_sync', value: new Date().toISOString() });

            this.lastSyncTime = new Date();
            this.isSyncing = false;

            return results;
        } catch (error) {
            this.isSyncing = false;
            throw error;
        }
    }

    /**
     * Upload pending changes to server
     */
    async uploadToServer() {
        if (!this.isOnline()) {
            throw new Error('No internet connection');
        }

        const pendingItems = await this.localDB.getPendingSyncItems();
        const results = {
            uploaded: 0,
            failed: 0,
            errors: []
        };

        for (const item of pendingItems) {
            try {
                let endpoint = '';
                let method = '';
                let body = null;

                switch (item.action) {
                    case 'create':
                        endpoint = `${this.serverURL}/api/${item.storeName}/`;
                        method = 'POST';
                        body = JSON.stringify(item.data);
                        break;

                    case 'update':
                        endpoint = `${this.serverURL}/api/${item.storeName}/${item.recordId}/`;
                        method = 'PUT';
                        body = JSON.stringify(item.data);
                        break;

                    case 'delete':
                        endpoint = `${this.serverURL}/api/${item.storeName}/${item.recordId}/`;
                        method = 'DELETE';
                        break;
                }

                const response = await fetch(endpoint, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: body
                });

                if (response.ok) {
                    // Mark as synced
                    await this.localDB.update('sync_queue', item.id, { status: 'synced' });
                    results.uploaded++;
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (error) {
                // Mark as error and increment retries
                await this.localDB.update('sync_queue', item.id, {
                    status: 'error',
                    retries: item.retries + 1,
                    lastError: error.message
                });
                results.failed++;
                results.errors.push({
                    item: item,
                    error: error.message
                });
            }
        }

        return results;
    }

    /**
     * Full sync (both ways)
     */
    async fullSync() {
        if (!this.isOnline()) {
            return {
                success: false,
                message: 'لا يوجد اتصال بالإنترنت'
            };
        }

        try {
            this.isSyncing = true;

            // First upload local changes
            const uploadResults = await this.uploadToServer();

            // Then download server data
            const downloadResults = await this.downloadFromServer();

            this.isSyncing = false;

            return {
                success: true,
                upload: uploadResults,
                download: downloadResults,
                message: 'تمت المزامنة بنجاح'
            };
        } catch (error) {
            this.isSyncing = false;
            return {
                success: false,
                message: `خطأ في المزامنة: ${error.message}`,
                error: error
            };
        }
    }

    /**
     * Export database as file
     */
    async exportDatabase() {
        const data = await this.localDB.exportToJSON();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `electoral-db-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Import database from file
     */
    async importDatabase(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onload = async (e) => {
                try {
                    const data = JSON.parse(e.target.result);
                    await this.localDB.importFromJSON(data);
                    resolve({
                        success: true,
                        message: 'تم استيراد البيانات بنجاح'
                    });
                } catch (error) {
                    reject({
                        success: false,
                        message: `خطأ في الاستيراد: ${error.message}`
                    });
                }
            };

            reader.onerror = () => reject({
                success: false,
                message: 'خطأ في قراءة الملف'
            });

            reader.readAsText(file);
        });
    }

    /**
     * Get CSRF Token
     */
    getCSRFToken() {
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

    /**
     * Auto sync on interval
     */
    startAutoSync(intervalMinutes = 30) {
        setInterval(async () => {
            if (this.isOnline() && !this.isSyncing) {
                console.log('🔄 Auto sync starting...');
                await this.fullSync();
            }
        }, intervalMinutes * 60 * 1000);
    }

    /**
     * Sync when coming back online
     */
    setupOnlineListener() {
        window.addEventListener('online', async () => {
            console.log('✅ Back online, syncing...');
            await this.fullSync();
        });
    }
}

// Global instance
const syncManager = new SyncManager(localDB);

// Setup listeners
if (typeof window !== 'undefined') {
    window.addEventListener('localdb-ready', () => {
        syncManager.setupOnlineListener();
        // Auto sync every 30 minutes
        syncManager.startAutoSync(30);
    });
}
