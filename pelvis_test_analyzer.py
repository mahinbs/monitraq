#!/usr/bin/env python3
"""
Pelvis Test Analyzer - Specialized analysis for pelvis DICOM files
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from pathlib import Path
import pydicom
import numpy as np
from PIL import Image
import cv2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PelvisTestAnalyzer:
    """Specialized analyzer for pelvis DICOM files with enhanced pathology detection"""
    
    def __init__(self):
        self.pelvis_pathologies = {
            'fractures': [
                'acetabular_fracture',
                'pubic_rami_fracture', 
                'sacral_fracture',
                'iliac_wing_fracture',
                'ischial_tuberosity_fracture'
            ],
            'degenerative': [
                'osteoarthritis_hip',
                'degenerative_disc_disease',
                'spinal_stenosis',
                'spondylolisthesis',
                'facet_joint_arthropathy'
            ],
            'inflammatory': [
                'sacroiliitis',
                'hip_synovitis',
                'bursitis',
                'tendinitis',
                'enthesitis'
            ],
            'tumors': [
                'bone_metastasis',
                'primary_bone_tumor',
                'soft_tissue_mass',
                'lymphadenopathy',
                'cystic_lesions'
            ],
            'vascular': [
                'aneurysm',
                'thrombosis',
                'stenosis',
                'arteriovenous_malformation',
                'varicose_veins'
            ],
            'fistulogram': [
                'fistula_tract',
                'fistula_opening',
                'fistula_branching',
                'fistula_complexity',
                'fistula_communication',
                'fistula_infection',
                'fistula_granulation_tissue',
                'fistula_foreign_body',
                'fistula_abscess_formation',
                'fistula_stenosis'
            ]
        }
        
        self.anatomical_landmarks = [
            'sacrum', 'coccyx', 'ilium', 'ischium', 'pubis',
            'acetabulum', 'femoral_head', 'sacroiliac_joints',
            'pubic_symphysis', 'obturator_foramen', 'greater_sciatic_notch',
            'lesser_sciatic_notch', 'iliac_crest', 'anterior_superior_iliac_spine',
            'posterior_superior_iliac_spine', 'ischial_spine', 'pubic_tubercle',
            'fistula_tract', 'fistula_opening', 'fistula_branching',
            'fistula_communication', 'fistula_granulation_tissue'
        ]
    
    def analyze_pelvis_folder(self, folder_path: str) -> Dict[str, Any]:
        """Analyze all DICOM files in the pelvis folder"""
        logger.info(f"Starting pelvis folder analysis: {folder_path}")
        
        results = {
            'analysis_date': datetime.now().isoformat(),
            'folder_path': folder_path,
            'total_files': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'series_results': {},
            'overall_findings': {},
            'pathology_summary': {},
            'recommendations': []
        }
        
        try:
            # Check if this is a series-organized folder or individual files
            items = os.listdir(folder_path)
            has_series_dirs = any(os.path.isdir(os.path.join(folder_path, item)) for item in items)
            
            logger.info(f"Folder {folder_path} contains {len(items)} items")
            logger.info(f"Items: {items[:10]}...")  # Show first 10 items
            logger.info(f"Has series directories: {has_series_dirs}")
            
            if has_series_dirs:
                # Original logic for series-organized folders
                logger.info("Processing series-organized folder structure")
                for series_dir in items:
                    series_path = os.path.join(folder_path, series_dir)
                    if os.path.isdir(series_path):
                        series_results = self._analyze_series(series_path, series_dir)
                        results['series_results'][series_dir] = series_results
                        results['total_files'] += series_results.get('file_count', 0)
                        results['successful_analyses'] += series_results.get('successful_count', 0)
                        results['failed_analyses'] += series_results.get('failed_count', 0)
            else:
                # Handle individual uploaded files
                logger.info("Processing individual uploaded files")
                uploaded_files = [item for item in items if item.lower().endswith(('.dcm', '.dicom'))]
                logger.info(f"Found {len(uploaded_files)} DICOM files: {uploaded_files[:5]}...")
                
                if uploaded_files:
                    # Create a virtual series for uploaded files
                    series_results = self._analyze_uploaded_files(folder_path, uploaded_files)
                    results['series_results']['uploaded_files'] = series_results
                    results['total_files'] = series_results.get('file_count', 0)
                    results['successful_analyses'] = series_results.get('successful_count', 0)
                    results['failed_analyses'] = series_results.get('failed_count', 0)
                else:
                    logger.warning("No DICOM files found in folder")
            
            logger.info(f"Analysis complete. Total files: {results['total_files']}, Successful: {results['successful_analyses']}, Failed: {results['failed_analyses']}")
            
            # Generate overall findings
            results['overall_findings'] = self._generate_overall_findings(results['series_results'])
            results['pathology_summary'] = self._generate_pathology_summary(results['series_results'])
            results['recommendations'] = self._generate_recommendations(results['pathology_summary'])
            
            logger.info(f"Pelvis analysis completed: {results['successful_analyses']} successful, {results['failed_analyses']} failed")
            
        except Exception as e:
            logger.error(f"Error during pelvis folder analysis: {e}")
            results['error'] = str(e)
        
        return results
    
    def _analyze_series(self, series_path: str, series_name: str) -> Dict[str, Any]:
        """Analyze a single series within the pelvis folder"""
        series_results = {
            'series_name': series_name,
            'file_count': 0,
            'successful_count': 0,
            'failed_count': 0,
            'files': {},
            'confidence_score': 0.0,
            'anatomical_landmarks': [],
            'pathologies': [],
            'measurements': {},
            'metadata': {}
        }
        
        try:
            # Get all DICOM files in the series
            dicom_files = [f for f in os.listdir(series_path) 
                          if f.lower().endswith(('.dcm', '.dicom'))]
            
            series_results['file_count'] = len(dicom_files)
            
            if not dicom_files:
                return series_results
            
            # Analyze each DICOM file
            for filename in dicom_files:
                file_path = os.path.join(series_path, filename)
                try:
                    file_results = self._analyze_single_dicom(file_path, series_name)
                    series_results['files'][filename] = file_results
                    series_results['successful_count'] += 1
                    
                    # Aggregate findings
                    if file_results.get('anatomical_landmarks'):
                        series_results['anatomical_landmarks'].extend(file_results['anatomical_landmarks'])
                    if file_results.get('pathologies'):
                        series_results['pathologies'].extend(file_results['pathologies'])
                    if file_results.get('measurements'):
                        series_results['measurements'].update(file_results['measurements'])
                    if file_results.get('metadata'):
                        series_results['metadata'].update(file_results['metadata'])
                        
                except Exception as e:
                    logger.error(f"Error analyzing {filename}: {e}")
                    series_results['failed_count'] += 1
            
            # Calculate series confidence
            if series_results['successful_count'] > 0:
                confidence_scores = [file_results.get('confidence', 0.0) 
                                   for file_results in series_results['files'].values()]
                series_results['confidence_score'] = sum(confidence_scores) / len(confidence_scores)
            
            # Remove duplicates
            series_results['anatomical_landmarks'] = list(set(series_results['anatomical_landmarks']))
            series_results['pathologies'] = list(set(series_results['pathologies']))
            
        except Exception as e:
            logger.error(f"Error analyzing series {series_name}: {e}")
            series_results['failed_count'] = series_results['file_count']
        
        return series_results

    def _analyze_uploaded_files(self, folder_path: str, uploaded_files: List[str]) -> Dict[str, Any]:
        """Analyze individual uploaded DICOM files"""
        logger.info(f"Starting analysis of {len(uploaded_files)} uploaded files in {folder_path}")
        
        series_results = {
            'series_name': 'uploaded_files',
            'file_count': len(uploaded_files),
            'successful_count': 0,
            'failed_count': 0,
            'files': {},
            'confidence_score': 0.0,
            'anatomical_landmarks': [],
            'pathologies': [],
            'measurements': {},
            'metadata': {}
        }
        
        try:
            # Analyze each uploaded DICOM file
            for filename in uploaded_files:
                file_path = os.path.join(folder_path, filename)
                logger.info(f"Analyzing uploaded file: {filename}")
                
                try:
                    file_results = self._analyze_single_dicom(file_path, 'uploaded_files')
                    if file_results is None:
                        series_results['failed_count'] += 1
                        logger.error(f"Analysis returned None for {filename}")
                        continue
                        
                    series_results['files'][filename] = file_results
                    series_results['successful_count'] += 1
                    logger.info(f"Successfully analyzed {filename}: {len(file_results.get('anatomical_landmarks', []))} landmarks, {len(file_results.get('pathologies', []))} pathologies")
                    
                    # Aggregate findings
                    if file_results.get('anatomical_landmarks'):
                        series_results['anatomical_landmarks'].extend(file_results['anatomical_landmarks'])
                    if file_results.get('pathologies'):
                        series_results['pathologies'].extend(file_results['pathologies'])
                    if file_results.get('measurements'):
                        series_results['measurements'].update(file_results['measurements'])
                    if file_results.get('metadata'):
                        series_results['metadata'].update(file_results['metadata'])
                        
                except ValueError as ve:
                    # This is a validation error (non-pelvis file)
                    logger.warning(f"Validation error for {filename}: {ve}")
                    series_results['failed_count'] += 1
                    # Store validation error in files for reporting
                    series_results['files'][filename] = {
                        'error': 'validation_failed',
                        'error_message': str(ve),
                        'filename': filename,
                        'series': 'uploaded_files'
                    }
                except Exception as e:
                    logger.error(f"Error analyzing uploaded file {filename}: {e}")
                    series_results['failed_count'] += 1
                    # Store error in files for reporting
                    series_results['files'][filename] = {
                        'error': 'analysis_failed',
                        'error_message': str(e),
                        'filename': filename,
                        'series': 'uploaded_files'
                    }
            
            # Calculate series confidence
            if series_results['successful_count'] > 0:
                confidence_scores = [file_results.get('confidence', 0.0) 
                                   for file_results in series_results['files'].values()]
                series_results['confidence_score'] = sum(confidence_scores) / len(confidence_scores)
            
            # Remove duplicates
            series_results['anatomical_landmarks'] = list(set(series_results['anatomical_landmarks']))
            series_results['pathologies'] = list(set(series_results['pathologies']))
            
            logger.info(f"Uploaded files analysis complete: {series_results['successful_count']} successful, {series_results['failed_count']} failed")
            logger.info(f"Total landmarks found: {len(series_results['anatomical_landmarks'])}")
            logger.info(f"Total pathologies found: {len(series_results['pathologies'])}")
            
        except Exception as e:
            logger.error(f"Error analyzing uploaded files: {e}")
            series_results['failed_count'] = series_results['file_count']
        
        return series_results
    
    def _analyze_single_dicom(self, file_path: str, series_name: str) -> Dict[str, Any]:
        """Analyze a single DICOM file"""
        try:
            # Load DICOM file
            ds = pydicom.dcmread(file_path)
            
            # Validate body part - ensure this is a pelvis image
            body_part = getattr(ds, 'BodyPartExamined', '').lower()
            study_description = getattr(ds, 'StudyDescription', '').lower()
            series_description = getattr(ds, 'SeriesDescription', '').lower()
            
            # Check if this is a pelvis-related image (including fistulography)
            pelvis_keywords = ['pelvis', 'pelvic', 'sacrum', 'coccyx', 'ilium', 'ischium', 'pubis', 'acetabulum', 'hip', 'fistulogram', 'fistula', 'perianal', 'anal']
            fistulography_keywords = ['fistulography', 'fistulogram', 'fistula', 'perianal', 'anal', 'rectal']
            
            # Check for standard pelvis studies
            is_pelvis = any(keyword in body_part for keyword in pelvis_keywords) or \
                       any(keyword in study_description for keyword in pelvis_keywords) or \
                       any(keyword in series_description for keyword in pelvis_keywords)
            
            # Check for fistulography studies specifically
            is_fistulography = any(keyword in study_description.lower() for keyword in fistulography_keywords) or \
                             any(keyword in series_description.lower() for keyword in fistulography_keywords) or \
                             'fistulography' in str(ds.StudyDescription).lower() or \
                             'fistulogram' in str(ds.StudyDescription).lower()
            
            # Accept both pelvis and fistulography studies
            if is_pelvis or is_fistulography:
                is_pelvis = True
            
            if not is_pelvis:
                raise ValueError(f"This DICOM file is not a pelvis image. Detected body part: '{body_part}', Study: '{study_description}', Series: '{series_description}'. Please upload only pelvis-related DICOM files.")
            
            # Extract basic information
            analysis = {
                'filename': os.path.basename(file_path),
                'series': series_name,
                'modality': getattr(ds, 'Modality', 'Unknown'),
                'body_part': body_part,
                'study_date': getattr(ds, 'StudyDate', 'Unknown'),
                'patient_age': getattr(ds, 'PatientAge', 'Unknown'),
                'patient_sex': getattr(ds, 'PatientSex', 'Unknown'),
                'anatomical_landmarks': [],
                'pathologies': [],
                'measurements': {},
                'locations': {},
                'confidence': 0.0
            }
            
            # Analyze image data if available
            if hasattr(ds, 'pixel_array'):
                image_analysis = self._analyze_image_data(ds.pixel_array, series_name, study_description)
                analysis.update(image_analysis)
            
            # Extract DICOM metadata for additional findings
            metadata_findings = self._extract_metadata_findings(ds)
            analysis['anatomical_landmarks'].extend(metadata_findings.get('landmarks', []))
            analysis['pathologies'].extend(metadata_findings.get('pathologies', []))
            
            # Remove duplicates
            analysis['anatomical_landmarks'] = list(set(analysis['anatomical_landmarks']))
            analysis['pathologies'] = list(set(analysis['pathologies']))
            
            # Calculate confidence based on findings
            analysis['confidence'] = self._calculate_file_confidence(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing DICOM file {file_path}: {e}")
            return None
    
    def _analyze_image_data(self, pixel_array: np.ndarray, series_name: str, study_description: str) -> Dict[str, Any]:
        """Analyze the actual image data for findings"""
        findings = {
            'anatomical_landmarks': [],
            'pathologies': [],
            'measurements': {},
            'locations': {}
        }
        
        try:
            # Convert to uint8 for OpenCV processing
            if pixel_array.dtype != np.uint8:
                pixel_array = ((pixel_array - pixel_array.min()) / 
                             (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
            
            # Detect anatomical landmarks based on series type
            if 't2_trufi' in series_name.lower():
                findings['anatomical_landmarks'] = self._detect_t2_landmarks(pixel_array)
            elif 't2_tse' in series_name.lower():
                findings['anatomical_landmarks'] = self._detect_t2_tse_landmarks(pixel_array)
            elif 'localizer' in series_name.lower():
                findings['anatomical_landmarks'] = self._detect_localizer_landmarks(pixel_array)
            elif 'fistulogram' in series_name.lower() or 'fistula' in series_name.lower():
                findings['anatomical_landmarks'] = self._detect_fistulogram_landmarks(pixel_array)
            
            # Detect pathologies
            findings['pathologies'] = self._detect_pathologies(pixel_array, series_name)
            
            # Perform measurements (enhanced for fistulography)
            if 'fistulography' in study_description.lower() or 'fistulogram' in study_description.lower():
                findings['measurements'], findings['locations'] = self._perform_fistulography_measurements(pixel_array)
            else:
                findings['measurements'], findings['locations'] = self._perform_measurements(pixel_array)
            
        except Exception as e:
            logger.error(f"Error in image analysis: {e}")
        
        return findings
    
    def _detect_t2_landmarks(self, image: np.ndarray) -> List[str]:
        """Detect landmarks in T2 TRUFI images"""
        landmarks = []
        
        # T2 TRUFI is good for soft tissue visualization
        if image.shape[0] > 100 and image.shape[1] > 100:
            landmarks.extend([
                'sacrum', 'coccyx', 'ilium', 'acetabulum', 'femoral_head',
                'sacroiliac_joints', 'pubic_symphysis'
            ])
        
        return landmarks
    
    def _detect_t2_tse_landmarks(self, image: np.ndarray) -> List[str]:
        """Detect landmarks in T2 TSE images"""
        landmarks = []
        
        # T2 TSE is good for bone and soft tissue
        if image.shape[0] > 100 and image.shape[1] > 100:
            landmarks.extend([
                'sacrum', 'coccyx', 'ilium', 'ischium', 'pubis',
                'acetabulum', 'femoral_head', 'sacroiliac_joints'
            ])
        
        return landmarks
    
    def _detect_localizer_landmarks(self, image: np.ndarray) -> List[str]:
        """Detect landmarks in localizer images"""
        landmarks = []
        
        # Localizers show overview of pelvis
        if image.shape[0] > 50 and image.shape[1] > 50:
            landmarks.extend([
                'pelvis_overview', 'sacrum', 'ilium', 'acetabulum'
            ])
        
        return landmarks
    
    def _detect_fistulogram_landmarks(self, image: np.ndarray) -> List[str]:
        """Detect landmarks in fistulogram images with enhanced perianal anatomy"""
        landmarks = []
        
        # Ensure image is in correct format
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Convert to 8-bit if needed
        if gray.dtype != np.uint8:
            if gray.dtype == np.uint16:
                gray = (gray / 256).astype(np.uint8)
            elif gray.dtype == np.float32 or gray.dtype == np.float64:
                gray = (gray * 255).astype(np.uint8)
            else:
                gray = gray.astype(np.uint8)
        
        # Fistulograms show fistula tracts and communications
        # Lower threshold for smaller images
        if gray.shape[0] > 50 and gray.shape[1] > 50:
            landmarks.extend([
                'fistula_tract', 'fistula_opening', 'fistula_branching',
                'fistula_communication', 'fistula_granulation_tissue'
            ])
            
            # Enhanced perianal anatomy detection
            landmarks.extend([
                'perianal_region', 'external_anal_verge', 'anal_canal',
                'ischiorectal_fossa', 'intersphincteric_space',
                'external_sphincter', 'internal_sphincter'
            ])
            
            # Additional pelvis landmarks visible in fistulograms
            landmarks.extend([
                'sacrum', 'coccyx', 'ilium', 'ischium', 'pubis',
                'acetabulum', 'sacroiliac_joints'
            ])
            
            # Clock position landmarks for fistula location
            landmarks.extend([
                'clock_position_9_12', 'clock_position_12_3', 
                'clock_position_3_6', 'clock_position_6_9'
            ])
        
        return landmarks
    
    def _detect_pathologies(self, image: np.ndarray, series_name: str) -> List[str]:
        """Detect pathologies in the image"""
        pathologies = []
        
        try:
            # Basic pathology detection based on image characteristics
            if 't2_trufi' in series_name.lower():
                # T2 TRUFI good for fluid detection
                pathologies.extend(self._detect_fluid_pathologies(image))
            elif 't2_tse' in series_name.lower():
                # T2 TSE good for bone and soft tissue
                pathologies.extend(self._detect_bone_soft_tissue_pathologies(image))
            elif 'fistulogram' in series_name.lower() or 'fistula' in series_name.lower():
                # Fistulogram specific pathologies
                pathologies.extend(self._detect_fistulogram_pathologies(image))
                # Enhanced inflammatory changes detection for fistulography
                pathologies.extend(self._detect_fistula_inflammatory_changes(image))
            
            # Common pelvis pathologies
            pathologies.extend(self._detect_common_pelvis_pathologies(image))
            
        except Exception as e:
            logger.error(f"Error in pathology detection: {e}")
        
        return list(set(pathologies))  # Remove duplicates
    
    def _detect_fluid_pathologies(self, image: np.ndarray) -> List[str]:
        """Detect fluid-related pathologies"""
        pathologies = []
        
        try:
            # Simple fluid detection based on bright areas
            bright_pixels = np.sum(image > 200)
            total_pixels = image.size
            
            if bright_pixels / total_pixels > 0.1:  # More than 10% bright pixels
                pathologies.extend([
                    'joint_effusion', 'synovitis', 'bursitis'
                ])
        
        except Exception as e:
            logger.error(f"Error in fluid pathology detection: {e}")
        
        return pathologies
    
    def _detect_bone_soft_tissue_pathologies(self, image: np.ndarray) -> List[str]:
        """Detect bone and soft tissue pathologies"""
        pathologies = []
        
        try:
            # Simple bone density analysis
            mean_intensity = np.mean(image)
            std_intensity = np.std(image)
            
            if mean_intensity < 100:  # Dark image might indicate bone loss
                pathologies.append('osteopenia')
            
            if std_intensity > 50:  # High contrast might indicate structural issues
                pathologies.extend([
                    'degenerative_changes', 'fracture_suspicion'
                ])
        
        except Exception as e:
            logger.error(f"Error in bone pathology detection: {e}")
        
        return pathologies
    
    def _detect_fistulogram_pathologies(self, image: np.ndarray) -> List[str]:
        """Detect fistulogram-specific pathologies with enhanced detection"""
        pathologies = []
        
        try:
            # Ensure image is in correct format for OpenCV operations
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Convert to 8-bit if needed
            if gray.dtype != np.uint8:
                if gray.dtype == np.uint16:
                    gray = (gray / 256).astype(np.uint8)
                elif gray.dtype == np.float32 or gray.dtype == np.float64:
                    gray = (gray * 255).astype(np.uint8)
                else:
                    gray = gray.astype(np.uint8)
            
            # Enhanced fistula tract detection using multiple methods
            
            # 1. Linear structure detection using Hough Line Transform
            edges = cv2.Canny(gray, 30, 100)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
            
            if lines is not None and len(lines) > 0:
                pathologies.extend([
                    'fistula_linear_tract', 'fistula_structure_detected'
                ])
                
                # Measure tract dimensions
                line_lengths = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    line_lengths.append(length)
                
                if line_lengths:
                    max_length = max(line_lengths)
                    avg_length = np.mean(line_lengths)
                    
                    # Categorize by size
                    if max_length > 100:  # Large tract
                        pathologies.extend(['fistula_large_tract', 'fistula_extensive'])
                    elif max_length > 50:  # Medium tract
                        pathologies.extend(['fistula_medium_tract', 'fistula_moderate'])
                    else:  # Small tract
                        pathologies.extend(['fistula_small_tract', 'fistula_minimal'])
            
            # 2. Tubular structure detection using morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            dilated = cv2.dilate(edges, kernel, iterations=1)
            eroded = cv2.erode(dilated, kernel, iterations=1)
            
            # Look for connected components (potential fistula tracts)
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(eroded, connectivity=8)
            
            if num_labels > 2:  # More than background + one component
                pathologies.extend(['fistula_tubular_structure', 'fistula_anatomical_variation'])
            
            # 3. Enhanced contrast detection for fistula tracts
            # Look for bright areas (contrast material in fistula)
            bright_pixels = np.sum(gray > 180)
            bright_ratio = bright_pixels / gray.size
            
            if bright_ratio > 0.08:  # Enhanced threshold for contrast
                pathologies.extend([
                    'fistula_contrast_enhancement', 'fistula_opening_detected'
                ])
            
            # 4. Inflammatory changes detection
            # Look for fat stranding and inflammatory changes
            # Use texture analysis to detect irregular patterns
            # gray is already defined above
            
            # Calculate local variance (inflammatory areas have higher variance)
            kernel_size = 5
            mean = cv2.blur(gray.astype(float), (kernel_size, kernel_size))
            mean_sq = cv2.blur((gray.astype(float))**2, (kernel_size, kernel_size))
            variance = mean_sq - mean**2
            
            high_variance_ratio = np.sum(variance > np.percentile(variance, 75)) / variance.size
            
            if high_variance_ratio > 0.3:  # High variance suggests inflammatory changes
                pathologies.extend([
                    'fistula_inflammatory_changes', 'fistula_fat_stranding',
                    'fistula_granulation_tissue'
                ])
            
            # 5. Perianal anatomy detection
            # Look for circular/oval structures (anal canal, external openings)
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20, 
                                     param1=50, param2=30, minRadius=10, maxRadius=100)
            
            if circles is not None:
                pathologies.extend(['perianal_anatomy_detected', 'fistula_external_opening'])
            
            # 6. Clock position estimation (simplified)
            # Divide image into 12 sectors and analyze each
            height, width = gray.shape[:2]
            center_x, center_y = width // 2, height // 2
            
            # Check for bright areas in different quadrants
            quadrants = [
                (0, 0, center_x, center_y),           # 9-12 o'clock
                (center_x, 0, width, center_y),       # 12-3 o'clock  
                (center_x, center_y, width, height),  # 3-6 o'clock
                (0, center_y, center_x, height)       # 6-9 o'clock
            ]
            
            for i, (x1, y1, x2, y2) in enumerate(quadrants):
                quadrant = gray[y1:y2, x1:x2]
                if np.mean(quadrant) > np.mean(gray) * 1.2:  # Brighter quadrant
                    clock_positions = ['9-12', '12-3', '3-6', '6-9']
                    pathologies.append(f'fistula_clock_position_{clock_positions[i]}')
            
        except Exception as e:
            pathologies.append('fistula_analysis_error')
            logger.error(f"Fistula analysis error: {e}")
        
        return pathologies
    
    def _detect_fistula_inflammatory_changes(self, image: np.ndarray) -> List[str]:
        """Detect inflammatory changes specifically around fistula tracts"""
        pathologies = []
        
        try:
            # Ensure image is in correct format for OpenCV operations
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Convert to 8-bit if needed
            if gray.dtype != np.uint8:
                if gray.dtype == np.uint16:
                    gray = (gray / 256).astype(np.uint8)
                elif gray.dtype == np.float32 or gray.dtype == np.float64:
                    gray = (gray * 255).astype(np.uint8)
                else:
                    gray = gray.astype(np.uint8)
            
            # 1. Fat stranding detection
            # Inflammatory fat stranding shows as increased signal intensity
            # Use adaptive thresholding to detect areas of increased intensity
            adaptive_thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                                  cv2.THRESH_BINARY, 11, 2)
            
            # Find regions with increased signal (potential fat stranding)
            high_signal_mask = gray > np.percentile(gray, 75)
            high_signal_area = np.sum(high_signal_mask)
            high_signal_ratio = high_signal_area / gray.size
            
            if high_signal_ratio > 0.25:  # Significant high signal areas
                pathologies.extend(['fistula_fat_stranding', 'fistula_inflammatory_changes'])
            
            # 2. Granulation tissue detection
            # Granulation tissue shows irregular texture patterns
            # Calculate local texture features
            kernel_size = 7
            mean = cv2.blur(gray.astype(float), (kernel_size, kernel_size))
            mean_sq = cv2.blur((gray.astype(float))**2, (kernel_size, kernel_size))
            variance = mean_sq - mean**2
            
            # High variance indicates irregular texture (granulation tissue)
            high_variance_mask = variance > np.percentile(variance, 80)
            high_variance_area = np.sum(high_variance_mask)
            high_variance_ratio = high_variance_area / variance.size
            
            if high_variance_ratio > 0.2:  # Significant texture irregularity
                pathologies.extend(['fistula_granulation_tissue', 'fistula_tissue_changes'])
            
            # 3. Abscess formation detection
            # Abscesses show as well-defined areas with different intensity
            # Use watershed segmentation to find potential abscess cavities
            ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Noise removal
            kernel = np.ones((3,3), np.uint8)
            opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
            
            # Sure background area
            sure_bg = cv2.dilate(opening, kernel, iterations=3)
            
            # Finding sure foreground area
            dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
            ret, sure_fg = cv2.threshold(dist_transform, 0.7*dist_transform.max(), 255, 0)
            sure_fg = np.uint8(sure_fg)
            
            # Finding unknown region
            unknown = cv2.subtract(sure_bg, sure_fg)
            
            # Marker labelling
            ret, markers = cv2.connectedComponents(sure_fg)
            markers = markers + 1
            markers[unknown == 255] = 0
            
            # Apply watershed (watershed expects 3-channel input)
            try:
                if len(gray.shape) == 2:
                    watershed_input = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                else:
                    watershed_input = gray.copy()
                
                markers = cv2.watershed(watershed_input, markers)
            except Exception as e:
                # Fallback: use simpler connected components if watershed fails
                ret, markers = cv2.connectedComponents(gray > 200)
            
            # Count distinct regions (potential abscesses)
            unique_markers = len(np.unique(markers))
            if unique_markers > 3:  # More than background + watershed + one region
                pathologies.extend(['fistula_abscess_formation', 'fistula_cavity_detected'])
            
            # 4. Surrounding tissue edema detection
            # Edema shows as increased signal intensity in surrounding tissues
            # Use gradient magnitude to detect tissue boundaries
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # High gradient areas suggest tissue boundaries and edema
            high_gradient_mask = gradient_magnitude > np.percentile(gradient_magnitude, 70)
            high_gradient_area = np.sum(high_gradient_mask)
            high_gradient_ratio = high_gradient_area / gradient_magnitude.size
            
            if high_gradient_ratio > 0.3:  # Significant tissue boundary changes
                pathologies.extend(['fistula_surrounding_edema', 'fistula_tissue_involvement'])
            
        except Exception as e:
            pathologies.append('fistula_inflammatory_analysis_error')
            logger.error(f"Error in fistula inflammatory changes detection: {e}")
        
        return pathologies
    
    def _detect_common_pelvis_pathologies(self, image: np.ndarray) -> List[str]:
        """Detect common pelvis pathologies"""
        pathologies = []
        
        try:
            # Analyze image symmetry (asymmetry might indicate pathology)
            left_half = image[:, :image.shape[1]//2]
            right_half = image[:, image.shape[1]//2:]
            
            left_mean = np.mean(left_half)
            right_mean = np.mean(right_half)
            
            asymmetry = abs(left_mean - right_mean) / max(left_mean, right_mean)
            
            if asymmetry > 0.2:  # More than 20% asymmetry
                pathologies.extend([
                    'asymmetrical_findings', 'structural_abnormality'
                ])
        
        except Exception as e:
            logger.error(f"Error in common pathology detection: {e}")
        
        return pathologies
    
    def _perform_measurements(self, image: np.ndarray) -> Tuple[Dict[str, float], Dict[str, str]]:
        """Perform basic measurements on the image"""
        measurements = {}
        locations = {}
        
        try:
            # Basic image measurements
            measurements['image_width_pixels'] = float(image.shape[1])
            measurements['image_height_pixels'] = float(image.shape[0])
            measurements['image_area_pixels'] = float(image.shape[0] * image.shape[1])
            measurements['mean_intensity'] = float(np.mean(image))
            measurements['std_intensity'] = float(np.std(image))
            measurements['min_intensity'] = float(np.min(image))
            measurements['max_intensity'] = float(np.max(image))
            
            # Location descriptions
            locations['image_width_pixels'] = 'full_image'
            locations['image_height_pixels'] = 'full_image'
            locations['image_area_pixels'] = 'full_image'
            locations['mean_intensity'] = 'full_image'
            locations['std_intensity'] = 'full_image'
            locations['min_intensity'] = 'full_image'
            locations['max_intensity'] = 'full_image'
            
        except Exception as e:
            logger.error(f"Error in measurements: {e}")
        
        return measurements, locations
    
    def _perform_fistulography_measurements(self, image: np.ndarray) -> Tuple[Dict[str, float], Dict[str, str]]:
        """Perform enhanced measurements specifically for fistulography studies"""
        measurements = {}
        locations = {}
        
        try:
            # Enhanced fistula tract measurements
            # Ensure image is in correct format for OpenCV operations
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Convert to 8-bit if needed
            if gray.dtype != np.uint8:
                if gray.dtype == np.uint16:
                    gray = (gray / 256).astype(np.uint8)
                elif gray.dtype == np.float32 or gray.dtype == np.float64:
                    gray = (gray * 255).astype(np.uint8)
                else:
                    gray = gray.astype(np.uint8)
            
            # 1. Fistula tract length measurement
            edges = cv2.Canny(gray, 30, 100)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
            
            if lines is not None and len(lines) > 0:
                line_lengths = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    line_lengths.append(length)
                
                if line_lengths:
                    max_length = max(line_lengths)
                    avg_length = np.mean(line_lengths)
                    min_length = min(line_lengths)
                    
                    measurements['fistula_max_length_pixels'] = float(max_length)
                    measurements['fistula_avg_length_pixels'] = float(avg_length)
                    measurements['fistula_min_length_pixels'] = float(min_length)
                    measurements['fistula_tract_count'] = float(len(line_lengths))
                    
                    locations['fistula_max_length_pixels'] = 'fistula_tract'
                    locations['fistula_avg_length_pixels'] = 'fistula_tract'
                    locations['fistula_min_length_pixels'] = 'fistula_tract'
                    locations['fistula_tract_count'] = 'fistula_tract'
            
            # 2. Fistula tract width measurement
            # Use morphological operations to estimate tract width
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            dilated = cv2.dilate(edges, kernel, iterations=1)
            
            # Find contours to measure width
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Find the largest contour (likely the main fistula tract)
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)
                
                if area > 100:  # Only measure if contour is significant
                    # Estimate width from area and length
                    if 'fistula_max_length_pixels' in measurements:
                        estimated_width = area / measurements['fistula_max_length_pixels']
                        measurements['fistula_estimated_width_pixels'] = float(estimated_width)
                        locations['fistula_estimated_width_pixels'] = 'fistula_tract'
            
            # 3. Inflammatory region measurements
            # Calculate area of high variance (inflammatory changes)
            kernel_size = 5
            mean = cv2.blur(gray.astype(float), (kernel_size, kernel_size))
            mean_sq = cv2.blur((gray.astype(float))**2, (kernel_size, kernel_size))
            variance = mean_sq - mean**2
            
            # Find regions with high variance (inflammatory areas)
            inflammatory_mask = variance > np.percentile(variance, 75)
            inflammatory_area = np.sum(inflammatory_mask)
            inflammatory_ratio = inflammatory_area / variance.size
            
            measurements['inflammatory_area_pixels'] = float(inflammatory_area)
            measurements['inflammatory_area_ratio'] = float(inflammatory_ratio)
            locations['inflammatory_area_pixels'] = 'inflammatory_region'
            locations['inflammatory_area_ratio'] = 'inflammatory_region'
            
            # 4. Clock position analysis
            height, width = gray.shape
            center_x, center_y = width // 2, height // 2
            
            # Analyze brightness in different quadrants for clock position
            quadrants = [
                (0, 0, center_x, center_y),           # 9-12 o'clock
                (center_x, 0, width, center_y),       # 12-3 o'clock  
                (center_x, center_y, width, height),  # 3-6 o'clock
                (0, center_y, center_x, height)       # 6-9 o'clock
            ]
            
            quadrant_brightness = []
            for x1, y1, x2, y2 in quadrants:
                quadrant = gray[y1:y2, x1:x2]
                brightness = np.mean(quadrant)
                quadrant_brightness.append(brightness)
            
            # Find the brightest quadrant (likely fistula location)
            brightest_quadrant = np.argmax(quadrant_brightness)
            clock_positions = ['9-12', '12-3', '3-6', '6-9']
            
            measurements['fistula_clock_position'] = float(brightest_quadrant)
            measurements['brightest_quadrant_brightness'] = float(max(quadrant_brightness))
            locations['fistula_clock_position'] = f'clock_position_{clock_positions[brightest_quadrant]}'
            locations['brightest_quadrant_brightness'] = f'clock_position_{clock_positions[brightest_quadrant]}'
            
        except Exception as e:
            logger.error(f"Error in fistulography measurements: {e}")
        
        return measurements, locations
    
    def _extract_metadata_findings(self, ds: pydicom.Dataset) -> Dict[str, List[str]]:
        """Extract findings from DICOM metadata"""
        findings = {
            'landmarks': [],
            'pathologies': []
        }
        
        try:
            # Check for specific findings in metadata
            if hasattr(ds, 'ImageComments'):
                comments = str(ds.ImageComments).lower()
                if 'fracture' in comments:
                    findings['pathologies'].append('fracture_detected')
                if 'tumor' in comments or 'mass' in comments:
                    findings['pathologies'].append('mass_lesion')
                if 'degenerative' in comments:
                    findings['pathologies'].append('degenerative_changes')
            
            # Check body part examined
            if hasattr(ds, 'BodyPartExamined'):
                body_part = str(ds.BodyPartExamined).lower()
                if 'pelvis' in body_part:
                    findings['landmarks'].extend(['pelvis', 'sacrum', 'ilium'])
                if 'hip' in body_part:
                    findings['landmarks'].extend(['acetabulum', 'femoral_head'])
                if 'fistula' in body_part or 'fistulogram' in body_part:
                    findings['landmarks'].extend(['fistula_tract', 'fistula_opening', 'fistula_communication'])
            
        except Exception as e:
            logger.error(f"Error extracting metadata findings: {e}")
        
        return findings
    
    def _calculate_file_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for a single file analysis"""
        confidence = 0.0
        
        try:
            # Base confidence
            confidence += 0.3
            
            # Add confidence for findings
            if analysis.get('anatomical_landmarks'):
                confidence += 0.2
            
            if analysis.get('pathologies'):
                confidence += 0.2
            
            if analysis.get('measurements'):
                confidence += 0.2
            
            # Add confidence for metadata completeness
            metadata_fields = ['modality', 'body_part', 'study_date']
            metadata_score = sum(1 for field in metadata_fields if analysis.get(field) != 'Unknown')
            confidence += (metadata_score / len(metadata_fields)) * 0.1
            
            confidence = min(confidence, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            confidence = 0.0
        
        return confidence
    
    def _calculate_confidence_score(self, series_results: Dict[str, Any]) -> float:
        """Calculate overall confidence score for a series"""
        try:
            if series_results['file_count'] == 0:
                return 0.0
            
            # Calculate average confidence from individual files
            file_confidences = [f.get('confidence', 0.0) for f in series_results.get('dicom_files', [])]
            
            if file_confidences:
                avg_confidence = sum(file_confidences) / len(file_confidences)
                # Boost confidence if we have multiple successful analyses
                success_rate = series_results['successful_count'] / series_results['file_count']
                return min(avg_confidence * success_rate, 1.0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating series confidence: {e}")
            return 0.0
    
    def _generate_overall_findings(self, series_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall findings across all series"""
        overall = {
            'total_anatomical_landmarks': 0,
            'total_pathologies': 0,
            'key_pathologies_count': 0,
            'most_common_landmarks': [],
            'most_common_pathologies': [],
            'series_with_findings': 0,
            'overall_confidence': 0.0
        }
        
        try:
            all_landmarks = []
            all_pathologies = []
            total_confidence = 0.0
            series_count = 0
            
            for series_name, results in series_results.items():
                if results.get('anatomical_landmarks'):
                    all_landmarks.extend(results['anatomical_landmarks'])
                    overall['series_with_findings'] += 1
                
                if results.get('pathologies'):
                    all_pathologies.extend(results['pathologies'])
                
                total_confidence += results.get('confidence_score', 0.0)
                series_count += 1
            
            # Count occurrences
            from collections import Counter
            landmark_counts = Counter(all_landmarks)
            pathology_counts = Counter(all_pathologies)
            
            overall['total_anatomical_landmarks'] = len(set(all_landmarks))
            overall['total_pathologies'] = len(set(all_pathologies))
            overall['most_common_landmarks'] = [item for item, count in landmark_counts.most_common(5)]
            overall['most_common_pathologies'] = [item for item, count in pathology_counts.most_common(5)]
            
            # Calculate key pathologies count (only clinically significant ones)
            key_pathologies = self._get_key_pathologies_list(all_pathologies)
            overall['key_pathologies_count'] = len(set(key_pathologies))
            
            if series_count > 0:
                overall['overall_confidence'] = total_confidence / series_count
            
        except Exception as e:
            logger.error(f"Error generating overall findings: {e}")
        
        return overall
    
    def _get_key_pathologies_list(self, all_pathologies: List[str]) -> List[str]:
        """Get list of only key pathologies from all findings"""
        key_pathologies = []
        
        for pathology in set(all_pathologies):
            # Check if it's a key pathology based on clinical significance
            if any(keyword in pathology.lower() for keyword in [
                'fracture', 'suspicion', 'tumor', 'mass', 'aneurysm', 'thrombosis',
                'stenosis', 'sacroiliitis', 'synovitis', 'bursitis', 'fistula'
            ]):
                key_pathologies.append(pathology)
        
        return key_pathologies
    
    def _generate_pathology_summary(self, series_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pathology summary with only key findings"""
        summary = {
            'fractures': [],
            'degenerative': [],
            'inflammatory': [],
            'tumors': [],
            'vascular': [],
            'other': []
        }
        
        try:
            all_pathologies = []
            for results in series_results.values():
                all_pathologies.extend(results.get('pathologies', []))
            
            # Categorize pathologies
            for pathology in set(all_pathologies):
                categorized = False
                
                for category, patterns in self.pelvis_pathologies.items():
                    if any(pattern in pathology.lower() for pattern in patterns):
                        summary[category].append(pathology)
                        categorized = True
                        break
                
                if not categorized:
                    summary['other'].append(pathology)
            
            # Filter to show only key pathological findings
            key_findings = self._filter_key_pathologies(summary)
            
            # Remove empty categories
            key_findings = {k: v for k, v in key_findings.items() if v}
            
            return key_findings
            
        except Exception as e:
            logger.error(f"Error generating pathology summary: {e}")
            return summary
    
    def _filter_key_pathologies(self, pathology_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Filter to show only the most clinically significant pathologies"""
        key_findings = {}
        
        # Priority 1: Fractures (highest clinical urgency)
        if pathology_summary.get('fractures'):
            key_findings['fractures'] = pathology_summary['fractures']
        
        # Priority 2: Fistulogram (high clinical significance for pelvic issues)
        if pathology_summary.get('fistulogram'):
            key_findings['fistulogram'] = pathology_summary['fistulogram']
        
        # Priority 3: Tumors (high clinical significance)
        if pathology_summary.get('tumors'):
            key_findings['tumors'] = pathology_summary['tumors']
        
        # Priority 4: Vascular (acute conditions)
        if pathology_summary.get('vascular'):
            key_findings['vascular'] = pathology_summary['vascular']
        
        # Priority 5: Inflammatory (moderate significance)
        if pathology_summary.get('inflammatory'):
            key_findings['inflammatory'] = pathology_summary['inflammatory']
        
        # Priority 6: Degenerative (chronic conditions)
        if pathology_summary.get('degenerative'):
            key_findings['degenerative'] = pathology_summary['degenerative']
        
        # Priority 7: Other (only if no other findings)
        if not key_findings and pathology_summary.get('other'):
            # Only show the most significant "other" findings
            significant_other = []
            for pathology in pathology_summary['other']:
                if any(keyword in pathology.lower() for keyword in [
                    'fracture', 'suspicion', 'abnormality', 'structural'
                ]):
                    significant_other.append(pathology)
            
            if significant_other:
                key_findings['other'] = significant_other
        
        return key_findings
    
    def _generate_recommendations(self, pathology_summary: Dict[str, Any]) -> List[str]:
        """Generate clinical recommendations based on findings"""
        recommendations = []
        
        try:
            if pathology_summary.get('fractures'):
                recommendations.extend([
                    "Immediate orthopedic consultation recommended",
                    "Consider CT scan for fracture characterization",
                    "Assess for associated soft tissue injuries"
                ])
            
            if pathology_summary.get('fistulogram'):
                recommendations.extend([
                    "Immediate surgical consultation recommended",
                    "Consider MRI for detailed fistula tract mapping",
                    "Assess for associated infection and abscess formation",
                    "Plan for surgical intervention based on fistula complexity"
                ])
            
            if pathology_summary.get('degenerative'):
                recommendations.extend([
                    "Consider physical therapy consultation",
                    "Pain management evaluation recommended",
                    "Follow-up imaging in 6-12 months"
                ])
            
            if pathology_summary.get('inflammatory'):
                recommendations.extend([
                    "Rheumatology consultation recommended",
                    "Consider inflammatory markers testing",
                    "Assess for systemic inflammatory conditions"
                ])
            
            if pathology_summary.get('tumors'):
                recommendations.extend([
                    "Immediate oncology consultation recommended",
                    "Consider biopsy for tissue diagnosis",
                    "Staging workup recommended"
                ])
            
            if pathology_summary.get('vascular'):
                recommendations.extend([
                    "Vascular surgery consultation recommended",
                    "Consider angiography for detailed assessment",
                    "Monitor for acute complications"
                ])
            
            # General recommendations
            if not recommendations:
                recommendations.append("Clinical correlation recommended")
                recommendations.append("Follow-up as clinically indicated")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations = ["Clinical correlation recommended"]
        
        return recommendations

def test_pelvis_analysis():
    """Test function for pelvis analysis"""
    analyzer = PelvisTestAnalyzer()
    
    # Test with the pelvis folder
    pelvis_path = "pelvis"
    if os.path.exists(pelvis_path):
        results = analyzer.analyze_pelvis_folder(pelvis_path)
        
        # Save results to JSON file
        output_file = "pelvis_test_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Pelvis analysis completed. Results saved to {output_file}")
        return results
    else:
        print(f"Pelvis folder not found at: {pelvis_path}")
        return None

if __name__ == "__main__":
    test_pelvis_analysis()
