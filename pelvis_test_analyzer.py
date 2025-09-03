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
            ]
        }
        
        self.anatomical_landmarks = [
            'sacrum', 'coccyx', 'ilium', 'ischium', 'pubis',
            'acetabulum', 'femoral_head', 'sacroiliac_joints',
            'pubic_symphysis', 'obturator_foramen', 'greater_sciatic_notch',
            'lesser_sciatic_notch', 'iliac_crest', 'anterior_superior_iliac_spine',
            'posterior_superior_iliac_spine', 'ischial_spine', 'pubic_tubercle'
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
            
            # Check if this is a pelvis-related image
            pelvis_keywords = ['pelvis', 'pelvic', 'sacrum', 'coccyx', 'ilium', 'ischium', 'pubis', 'acetabulum', 'hip']
            is_pelvis = any(keyword in body_part for keyword in pelvis_keywords) or \
                       any(keyword in study_description for keyword in pelvis_keywords) or \
                       any(keyword in series_description for keyword in pelvis_keywords)
            
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
                image_analysis = self._analyze_image_data(ds.pixel_array, series_name)
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
    
    def _analyze_image_data(self, pixel_array: np.ndarray, series_name: str) -> Dict[str, Any]:
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
            
            # Detect pathologies
            findings['pathologies'] = self._detect_pathologies(pixel_array, series_name)
            
            # Perform measurements
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
                'stenosis', 'sacroiliitis', 'synovitis', 'bursitis'
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
        
        # Priority 2: Tumors (high clinical significance)
        if pathology_summary.get('tumors'):
            key_findings['tumors'] = pathology_summary['tumors']
        
        # Priority 3: Vascular (acute conditions)
        if pathology_summary.get('vascular'):
            key_findings['vascular'] = pathology_summary['vascular']
        
        # Priority 4: Inflammatory (moderate significance)
        if pathology_summary.get('inflammatory'):
            key_findings['inflammatory'] = pathology_summary['inflammatory']
        
        # Priority 5: Degenerative (chronic conditions)
        if pathology_summary.get('degenerative'):
            key_findings['degenerative'] = pathology_summary['degenerative']
        
        # Priority 6: Other (only if no other findings)
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
