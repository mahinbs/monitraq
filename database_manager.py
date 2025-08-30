#!/usr/bin/env python3
"""
Supabase Database Manager for DICOM Analyzer
Handles all database operations for storing analysis results and history
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import uuid

from supabase import create_client, Client
from dotenv import load_dotenv
import io

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages Supabase database operations for DICOM analysis"""

    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')

        if not self.supabase_url or not self.supabase_key:
            logger.warning(
                "Supabase credentials not found. Database features will be disabled.")
            self.client = None
            return

        try:
            self.client: Client = create_client(
                self.supabase_url, self.supabase_key)
            logger.info("Supabase client initialized successfully")
            self._initialize_tables()
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None

    def _initialize_tables(self):
        """Create database tables if they don't exist"""
        if not self.client:
            return

        try:
            # Check if tables exist by trying to select from them
            # If they don't exist, Supabase will create them automatically when we insert data

            # Create patient_reports table for professional PDF generation
            self._create_patient_reports_table()
            logger.info("Database tables initialized")
        except Exception as e:
            logger.error(f"Error initializing tables: {e}")

    def _create_patient_reports_table(self):
        """Create patient reports table for storing professional reports"""
        try:
            # This table will store patient data for professional radiologist reports
            # The table structure will be created automatically by Supabase when we first insert data
            logger.info("Patient reports table structure ready")
        except Exception as e:
            logger.error(f"Error creating patient reports table: {e}")

    def save_analysis_result(self, analysis_result: Dict[str, Any], file_info: Dict[str, Any]) -> Optional[str]:
        """
        Save analysis result to database

        Args:
            analysis_result: The analysis result from DICOM analyzer
            file_info: File information (name, size, etc.)

        Returns:
            str: Record ID if successful, None if failed
        """
        if not self.client:
            logger.warning("Database not available. Skipping save operation.")
            return None

        try:
            # Generate unique ID
            record_id = str(uuid.uuid4())

            # Prepare data for database
            db_record = {
                'id': record_id,
                'created_at': datetime.now().isoformat(),
                'filename': file_info.get('filename', 'unknown'),
                'file_size': file_info.get('file_size', 0),
                'file_hash': file_info.get('file_hash', ''),

                # Patient Information
                'patient_name': analysis_result.get('patient_info', {}).get('name', 'Unknown'),
                'patient_id': analysis_result.get('patient_info', {}).get('id', 'Unknown'),
                'patient_birth_date': analysis_result.get('patient_info', {}).get('birth_date', None),
                'patient_sex': analysis_result.get('patient_info', {}).get('sex', 'Unknown'),
                'patient_age': analysis_result.get('patient_info', {}).get('age', None),

                # Study Information
                'study_date': analysis_result.get('patient_info', {}).get('study_date', 'Unknown'),
                'study_time': analysis_result.get('patient_info', {}).get('study_time', None),
                'study_description': analysis_result.get('study_description', 'Unknown'),
                'study_instance_uid': analysis_result.get('patient_info', {}).get('study_instance_uid', None),
                'series_description': analysis_result.get('patient_info', {}).get('series_description', None),
                'series_number': analysis_result.get('patient_info', {}).get('series_number', None),

                # Doctor/Institution Information
                'referring_physician': analysis_result.get('patient_info', {}).get('referring_physician', 'Unknown'),
                'performing_physician': analysis_result.get('patient_info', {}).get('performing_physician', 'Unknown'),
                'institution_name': analysis_result.get('patient_info', {}).get('institution_name', 'Unknown'),
                'department_name': analysis_result.get('patient_info', {}).get('department_name', 'Unknown'),

                # Analysis Results
                'modality': analysis_result.get('modality', 'Unknown'),
                'body_part': analysis_result.get('body_part', 'Unknown'),
                'confidence': analysis_result.get('confidence', 0.0),
                'anatomical_landmarks': json.dumps(analysis_result.get('anatomical_landmarks', [])),
                'pathologies': json.dumps(analysis_result.get('pathologies', [])),
                'recommendations': json.dumps(analysis_result.get('recommendations', [])),

                # Technical Information
                'image_size': json.dumps(analysis_result.get('image_size', [])),
                'pixel_spacing': json.dumps(analysis_result.get('pixel_spacing', [])),
                'slice_thickness': analysis_result.get('slice_thickness', None),

                # Analysis metadata
                'analysis_timestamp': analysis_result.get('analysis_timestamp', datetime.now().isoformat()),
                'analyzer_version': '2.0',
                'ai_model_used': 'OpenAI GPT-4 Vision'
            }

            # Insert into database
            result = self.client.table(
                'dicom_analyses').insert(db_record).execute()

            if result.data:
                logger.info(
                    f"Analysis result saved to database with ID: {record_id}")
                return record_id
            else:
                logger.error("Failed to save analysis result to database")
                return None

        except Exception as e:
            logger.error(f"Error saving analysis result: {e}")
            return None

    def save_ai_analysis(self, ai_analysis: Dict[str, Any], analysis_ids: List[str]) -> Optional[str]:
        """
        Save comprehensive AI analysis result

        Args:
            ai_analysis: AI analysis result from Gemini
            analysis_ids: List of related analysis record IDs

        Returns:
            str: AI analysis record ID if successful
        """
        if not self.client:
            return None

        try:
            record_id = str(uuid.uuid4())

            db_record = {
                'id': record_id,
                'created_at': datetime.now().isoformat(),
                'related_analyses': json.dumps(analysis_ids),
                'files_analyzed': ai_analysis.get('files_analyzed', 0),
                'summary': ai_analysis.get('summary', ''),
                'clinical_insights': json.dumps(ai_analysis.get('clinical_insights', [])),
                'differential_diagnosis': json.dumps(ai_analysis.get('differential_diagnosis', [])),
                'recommendations': json.dumps(ai_analysis.get('recommendations', [])),
                'risk_assessment': ai_analysis.get('risk_assessment', ''),
                'follow_up_plan': ai_analysis.get('follow_up_plan', ''),
                'ai_confidence': ai_analysis.get('ai_confidence', 0.0),
                'ai_model_used': 'Google Gemini',
                'analysis_timestamp': ai_analysis.get('analysis_timestamp', datetime.now().isoformat())
            }

            result = self.client.table(
                'ai_analyses').insert(db_record).execute()

            if result.data:
                logger.info(
                    f"AI analysis saved to database with ID: {record_id}")
                return record_id
            else:
                logger.error("Failed to save AI analysis to database")
                return None

        except Exception as e:
            logger.error(f"Error saving AI analysis: {e}")
            return None

    def save_patient_report(self, analysis_result: Dict[str, Any], doctor_name: str = None) -> Optional[str]:
        """
        Save patient data for professional radiologist report generation

        Args:
            analysis_result: The analysis result from DICOM analyzer
            doctor_name: Doctor name extracted from patient data

        Returns:
            str: Report ID if successful, None if failed
        """
        if not self.client:
            logger.warning(
                "Database not available. Skipping patient report save.")
            return None

        try:
            # Generate unique report ID
            report_id = str(uuid.uuid4())

            # Extract patient info
            patient_info = analysis_result.get('patient_info', {})

            # Clean patient name (remove doctor name part)
            raw_name = patient_info.get('name', 'Unknown')
            clean_patient_name = self._clean_patient_name(raw_name)

            # Extract doctor name from raw name if not provided
            if not doctor_name:
                doctor_name = self._extract_doctor_name(raw_name)

            # Prepare patient report data
            report_data = {
                'id': report_id,
                'created_at': datetime.now().isoformat(),
                'report_date': datetime.now().strftime('%Y-%m-%d'),

                # Cleaned Patient Information
                'patient_name': clean_patient_name,
                'patient_id': patient_info.get('patient_id', 'Unknown'),
                'patient_sex': patient_info.get('sex', 'Unknown'),
                'patient_age': patient_info.get('age', 'Unknown'),
                'study_date': patient_info.get('study_date', 'Unknown'),

                # Doctor Information
                'doctor_name': doctor_name,

                # Analysis Results
                'body_part': analysis_result.get('body_part', 'Unknown'),
                'confidence': analysis_result.get('confidence', 0.0),
                'modality': analysis_result.get('modality', 'Unknown'),
                'study_description': analysis_result.get('study_description', 'Unknown'),
                'anatomical_landmarks': json.dumps(analysis_result.get('anatomical_landmarks', [])),
                'pathologies': json.dumps(analysis_result.get('pathologies', [])),
                'recommendations': json.dumps(analysis_result.get('recommendations', [])),

                # Report Status
                'report_status': 'pending',  # pending, completed, downloaded
                'is_professional': True,
                'report_type': 'radiologist_report',

                # Technical Information
                'image_size': json.dumps(analysis_result.get('image_size', [])),
                'pixel_spacing': json.dumps(analysis_result.get('pixel_spacing', [])),
                'slice_thickness': analysis_result.get('slice_thickness', None),

                # Metadata
                'analysis_timestamp': analysis_result.get('analysis_timestamp', datetime.now().isoformat()),
                'files_analyzed': analysis_result.get('file_count', 1)
            }

            # Insert into patient_reports table
            result = self.client.table(
                'patient_reports').insert(report_data).execute()

            if result.data:
                logger.info(f"Patient report saved with ID: {report_id}")
                return report_id
            else:
                logger.error("Failed to save patient report to database")
                return None

        except Exception as e:
            logger.error(f"Error saving patient report: {e}")
            return None

    def _clean_patient_name(self, raw_name: str) -> str:
        """Clean patient name by removing doctor name part"""
        if not raw_name or raw_name == 'Unknown':
            return 'Unknown'

        # Extract just the first part before any "DR." appears
        parts = raw_name.split(' DR.')
        if len(parts) > 0:
            return parts[0].strip()

        # Alternative pattern
        parts = raw_name.split('DR ')
        if len(parts) > 0:
            return parts[0].strip()

        return raw_name.strip()

    def _extract_doctor_name(self, raw_name: str) -> str:
        """Extract doctor name from patient name field"""
        if not raw_name or raw_name == 'Unknown':
            return 'DR.S KAR'

        # Look for "DR." pattern and extract what comes after
        if 'DR.' in raw_name.upper():
            parts = raw_name.upper().split('DR.')
            if len(parts) > 1:
                doctor_part = parts[1].strip()
                if doctor_part:
                    return f"DR.{doctor_part}"

        # Look for "DR " pattern
        if 'DR ' in raw_name.upper():
            parts = raw_name.upper().split('DR ')
            if len(parts) > 1:
                doctor_part = parts[1].strip()
                if doctor_part:
                    return f"DR {doctor_part}"

        # Default fallback
        return 'DR.S KAR'

    def get_patient_reports(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get patient reports for PDF generation

        Args:
            limit: Number of records to return
            offset: Number of records to skip

        Returns:
            List of patient report records
        """
        if not self.client:
            return []

        try:
            result = self.client.table('patient_reports')\
                .select('*')\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error fetching patient reports: {e}")
            return []

    def get_patient_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific patient report by ID

        Args:
            report_id: Report ID to fetch

        Returns:
            Patient report data or None
        """
        if not self.client:
            return None

        try:
            result = self.client.table('patient_reports')\
                .select('*')\
                .eq('id', report_id)\
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error fetching patient report {report_id}: {e}")
            return None

    def update_report_status(self, report_id: str, status: str) -> bool:
        """
        Update report status (pending, completed, downloaded)

        Args:
            report_id: Report ID to update
            status: New status

        Returns:
            bool: True if successful
        """
        if not self.client:
            return False

        try:
            result = self.client.table('patient_reports')\
                .update({'report_status': status, 'updated_at': datetime.now().isoformat()})\
                .eq('id', report_id)\
                .execute()

            return result.data is not None

        except Exception as e:
            logger.error(f"Error updating report status: {e}")
            return False

    def get_analysis_history(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get analysis history with pagination

        Args:
            limit: Number of records to return
            offset: Number of records to skip

        Returns:
            List of analysis records
        """
        if not self.client:
            return []

        try:
            result = self.client.table('dicom_analyses')\
                .select('*')\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()

            if result.data:
                # Parse JSON fields back to lists
                for record in result.data:
                    record['anatomical_landmarks'] = json.loads(
                        record.get('anatomical_landmarks', '[]'))
                    record['pathologies'] = json.loads(
                        record.get('pathologies', '[]'))
                    record['recommendations'] = json.loads(
                        record.get('recommendations', '[]'))
                    record['image_size'] = json.loads(
                        record.get('image_size', '[]'))
                    record['pixel_spacing'] = json.loads(
                        record.get('pixel_spacing', '[]'))

                return result.data
            return []

        except Exception as e:
            logger.error(f"Error getting analysis history: {e}")
            return []

    def get_analysis_by_category(self, category_type: str, category_value: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get analyses filtered by category (body_part, modality, patient_id, etc.)

        Args:
            category_type: Type of category (body_part, modality, patient_id, etc.)
            category_value: Value to filter by
            limit: Number of records to return

        Returns:
            List of filtered analysis records
        """
        if not self.client:
            return []

        try:
            result = self.client.table('dicom_analyses')\
                .select('*')\
                .eq(category_type, category_value)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()

            if result.data:
                # Parse JSON fields
                for record in result.data:
                    record['anatomical_landmarks'] = json.loads(
                        record.get('anatomical_landmarks', '[]'))
                    record['pathologies'] = json.loads(
                        record.get('pathologies', '[]'))
                    record['recommendations'] = json.loads(
                        record.get('recommendations', '[]'))

                return result.data
            return []

        except Exception as e:
            logger.error(f"Error getting analysis by category: {e}")
            return []

    def get_analysis_statistics(self) -> Dict[str, Any]:
        """
        Get analysis statistics for dashboard

        Returns:
            Dictionary with various statistics
        """
        if not self.client:
            return {}

        try:
            # Get total count
            total_result = self.client.table('dicom_analyses').select(
                'id', count='exact').execute()
            total_analyses = len(total_result.data) if total_result.data else 0

            # Get body part distribution
            body_parts_result = self.client.table('dicom_analyses')\
                .select('body_part')\
                .execute()

            body_part_counts = {}
            modality_counts = {}

            if body_parts_result.data:
                for record in body_parts_result.data:
                    body_part = record.get('body_part', 'Unknown')
                    body_part_counts[body_part] = body_part_counts.get(
                        body_part, 0) + 1

            # Get modality distribution
            modality_result = self.client.table('dicom_analyses')\
                .select('modality')\
                .execute()

            if modality_result.data:
                for record in modality_result.data:
                    modality = record.get('modality', 'Unknown')
                    modality_counts[modality] = modality_counts.get(
                        modality, 0) + 1

            return {
                'total_analyses': total_analyses,
                'body_part_distribution': body_part_counts,
                'modality_distribution': modality_counts,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    def search_analyses(self, search_term: str, search_fields: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search analyses by various fields

        Args:
            search_term: Term to search for
            search_fields: Fields to search in (default: patient_name, patient_id, study_description)

        Returns:
            List of matching analysis records
        """
        if not self.client:
            return []

        if search_fields is None:
            search_fields = ['patient_name', 'patient_id',
                             'study_description', 'referring_physician']

        try:
            # Build search query (this is a simplified version - Supabase supports more complex searches)
            results = []

            for field in search_fields:
                result = self.client.table('dicom_analyses')\
                    .select('*')\
                    .ilike(field, f'%{search_term}%')\
                    .order('created_at', desc=True)\
                    .limit(20)\
                    .execute()

                if result.data:
                    results.extend(result.data)

            # Remove duplicates based on ID
            unique_results = []
            seen_ids = set()

            for record in results:
                if record['id'] not in seen_ids:
                    # Parse JSON fields
                    record['anatomical_landmarks'] = json.loads(
                        record.get('anatomical_landmarks', '[]'))
                    record['pathologies'] = json.loads(
                        record.get('pathologies', '[]'))
                    record['recommendations'] = json.loads(
                        record.get('recommendations', '[]'))

                    unique_results.append(record)
                    seen_ids.add(record['id'])

            return unique_results

        except Exception as e:
            logger.error(f"Error searching analyses: {e}")
            return []

    def delete_analysis(self, analysis_id: str) -> bool:
        """
        Delete an analysis record

        Args:
            analysis_id: ID of the analysis to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            result = self.client.table('dicom_analyses')\
                .delete()\
                .eq('id', analysis_id)\
                .execute()

            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Error deleting analysis: {e}")
            return False

    def is_available(self) -> bool:
        """Check if database is available"""
        return self.client is not None

    def upload_pdf_to_storage(self, pdf_content: bytes, filename: str, bucket_name: str = "patient-reports") -> Optional[Dict[str, str]]:
        """
        Upload PDF file to Supabase Storage bucket

        Args:
            pdf_content: PDF file content as bytes
            filename: Name for the file in storage
            bucket_name: Storage bucket name

        Returns:
            Dict with storage info (path, public_url) or None if failed
        """
        if not self.client:
            logger.warning("Database not available for storage upload")
            return None

        try:
            # Upload file to storage bucket with proper options
            result = self.client.storage.from_(bucket_name).upload(
                path=filename,
                file=pdf_content,
                file_options={
                    "content-type": "application/pdf",
                    "upsert": "true"  # Must be string, not boolean
                }
            )

            if result:
                # Get public URL
                public_url = self.client.storage.from_(
                    bucket_name).get_public_url(filename)

                logger.info(f"PDF uploaded successfully to: {public_url}")
                return {
                    "storage_path": filename,
                    "public_url": public_url,
                    "bucket_name": bucket_name,
                    "file_size": len(pdf_content)
                }
            else:
                logger.error(
                    "Failed to upload PDF to storage - no result returned")
                return None

        except Exception as e:
            logger.error(f"Error uploading PDF to storage: {e}")
            # Try alternative upload method
            try:
                # Alternative: use update method if upload fails
                result = self.client.storage.from_(bucket_name).update(
                    path=filename,
                    file=pdf_content,
                    file_options={"content-type": "application/pdf"}
                )

                if result:
                    public_url = self.client.storage.from_(
                        bucket_name).get_public_url(filename)
                    logger.info(f"PDF updated successfully to: {public_url}")
                    return {
                        "storage_path": filename,
                        "public_url": public_url,
                        "bucket_name": bucket_name,
                        "file_size": len(pdf_content)
                    }
            except Exception as e2:
                logger.error(f"Alternative upload method also failed: {e2}")

            return None

    def update_patient_report_with_storage_info(self, report_id: str, storage_info: Dict[str, str]) -> bool:
        """
        Update patient report with storage bucket information

        Args:
            report_id: Patient report ID
            storage_info: Storage information from upload

        Returns:
            bool: True if successful
        """
        if not self.client:
            return False

        try:
            update_data = {
                'pdf_storage_bucket': storage_info.get('bucket_name'),
                'pdf_storage_path': storage_info.get('storage_path'),
                'pdf_storage_url': storage_info.get('public_url'),
                'pdf_file_size': storage_info.get('file_size'),
                'pdf_generated_at': datetime.now().isoformat(),
                'report_status': 'completed',
                'updated_at': datetime.now().isoformat()
            }

            result = self.client.table('patient_reports')\
                .update(update_data)\
                .eq('id', report_id)\
                .execute()

            return result.data is not None

        except Exception as e:
            logger.error(
                f"Error updating patient report with storage info: {e}")
            return False

    def get_pdf_download_url(self, report_id: str) -> Optional[str]:
        """
        Get PDF download URL for a patient report

        Args:
            report_id: Patient report ID

        Returns:
            Download URL or None
        """
        if not self.client:
            return None

        try:
            # Get report data
            result = self.client.table('patient_reports')\
                .select('pdf_storage_bucket, pdf_storage_path, pdf_storage_url')\
                .eq('id', report_id)\
                .execute()

            if result.data and len(result.data) > 0:
                report_data = result.data[0]

                # Return existing public URL if available
                if report_data.get('pdf_storage_url'):
                    return report_data['pdf_storage_url']

                # Generate new URL if path exists
                bucket = report_data.get(
                    'pdf_storage_bucket', 'patient-reports')
                path = report_data.get('pdf_storage_path')

                if path:
                    return self.client.storage.from_(bucket).get_public_url(path)

            return None

        except Exception as e:
            logger.error(f"Error getting PDF download URL: {e}")
            return None


# Global database manager instance
db_manager = DatabaseManager()
