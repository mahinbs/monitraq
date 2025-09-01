/**
 * Critical: Cache Isolation for Patient Data Safety
 * Prevents patient data contamination and caching mix-ups
 */

class PatientDataIsolation {
    constructor() {
        this.currentSessionId = null;
        this.lastPatientId = null;
        this.lastBodyPart = null;
        this.isolationActive = false;
    }

    /**
     * CRITICAL: Clear all cached patient data before new analysis
     */
    aggressiveClearCache() {
        console.log('🧹 CRITICAL: Aggressive cache clearing for patient safety');
        
        try {
            // Clear all browser storage
            localStorage.clear();
            sessionStorage.clear();
            
            // Clear any IndexedDB data
            if ('indexedDB' in window) {
                indexedDB.databases().then(databases => {
                    databases.forEach(db => {
                        indexedDB.deleteDatabase(db.name);
                    });
                });
            }
            
            // Clear application cache (if exists)
            if ('applicationCache' in window) {
                window.applicationCache.swapCache();
            }
            
            // Force garbage collection hint
            if (window.gc) {
                window.gc();
            }
            
            console.log('✅ All browser cache cleared for patient safety');
            
        } catch (error) {
            console.error('❌ Cache clearing error:', error);
        }
    }

    /**
     * CRITICAL: Create isolated session for new patient
     */
    createIsolatedSession(patientData) {
        console.log('🔒 Creating isolated session for patient safety');
        
        // Generate unique session identifier
        const timestamp = Date.now();
        const random = Math.random().toString(36).substring(2);
        const sessionId = `${patientData.body_part}_${patientData.patient_id}_${timestamp}_${random}`;
        
        // Clear everything before new session
        this.aggressiveClearCache();
        this.clearAllDOMContainers();
        this.resetAllVariables();
        
        // Set new session
        this.currentSessionId = sessionId;
        this.lastPatientId = patientData.patient_id;
        this.lastBodyPart = patientData.body_part;
        this.isolationActive = true;
        
        // Store session info
        sessionStorage.setItem('patientSessionId', sessionId);
        sessionStorage.setItem('patientId', patientData.patient_id);
        sessionStorage.setItem('bodyPart', patientData.body_part);
        sessionStorage.setItem('sessionStart', timestamp.toString());
        
        console.log(`✅ Isolated session created: ${sessionId}`);
        return sessionId;
    }

    /**
     * CRITICAL: Validate no cross-contamination between patients
     */
    validatePatientIsolation(newPatientData) {
        console.log('🔍 Validating patient isolation...');
        
        const storedPatientId = sessionStorage.getItem('patientId');
        const storedBodyPart = sessionStorage.getItem('bodyPart');
        
        // Check for potential contamination
        if (storedPatientId && storedPatientId !== newPatientData.patient_id) {
            console.warn('⚠️ PATIENT CHANGE DETECTED - Forcing isolation');
            this.forcePatientIsolation();
            return false;
        }
        
        if (storedBodyPart && storedBodyPart !== newPatientData.body_part) {
            console.warn('⚠️ BODY PART CHANGE DETECTED - Forcing isolation');
            this.forcePatientIsolation();
            return false;
        }
        
        console.log('✅ Patient isolation validated');
        return true;
    }

    /**
     * CRITICAL: Force complete isolation when contamination detected
     */
    forcePatientIsolation() {
        console.log('🚨 FORCING COMPLETE PATIENT ISOLATION');
        
        // Nuclear option - clear everything
        this.aggressiveClearCache();
        this.clearAllDOMContainers();
        this.resetAllVariables();
        
        // Clear any cached fetch requests
        if ('caches' in window) {
            caches.keys().then(names => {
                names.forEach(name => {
                    caches.delete(name);
                });
            });
        }
        
        // Reset application state
        this.currentSessionId = null;
        this.lastPatientId = null;
        this.lastBodyPart = null;
        this.isolationActive = false;
        
        // Force page reload as last resort
        setTimeout(() => {
            console.log('🔄 FORCING PAGE RELOAD for complete isolation');
            window.location.reload(true);
        }, 1000);
    }

    /**
     * Clear all DOM containers that might hold patient data
     */
    clearAllDOMContainers() {
        console.log('🧹 Clearing all DOM containers');
        
        const containers = [
            'pathologiesList',
            'landmarksList', 
            'measurementsList',
            'locationsList',
            'recommendationsList',
            'patientName',
            'patientId',
            'studyDescription',
            'bodyPart'
        ];
        
        containers.forEach(containerId => {
            const element = document.getElementById(containerId);
            if (element) {
                if (element.tagName === 'INPUT' || element.tagName === 'SELECT') {
                    element.value = '';
                } else {
                    element.innerHTML = '';
                    element.textContent = '';
                }
            }
        });
        
        console.log('✅ All DOM containers cleared');
    }

    /**
     * Reset all JavaScript variables that might hold patient data
     */
    resetAllVariables() {
        console.log('🔄 Resetting all variables');
        
        // Reset global variables if they exist
        if (window.lastAnalysisResult) {
            window.lastAnalysisResult = null;
        }
        if (window.currentPatient) {
            window.currentPatient = null;
        }
        if (window.analysisHistory) {
            window.analysisHistory = [];
        }
        
        console.log('✅ All variables reset');
    }

    /**
     * Add contamination detection before displaying results
     */
    detectContamination(newResult, expectedPatient) {
        console.log('🔍 Detecting potential patient data contamination');
        
        // Check patient name mismatch
        if (newResult.patient_info?.name !== expectedPatient.name) {
            console.error('🚨 CONTAMINATION: Patient name mismatch!');
            return true;
        }
        
        // Check body part mismatch
        if (newResult.body_part !== expectedPatient.body_part) {
            console.error('🚨 CONTAMINATION: Body part mismatch!');
            return true;
        }
        
        // Check for brain landmarks in non-brain studies
        if (newResult.body_part !== 'brain' && 
            newResult.anatomical_landmarks?.some(landmark => 
                landmark.includes('brain') || landmark.includes('pituitary'))) {
            console.error('🚨 CONTAMINATION: Brain landmarks in non-brain study!');
            return true;
        }
        
        console.log('✅ No contamination detected');
        return false;
    }

    /**
     * Safe display with contamination protection
     */
    safeDisplayResults(result, expectedPatient) {
        console.log('🔒 Safe display with contamination protection');
        
        // Check for contamination
        if (this.detectContamination(result, expectedPatient)) {
            console.error('🚨 CONTAMINATION DETECTED - Blocking display');
            this.forcePatientIsolation();
            return false;
        }
        
        // Validate patient isolation
        if (!this.validatePatientIsolation(expectedPatient)) {
            console.warn('⚠️ Isolation validation failed - Re-isolating');
            return false;
        }
        
        // Safe to display
        console.log('✅ Safe to display results');
        return true;
    }

    /**
     * Add visual indicators for active isolation
     */
    addIsolationIndicators(result) {
        // Add visual confirmation that isolation is active
        const isolationBanner = document.createElement('div');
        isolationBanner.id = 'isolationBanner';
        isolationBanner.style.cssText = `
            background: #d1ecf1; 
            border: 1px solid #bee5eb; 
            border-radius: 4px; 
            padding: 10px; 
            margin: 10px 0; 
            color: #0c5460;
            font-weight: bold;
        `;
        isolationBanner.innerHTML = `
            🔒 PATIENT ISOLATION ACTIVE | Session: ${this.currentSessionId?.substring(0, 20)}... | 
            Patient: ${result.patient_info?.name} | Body Part: ${result.body_part?.toUpperCase()}
        `;
        
        // Add to top of results
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.insertBefore(isolationBanner, resultsSection.firstChild);
        }
    }
}

// Global isolation manager
window.patientIsolation = new PatientDataIsolation();
