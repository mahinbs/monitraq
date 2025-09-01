"""
Patient Session Manager - Critical medical data isolation
"""

import uuid
import hashlib
import time
from datetime import datetime
import threading

class PatientSessionManager:
    """Manages isolated patient sessions to prevent data contamination"""
    
    def __init__(self):
        self.active_sessions = {}
        self.session_lock = threading.Lock()
        self.cleanup_interval = 3600  # 1 hour session timeout
    
    def create_patient_session(self, patient_name, patient_id, study_date, body_part, filename):
        """Create a unique isolated session for a patient"""
        
        # Generate unique session ID components
        timestamp = int(time.time() * 1000)  # Millisecond precision
        session_uuid = str(uuid.uuid4())
        
        # Create patient identifier hash for privacy
        patient_data = f"{patient_name}_{patient_id}_{study_date}_{body_part}"
        patient_hash = hashlib.sha256(patient_data.encode()).hexdigest()[:16]
        
        # Create session ID: BODYPART_PATIENTHASH_TIMESTAMP_UUID
        session_id = f"{body_part.upper()}_{patient_hash}_{timestamp}_{session_uuid}"
        
        session_data = {
            'session_id': session_id,
            'patient_name': patient_name,
            'patient_id': patient_id,
            'study_date': study_date,
            'body_part': body_part,
            'filename': filename,
            'created_at': timestamp,
            'last_accessed': timestamp,
            'isolated': True,
            'checksum': self.generate_checksum(patient_name, patient_id, body_part)
        }
        
        with self.session_lock:
            self.active_sessions[session_id] = session_data
        
        return session_id, session_data
    
    def generate_checksum(self, patient_name, patient_id, body_part):
        """Generate verification checksum for patient data"""
        data = f"{patient_name}_{patient_id}_{body_part}_{int(time.time())}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def validate_session(self, session_id, patient_data):
        """Validate that session data matches expected patient"""
        
        if session_id not in self.active_sessions:
            return False, "Session not found"
        
        session = self.active_sessions[session_id]
        
        # Update last accessed time
        session['last_accessed'] = int(time.time() * 1000)
        
        # Validate patient data matches session
        if (session['patient_name'] != patient_data.get('name') or
            session['patient_id'] != patient_data.get('patient_id') or
            session['body_part'] != patient_data.get('body_part')):
            return False, "Patient data mismatch - possible contamination"
        
        return True, "Session valid"
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions to prevent memory leaks"""
        
        current_time = int(time.time() * 1000)
        expired_sessions = []
        
        with self.session_lock:
            for session_id, session_data in self.active_sessions.items():
                if current_time - session_data['last_accessed'] > (self.cleanup_interval * 1000):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
        
        return len(expired_sessions)
    
    def get_session_info(self, session_id):
        """Get session information for validation"""
        return self.active_sessions.get(session_id)
    
    def clear_session(self, session_id):
        """Explicitly clear a session"""
        with self.session_lock:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                return True
        return False

# Global session manager instance
session_manager = PatientSessionManager()
