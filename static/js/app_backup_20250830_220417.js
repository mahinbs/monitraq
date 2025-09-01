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
        document.getElementById('doctorName').textContent = doctorName;

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

        // Update recommendations
        this.updateList(this.recommendationsList, result.recommendations, 'recommendation-item');

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
        container.innerHTML = '';

        if (items && items.length > 0) {
            items.forEach(item => {
                const element = document.createElement('div');
                element.className = className;
                element.textContent = item;
                container.appendChild(element);
            });
        } else {
            const noData = document.createElement('p');
            noData.className = 'no-data';
            noData.textContent = container.id.includes('landmarks') ? 'No landmarks identified' :
                container.id.includes('pathologies') ? 'No pathologies detected' :
                    'No recommendations available';
            container.appendChild(noData);
        }
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

    // Hide professional report button
    document.getElementById('downloadProfessionalReportBtn').style.display = 'none';

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
    }
});

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
        // Show loading state
        const aiAnalyzeBtn = document.getElementById('aiAnalyzeBtn');
        const originalText = aiAnalyzeBtn.innerHTML;
        aiAnalyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        aiAnalyzeBtn.disabled = true;

        // Show AI analysis section if hidden
        const aiAnalysisSection = document.getElementById('aiAnalysisSection');
        aiAnalysisSection.style.display = 'block';

        // Call the AI analysis endpoint
        const response = await fetch('/api/ai-analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            // Store the analysis data for PDF download
            window.lastAIAnalysis = data;

            // Display AI analysis results
            displayAIAnalysisResults(data.ai_analysis);
            showNotification('AI analysis completed successfully!', 'success');

            // Show download button
            const downloadBtn = document.getElementById('downloadReportBtn');
            downloadBtn.style.display = 'inline-flex';
            console.log('Download button should now be visible');

            // Show AI analysis popup
            showAIAnalysisPopup(data.ai_analysis);
        } else {
            throw new Error(data.error || 'AI analysis failed');
        }

    } catch (error) {
        console.error('AI Analysis error:', error);
        showNotification(`AI analysis failed: ${error.message}`, 'error');
    } finally {
        // Reset button state
        const aiAnalyzeBtn = document.getElementById('aiAnalyzeBtn');
        aiAnalyzeBtn.innerHTML = '<i class="fas fa-brain"></i> Get AI Analysis';
        aiAnalyzeBtn.disabled = false;
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

    // Update popup summary
    const popupSummary = document.getElementById('aiPopupSummary');
    if (popupSummary) {
        popupSummary.textContent = aiAnalysis.summary || 'AI analysis completed successfully.';
        console.log('Updated popup summary');
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

    // Scroll to AI analysis section
    const aiSection = document.getElementById('aiAnalysisSection');
    aiSection.scrollIntoView({ behavior: 'smooth' });

    // Show the full results grid
    const aiResultsGrid = document.getElementById('aiResultsGrid');
    aiResultsGrid.style.display = 'grid';
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
    // Display AI Summary
    document.getElementById('aiSummary').textContent = aiAnalysis.summary || 'No summary available';

    // Display Clinical Insights
    const clinicalInsights = document.getElementById('clinicalInsights');
    if (aiAnalysis.clinical_insights && aiAnalysis.clinical_insights.length > 0) {
        clinicalInsights.innerHTML = aiAnalysis.clinical_insights.map(insight =>
            `<div class="insight-item">• ${insight}</div>`
        ).join('');
    } else {
        clinicalInsights.innerHTML = '<p class="no-data">No clinical insights available</p>';
    }

    // Display Differential Diagnosis
    const differentialDiagnosis = document.getElementById('differentialDiagnosis');
    if (aiAnalysis.differential_diagnosis && aiAnalysis.differential_diagnosis.length > 0) {
        differentialDiagnosis.innerHTML = aiAnalysis.differential_diagnosis.map(diagnosis =>
            `<div class="diagnosis-item">• ${diagnosis}</div>`
        ).join('');
    } else {
        differentialDiagnosis.innerHTML = '<p class="no-data">No differential diagnosis available</p>';
    }

    // Display AI Recommendations
    const aiRecommendations = document.getElementById('aiRecommendations');
    if (aiAnalysis.recommendations && aiAnalysis.recommendations.length > 0) {
        aiRecommendations.innerHTML = aiAnalysis.recommendations.map(recommendation =>
            `<div class="recommendation-item">• ${recommendation}</div>`
        ).join('');
    } else {
        aiRecommendations.innerHTML = '<p class="no-data">No AI recommendations available</p>';
    }

    // Display Risk Assessment
    document.getElementById('riskLevel').textContent = aiAnalysis.risk_assessment || 'Not assessed';
    document.getElementById('aiConfidence').textContent =
        aiAnalysis.ai_confidence ? `${(aiAnalysis.ai_confidence * 100).toFixed(1)}%` : 'Not available';

    // Display Follow-up Plan
    document.getElementById('followUpPlan').textContent = aiAnalysis.follow_up_plan || 'No follow-up plan available';

    // Show the AI results grid
    document.getElementById('aiResultsGrid').style.display = 'grid';
}

// Update the displayResults function to show AI analysis section
function displayResults(result) {
    // ... existing display logic ...

    // Show AI analysis section after regular results
    document.getElementById('aiAnalysisSection').style.display = 'block';
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
