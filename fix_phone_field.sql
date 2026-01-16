-- =====================================================
-- إصلاح حقل phone في جدول elections_voter
-- نفّذ هذا الملف مباشرة على PostgreSQL في Railway
-- =====================================================

-- الخطوة 1: زيادة طول حقل phone إلى 30 حرف
ALTER TABLE elections_voter 
ALTER COLUMN phone TYPE VARCHAR(30);

-- الخطوة 2: إزالة قيد unique من الحقل (إذا كان موجوداً)
ALTER TABLE elections_voter 
DROP CONSTRAINT IF EXISTS elections_voter_phone_key;

-- الخطوة 3: السماح بقيم null في الحقل
ALTER TABLE elections_voter 
ALTER COLUMN phone DROP NOT NULL;

-- =====================================================
-- بعد تنفيذ هذا الملف بنجاح، افتح الرابط التالي:
-- https://web-production-42c39.up.railway.app/tool/import-final-data/?secret=shems_voter_import_2024_secure
-- =====================================================
