/**
 * Barcode Scanner JavaScript - IHEC Style
 * نظام مسح الباركود لجرد الأصوات
 */

class BarcodeScanner {
    constructor() {
        this.html5QrCode = null;
        this.isScanning = false;
        this.sessionId = null;
        this.sessionCode = null;
        this.stats = {
            total: 0,
            successful: 0,
            failed: 0
        };

        this.init();
    }

    init() {
        // Initialize event listeners
        document.addEventListener('DOMContentLoaded', () => {
            this.setupEventListeners();
            this.checkActiveSession();
        });
    }

    setupEventListeners() {
        // Start/Stop scanning button
        const startBtn = document.getElementById('start-scan-btn');
        const stopBtn = document.getElementById('stop-scan-btn');
        const startSessionBtn = document.getElementById('start-session-btn');
        const endSessionBtn = document.getElementById('end-session-btn');

        if (startBtn) {
            startBtn.addEventListener('click', () => this.startScanning());
        }

        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopScanning());
        }

        if (startSessionBtn) {
            startSessionBtn.addEventListener('click', () => this.startSession());
        }

        if (endSessionBtn) {
            endSessionBtn.addEventListener('click', () => this.endSession());
        }

        // Manual barcode input
        const manualInput = document.getElementById('manual-barcode-input');
        const manualSubmit = document.getElementById('manual-submit-btn');

        if (manualInput && manualSubmit) {
            manualSubmit.addEventListener('click', () => {
                const barcodeData = manualInput.value.trim();
                if (barcodeData) {
                    this.processBarcode(barcodeData, 'MANUAL');
                    manualInput.value = '';
                }
            });

            manualInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    manualSubmit.click();
                }
            });
        }
    }

    checkActiveSession() {
        // Check if there's an active session from the server
        const sessionElement = document.getElementById('active-session-data');
        if (sessionElement) {
            this.sessionId = sessionElement.dataset.sessionId;
            this.sessionCode = sessionElement.dataset.sessionCode;

            if (this.sessionId) {
                this.updateUIForActiveSession(true);
            }
        }
    }

    async startSession() {
        const voteType = document.getElementById('vote-type-select')?.value || 'general';

        try {
            const response = await fetch('/barcode/api/session/start/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    vote_type: voteType
                })
            });

            const data = await response.json();

            if (data.success) {
                this.sessionId = data.session_id;
                this.sessionCode = data.session_code;

                this.showSuccess(`تم بدء جلسة المسح: ${data.session_code}`);
                this.updateUIForActiveSession(true);
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('فشل في بدء الجلسة: ' + error.message);
        }
    }

    async endSession() {
        if (!this.sessionId) {
            this.showError('لا توجد جلسة نشطة');
            return;
        }

        if (!confirm('هل أنت متأكد من إنهاء جلسة المسح؟')) {
            return;
        }

        try {
            const response = await fetch(`/barcode/api/session/${this.sessionId}/end/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('تم إنهاء الجلسة بنجاح');
                this.displaySessionStats(data.stats);

                this.sessionId = null;
                this.sessionCode = null;
                this.updateUIForActiveSession(false);

                // Optionally redirect to session detail
                setTimeout(() => {
                    window.location.href = '/barcode/sessions/';
                }, 2000);
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('فشل في إنهاء الجلسة: ' + error.message);
        }
    }

    async startScanning() {
        if (this.isScanning) {
            this.showWarning('المسح نشط بالفعل');
            return;
        }

        if (!this.sessionId) {
            this.showError('يجب بدء جلسة مسح أولاً');
            return;
        }

        const config = {
            fps: 10,
            qrbox: { width: 300, height: 150 },
            aspectRatio: 16 / 9,
            // Support multiple barcode formats
            formatsToSupport: [
                Html5QrcodeSupportedFormats.QR_CODE,
                Html5QrcodeSupportedFormats.CODE_128,
                Html5QrcodeSupportedFormats.CODE_39,
                Html5QrcodeSupportedFormats.EAN_13,
                Html5QrcodeSupportedFormats.EAN_8
            ]
        };

        this.html5QrCode = new Html5Qrcode("qr-reader");

        try {
            // المحاولة الأولى: الكاميرا الخلفية (environment)
            const config = {
                fps: 10,
                qrbox: { width: 250, height: 250 }, // مربع أصغر لتركيز أفضل
                aspectRatio: 1.0
            };

            // استخدام معرف الكاميرا الخلفية صراحة إذا أمكن
            const cameras = await Html5Qrcode.getCameras();
            if (cameras && cameras.length) {
                // محاولة العثور على الكاميرا الخلفية
                const backCamera = cameras.find(camera => camera.label.toLowerCase().includes('back') || camera.label.toLowerCase().includes('environment'));
                const cameraId = backCamera ? backCamera.id : cameras[0].id; // استخدام الخلفية أو الأولى

                await this.html5QrCode.start(
                    cameraId,
                    config,
                    (decodedText, decodedResult) => {
                        this.onScanSuccess(decodedText, decodedResult);
                    },
                    (errorMessage) => {
                        // تجاهل أخطاء المسح المستمرة
                    }
                );
            } else {
                // Fallback للطريقة العامة إذا لم نتمكن من جلب الكاميرات
                await this.html5QrCode.start(
                    { facingMode: { exact: "environment" } },
                    config,
                    (decodedText, decodedResult) => this.onScanSuccess(decodedText, decodedResult),
                    (errorMessage) => { }
                ).catch(async () => {
                    // إذا فشل exact environment، جرب أي كاميرا خلفية
                    await this.html5QrCode.start(
                        { facingMode: "environment" },
                        config,
                        (decodedText, decodedResult) => this.onScanSuccess(decodedText, decodedResult),
                        (errorMessage) => { }
                    );
                });
            }

            this.isScanning = true;
            this.updateScanningUI(true);
            this.showSuccess('تم تفعيل الكاميرا - ابدأ بمسح الباركود');

        } catch (err) {
            console.error(err);
            this.showError('فشل في تفعيل الكاميرا: يرجى التأكد من منح الصلاحية للمتصفح.');
            this.isScanning = false;
        }
    }

    async stopScanning() {
        if (!this.isScanning || !this.html5QrCode) {
            return;
        }

        try {
            await this.html5QrCode.stop();
            this.html5QrCode = null;
            this.isScanning = false;
            this.updateScanningUI(false);
            this.showInfo('تم إيقاف المسح');
        } catch (err) {
            this.showError('فشل في إيقاف الكاميرا: ' + err);
        }
    }

    async onScanSuccess(decodedText, decodedResult) {
        // Play beep sound
        this.playBeep();

        // Vibrate if supported
        if (navigator.vibrate) {
            navigator.vibrate(100);
        }

        // Show scanning indicator
        this.showScanningIndicator();

        // Process the barcode
        await this.processBarcode(decodedText, decodedResult.result.format?.formatName || 'UNKNOWN');
    }

    async processBarcode(barcodeData, barcodeType) {
        // Show processing state
        this.updateProcessingUI(true);

        try {
            const response = await fetch('/barcode/api/process/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    barcode_data: barcodeData,
                    barcode_type: barcodeType,
                    session_id: this.sessionId
                })
            });

            const data = await response.json();

            if (data.success) {
                this.handleScanSuccess(data);
            } else {
                this.handleScanError(data);
            }

        } catch (error) {
            this.showError('فشل في معالجة الباركود: ' + error.message);
        } finally {
            this.updateProcessingUI(false);
        }
    }

    handleScanSuccess(data) {
        // Update stats
        this.updateStats(data.session_stats);

        // Show result
        this.displayScanResult(data.data, data.validation, 'success');

        // Add to recent scans list
        this.addToRecentScans(data.data, data.status);

        // Success notification
        this.showSuccess(`تم مسح المحطة: ${data.data.full_station_code || 'غير محدد'}`);
    }

    handleScanError(data) {
        // عرض رسالة خطأ مفصلة
        let errorMessage = data.error || 'فشل في معالجة المسح';

        // إذا كان التكرار، أضف معلومات إضافية
        if (data.status === 'duplicate' && data.duplicate_details) {
            const details = data.duplicate_details;
            errorMessage += '\n\n';
            errorMessage += '📋 معلومات المسح السابق:\n';
            if (details.previous_session) {
                errorMessage += `• الجلسة: ${details.previous_session}\n`;
            }
            if (details.scan_date) {
                errorMessage += `• التاريخ: ${details.scan_date}\n`;
            }
            if (details.operator) {
                errorMessage += `• المشغل: ${details.operator}`;
            }
        }

        this.showError(errorMessage);

        // Still update stats if available
        if (data.session_stats) {
            this.updateStats(data.session_stats);
        }
    }

    displayScanResult(scanData, validation, status) {
        const resultContainer = document.getElementById('scan-result-display');
        if (!resultContainer) return;

        const statusClass = status === 'success' ? 'success' : 'error';
        const statusIcon = status === 'success' ? '✓' : '✗';

        let validationHTML = '';
        if (validation) {
            if (validation.warnings && validation.warnings.length > 0) {
                validationHTML = '<div class="warnings">';
                validation.warnings.forEach(warning => {
                    validationHTML += `<p class="warning">⚠ ${warning}</p>`;
                });
                validationHTML += '</div>';
            }

            if (validation.errors && validation.errors.length > 0) {
                validationHTML = '<div class="errors">';
                validation.errors.forEach(error => {
                    validationHTML += `<p class="error">✗ ${error}</p>`;
                });
                validationHTML += '</div>';
            }
        }

        resultContainer.innerHTML = `
            <div class="scan-result ${statusClass}">
                <div class="result-header">
                    <span class="status-icon">${statusIcon}</span>
                    <h3>نتيجة المسح</h3>
                </div>
                <div class="result-body">
                    <div class="result-row">
                        <span class="label">رقم المركز:</span>
                        <span class="value">${scanData.center_number || 'غير محدد'}</span>
                    </div>
                    <div class="result-row">
                        <span class="label">رقم المحطة:</span>
                        <span class="value">${scanData.station_number || 'غير محدد'}</span>
                    </div>
                    <div class="result-row">
                        <span class="label">الرمز الكامل:</span>
                        <span class="value highlight">${scanData.full_station_code || 'غير محدد'}</span>
                    </div>
                    ${scanData.polling_center ? `
                    <div class="result-row">
                        <span class="label">اسم المركز:</span>
                        <span class="value">${scanData.polling_center}</span>
                    </div>
                    ` : ''}
                    ${scanData.total_votes !== null ? `
                    <div class="result-row">
                        <span class="label">إجمالي الأصوات:</span>
                        <span class="value">${scanData.total_votes}</span>
                    </div>
                    ` : ''}
                    ${scanData.valid_votes !== null ? `
                    <div class="result-row">
                        <span class="label">أصوات صحيحة:</span>
                        <span class="value">${scanData.valid_votes}</span>
                    </div>
                    ` : ''}
                    ${scanData.invalid_votes !== null ? `
                    <div class="result-row">
                        <span class="label">أصوات باطلة:</span>
                        <span class="value">${scanData.invalid_votes}</span>
                    </div>
                    ` : ''}
                </div>
                ${validationHTML}
            </div>
        `;

        resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    addToRecentScans(scanData, status) {
        const recentList = document.getElementById('recent-scans-list');
        if (!recentList) return;

        const time = new Date().toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' });
        const statusClass = status === 'validated' ? 'success' : 'pending';
        const statusText = status === 'validated' ? 'تم التحقق' : 'قيد المعالجة';

        const scanItem = document.createElement('div');
        scanItem.className = `recent-scan-item ${statusClass}`;
        scanItem.innerHTML = `
            <div class="scan-time">${time}</div>
            <div class="scan-info">
                <strong>${scanData.full_station_code || 'غير محدد'}</strong>
                <span class="scan-status">${statusText}</span>
            </div>
        `;

        // Add to top of list
        recentList.insertBefore(scanItem, recentList.firstChild);

        // Keep only last 10 scans
        while (recentList.children.length > 10) {
            recentList.removeChild(recentList.lastChild);
        }
    }

    updateStats(stats) {
        this.stats = stats;

        // Update UI elements
        const totalEl = document.getElementById('stat-total-scans');
        const successEl = document.getElementById('stat-successful-scans');
        const failedEl = document.getElementById('stat-failed-scans');
        const rateEl = document.getElementById('stat-success-rate');

        if (totalEl) totalEl.textContent = stats.total_scans || 0;
        if (successEl) successEl.textContent = stats.successful || 0;
        if (failedEl) failedEl.textContent = stats.failed || 0;
        if (rateEl) rateEl.textContent = `${stats.success_rate || 0}%`;
    }

    displaySessionStats(stats) {
        const message = `
            <div class="session-stats">
                <h3>إحصائيات الجلسة</h3>
                <p>إجمالي المسحات: ${stats.total}</p>
                <p>ناجحة: ${stats.successful}</p>
                <p>فاشلة: ${stats.failed}</p>
                <p>مكررة: ${stats.duplicates}</p>
                <p>نسبة النجاح: ${stats.success_rate}%</p>
            </div>
        `;
        this.showInfo(message);
    }

    updateUIForActiveSession(isActive) {
        const startSessionBtn = document.getElementById('start-session-btn');
        const endSessionBtn = document.getElementById('end-session-btn');
        const scanControls = document.getElementById('scan-controls');
        const sessionInfo = document.getElementById('session-info-display');

        if (startSessionBtn) startSessionBtn.style.display = isActive ? 'none' : 'inline-block';
        if (endSessionBtn) endSessionBtn.style.display = isActive ? 'inline-block' : 'none';
        if (scanControls) scanControls.style.display = isActive ? 'block' : 'none';

        if (sessionInfo && isActive) {
            sessionInfo.innerHTML = `
                <div class="active-session-badge">
                    <span class="badge-icon">📷</span>
                    <span>جلسة نشطة: ${this.sessionCode}</span>
                </div>
            `;
        } else if (sessionInfo) {
            sessionInfo.innerHTML = '';
        }
    }

    updateScanningUI(isScanning) {
        const startBtn = document.getElementById('start-scan-btn');
        const stopBtn = document.getElementById('stop-scan-btn');
        const readerContainer = document.getElementById('qr-reader-container');

        if (startBtn) startBtn.style.display = isScanning ? 'none' : 'inline-block';
        if (stopBtn) stopBtn.style.display = isScanning ? 'inline-block' : 'none';
        if (readerContainer) readerContainer.classList.toggle('active', isScanning);
    }

    updateProcessingUI(isProcessing) {
        const processingIndicator = document.getElementById('processing-indicator');
        if (processingIndicator) {
            processingIndicator.style.display = isProcessing ? 'block' : 'none';
        }
    }

    showScanningIndicator() {
        const indicator = document.getElementById('scanning-flash');
        if (indicator) {
            indicator.classList.add('flash');
            setTimeout(() => indicator.classList.remove('flash'), 300);
        }
    }

    // Utility functions
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    playBeep() {
        // Create a simple beep sound
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.frequency.value = 800;
        oscillator.type = 'sine';

        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);

        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
    }

    // Notification functions
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showWarning(message) {
        this.showNotification(message, 'warning');
    }

    showInfo(message) {
        this.showNotification(message, 'info');
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container') || this.createNotificationContainer();

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = message;

        container.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }

    createNotificationContainer() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 10000;';
        document.body.appendChild(container);
        return container;
    }
}

// Initialize the scanner
const barcodeScanner = new BarcodeScanner();
