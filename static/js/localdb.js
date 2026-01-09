/**
 * Local Database Manager - IndexedDB
 * قاعدة البيانات المحلية الكاملة
 */

class LocalDB {
    constructor() {
        this.dbName = 'ElectoralOfficeDB';
        this.version = 1;
        this.db = null;
    }

    /**
     * Initialize Database
     */
    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                console.log('✅ Database initialized');
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Voters Store
                if (!db.objectStoreNames.contains('voters')) {
                    const voterStore = db.createObjectStore('voters', { keyPath: 'id', autoIncrement: true });
                    voterStore.createIndex('voter_number', 'voter_number', { unique: true });
                    voterStore.createIndex('full_name', 'full_name', { unique: false });
                    voterStore.createIndex('classification', 'classification', { unique: false });
                    voterStore.createIndex('introducer_id', 'introducer_id', { unique: false });
                    voterStore.createIndex('phone', 'phone', { unique: false });
                }

                // Candidates Store
                if (!db.objectStoreNames.contains('candidates')) {
                    const candidateStore = db.createObjectStore('candidates', { keyPath: 'id', autoIncrement: true });
                    candidateStore.createIndex('full_name', 'full_name', { unique: false });
                    candidateStore.createIndex('party_id', 'party_id', { unique: false });
                    candidateStore.createIndex('serial_number', 'serial_number', { unique: false });
                }

                // Anchors Store
                if (!db.objectStoreNames.contains('anchors')) {
                    const anchorStore = db.createObjectStore('anchors', { keyPath: 'id', autoIncrement: true });
                    anchorStore.createIndex('candidate_id', 'candidate_id', { unique: false });
                    anchorStore.createIndex('voter_number', 'voter_number', { unique: false });
                }

                // Introducers Store
                if (!db.objectStoreNames.contains('introducers')) {
                    const introducerStore = db.createObjectStore('introducers', { keyPath: 'id', autoIncrement: true });
                    introducerStore.createIndex('anchor_id', 'anchor_id', { unique: false });
                    introducerStore.createIndex('voter_number', 'voter_number', { unique: false });
                }

                // Parties Store
                if (!db.objectStoreNames.contains('parties')) {
                    const partyStore = db.createObjectStore('parties', { keyPath: 'id', autoIncrement: true });
                    partyStore.createIndex('name', 'name', { unique: false });
                    partyStore.createIndex('serial_number', 'serial_number', { unique: true });
                }

                // Sync Queue Store (للتغييرات المعلقة)
                if (!db.objectStoreNames.contains('sync_queue')) {
                    const syncStore = db.createObjectStore('sync_queue', { keyPath: 'id', autoIncrement: true });
                    syncStore.createIndex('timestamp', 'timestamp', { unique: false });
                    syncStore.createIndex('status', 'status', { unique: false });
                }

                // Settings Store
                if (!db.objectStoreNames.contains('settings')) {
                    db.createObjectStore('settings', { keyPath: 'key' });
                }

                console.log('✅ Database schema created');
            };
        });
    }

    /**
     * Add data to store
     */
    async add(storeName, data) {
        const tx = this.db.transaction(storeName, 'readwrite');
        const store = tx.objectStore(storeName);

        // Add timestamp
        data.created_at = data.created_at || new Date().toISOString();
        data.updated_at = new Date().toISOString();
        data.synced = false;

        return new Promise((resolve, reject) => {
            const request = store.add(data);
            request.onsuccess = () => {
                // Add to sync queue
                this.addToSyncQueue('create', storeName, request.result, data);
                resolve(request.result);
            };
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Update data in store
     */
    async update(storeName, id, data) {
        const tx = this.db.transaction(storeName, 'readwrite');
        const store = tx.objectStore(storeName);

        return new Promise((resolve, reject) => {
            const getRequest = store.get(id);
            getRequest.onsuccess = () => {
                const existingData = getRequest.result;
                const updatedData = { ...existingData, ...data, updated_at: new Date().toISOString(), synced: false };

                const putRequest = store.put(updatedData);
                putRequest.onsuccess = () => {
                    // Add to sync queue
                    this.addToSyncQueue('update', storeName, id, updatedData);
                    resolve(putRequest.result);
                };
                putRequest.onerror = () => reject(putRequest.error);
            };
            getRequest.onerror = () => reject(getRequest.error);
        });
    }

    /**
     * Delete data from store
     */
    async delete(storeName, id) {
        const tx = this.db.transaction(storeName, 'readwrite');
        const store = tx.objectStore(storeName);

        return new Promise((resolve, reject) => {
            const request = store.delete(id);
            request.onsuccess = () => {
                // Add to sync queue
                this.addToSyncQueue('delete', storeName, id, null);
                resolve();
            };
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get by ID
     */
    async get(storeName, id) {
        const tx = this.db.transaction(storeName, 'readonly');
        const store = tx.objectStore(storeName);

        return new Promise((resolve, reject) => {
            const request = store.get(id);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get all from store
     */
    async getAll(storeName) {
        const tx = this.db.transaction(storeName, 'readonly');
        const store = tx.objectStore(storeName);

        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Search with index
     */
    async searchByIndex(storeName, indexName, value) {
        const tx = this.db.transaction(storeName, 'readonly');
        const store = tx.objectStore(storeName);
        const index = store.index(indexName);

        return new Promise((resolve, reject) => {
            const request = index.getAll(value);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Full text search (simple)
     */
    async search(storeName, searchTerm, fields = ['full_name']) {
        const allData = await this.getAll(storeName);
        const lowerSearch = searchTerm.toLowerCase();

        return allData.filter(item => {
            return fields.some(field => {
                const value = item[field];
                return value && value.toString().toLowerCase().includes(lowerSearch);
            });
        });
    }

    /**
     * Count records
     */
    async count(storeName) {
        const tx = this.db.transaction(storeName, 'readonly');
        const store = tx.objectStore(storeName);

        return new Promise((resolve, reject) => {
            const request = store.count();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Clear store
     */
    async clear(storeName) {
        const tx = this.db.transaction(storeName, 'readwrite');
        const store = tx.objectStore(storeName);

        return new Promise((resolve, reject) => {
            const request = store.clear();
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Add to sync queue
     */
    async addToSyncQueue(action, storeName, recordId, data) {
        const tx = this.db.transaction('sync_queue', 'readwrite');
        const store = tx.objectStore('sync_queue');

        const syncItem = {
            action: action,          // create, update, delete
            storeName: storeName,
            recordId: recordId,
            data: data,
            timestamp: new Date().toISOString(),
            status: 'pending',       // pending, syncing, synced, error
            retries: 0
        };

        return new Promise((resolve, reject) => {
            const request = store.add(syncItem);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get pending sync items
     */
    async getPendingSyncItems() {
        return await this.searchByIndex('sync_queue', 'status', 'pending');
    }

    /**
     * Export database to JSON
     */
    async exportToJSON() {
        const data = {};
        const stores = ['voters', 'candidates', 'anchors', 'introducers', 'parties'];

        for (const storeName of stores) {
            data[storeName] = await this.getAll(storeName);
        }

        data.exportDate = new Date().toISOString();
        data.version = this.version;

        return data;
    }

    /**
     * Import from JSON
     */
    async importFromJSON(jsonData) {
        const stores = ['voters', 'candidates', 'anchors', 'introducers', 'parties'];

        for (const storeName of stores) {
            if (jsonData[storeName]) {
                // Clear existing data
                await this.clear(storeName);

                // Add new data
                const tx = this.db.transaction(storeName, 'readwrite');
                const store = tx.objectStore(storeName);

                for (const item of jsonData[storeName]) {
                    store.add(item);
                }

                await new Promise((resolve, reject) => {
                    tx.oncomplete = () => resolve();
                    tx.onerror = () => reject(tx.error);
                });
            }
        }

        console.log('✅ Data imported successfully');
    }

    /**
     * Get statistics
     */
    async getStats() {
        return {
            voters: await this.count('voters'),
            candidates: await this.count('candidates'),
            anchors: await this.count('anchors'),
            introducers: await this.count('introducers'),
            parties: await this.count('parties'),
            pendingSync: await this.count('sync_queue')
        };
    }
}

// Global instance
const localDB = new LocalDB();

// Initialize on load
if (typeof window !== 'undefined') {
    window.addEventListener('DOMContentLoaded', async () => {
        try {
            await localDB.init();
            console.log('✅ Local database ready');

            // Dispatch event
            window.dispatchEvent(new CustomEvent('localdb-ready'));
        } catch (error) {
            console.error('❌ Database initialization failed:', error);
        }
    });
}
