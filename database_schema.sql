-- DICOM Analyzer Database Schema
-- This file contains the SQL statements to create all necessary tables
-- Run this file directly in your database (PostgreSQL/Supabase)

-- Enable UUID extension if not already enabled (for PostgreSQL/Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ⚠️  CRITICAL: STORAGE BUCKET CANNOT BE CREATED VIA SQL!
-- ⚠️  YOU MUST CREATE IT MANUALLY IN SUPABASE DASHBOARD AFTER RUNNING THIS SQL!
-- 
-- STEP 1: Run this SQL file to create all database tables
-- STEP 2: Go to Supabase Dashboard and create storage bucket manually
--
-- EXACT STEPS FOR STORAGE BUCKET CREATION:
-- 1. Open your Supabase project dashboard
-- 2. Click "Storage" in left sidebar  
-- 3. Click "Create a new bucket" button
-- 4. Enter these EXACT settings:
--    - Name: patient-reports
--    - Public: YES (toggle ON - this is CRITICAL!)
--    - File size limit: 50MB
--    - Allowed MIME types: application/pdf
-- 5. Click "Create bucket"
-- 6. IMPORTANT: Go to "Policies" tab and ensure these policies exist:
--    - Allow public read access
--    - Allow authenticated uploads
--    - Allow file updates/overwrites
--
-- After creating bucket, the PDF download will work automatically!

-- Table for storing DICOM analysis results
CREATE TABLE IF NOT EXISTS dicom_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- File Information
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT DEFAULT 0,
    file_hash VARCHAR(64),
    
    -- Patient Information
    patient_name VARCHAR(255),
    patient_id VARCHAR(100),
    patient_birth_date DATE,
    patient_sex VARCHAR(10),
    patient_age VARCHAR(20),
    
    -- Study Information
    study_date VARCHAR(20),
    study_time VARCHAR(20),
    study_description TEXT,
    study_instance_uid VARCHAR(255),
    series_description TEXT,
    series_number VARCHAR(20),
    
    -- Doctor/Institution Information
    referring_physician VARCHAR(255),
    performing_physician VARCHAR(255),
    institution_name VARCHAR(255),
    department_name VARCHAR(255),
    
    -- Analysis Results
    modality VARCHAR(10),
    body_part VARCHAR(100),
    confidence DECIMAL(5,4) DEFAULT 0.0,
    anatomical_landmarks JSON,
    pathologies JSON,
    recommendations JSON,
    
    -- Technical Information
    image_size JSON,
    pixel_spacing JSON,
    slice_thickness DECIMAL(10,4),
    
    -- Analysis Metadata
    analysis_timestamp TIMESTAMP WITH TIME ZONE,
    analyzer_version VARCHAR(20),
    ai_model_used VARCHAR(100)
);

-- Table for storing AI comprehensive analysis results
CREATE TABLE IF NOT EXISTS ai_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Related Analysis Information
    related_analyses JSON, -- Array of analysis IDs
    files_analyzed INTEGER DEFAULT 0,
    
    -- AI Analysis Results
    summary TEXT,
    clinical_insights JSON,
    differential_diagnosis JSON,
    recommendations JSON,
    risk_assessment TEXT,
    follow_up_plan TEXT,
    ai_confidence DECIMAL(5,4) DEFAULT 0.0,
    
    -- AI Metadata
    ai_model_used VARCHAR(100),
    analysis_timestamp TIMESTAMP WITH TIME ZONE
);

-- Table for storing patient reports for professional PDF generation
CREATE TABLE IF NOT EXISTS patient_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    report_date DATE DEFAULT CURRENT_DATE,
    
    -- Cleaned Patient Information
    patient_name VARCHAR(255) NOT NULL,
    patient_id VARCHAR(100),
    patient_sex VARCHAR(10),
    patient_age VARCHAR(20),
    study_date VARCHAR(20),
    
    -- Doctor Information
    doctor_name VARCHAR(255) DEFAULT 'DR.S KAR',
    
    -- Analysis Results
    body_part VARCHAR(100),
    confidence DECIMAL(5,4) DEFAULT 0.0,
    modality VARCHAR(10),
    study_description TEXT,
    anatomical_landmarks JSON,
    pathologies JSON,
    recommendations JSON,
    
    -- Report Status and Type
    report_status VARCHAR(20) DEFAULT 'pending', -- pending, completed, downloaded
    is_professional BOOLEAN DEFAULT TRUE,
    report_type VARCHAR(50) DEFAULT 'radiologist_report',
    
    -- Technical Information
    image_size JSON,
    pixel_spacing JSON,
    slice_thickness DECIMAL(10,4),
    
    -- Metadata
    analysis_timestamp TIMESTAMP WITH TIME ZONE,
    files_analyzed INTEGER DEFAULT 1,
    
    -- PDF Generation Information
    pdf_generated_at TIMESTAMP WITH TIME ZONE,
    pdf_downloaded_at TIMESTAMP WITH TIME ZONE,
    download_count INTEGER DEFAULT 0,
    
    -- Storage Bucket Information
    pdf_storage_bucket VARCHAR(100) DEFAULT 'patient-reports',
    pdf_storage_path VARCHAR(500), -- Path to PDF in storage bucket
    pdf_storage_url TEXT, -- Public/signed URL to download PDF
    pdf_file_size BIGINT, -- Size of PDF file in bytes
    pdf_mime_type VARCHAR(50) DEFAULT 'application/pdf'
);

-- Note: PDF files will be stored in Supabase Storage bucket 'patient-reports'
-- Only metadata is stored in the database, actual files are in storage bucket

-- Table for storing PDF report generation logs
CREATE TABLE IF NOT EXISTS report_generation_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Report Reference
    patient_report_id UUID REFERENCES patient_reports(id) ON DELETE CASCADE,
    
    -- Generation Information
    generation_type VARCHAR(50), -- 'ai_report', 'professional_report'
    status VARCHAR(20), -- 'started', 'completed', 'failed'
    error_message TEXT,
    generation_time_ms INTEGER,
    
    -- File Information
    pdf_filename VARCHAR(255),
    pdf_size_bytes BIGINT,
    
    -- User Information (if applicable)
    user_ip VARCHAR(45),
    user_agent TEXT
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_dicom_analyses_created_at ON dicom_analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dicom_analyses_patient_id ON dicom_analyses(patient_id);
CREATE INDEX IF NOT EXISTS idx_dicom_analyses_body_part ON dicom_analyses(body_part);
CREATE INDEX IF NOT EXISTS idx_dicom_analyses_modality ON dicom_analyses(modality);

CREATE INDEX IF NOT EXISTS idx_patient_reports_created_at ON patient_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_patient_reports_patient_id ON patient_reports(patient_id);
CREATE INDEX IF NOT EXISTS idx_patient_reports_status ON patient_reports(report_status);
CREATE INDEX IF NOT EXISTS idx_patient_reports_doctor ON patient_reports(doctor_name);

CREATE INDEX IF NOT EXISTS idx_ai_analyses_created_at ON ai_analyses(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_report_logs_created_at ON report_generation_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_logs_patient_report_id ON report_generation_logs(patient_report_id);

-- Views for easy data access
CREATE OR REPLACE VIEW patient_reports_summary AS
SELECT 
    pr.id,
    pr.created_at,
    pr.patient_name,
    pr.patient_id,
    pr.doctor_name,
    pr.body_part,
    pr.modality,
    pr.confidence,
    pr.report_status,
    pr.files_analyzed,
    pr.download_count,
    pr.pdf_downloaded_at,
    CASE 
        WHEN pr.pathologies::text != '[]' THEN 
            array_length(
                ARRAY(SELECT json_array_elements_text(pr.pathologies)), 1
            )
        ELSE 0 
    END as pathology_count
FROM patient_reports pr
ORDER BY pr.created_at DESC;

-- View for analysis statistics
CREATE OR REPLACE VIEW analysis_statistics AS
SELECT 
    COUNT(*) as total_analyses,
    COUNT(DISTINCT patient_id) as unique_patients,
    COUNT(DISTINCT body_part) as unique_body_parts,
    AVG(confidence) as avg_confidence,
    mode() WITHIN GROUP (ORDER BY body_part) as most_common_body_part,
    mode() WITHIN GROUP (ORDER BY modality) as most_common_modality,
    DATE_TRUNC('day', created_at) as analysis_date,
    COUNT(*) as daily_count
FROM dicom_analyses
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY analysis_date DESC;

-- Function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update updated_at timestamps
CREATE TRIGGER update_dicom_analyses_updated_at 
    BEFORE UPDATE ON dicom_analyses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_patient_reports_updated_at 
    BEFORE UPDATE ON patient_reports 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_analyses_updated_at 
    BEFORE UPDATE ON ai_analyses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies for Supabase
-- Enable RLS on all tables
ALTER TABLE dicom_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_generation_logs ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your authentication requirements)
-- For now, allowing all operations - you may want to restrict these based on your auth setup

CREATE POLICY "Allow all operations on dicom_analyses" ON dicom_analyses
FOR ALL USING (true);

CREATE POLICY "Allow all operations on ai_analyses" ON ai_analyses
FOR ALL USING (true);

CREATE POLICY "Allow all operations on patient_reports" ON patient_reports
FOR ALL USING (true);

CREATE POLICY "Allow all operations on report_generation_logs" ON report_generation_logs
FOR ALL USING (true);

-- Insert some sample data for testing (optional - remove if not needed)
-- INSERT INTO patient_reports (
--     patient_name, patient_id, patient_sex, patient_age, study_date,
--     doctor_name, body_part, confidence, modality, study_description,
--     anatomical_landmarks, pathologies, recommendations
-- ) VALUES (
--     'MOBARAK ALI', 'ERW45', 'M', '060Y', '05/17/2025',
--     'DR.S KAR', 'knee', 0.95, 'MR', 'Multi-file analysis (28 files)',
--     '["patella", "femur", "tibia", "meniscus"]',
--     '["no obvious abnormality detected"]',
--     '["clinical correlation required", "follow-up if symptoms persist"]'
-- );

-- Comments for documentation
COMMENT ON TABLE dicom_analyses IS 'Stores detailed DICOM analysis results from the AI analyzer';
COMMENT ON TABLE ai_analyses IS 'Stores comprehensive AI analysis results from Gemini/advanced AI models';
COMMENT ON TABLE patient_reports IS 'Stores cleaned patient data for professional radiologist report generation';
COMMENT ON TABLE report_generation_logs IS 'Logs all PDF report generation activities for auditing';

COMMENT ON COLUMN patient_reports.patient_name IS 'Cleaned patient name (doctor name removed)';
COMMENT ON COLUMN patient_reports.doctor_name IS 'Extracted doctor name (e.g., DR.S KAR)';
COMMENT ON COLUMN patient_reports.report_status IS 'Status: pending, completed, downloaded';
COMMENT ON COLUMN patient_reports.is_professional IS 'Flag indicating if this is for professional radiologist use';

-- Grant permissions (adjust based on your needs)
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Print completion message
DO $$
BEGIN
    RAISE NOTICE 'DICOM Analyzer database schema created successfully!';
    RAISE NOTICE 'Tables created: dicom_analyses, ai_analyses, patient_reports, report_generation_logs';
    RAISE NOTICE 'Views created: patient_reports_summary, analysis_statistics';
    RAISE NOTICE 'Indexes and triggers created for optimal performance';
    RAISE NOTICE 'Row Level Security enabled with permissive policies';
    RAISE NOTICE '';
    RAISE NOTICE '=== SETUP COMPLETE ===';
    RAISE NOTICE 'Your DICOM Analyzer database is ready!';
    RAISE NOTICE '';
    RAISE NOTICE '🚨 CRITICAL: DATABASE TABLES CREATED SUCCESSFULLY!';
    RAISE NOTICE '🚨 BUT YOU MUST CREATE STORAGE BUCKET MANUALLY!';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  NEXT STEP REQUIRED - STORAGE BUCKET:';
    RAISE NOTICE 'SQL CANNOT create storage buckets - you must do this manually:';
    RAISE NOTICE '';
    RAISE NOTICE '📋 EXACT STEPS:';
    RAISE NOTICE '1. Open Supabase project dashboard in browser';
    RAISE NOTICE '2. Click "Storage" in left sidebar';
    RAISE NOTICE '3. Click "Create a new bucket" button';
    RAISE NOTICE '4. Enter name: patient-reports';
    RAISE NOTICE '5. Toggle "Public bucket" to YES (CRITICAL!)';
    RAISE NOTICE '6. Set file size limit: 50MB';
    RAISE NOTICE '7. Add allowed MIME type: application/pdf';
    RAISE NOTICE '8. Click "Create bucket"';
    RAISE NOTICE '';
    RAISE NOTICE '✅ After bucket creation, PDF downloads will work automatically!';
END $$;

/*
🚨 IMPORTANT: SQL vs MANUAL SETUP 🚨

❌ WHAT SQL CANNOT DO:
   - Create Supabase Storage buckets
   - Set bucket permissions
   - Configure storage policies
   
✅ WHAT SQL CREATES:
   - All database tables (dicom_analyses, patient_reports, etc.)
   - Indexes for fast queries
   - Views for easy data access
   - Triggers for auto-updates
   - Row Level Security policies

🔧 WHAT YOU MUST DO MANUALLY:
   1. Run this SQL file → Creates all database tables ✅
   2. Go to Supabase Dashboard → Storage → Create bucket:
      - Name: patient-reports
      - Public: YES (CRITICAL!)
      - Size limit: 50MB  
      - MIME type: application/pdf
   3. App will work perfectly! ✅

💡 WHY MANUAL?
   Supabase Storage is a separate service from PostgreSQL.
   Storage buckets must be created via Dashboard or REST API, not SQL.
   
🎯 RESULT:
   Database stores PDF metadata, Storage bucket stores actual PDF files.
   Best of both worlds - fast queries + fast downloads!

*/
