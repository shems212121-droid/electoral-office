/**
 * Voter Auto-fill Utility
 * Automatically fills form fields when a valid voter number is entered
 * Version: 2.0
 * Last Updated: 2026-01-15
 */

(function () {
    'use strict';

    // Configuration
    const CONFIG = {
        minLength: 3,           // Minimum characters before triggering lookup
        debounceDelay: 500,     // Milliseconds to wait after user stops typing
        successDisplayTime: 3000, // How long to show success message
        apiEndpoint: '/api/voter-lookup/',
    };

    // Arabic to English numeral mapping
    const ARABIC_TO_ENGLISH = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    };

    /**
     * Normalizes Arabic numerals to English
     */
    function normalizeArabicNumerals(text) {
        let normalized = text;
        for (const [arabic, english] of Object.entries(ARABIC_TO_ENGLISH)) {
            normalized = normalized.replace(new RegExp(arabic, 'g'), english);
        }
        return normalized;
    }

    /**
     * Maps API response fields to form input names
     */
    const FIELD_MAPPING = {
        // Basic Info
        'full_name': 'full_name',
        'date_of_birth': 'date_of_birth',
        'phone': 'phone',
        'family_number': 'family_number',

        // Voting Center Info
        'voting_center_name': 'voting_center_name',
        'voting_center_number': 'voting_center_number',
        'station_number': 'station_number',

        // Registration Center Info
        'registration_center_name': 'registration_center_name',
        'registration_center_number': 'registration_center_number',

        // Location Info
        'governorate': 'governorate',
        'section': 'section',
        'district': 'district',

        // Additional fields
        'polling_center_name': 'polling_center_name',
        'polling_center_number': 'polling_center_number',
    };

    /**
     * UI Element selectors
     */
    function getUIElements() {
        return {
            voterInput: document.querySelector('input[name="voter_number"]'),
            spinner: document.getElementById('voterLookupSpinner'),
            errorDiv: document.getElementById('voterLookupError'),
            successDiv: document.getElementById('voterLookupSuccess')
        };
    }

    /**
     * Shows/hides UI elements
     */
    function showElement(element, show = true) {
        if (element) {
            element.style.display = show ? 'block' : 'none';
        }
    }

    function showSpinner(element, show = true) {
        if (element) {
            element.style.display = show ? 'inline-block' : 'none';
        }
    }

    /**
     * Fills form fields with voter data
     */
    function fillFormFields(data) {
        let filledCount = 0;

        for (const [apiField, formField] of Object.entries(FIELD_MAPPING)) {
            const value = data[apiField];
            if (value === null || value === undefined || value === '') {
                continue;
            }

            // Try different selector strategies
            const selectors = [
                `input[name="${formField}"]`,
                `select[name="${formField}"]`,
                `textarea[name="${formField}"]`,
                `#id_${formField}`
            ];

            for (const selector of selectors) {
                const element = document.querySelector(selector);
                if (element) {
                    // Don't overwrite phone if user already entered something
                    if (formField === 'phone' && element.value.trim()) {
                        continue;
                    }

                    element.value = value;
                    filledCount++;

                    // Trigger change event for any listeners
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    break;
                }
            }
        }

        console.log(`✅ Voter Auto-fill: ${filledCount} fields filled successfully`);
        return filledCount;
    }

    /**
     * Performs the voter lookup API call
     */
    async function performVoterLookup(voterNumber, ui) {
        showSpinner(ui.spinner, true);
        showElement(ui.errorDiv, false);
        showElement(ui.successDiv, false);

        try {
            const response = await fetch(
                `${CONFIG.apiEndpoint}?voter_number=${encodeURIComponent(voterNumber)}`
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'خطأ في البحث عن رقم الناخب');
            }

            const data = await response.json();
            const filledCount = fillFormFields(data);

            showSpinner(ui.spinner, false);

            if (filledCount > 0) {
                showElement(ui.successDiv, true);
                setTimeout(() => showElement(ui.successDiv, false), CONFIG.successDisplayTime);
            } else {
                throw new Error('لم يتم العثور على بيانات كافية للناخب');
            }

        } catch (error) {
            console.error('❌ Voter lookup error:', error);
            showSpinner(ui.spinner, false);

            if (ui.errorDiv) {
                ui.errorDiv.textContent = error.message;
                showElement(ui.errorDiv, true);
            }
        }
    }

    /**
     * Initializes the voter auto-fill functionality
     */
    function initVoterAutofill() {
        const ui = getUIElements();

        if (!ui.voterInput) {
            console.warn('⚠️ Voter number input not found. Auto-fill will not be initialized.');
            return;
        }

        console.log('✅ Voter Auto-fill initialized');

        let lookupTimeout = null;

        ui.voterInput.addEventListener('input', function () {
            // Clear previous timeout
            if (lookupTimeout) {
                clearTimeout(lookupTimeout);
            }

            // Normalize and clean input
            let voterNumber = this.value.trim();
            voterNumber = normalizeArabicNumerals(voterNumber);

            // Update input with normalized value
            if (this.value !== voterNumber) {
                this.value = voterNumber;
            }

            // Hide previous messages
            showElement(ui.errorDiv, false);
            showElement(ui.successDiv, false);

            // Check minimum length
            if (voterNumber.length < CONFIG.minLength) {
                return;
            }

            // Debounce the lookup
            lookupTimeout = setTimeout(() => {
                performVoterLookup(voterNumber, ui);
            }, CONFIG.debounceDelay);
        });
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initVoterAutofill);
    } else {
        initVoterAutofill();
    }

})();
