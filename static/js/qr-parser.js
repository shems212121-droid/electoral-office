/**
 * محلل بيانات QR للمفوضية العليا المستقلة للانتخابات في العراق
 * Iraqi High Electoral Commission QR Code Parser
 */

class IHECQRParser {
    constructor() {
        this.votingTypes = {
            '1': 'special',  // تصويت خاص
            '2': 'general'   // تصويت عام
        };
    }

    /**
     * تحليل بيانات QR code
     * @param {string} qrText - النص المقروء من QR code
     * @returns {object} - البيانات المحللة
     */
    parse(qrText) {
        try {
            const parts = qrText.split('-');

            if (parts.length < 5) {
                throw new Error('تنسيق QR code غير صحيح');
            }

            const votingType = parts[0];
            const centerNumber = parts[1];
            const dataType = parts[2];
            const stationNumber = parts[3];
            const encodedData = parts.slice(4).join('-'); // البيانات المشفرة قد تحتوي على -

            // فك تشفير البيانات
            const decodedVotes = this.decodeVoteData(encodedData);

            return {
                success: true,
                votingType: this.votingTypes[votingType] || 'unknown',
                centerNumber: centerNumber,
                stationNumber: stationNumber,
                votes: decodedVotes,
                rawData: qrText
            };
        } catch (error) {
            console.error('خطأ في تحليل QR:', error);
            return {
                success: false,
                error: error.message,
                rawData: qrText
            };
        }
    }

    /**
     * فك تشفير بيانات الأصوات من Base64
     * @param {string} encodedData - البيانات المشفرة
     * @returns {array} - قائمة الأصوات
     */
    decodeVoteData(encodedData) {
        try {
            // محاولة فك تشفير Base64
            const binaryString = atob(encodedData);
            const bytes = new Uint8Array(binaryString.length);

            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }

            // تحليل البيانات الثنائية
            return this.parseBinaryVoteData(bytes);
        } catch (error) {
            console.error('خطأ في فك التشفير:', error);
            return [];
        }
    }

    /**
     * تحليل البيانات الثنائية للأصوات
     * @param {Uint8Array} bytes - البيانات الثنائية
     * @returns {array} - قائمة الأصوات
     */
    parseBinaryVoteData(bytes) {
        const votes = [];

        // هذا مثال افتراضي - التنسيق الفعلي يحتاج للمواصفات الرسمية من المفوضية
        // Format assumption: [candidate_id (2 bytes), vote_count (4 bytes)]

        try {
            let offset = 0;

            while (offset + 6 <= bytes.length) {
                // قراءة معرف المرشح (2 bytes)
                const candidateId = (bytes[offset] << 8) | bytes[offset + 1];
                offset += 2;

                // قراءة عدد الأصوات (4 bytes, little-endian)
                const voteCount = bytes[offset] |
                    (bytes[offset + 1] << 8) |
                    (bytes[offset + 2] << 16) |
                    (bytes[offset + 3] << 24);
                offset += 4;

                if (candidateId > 0 && voteCount >= 0) {
                    votes.push({
                        candidateId: candidateId,
                        voteCount: voteCount
                    });
                }
            }
        } catch (error) {
            console.error('خطأ في تحليل البيانات الثنائية:', error);
        }

        return votes;
    }

    /**
     * إنشاء بيانات تجريبية للاختبار
     * @param {string} qrText - النص من QR
     * @returns {object} - بيانات تجريبية
     */
    createMockData(qrText) {
        const parts = qrText.split('-');

        return {
            success: true,
            votingType: this.votingTypes[parts[0]] || 'general',
            centerNumber: parts[1],
            stationNumber: parts[3],
            votes: [
                // بيانات تجريبية - يجب استخدام البيانات الحقيقية من فك التشفير
                { candidateId: 114, voteCount: 45 },
                { candidateId: 115, voteCount: 32 },
                { candidateId: 116, voteCount: 28 },
                { candidateId: 117, voteCount: 15 },
            ],
            rawData: qrText,
            isMockData: true
        };
    }
}

// تصدير للاستخدام العام
window.IHECQRParser = IHECQRParser;
