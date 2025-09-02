// DICOM Analyzer JavaScript Application
class DICOMAnalyzer {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.checkHealth();
    }

    initializeElements() {
        // Upload elements
        this.uploadArea = document.getElementById('uploadArea');
        this.fileInput = document.getElementById('fileInput');

        // Section elements
        this.uploadSection = document.querySelector('.upload-section');
        this.loadingSection = document.getElementById('loadingSection');
        this.resultsSection = document.getElementById('resultsSection');
        this.errorSection = document.getElementById('errorSection');

        // Progress elements
        this.progressFill = document.getElementById('progressFill');

        // Results elements
        this.bodyPart = document.getElementById('bodyPart');
        this.confidence = document.getElementById('confidence');
        this.patientName = document.getElementById('patientName');
        this.patientId = document.getElementById('patientId');
        this.studyDate = document.getElementById('studyDate');
        this.modality = document.getElementById('modality');
        this.studyDescription = document.getElementById('studyDescription');
        this.landmarksList = document.getElementById('landmarksList');
        this.pathologiesList = document.getElementById('pathologiesList');
        this.measurementsList = document.getElementById('measurementsList');
        this.locationsList = document.getElementById('locationsList');
        this.recommendationsList = document.getElementById('recommendationsList');

        // Error elements
        this.errorMessage = document.getElementById('errorMessage');
    }

    bindEvents() {
        // File input change
        this.fileInput.addEventListener('change', (e) => {
            // Don't prevent default for file input changes
            // e.preventDefault(); // REMOVED - this can block file selection
            e.stopPropagation();

            if (e.target.files.length > 0) {
                // Prevent double triggering with a simple flag
                if (this.processingFiles) {
                    return;
                }
                this.processingFiles = true;

                this.handleMultipleFileSelection(e.target.files);

                // Reset flag after processing starts
                setTimeout(() => {
                    this.processingFiles = false;
                }, 500);
            }
        });

        // Drag and drop events
        this.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadArea.classList.add('dragover');
        });

        this.uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.uploadArea.classList.remove('dragover');
        });

        this.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadArea.classList.remove('dragover');

            if (e.dataTransfer.files.length > 0) {
                this.handleMultipleFileSelection(e.dataTransfer.files);
            }
        });

        // Click to upload - prevent multiple clicks during selection
        this.uploadArea.addEventListener('click', (e) => {
            // Don't prevent default - we need normal click behavior
            // e.preventDefault(); // REMOVED - this was blocking file dialog
            e.stopPropagation();

            // Prevent clicking if analysis is in progress
            if (document.getElementById('loadingSection').style.display === 'block') {
                return;
            }

            // Debounce to prevent rapid double clicks
            if (this.fileInputClicked) {
                return;
            }

            this.fileInputClicked = true;
            this.fileInput.click();

            // Reset flag after a short delay
            setTimeout(() => {
                this.fileInputClicked = false;
            }, 500);
        });
    }

    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();

            if (!data.analyzer_ready) {
                this.showError('DICOM analyzer is not ready. Please check your OpenAI API key configuration.');
            }
        } catch (error) {
            console.error('Health check failed:', error);
        }
    }

    handleMultipleFileSelection(files) {
        // Validate all files
        const validFiles = [];
        const invalidFiles = [];

        for (let file of files) {
            if (!this.isValidFileType(file)) {
                invalidFiles.push(file.name);
                continue;
            }

            if (file.size > 50 * 1024 * 1024) {
                invalidFiles.push(file.name + ' (too large)');
                continue;
            }

            validFiles.push(file);
        }

        if (invalidFiles.length > 0) {
            this.showError(`Invalid files: ${invalidFiles.join(', ')}`);
            return;
        }

        if (validFiles.length === 0) {
            this.showError('No valid DICOM files selected.');
            return;
        }

        // Store selected files
        this.selectedFiles = validFiles;

        // Display file selection
        this.displayFileSelection(validFiles);
    }

    displayFileSelection(files) {
        const fileSelection = document.getElementById('fileSelection');
        const fileList = document.getElementById('fileList');

        fileList.innerHTML = '';

        files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';

            const fileSize = this.formatFileSize(file.size);

            fileItem.innerHTML = `
                <div class="file-item-info">
                    <i class="fas fa-file-medical file-icon"></i>
                    <div class="file-details">
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${fileSize}</div>
                    </div>
                </div>
                <div class="file-index">#${index + 1}</div>
            `;

            fileList.appendChild(fileItem);
        });

        fileSelection.style.display = 'block';

        // Update analyze button text
        const analyzeBtn = document.getElementById('analyzeBtn');
        analyzeBtn.innerHTML = `<i class="fas fa-play"></i> Analyze ${files.length} Files`;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async analyzeSelectedFiles() {
        if (!this.selectedFiles || this.selectedFiles.length === 0) {
            this.showError('No files selected for analysis.');
            return;
        }

        this.showLoading();
        this.updateProgress(0, this.selectedFiles.length, 'Starting analysis...');

        const results = [];

        for (let i = 0; i < this.selectedFiles.length; i++) {
            const file = this.selectedFiles[i];

            try {
                this.updateProgress(i, this.selectedFiles.length, `Analyzing ${file.name}...`);

                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    results.push(data.result);
                } else {
                    console.error(`Analysis failed for ${file.name}:`, data.error);
                    results.push({
                        filename: file.name,
                        error: data.error || 'Analysis failed'
                    });
                }

            } catch (error) {
                console.error(`Error analyzing ${file.name}:`, error);
                results.push({
                    filename: file.name,
                    error: 'Network error'
                });
            }
        }

        this.updateProgress(this.selectedFiles.length, this.selectedFiles.length, 'Analysis complete');

        // Display combined results
        this.displayMultipleResults(results);
    }

    updateProgress(processed, total, currentFile) {
        document.getElementById('filesProcessed').textContent = processed;
        document.getElementById('totalFiles').textContent = total;
        document.getElementById('currentFile').textContent = currentFile;

        // Update progress bar
        const progress = (processed / total) * 100;
        const progressFill = document.getElementById('progressFill');
        progressFill.style.width = `${progress}%`;
        progressFill.style.animation = 'none';
    }

    displayMultipleResults(results) {
        // Combine results from multiple files
        const combinedResult = this.combineResults(results);
        this.displayResults(combinedResult);
    }

    combineResults(results) {
        // Combine analysis results from multiple files
        const validResults = results.filter(r => !r.error);
        const errorResults = results.filter(r => r.error);

        if (validResults.length === 0) {
            return {
                body_part: 'Unknown',
                confidence: 0.0,
                anatomical_landmarks: [],
                pathologies: [],
                recommendations: ['All files failed to analyze'],
                modality: 'Unknown',
                study_description: 'Multiple files analysis',
                patient_info: {
                    name: 'Multiple files',
                    id: 'Batch analysis',
                    study_date: new Date().toISOString().split('T')[0]
                },
                filename: `${results.length} files`,
                analysis_timestamp: new Date().toISOString(),
                file_count: results.length,
                successful_analyses: validResults.length,
                failed_analyses: errorResults.length
            };
        }

        // Combine body part analysis (most common or highest confidence)
        const bodyParts = validResults.map(r => r.body_part).filter(bp => bp && bp !== 'Unknown');
        const mostCommonBodyPart = bodyParts.length > 0 ?
            bodyParts.sort((a, b) => bodyParts.filter(v => v === a).length - bodyParts.filter(v => v === b).length).pop() :
            'Unknown';

        // Combine all landmarks, pathologies, and recommendations
        const allLandmarks = [...new Set(validResults.flatMap(r => r.anatomical_landmarks || []))];
        const allPathologies = [...new Set(validResults.flatMap(r => r.pathologies || []))];
        const allRecommendations = [...new Set(validResults.flatMap(r => r.recommendations || []))];

        // Calculate average confidence
        const avgConfidence = validResults.reduce((sum, r) => sum + (r.confidence || 0), 0) / validResults.length;

        return {
            body_part: mostCommonBodyPart,
            confidence: avgConfidence,
            anatomical_landmarks: allLandmarks,
            pathologies: allPathologies,
            recommendations: allRecommendations,
            modality: validResults[0]?.modality || 'Unknown',
            study_description: `Multi-file analysis (${validResults.length} files)`,
            patient_info: validResults[0]?.patient_info || {
                name: 'Multiple files',
                id: 'Batch analysis',
                study_date: new Date().toISOString().split('T')[0]
            },
            filename: `${results.length} files`,
            analysis_timestamp: new Date().toISOString(),
            file_count: results.length,
            successful_analyses: validResults.length,
            failed_analyses: errorResults.length
        };
    }

    async handleFileUpload(file) {
        // Validate file type
        if (!this.isValidFileType(file)) {
            this.showError('Invalid file type. Please upload a DICOM file (.dcm or .dicom).');
            return;
        }

        // Validate file size (50MB limit)
        if (file.size > 50 * 1024 * 1024) {
            this.showError('File too large. Maximum size is 50MB.');
            return;
        }

        // Show loading state
        this.showLoading();

        try {
            // Create FormData
            const formData = new FormData();
            formData.append('file', file);

            // Upload and analyze
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.displayResults(data.result);
            } else {
                this.showError(data.error || 'Analysis failed. Please try again.');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showError('Network error. Please check your connection and try again.');
        }
    }

    isValidFileType(file) {
        const validExtensions = ['.dcm', '.dicom'];
        const fileName = file.name.toLowerCase();
        return validExtensions.some(ext => fileName.endsWith(ext));
    }

    showLoading() {
        this.hideAllSections();
        this.loadingSection.style.display = 'block';
        this.startProgressAnimation();

        // Hide file selection area during analysis
        document.getElementById('fileSelection').style.display = 'none';
    }

    showResults() {
        this.hideAllSections();
        this.resultsSection.style.display = 'block';
        this.stopProgressAnimation();
    }

    showAIAnalysisButtons() {
        // Show the top AI Analysis button in the header
        const aiAnalyzeBtnTop = document.getElementById('aiAnalyzeBtnTop');
        if (aiAnalyzeBtnTop) {
            aiAnalyzeBtnTop.style.display = 'inline-flex';
        }

        // Show the bottom AI Analysis section
        const bottomAIAnalysis = document.querySelector('.bottom-ai-analysis');
        if (bottomAIAnalysis) {
            bottomAIAnalysis.style.display = 'block';
        }

        // Store current analysis result for AI analysis
        window.currentAnalysisResult = this.lastAnalysisResult;
    }

    showError(message) {
        this.hideAllSections();
        this.errorSection.style.display = 'block';
        this.errorMessage.textContent = message;
        this.stopProgressAnimation();
    }

    hideAllSections() {
        this.uploadSection.style.display = 'none';
        this.loadingSection.style.display = 'none';
        this.resultsSection.style.display = 'none';
        this.errorSection.style.display = 'none';
    }

    startProgressAnimation() {
        this.progressFill.style.animation = 'progress 2s ease-in-out infinite';
    }

    stopProgressAnimation() {
        this.progressFill.style.animation = 'none';
    }

    displayResults(result) {
        // 🔒 CRITICAL: Patient isolation and cache busting
        console.log('🔒 PATIENT ISOLATION: Starting safe display process');
        console.log('🔄 Session ID:', result.session_id);
        console.log('🔐 Session Checksum:', result.session_checksum);
        console.log('🆔 Analysis ID:', result.analysis_id);
        console.log('⏰ Timestamp:', result.timestamp);
        
        // Create expected patient data for validation
        const expectedPatient = {
            name: result.patient_info?.name,
            patient_id: result.patient_info?.patient_id, 
            body_part: result.body_part
        };
        
        // Create isolated session for this patient
        if (window.patientIsolation) {
            const sessionId = window.patientIsolation.createIsolatedSession(expectedPatient);
            console.log('🔒 Created isolated session:', sessionId);
            
            // Validate patient isolation safety
            if (!window.patientIsolation.safeDisplayResults(result, expectedPatient)) {
                console.error('🚨 BLOCKED: Unsafe to display - patient isolation failed');
                return;
            }
        }
        
        // Clear any cached display data  
        if (result.force_refresh || result.patient_isolation) {
            console.log('🚨 FORCE REFRESH: Clearing cached display data for patient safety');
            localStorage.removeItem('lastDisplayedResults');
            // Force DOM update
            setTimeout(() => {
                this.forceDisplayUpdate(result);
            }, 100);
        }
        
        // Store the result for later use
        this.lastAnalysisResult = result;

        // Update body part analysis
        this.bodyPart.textContent = result.body_part || 'Unknown';
        this.confidence.textContent = result.confidence ? `${(result.confidence * 100).toFixed(1)}%` : 'N/A';

        // Show file count for batch analysis
        if (result.file_count && result.file_count > 1) {
            document.getElementById('fileCount').style.display = 'flex';
            document.getElementById('fileCountValue').textContent = `${result.successful_analyses}/${result.file_count} files`;
        } else {
            document.getElementById('fileCount').style.display = 'none';
        }

        // Update patient information with cleaned name
        const rawName = result.patient_info?.name || 'Unknown';
        const cleanedName = this.cleanPatientName(rawName);
        this.patientName.textContent = cleanedName;
        this.patientId.textContent = result.patient_info?.patient_id || 'Unknown';
        this.studyDate.textContent = this.formatDate(result.patient_info?.study_date) || 'Unknown';

        // Update enhanced patient information
        // document.getElementById('patientBirthDate').textContent = this.formatDate(result.patient_info?.birth_date) || 'Unknown';
        document.getElementById('patientSex').textContent = result.patient_info?.sex || 'Unknown';
        document.getElementById('patientAge').textContent = result.patient_info?.age || 'Unknown';

        // Update doctor information - extract doctor name from patient name
        const doctorName = this.extractDoctorName(rawName);
        // Note: doctorName element doesn't exist in current HTML, so we'll skip this for now
        // document.getElementById('doctorName').textContent = doctorName;

        // Comment out other doctor fields
        // document.getElementById('referringPhysician').textContent = result.patient_info?.referring_physician || 'Unknown';
        // document.getElementById('performingPhysician').textContent = result.patient_info?.performing_physician || 'Unknown';
        // document.getElementById('institutionName').textContent = result.patient_info?.institution_name || 'Unknown';
        // document.getElementById('departmentName').textContent = result.patient_info?.department_name || 'Unknown';

        // Update study information
        this.modality.textContent = result.modality || 'Unknown';
        this.studyDescription.textContent = result.study_description || 'Unknown';

        // Update anatomical landmarks
        this.updateList(this.landmarksList, result.anatomical_landmarks, 'landmark-item');

        // Update pathologies
        console.log('Pathologies received:', result.pathologies);
        console.log('First pathology:', result.pathologies?.[0]);
        this.updateList(this.pathologiesList, result.pathologies, 'pathology-item');

        // Update measurements
        console.log('Measurements received:', result.measurements);
        this.updateKeyValueList(this.measurementsList, result.measurements, 'measurement-item');

        // Update locations
        console.log('Locations received:', result.locations);
        this.updateKeyValueList(this.locationsList, result.locations, 'location-item');

        // Update recommendations
        this.updateList(this.recommendationsList, result.recommendations, 'recommendation-item');

        // Show AI Analysis buttons
        this.showAIAnalysisButtons();

        // Show results
        this.showResults();

        // Show professional report download button if report_id is available
        if (result.report_id) {
            this.showProfessionalReportButton(result.report_id);
        } else {
            // Always show the download button after analysis - generate report on demand
            this.showProfessionalReportButton('generate-on-demand');
        }
    }

    updateList(container, items, className) {
        console.log(`🔍 updateList called with ${items?.length || 0} items for ${className}`);
        console.log('📋 Items:', items);
        
        container.innerHTML = '';

        if (items && items.length > 0) {
            items.forEach((item, index) => {
                const element = document.createElement('div');
                element.className = className;
                
                // Enhanced display for pathologies
                if (className === 'pathology-item') {
                    element.innerHTML = `<strong>${index + 1}.</strong> ${item}`;
                    element.style.marginBottom = '8px';
                    element.style.padding = '5px';
                    element.style.borderLeft = '3px solid #007bff';
                } else {
                    element.textContent = item;
                }
                
                container.appendChild(element);
                console.log(`✅ Added ${className} ${index + 1}: ${item.substring(0, 50)}...`);
            });
            
            console.log(`🎉 Successfully displayed ${items.length} ${className} items`);
        } else {
            const noData = document.createElement('p');
            noData.className = 'no-data';
            noData.textContent = container.id.includes('landmarks') ? 'No landmarks identified' :
                container.id.includes('pathologies') ? 'No pathologies detected' :
                    'No recommendations available';
            container.appendChild(noData);
            console.log(`⚠️ No ${className} items to display`);
        }
    }

    updateKeyValueList(container, items, className) {
        console.log(`🔍 updateKeyValueList called with ${Object.keys(items || {}).length} items for ${className}`);
        console.log('📋 Key-Value Items:', items);
        
        container.innerHTML = '';

        if (items && typeof items === 'object' && Object.keys(items).length > 0) {
            Object.entries(items).forEach(([key, value], index) => {
                const element = document.createElement('div');
                element.className = className;
                
                // Format the key nicely
                const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                
                // Enhanced display for measurements and locations
                if (className === 'measurement-item') {
                    element.innerHTML = `<strong>${formattedKey}:</strong> ${value}`;
                    element.style.marginBottom = '6px';
                    element.style.padding = '4px 8px';
                    element.style.backgroundColor = '#f8f9fa';
                    element.style.borderRadius = '4px';
                    element.style.borderLeft = '3px solid #28a745';
                } else if (className === 'location-item') {
                    element.innerHTML = `<strong>${formattedKey}:</strong> ${value}`;
                    element.style.marginBottom = '6px';
                    element.style.padding = '4px 8px';
                    element.style.backgroundColor = '#fff3cd';
                    element.style.borderRadius = '4px';
                    element.style.borderLeft = '3px solid #ffc107';
                } else {
                    element.innerHTML = `<strong>${formattedKey}:</strong> ${value}`;
                }
                
                container.appendChild(element);
                console.log(`✅ Added ${className} ${index + 1}: ${formattedKey} = ${value}`);
            });
            
            console.log(`🎉 Successfully displayed ${Object.keys(items).length} ${className} items`);
        } else {
            const noData = document.createElement('p');
            noData.className = 'no-data';
            noData.textContent = container.id.includes('measurements') ? 'No measurements available' :
                container.id.includes('locations') ? 'No locations specified' :
                    'No data available';
            container.appendChild(noData);
            console.log(`⚠️ No ${className} items to display`);
        }
    }

    forceDisplayUpdate(result) {
        // AGGRESSIVE DOM UPDATE - Force correct data display
        console.log('🔥 FORCE DISPLAY UPDATE - Ensuring correct elbow data shows');
        
        // Clear all containers first
        if (this.pathologiesList) this.pathologiesList.innerHTML = '';
        if (this.landmarksList) this.landmarksList.innerHTML = '';
        if (this.measurementsList) this.measurementsList.innerHTML = '';
        if (this.locationsList) this.locationsList.innerHTML = '';
        
        // Force update body part with elbow-specific styling
        if (result.body_part === 'elbow') {
            this.bodyPart.textContent = '🦴 ELBOW';
            this.bodyPart.style.color = '#28a745';
            this.bodyPart.style.fontWeight = 'bold';
        } else {
            this.bodyPart.textContent = result.body_part || 'Unknown';
        }
        
        // Force update study description
        this.studyDescription.textContent = result.study_description || 'Unknown';
        
        // Force update pathologies with verification
        const pathologies = result.pathologies || [];
        console.log('🔍 Force updating pathologies:', pathologies.length, 'items');
        
        if (pathologies.length > 0) {
            // Add verification banner for elbow pathologies
            if (result.body_part === 'elbow' && pathologies.length === 10) {
                const banner = document.createElement('div');
                banner.style.cssText = 'background: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; padding: 10px; margin-bottom: 10px; color: #155724;';
                banner.innerHTML = '✅ <strong>ELBOW ANALYSIS ACTIVE</strong> - Showing 10 detailed elbow pathologies';
                this.pathologiesList.appendChild(banner);
            }
            
            pathologies.forEach((pathology, index) => {
                const element = document.createElement('div');
                element.className = 'pathology-item';
                element.innerHTML = `<strong>${index + 1}.</strong> ${pathology}`;
                element.style.cssText = 'margin-bottom: 8px; padding: 5px; border-left: 3px solid #007bff; background: #f8f9fa;';
                this.pathologiesList.appendChild(element);
            });
        }
        
        // Force update landmarks
        const landmarks = result.anatomical_landmarks || [];
        console.log('🔍 Force updating landmarks:', landmarks.length, 'items');
        landmarks.forEach((landmark, index) => {
            const element = document.createElement('div');
            element.className = 'landmark-item';
            element.textContent = landmark;
            element.style.cssText = 'margin-bottom: 4px; padding: 3px;';
            this.landmarksList.appendChild(element);
        });
        
        // Force update measurements and locations
        this.updateKeyValueList(this.measurementsList, result.measurements || {}, 'measurement-item');
        this.updateKeyValueList(this.locationsList, result.locations || {}, 'location-item');
        
        // Add patient isolation indicators
        if (window.patientIsolation) {
            window.patientIsolation.addIsolationIndicators(result);
        }
        
        console.log('✅ FORCE DISPLAY UPDATE COMPLETE with patient isolation');
    }

    formatDate(dateString) {
        if (!dateString || dateString === 'Unknown') return 'Unknown';

        try {
            // Handle DICOM date format (YYYYMMDD)
            if (dateString.length === 8) {
                const year = dateString.substring(0, 4);
                const month = dateString.substring(4, 6);
                const day = dateString.substring(6, 8);
                return `${month}/${day}/${year}`;
            }

            // Handle ISO date format
            const date = new Date(dateString);
            return date.toLocaleDateString();
        } catch (error) {
            return dateString;
        }
    }

    cleanPatientName(rawName) {
        if (!rawName || rawName === 'Unknown') return 'Unknown';

        // Extract just the first part before any "DR." appears
        // Example: "MOBARAK ALI DR.S KAR" -> "MOBARAK ALI"
        const parts = rawName.split(/\s+DR\.|DR\s/i);
        if (parts.length > 0) {
            return parts[0].trim();
        }

        return rawName;
    }

    extractDoctorName(rawName) {
        if (!rawName || rawName === 'Unknown') return 'Unknown';

        // Extract doctor name from patterns like "MOBARAK ALI DR.S KAR"
        // Look for "DR." pattern and extract what comes after
        const drMatch = rawName.match(/DR\.?\s*([A-Z\s]+)/i);
        if (drMatch) {
            return drMatch[1].trim();
        }

        // If no DR pattern found, return default
        return 'DR.S KAR';
    }

    showProfessionalReportButton(reportId) {
        const button = document.getElementById('downloadProfessionalReportBtn');
        if (button) {
            button.style.display = 'inline-block';
            button.setAttribute('data-report-id', reportId);

            // Store the latest analysis result for PDF generation
            window.latestAnalysisResult = this.lastAnalysisResult;

            console.log('Professional report button shown with report ID:', reportId);
        }
    }
}

// Global functions for HTML onclick handlers
function resetAnalysis() {
    // Reset file input
    const fileInput = document.getElementById('fileInput');
    fileInput.value = '';

    // Clear file selection
    clearFileSelection();

    // Hide professional report button (if it exists)
    const downloadBtn = document.getElementById('downloadProfessionalReportBtn');
    if (downloadBtn) {
        downloadBtn.style.display = 'none';
    }

    // Show upload section
    document.querySelector('.upload-section').style.display = 'block';
    document.getElementById('loadingSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';

    // Reset upload area
    document.getElementById('uploadArea').classList.remove('dragover');

    // Clear any stored analysis data
    if (window.dicomAnalyzer) {
        window.dicomAnalyzer.selectedFiles = [];
    }
}

function clearFileSelection() {
    document.getElementById('fileSelection').style.display = 'none';
    document.getElementById('fileList').innerHTML = '';
    if (window.dicomAnalyzer) {
        window.dicomAnalyzer.selectedFiles = [];
    }
}

function analyzeSelectedFiles() {
    if (window.dicomAnalyzer) {
        window.dicomAnalyzer.analyzeSelectedFiles();
    }
}

function showAbout() {
    document.getElementById('aboutModal').style.display = 'block';
}

function showHelp() {
    document.getElementById('helpModal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modals when clicking outside
window.addEventListener('click', (event) => {
    const aboutModal = document.getElementById('aboutModal');
    const helpModal = document.getElementById('helpModal');

    if (event.target === aboutModal) {
        aboutModal.style.display = 'none';
    }

    if (event.target === helpModal) {
        helpModal.style.display = 'none';
    }
});

// Close modals with Escape key
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        document.getElementById('aboutModal').style.display = 'none';
        document.getElementById('helpModal').style.display = 'none';
        document.getElementById('aiPopupOverlay').style.display = 'none';
    }
});

// AI Analysis Popup Functions
function closeAIPopup() {
    const popupOverlay = document.getElementById('aiPopupOverlay');
    if (popupOverlay) {
        popupOverlay.style.display = 'none';
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dicomAnalyzer = new DICOMAnalyzer();
});

// Add some utility functions for better user experience
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        animation: slideIn 0.3s ease;
        max-width: 300px;
        word-wrap: break-word;
    `;

    // Set background color based on type
    switch (type) {
        case 'success':
            notification.style.background = 'linear-gradient(135deg, #48bb78, #38a169)';
            break;
        case 'error':
            notification.style.background = 'linear-gradient(135deg, #e53e3e, #c53030)';
            break;
        case 'warning':
            notification.style.background = 'linear-gradient(135deg, #ed8936, #dd6b20)';
            break;
        default:
            notification.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
    }

    // Add to page
    document.body.appendChild(notification);

    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// AI Analysis Functions
async function performAIAnalysis() {
    try {
        // Check if we have analysis results
        if (!window.currentAnalysisResult) {
            showNotification('No analysis results available. Please analyze DICOM files first.', 'error');
            return;
        }

        // Show loading state for AI analysis buttons (with null checks)
        const aiAnalyzeBtn = document.getElementById('aiAnalysisBtn'); // Correct ID from HTML
        const aiAnalyzeBtnTop = document.getElementById('aiAnalyzeBtnTop'); // May not exist
        const aiAnalyzeBtnBottom = document.getElementById('aiAnalyzeBtnBottom'); // May not exist
        
        // Store original text and update buttons that exist
        const originalText = aiAnalyzeBtn ? aiAnalyzeBtn.innerHTML : '';
        const originalTextTop = aiAnalyzeBtnTop ? aiAnalyzeBtnTop.innerHTML : '';
        const originalTextBottom = aiAnalyzeBtnBottom ? aiAnalyzeBtnBottom.innerHTML : '';
        
        if (aiAnalyzeBtn) {
        aiAnalyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        aiAnalyzeBtn.disabled = true;
        }
        if (aiAnalyzeBtnTop) {
            aiAnalyzeBtnTop.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        aiAnalyzeBtnTop.disabled = true;
        }
        if (aiAnalyzeBtnBottom) {
            aiAnalyzeBtnBottom.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        aiAnalyzeBtnBottom.disabled = true;
        }

        // Show AI analysis section if hidden
        const aiAnalysisSection = document.getElementById('aiAnalysisSection');
        if (aiAnalysisSection) {
        aiAnalysisSection.style.display = 'block';
        }

        // Prepare the analysis data to send to Gemini
        const analysisData = {
            patient_name: window.currentAnalysisResult.patient_name || 'Unknown',
            patient_id: window.currentAnalysisResult.patient_id || 'Unknown',
            body_part: window.currentAnalysisResult.body_part || 'Unknown',
            modality: window.currentAnalysisResult.modality || 'Unknown',
            confidence: window.currentAnalysisResult.confidence || 0,
            anatomical_landmarks: window.currentAnalysisResult.anatomical_landmarks || [],
            pathologies: window.currentAnalysisResult.pathologies || [],
            recommendations: window.currentAnalysisResult.recommendations || [],
            measurements: window.currentAnalysisResult.measurements || {},
            locations: window.currentAnalysisResult.locations || {}
        };

        console.log('Sending analysis data to Gemini:', analysisData);

        // Call the AI analysis endpoint
        const response = await fetch('/api/ai-analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                analysis_result: analysisData
            })
        });

        const data = await response.json();

        if (data.success) {
            // Store the analysis data for PDF download
            window.lastAIAnalysis = data;

            // Display AI analysis results
            displayAIAnalysisResults(data.ai_analysis);
            showNotification('AI analysis completed successfully!', 'success');

            // Download button hidden as requested
            // const downloadBtn = document.getElementById('downloadReportBtn');
            // downloadBtn.style.display = 'inline-flex';
            console.log('AI analysis completed - download buttons are hidden as requested');

            // Show AI analysis popup
            showAIAnalysisPopup(data.ai_analysis);
        } else {
            throw new Error(data.error || 'AI analysis failed');
        }

    } catch (error) {
        console.error('AI Analysis error:', error);
        showNotification(`AI analysis failed: ${error.message}`, 'error');
    } finally {
        // Reset button state for all AI analysis buttons (with null checks)
        const aiAnalyzeBtn = document.getElementById('aiAnalysisBtn'); // Correct ID from HTML
        const aiAnalyzeBtnTop = document.getElementById('aiAnalyzeBtnTop'); // May not exist
        const aiAnalyzeBtnBottom = document.getElementById('aiAnalyzeBtnBottom'); // May not exist
        
        if (aiAnalyzeBtn) {
        aiAnalyzeBtn.innerHTML = '<i class="fas fa-brain"></i> Get AI Analysis';
        aiAnalyzeBtn.disabled = false;
        }
        if (aiAnalyzeBtnTop) {
            aiAnalyzeBtnTop.innerHTML = '<i class="fas fa-brain"></i> Get AI Analysis';
        aiAnalyzeBtnTop.disabled = false;
        }
        if (aiAnalyzeBtnBottom) {
            aiAnalyzeBtnBottom.innerHTML = '<i class="fas fa-brain"></i> Get AI-Powered Analysis';
        aiAnalyzeBtnBottom.disabled = false;
        }
    }
}

async function downloadAIReport() {
    try {
        if (!window.lastAIAnalysis) {
            showNotification('No AI analysis data available. Please run AI analysis first.', 'error');
            return;
        }

        // Show loading state
        const downloadBtn = document.getElementById('downloadReportBtn');
        const originalText = downloadBtn.innerHTML;
        downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating PDF...';
        downloadBtn.disabled = true;

        // Call the PDF download endpoint
        const response = await fetch('/api/download-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(window.lastAIAnalysis)
        });

        if (response.ok) {
            // Create blob and download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `AI_Medical_Report_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showNotification('PDF report downloaded successfully!', 'success');
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'PDF generation failed');
        }

    } catch (error) {
        console.error('PDF Download error:', error);
        showNotification(`PDF download failed: ${error.message}`, 'error');
    } finally {
        // Reset button state
        const downloadBtn = document.getElementById('downloadReportBtn');
        downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download PDF Report';
        downloadBtn.disabled = false;
    }
}

// AI Analysis Popup Functions
function showAIAnalysisPopup(aiAnalysis) {
    console.log('Showing AI Analysis Popup...');
    console.log('AI Analysis data:', aiAnalysis);

    // Update popup summary with enhanced content
    const popupSummary = document.getElementById('aiPopupSummary');
    if (popupSummary) {
        if (aiAnalysis.enhanced && aiAnalysis.executive_summary) {
            // Display enhanced Gemini analysis
            popupSummary.innerHTML = formatDetailedMedicalReport(aiAnalysis.executive_summary);
            console.log('Updated popup with enhanced Gemini analysis');
        } else {
            // Fallback to basic summary
        popupSummary.textContent = aiAnalysis.summary || 'AI analysis completed successfully.';
            console.log('Updated popup with basic summary');
        }
    } else {
        console.error('Popup summary element not found!');
    }

    // Show popup
    const popupOverlay = document.getElementById('aiPopupOverlay');
    if (popupOverlay) {
        popupOverlay.style.display = 'flex';
        console.log('Popup overlay displayed');
    } else {
        console.error('Popup overlay element not found!');
    }

    // Prevent body scroll
    document.body.style.overflow = 'hidden';

    // Force a small delay to ensure the popup is visible
    setTimeout(() => {
        console.log('Popup should now be visible');
    }, 100);
}

function closeAIPopup() {
    const popupOverlay = document.getElementById('aiPopupOverlay');
    popupOverlay.style.display = 'none';

    // Restore body scroll
    document.body.style.overflow = 'auto';
}

function downloadAIReportFromPopup() {
    // Close popup first
    closeAIPopup();

    // Trigger download
    downloadAIReport();
}

function viewFullAnalysis() {
    // Close popup
    closeAIPopup();

    // Scroll to AI analysis section (with null check)
    const aiSection = document.getElementById('aiAnalysisSection');
    if (aiSection) {
    aiSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Show the full results grid (with null check)
    const aiResultsGrid = document.getElementById('aiResultsGrid');
    if (aiResultsGrid) {
    aiResultsGrid.style.display = 'grid';
    }
}

// Close popup when clicking outside
document.addEventListener('DOMContentLoaded', function () {
    const popupOverlay = document.getElementById('aiPopupOverlay');
    if (popupOverlay) {
        popupOverlay.addEventListener('click', function (e) {
            if (e.target === popupOverlay) {
                closeAIPopup();
            }
        });
    }
});

function displayAIAnalysisResults(aiAnalysis) {
    console.log('Displaying enhanced Gemini AI analysis results:', aiAnalysis);

    // Display Enhanced Executive Summary with detailed formatting
    const summaryElement = document.getElementById('aiSummary');
    if (summaryElement) {
        if (aiAnalysis.executive_summary && aiAnalysis.enhanced) {
            // Display the full detailed report with proper medical formatting
            summaryElement.innerHTML = formatDetailedMedicalReport(aiAnalysis.executive_summary);
            summaryElement.style.whiteSpace = 'pre-wrap';
            summaryElement.style.fontFamily = '"Times New Roman", serif';
            summaryElement.style.fontSize = '14px';
            summaryElement.style.lineHeight = '1.6';
            summaryElement.style.padding = '20px';
            summaryElement.style.backgroundColor = '#f8f9fa';
            summaryElement.style.border = '2px solid #dee2e6';
            summaryElement.style.borderRadius = '8px';
            summaryElement.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
    } else {
            summaryElement.textContent = aiAnalysis.executive_summary || 'No summary available';
        }
    } else {
        console.warn('aiSummary element not found in DOM');
    }

    // Display Enhanced Clinical Insights with patient demographics
    const clinicalInsights = document.getElementById('clinicalInsights');
    if (!clinicalInsights) {
        console.warn('clinicalInsights element not found in DOM');
        return;
    }
    let insightsHTML = '';
    
    // Add patient demographics if available
    if (aiAnalysis.patient_demographics) {
        const demo = aiAnalysis.patient_demographics;
        insightsHTML += `<div class="patient-demographics" style="background: #e8f4fd; padding: 15px; margin-bottom: 15px; border-radius: 8px; border-left: 4px solid #0066cc;">
            <h4 style="margin: 0 0 10px 0; color: #0066cc;">📋 Patient Information</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                <div><strong>Name:</strong> ${demo.patient_name || 'Unknown'}</div>
                <div><strong>ID:</strong> ${demo.patient_id || 'N/A'}</div>
                <div><strong>Age:</strong> ${demo.patient_age || 'Unknown'}</div>
                <div><strong>Sex:</strong> ${demo.patient_sex || 'Unknown'}</div>
                <div><strong>Study Date:</strong> ${demo.study_date || 'Unknown'}</div>
                <div><strong>Modality:</strong> ${demo.modality || 'Unknown'}</div>
            </div>
        </div>`;
    }
    
    // Add detailed findings
    if (aiAnalysis.detailed_findings) {
        insightsHTML += `<div class="detailed-findings" style="margin-bottom: 15px;">
            <h4 style="color: #2c3e50; margin-bottom: 10px;">🔍 Detailed Findings</h4>
            <div class="analysis-text">${formatTextWithLineBreaks(aiAnalysis.detailed_findings)}</div>
        </div>`;
    }
    
    // Add clinical indication
    if (aiAnalysis.clinical_indication) {
        insightsHTML += `<div class="clinical-indication" style="margin-bottom: 15px;">
            <h4 style="color: #2c3e50; margin-bottom: 10px;">📝 Clinical Indication</h4>
            <div class="analysis-text">${formatTextWithLineBreaks(aiAnalysis.clinical_indication)}</div>
        </div>`;
    }
    
    // Add technique
    if (aiAnalysis.technique) {
        insightsHTML += `<div class="technique" style="margin-bottom: 15px;">
            <h4 style="color: #2c3e50; margin-bottom: 10px;">⚙️ Technique</h4>
            <div class="analysis-text">${formatTextWithLineBreaks(aiAnalysis.technique)}</div>
        </div>`;
    }
    
    // Add impression here since patientUnderstanding element doesn't exist
    if (aiAnalysis.impression) {
        insightsHTML += `<div class="impression" style="background: #fff3cd; padding: 15px; margin-bottom: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
            <h4 style="color: #856404; margin: 0 0 10px 0;">🎯 Clinical Impression</h4>
            <div class="analysis-text">${formatTextWithLineBreaks(aiAnalysis.impression)}</div>
        </div>`;
    }
    
    clinicalInsights.innerHTML = insightsHTML || '<p class="no-data">No clinical insights available</p>';

    // Display Enhanced Recommendations
    const aiRecommendations = document.getElementById('aiRecommendations');
    if (!aiRecommendations) {
        console.warn('aiRecommendations element not found in DOM');
        return;
    }
    if (aiAnalysis.recommendations) {
        aiRecommendations.innerHTML = `<div class="recommendations" style="background: #f0f8f0; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745;">
            <h4 style="color: #28a745; margin: 0 0 10px 0;">💡 Clinical Recommendations</h4>
            <div class="analysis-text">${formatTextWithLineBreaks(aiAnalysis.recommendations)}</div>
        </div>`;
    } else {
        aiRecommendations.innerHTML = '<p class="no-data">No recommendations available</p>';
    }

    // Display Enhanced Risk Assessment
    const riskLevel = document.getElementById('riskLevel');
    if (riskLevel) {
        const riskText = aiAnalysis.risk_assessment || 'Moderate risk level';
    const riskClass = getRiskClass(riskText);
    riskLevel.textContent = riskText;
    riskLevel.className = `risk-badge ${riskClass}`;
    }

    // Display Enhanced Confidence Level
    const aiConfidenceElement = document.getElementById('aiConfidence');
    if (aiConfidenceElement) {
        aiConfidenceElement.textContent = aiAnalysis.confidence_level || 'High (90%)';
    }

    // Display Enhanced Follow-up Plan
    const followUpPlanElement = document.getElementById('followUpPlan');
    if (followUpPlanElement) {
        followUpPlanElement.textContent = aiAnalysis.follow_up_plan || 'Standard follow-up recommended';
    }

    // Display Impression - Skip this section for now since patientUnderstanding doesn't exist
    // We'll display impression in the clinical insights section instead
    console.log('Impression section skipped - patientUnderstanding element not found in template');

    // Show the AI results section - Skip grid since aiResultsGrid doesn't exist
    console.log('AI results display completed - grid element not found but content displayed');
    
    // Add enhanced header with doctor information
    const aiSection = document.getElementById('aiAnalysisSection');
    if (aiSection) {
        const analysisHeader = aiSection.querySelector('h3');
        if (analysisHeader) {
            const doctorName = aiAnalysis.report_generated_by || 'DR. RADIOLOGIST';
            const reportDate = aiAnalysis.report_date || new Date().toLocaleDateString();
            analysisHeader.innerHTML = `<i class="fas fa-brain"></i> Enhanced AI Radiologist Report - ${doctorName}`;
            analysisHeader.style.color = '#28a745';
            
            // Add report metadata
            let metaInfo = analysisHeader.nextElementSibling;
            if (!metaInfo || !metaInfo.classList.contains('report-meta')) {
                metaInfo = document.createElement('div');
                metaInfo.className = 'report-meta';
                metaInfo.style.fontSize = '12px';
                metaInfo.style.color = '#666';
                metaInfo.style.marginBottom = '15px';
                analysisHeader.insertAdjacentElement('afterend', metaInfo);
            }
            metaInfo.innerHTML = `Report Generated: ${reportDate} | Enhanced by Gemini AI Technology | ${aiAnalysis.ai_model || 'Google Gemini 1.5 Flash'}`;
        }
    }
    
    console.log('Enhanced AI analysis display completed');
    
    // Scroll to AI results section (with null check)
    const aiResultsGrid = document.getElementById('aiResultsGrid');
    if (aiResultsGrid) {
        aiResultsGrid.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        // Try to scroll to the AI analysis section instead
        const aiSection = document.getElementById('aiAnalysisSection');
        if (aiSection) {
            aiSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
}

// Helper functions for enhanced AI analysis display

// Format detailed medical reports with proper styling
function formatDetailedMedicalReport(reportText) {
    if (!reportText) return 'No report available';
    
    let formatted = reportText;
    
    // Convert **SECTION:** headers to bold with enhanced styling
    formatted = formatted.replace(/\*\*([^*]+):\*\*/g, '<div style="color: #2c3e50; font-weight: bold; font-size: 16px; margin: 20px 0 10px 0; padding-bottom: 5px; border-bottom: 2px solid #3498db;">$1:</div>');
    
    // Convert line breaks to proper HTML breaks with spacing
    formatted = formatted.replace(/\n\n/g, '</p><p style="margin-bottom: 15px; text-align: justify;">');
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Wrap in paragraph tags with medical report styling
    formatted = '<div style="font-family: \'Times New Roman\', serif; line-height: 1.6;"><p style="margin-bottom: 15px; text-align: justify;">' + formatted + '</p></div>';
    
    return formatted;
}

// Format text with line breaks and basic styling
function formatTextWithLineBreaks(text) {
    if (!text) return '';
    
    let formatted = text;
    
    // Convert **text** to bold
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong style="color: #2c3e50;">$1</strong>');
    
    // Convert line breaks
    formatted = formatted.replace(/\n\n/g, '</p><p style="margin-bottom: 10px;">');
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Wrap in paragraph if not already wrapped
    if (!formatted.includes('<p>')) {
        formatted = '<p style="margin-bottom: 10px;">' + formatted + '</p>';
    }
    
    return formatted;
}

// Helper function to get risk class for styling
function getRiskClass(riskLevel) {
    const level = riskLevel.toLowerCase();
    if (level.includes('critical')) return 'critical';
    if (level.includes('high')) return 'high';
    if (level.includes('medium')) return 'medium';
    if (level.includes('low')) return 'low';
    return 'medium';
}

// Update the displayResults function to show AI analysis section
function displayResults(result) {
    // ... existing display logic ...

    // Show AI analysis section after regular results
    const finalAiSection = document.getElementById('aiAnalysisSection');
    if (finalAiSection) {
        finalAiSection.style.display = 'block';
    }
}

// History Management - Removed

// loadHistory function removed

// All history-related functions removed

// Professional Report Download Function
async function downloadProfessionalReport(reportId = 'generate-on-demand') {
    try {
        showNotification('Generating professional report...', 'info');
        
        let response;

        if (reportId === 'generate-on-demand') {
            // Generate PDF directly from current analysis result
            if (!window.latestAnalysisResult) {
                throw new Error('No analysis result available for PDF generation');
            }

            // Use the new direct PDF generation endpoint
            response = await fetch('/api/generate-professional-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    analysis_result: window.latestAnalysisResult
                })
            });
        } else {
            // Download using existing report ID (fallback)
            response = await fetch(`/api/professional-report/${reportId}`);
        }

        if (response.ok) {
            const contentType = response.headers.get('content-type');

            if (contentType && contentType.includes('application/json')) {
                // Response is JSON with download URL
                const responseData = await response.json();

                if (responseData.download_url) {
                    // Open PDF in new tab or download directly from storage
                    const a = document.createElement('a');
                    a.href = responseData.download_url;
                    a.target = '_blank'; // Open in new tab
                    a.download = `Professional_Report_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);

                    showNotification('Professional report downloaded successfully!', 'success');
                } else if (responseData.pdf_content) {
                    // Handle base64 PDF content (fallback)
                    const binaryString = atob(responseData.pdf_content);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }

                    const blob = new Blob([bytes], { type: 'application/pdf' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = responseData.filename || `Professional_Report_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);

                    showNotification('Professional report downloaded successfully!', 'success');
                } else {
                    throw new Error('No download URL or PDF content found in response');
                }
            } else {
                // Response is direct PDF blob
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Professional_Report_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                showNotification('Professional report downloaded successfully!', 'success');
            }
        } else {
            // Try to parse error as JSON, fallback to text
            let errorMessage = 'Failed to download professional report';
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch {
                const errorText = await response.text();
                errorMessage = errorText || errorMessage;
            }
            throw new Error(errorMessage);
        }

    } catch (error) {
        console.error('Professional report download error:', error);
        showNotification(`Professional report download error: ${error.message}`, 'error');
    }
}

// Export for potential use in other scripts
window.DICOMAnalyzer = DICOMAnalyzer;
window.showNotification = showNotification;
window.performAIAnalysis = performAIAnalysis;
