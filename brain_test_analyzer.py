#!/usr/bin/env python3
"""
Brain Test Analyzer - Specialized analysis for brain DICOM files
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

class BrainTestAnalyzer:
    """Specialized analyzer for brain DICOM files with enhanced pathology detection"""
    
    def __init__(self):
        self.brain_pathologies = {
            'ischemic': [
                'acute_ischemic_stroke',
                'subacute_ischemia',
                'chronic_ischemia',
                'lacunar_infarct',
                'watershed_infarct'
            ],
            'hemorrhagic': [
                'intracerebral_hemorrhage',
                'subarachnoid_hemorrhage',
                'subdural_hematoma',
                'epidural_hematoma',
                'microhemorrhage'
            ],
            'white_matter': [
                'white_matter_lesions',
                'demyelination',
                'leukoaraiosis',
                'multiple_sclerosis_lesions',
                'vasculitis_lesions'
            ],
            'mass_lesions': [
                'primary_brain_tumor',
                'metastatic_disease',
                'meningioma',
                'glioma',
                'cystic_lesions'
            ],
            'degenerative': [
                'brain_atrophy',
                'alzheimers_changes',
                'parkinsons_changes',
                'hydrocephalus',
                'ventricular_enlargement'
            ],
            'structural': [
                'developmental_anomaly',
                'chiari_malformation',
                'arachnoid_cyst',
                'pineal_cyst',
                'cavum_septum_pellucidum'
            ]
        }
        
        self.brain_landmarks = [
            'cerebral_hemispheres', 'cerebellum', 'brainstem', 'thalamus',
            'basal_ganglia', 'corpus_callosum', 'lateral_ventricles',
            'third_ventricle', 'fourth_ventricle', 'pituitary_gland',
            'pineal_gland', 'hippocampus', 'amygdala', 'optic_chiasm',
            'cerebral_peduncles', 'pons', 'medulla_oblongata'
        ]

    def analyze_brain_folder(self, folder_path: str) -> Dict[str, Any]:
        """Analyze all DICOM files in the brain folder"""
        logger.info(f"Starting brain folder analysis: {folder_path}")
        
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
            results['recommendations'] = self._generate_recommendations(results['overall_findings'])
            
        except Exception as e:
            logger.error(f"Error in brain folder analysis: {e}")
            results['error'] = str(e)
        
        return results

    def _analyze_series(self, series_path: str, series_name: str) -> Dict[str, Any]:
        """Analyze a single series within the brain folder"""
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
                    # This is a validation error (non-brain file)
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
            
            # Validate body part - ensure this is a brain image
            body_part = getattr(ds, 'BodyPartExamined', '').lower()
            study_description = getattr(ds, 'StudyDescription', '').lower()
            series_description = getattr(ds, 'SeriesDescription', '').lower()
            
            # Check if this is a brain-related image
            brain_keywords = ['brain', 'cerebral', 'cranial', 'head', 'skull', 'intracranial']
            is_brain = any(keyword in body_part for keyword in brain_keywords) or \
                      any(keyword in study_description for keyword in brain_keywords) or \
                      any(keyword in series_description for keyword in brain_keywords)
            
            if not is_brain:
                raise ValueError(f"This DICOM file is not a brain image. Detected body part: '{body_part}', Study: '{study_description}', Series: '{series_description}'. Please upload only brain-related DICOM files.")
            
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
                image_analysis = self._analyze_brain_image_data(ds.pixel_array, series_name)
                analysis.update(image_analysis)
            
            # Extract DICOM metadata for additional findings
            metadata_findings = self._extract_brain_metadata_findings(ds)
            analysis['anatomical_landmarks'].extend(metadata_findings.get('landmarks', []))
            analysis['pathologies'].extend(metadata_findings.get('pathologies', []))
            
            # Remove duplicates
            analysis['anatomical_landmarks'] = list(set(analysis['anatomical_landmarks']))
            analysis['pathologies'] = list(set(analysis['pathologies']))
            
            # Calculate confidence based on findings
            analysis['confidence'] = self._calculate_brain_file_confidence(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing DICOM file {file_path}: {e}")
            return None

    def _analyze_brain_image_data(self, pixel_array: np.ndarray, series_name: str) -> Dict[str, Any]:
        """Analyze the actual brain image data for findings"""
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
            if 't1' in series_name.lower():
                findings['anatomical_landmarks'] = self._detect_t1_landmarks(pixel_array)
            elif 't2' in series_name.lower() and 'flair' in series_name.lower():
                findings['anatomical_landmarks'] = self._detect_flair_landmarks(pixel_array)
            elif 'dwi' in series_name.lower():
                findings['anatomical_landmarks'] = self._detect_dwi_landmarks(pixel_array)
            elif 'swan' in series_name.lower():
                findings['anatomical_landmarks'] = self._detect_swan_landmarks(pixel_array)
            else:
                findings['anatomical_landmarks'] = self._detect_general_brain_landmarks(pixel_array)
            
            # Detect pathologies based on series type
            findings['pathologies'] = self._detect_brain_pathologies(pixel_array, series_name)
            
            # Perform measurements
            findings['measurements'], findings['locations'] = self._perform_brain_measurements(pixel_array)
            
        except Exception as e:
            logger.error(f"Error in brain image analysis: {e}")
        
        return findings
    
    def _detect_t1_landmarks(self, image: np.ndarray) -> List[str]:
        """Detect landmarks in T1 images"""
        landmarks = []
        
        # T1 is good for anatomical detail
        if image.shape[0] > 100 and image.shape[1] > 100:
            landmarks.extend([
                'cerebral_hemispheres', 'cerebellum', 'brainstem', 'thalamus',
                'basal_ganglia', 'corpus_callosum', 'lateral_ventricles'
            ])
        
        return landmarks
    
    def _detect_flair_landmarks(self, image: np.ndarray) -> List[str]:
        """Detect landmarks in T2 FLAIR images"""
        landmarks = []
        
        # FLAIR is good for white matter and pathology
        if image.shape[0] > 100 and image.shape[1] > 100:
            landmarks.extend([
                'white_matter', 'cerebral_cortex', 'ventricles', 'sulci',
                'gyri', 'corpus_callosum', 'periventricular_regions'
            ])
        
        return landmarks
    
    def _detect_dwi_landmarks(self, image: np.ndarray) -> List[str]:
        """Detect landmarks in DWI images"""
        landmarks = []
        
        # DWI is good for acute changes
        if image.shape[0] > 100 and image.shape[1] > 100:
            landmarks.extend([
                'cerebral_hemispheres', 'cerebellum', 'brainstem',
                'watershed_regions', 'basal_ganglia', 'thalamus'
            ])
        
        return landmarks
    
    def _detect_swan_landmarks(self, image: np.ndarray) -> List[str]:
        """Detect landmarks in SWAN images"""
        landmarks = []
        
        # SWAN is good for susceptibility effects
        if image.shape[0] > 100 and image.shape[1] > 100:
            landmarks.extend([
                'cerebral_hemispheres', 'cerebellum', 'brainstem',
                'basal_ganglia', 'thalamus', 'corpus_callosum'
            ])
        
        return landmarks
    
    def _detect_general_brain_landmarks(self, image: np.ndarray) -> List[str]:
        """Detect general brain landmarks"""
        landmarks = []
        
        if image.shape[0] > 100 and image.shape[1] > 100:
            landmarks.extend([
                'cerebral_hemispheres', 'cerebellum', 'brainstem'
            ])
        
        return landmarks

    def _detect_brain_pathologies(self, image: np.ndarray, series_name: str) -> List[str]:
        """Detect brain pathologies based on image analysis"""
        pathologies = []
        
        try:
            # Basic image analysis
            mean_intensity = np.mean(image)
            std_intensity = np.std(image)
            
            # Check for asymmetry (potential pathology)
            if image.shape[1] > 100:
                left_half = image[:, :image.shape[1]//2]
                right_half = image[:, image.shape[1]//2:]
                left_mean = np.mean(left_half)
                right_mean = np.mean(right_half)
                asymmetry = abs(left_mean - right_mean) / max(left_mean, right_mean)
                
                if asymmetry > 0.2:
                    pathologies.append('asymmetrical_findings')
            
            # Series-specific pathology detection
            if 'flair' in series_name.lower():
                pathologies.extend(self._detect_flair_pathologies(image))
            elif 'dwi' in series_name.lower():
                pathologies.extend(self._detect_dwi_pathologies(image))
            elif 'swan' in series_name.lower():
                pathologies.extend(self._detect_swan_pathologies(image))
            else:
                pathologies.extend(self._detect_general_brain_pathologies(image))
                
        except Exception as e:
            logger.error(f"Error in brain pathology detection: {e}")
        
        return pathologies
    
    def _detect_flair_pathologies(self, image: np.ndarray) -> List[str]:
        """Detect pathologies in FLAIR images"""
        pathologies = []
        
        try:
            # Look for hyperintense areas (potential white matter lesions)
            mean_intensity = np.mean(image)
            std_intensity = np.std(image)
            
            high_intensity_mask = image > (mean_intensity + 1.5 * std_intensity)
            if np.sum(high_intensity_mask) > 100:
                pathologies.append('white_matter_lesions_suspicion')
                
        except Exception as e:
            logger.error(f"Error in FLAIR pathology detection: {e}")
        
        return pathologies
    
    def _detect_dwi_pathologies(self, image: np.ndarray) -> List[str]:
        """Detect pathologies in DWI images"""
        pathologies = []
        
        try:
            # Look for hyperintense areas (potential acute ischemia)
            mean_intensity = np.mean(image)
            std_intensity = np.std(image)
            
            high_intensity_mask = image > (mean_intensity + 1.2 * std_intensity)
            if np.sum(high_intensity_mask) > 100:
                pathologies.append('acute_ischemia_suspicion')
                
        except Exception as e:
            logger.error(f"Error in DWI pathology detection: {e}")
        
        return pathologies
    
    def _detect_swan_pathologies(self, image: np.ndarray) -> List[str]:
        """Detect pathologies in SWAN images"""
        pathologies = []
        
        try:
            # Look for hypointense areas (potential hemorrhage or calcification)
            mean_intensity = np.mean(image)
            std_intensity = np.std(image)
            
            low_intensity_mask = image < (mean_intensity - 1.5 * std_intensity)
            if np.sum(low_intensity_mask) > 100:
                pathologies.append('hemorrhage_calcification_suspicion')
                
        except Exception as e:
            logger.error(f"Error in SWAN pathology detection: {e}")
        
        return pathologies
    
    def _detect_general_brain_pathologies(self, image: np.ndarray) -> List[str]:
        """Detect general brain pathologies"""
        pathologies = []
        
        try:
            # Basic pathology detection
            mean_intensity = np.mean(image)
            std_intensity = np.std(image)
            
            if std_intensity > 50:
                pathologies.append('structural_abnormality_suspicion')
                
        except Exception as e:
            logger.error(f"Error in general brain pathology detection: {e}")
        
        return pathologies

    def _perform_brain_measurements(self, image: np.ndarray) -> Tuple[Dict[str, float], Dict[str, str]]:
        """Perform basic measurements on the brain image"""
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
            locations['image_width_pixels'] = 'full_image'
            locations['image_area_pixels'] = 'full_image'
            locations['mean_intensity'] = 'full_image'
            locations['std_intensity'] = 'full_image'
            locations['min_intensity'] = 'full_image'
            locations['max_intensity'] = 'full_image'
            
        except Exception as e:
            logger.error(f"Error in brain measurements: {e}")
        
        return measurements, locations

    def _extract_brain_metadata_findings(self, ds: pydicom.Dataset) -> Dict[str, List[str]]:
        """Extract findings from brain DICOM metadata"""
        findings = {
            'landmarks': [],
            'pathologies': []
        }
        
        try:
            # Check for specific findings in metadata
            if hasattr(ds, 'ImageComments'):
                comments = str(ds.ImageComments).lower()
                if 'lesion' in comments:
                    findings['pathologies'].append('lesion_detected')
                if 'mass' in comments:
                    findings['pathologies'].append('mass_lesion')
                if 'edema' in comments:
                    findings['pathologies'].append('edema')
                if 'hemorrhage' in comments:
                    findings['pathologies'].append('hemorrhage')
            
            # Check series description for pathology clues
            if hasattr(ds, 'SeriesDescription'):
                series_desc = str(ds.SeriesDescription).lower()
                if 'tumor' in series_desc:
                    findings['pathologies'].append('tumor_imaging')
                if 'stroke' in series_desc:
                    findings['pathologies'].append('stroke_imaging')
                if 'trauma' in series_desc:
                    findings['pathologies'].append('trauma_imaging')
            
        except Exception as e:
            logger.error(f"Error extracting brain metadata findings: {e}")
        
        return findings

    def _calculate_brain_file_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for brain analysis"""
        confidence = 0.0
        
        try:
            # Base confidence
            confidence += 0.3
            
            # Add confidence for findings
            if analysis.get('anatomical_landmarks'):
                confidence += min(0.3, len(analysis['anatomical_landmarks']) * 0.05)
            
            if analysis.get('pathologies'):
                confidence += min(0.2, len(analysis['pathologies']) * 0.1)
            
            if analysis.get('measurements'):
                confidence += 0.1
            
            # Add confidence for metadata
            if analysis.get('metadata'):
                confidence += 0.1
            
            # Cap at 1.0
            confidence = min(1.0, confidence)
            
        except Exception as e:
            logger.error(f"Error calculating brain confidence: {e}")
            confidence = 0.0
        
        return confidence

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
            key_pathologies = self._get_key_brain_pathologies_list(all_pathologies)
            overall['key_pathologies_count'] = len(set(key_pathologies))
            
            if series_count > 0:
                overall['overall_confidence'] = total_confidence / series_count
            
        except Exception as e:
            logger.error(f"Error generating overall findings: {e}")
        
        return overall
    
    def _get_key_brain_pathologies_list(self, all_pathologies: List[str]) -> List[str]:
        """Get list of only key brain pathologies from all findings"""
        key_pathologies = []
        
        for pathology in set(all_pathologies):
            # Check if it's a key pathology based on clinical significance
            if any(keyword in pathology.lower() for keyword in [
                'stroke', 'ischemia', 'hemorrhage', 'tumor', 'mass', 'lesion',
                'edema', 'atrophy', 'trauma', 'suspicion'
            ]):
                key_pathologies.append(pathology)
        
        return key_pathologies
    
    def _generate_pathology_summary(self, series_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pathology summary with only key findings"""
        summary = {
            'ischemic': [],
            'hemorrhagic': [],
            'white_matter': [],
            'mass_lesions': [],
            'degenerative': [],
            'structural': [],
            'other': []
        }
        
        try:
            all_pathologies = []
            for results in series_results.values():
                all_pathologies.extend(results.get('pathologies', []))
            
            # Categorize pathologies
            for pathology in set(all_pathologies):
                categorized = False
                
                for category, patterns in self.brain_pathologies.items():
                    if any(pattern in pathology.lower() for pattern in patterns):
                        summary[category].append(pathology)
                        categorized = True
                        break
                
                if not categorized:
                    summary['other'].append(pathology)
            
            # Filter to show only key pathological findings
            key_findings = self._filter_key_brain_pathologies(summary)
            
            # Remove empty categories
            key_findings = {k: v for k, v in key_findings.items() if v}
            
            return key_findings
            
        except Exception as e:
            logger.error(f"Error generating brain pathology summary: {e}")
            return summary
    
    def _filter_key_brain_pathologies(self, pathology_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Filter to show only the most clinically significant brain pathologies"""
        key_findings = {}
        
        # Priority 1: Acute conditions
        if pathology_summary.get('ischemic'): key_findings['ischemic'] = pathology_summary['ischemic']
        if pathology_summary.get('hemorrhagic'): key_findings['hemorrhagic'] = pathology_summary['hemorrhagic']
        
        # Priority 2: Mass lesions
        if pathology_summary.get('mass_lesions'): key_findings['mass_lesions'] = pathology_summary['mass_lesions']
        
        # Priority 3: White matter
        if pathology_summary.get('white_matter'): key_findings['white_matter'] = pathology_summary['white_matter']
        
        # Priority 4: Degenerative
        if pathology_summary.get('degenerative'): key_findings['degenerative'] = pathology_summary['degenerative']
        
        # Priority 5: Structural
        if pathology_summary.get('structural'): key_findings['structural'] = pathology_summary['structural']
        
        # Priority 6: Other (only if no other findings and contains significant keywords)
        if not key_findings and pathology_summary.get('other'):
            significant_other = []
            for pathology in pathology_summary['other']:
                if any(keyword in pathology.lower() for keyword in ['suspicion', 'abnormality', 'structural', 'lesion']):
                    significant_other.append(pathology)
            if significant_other: key_findings['other'] = significant_other
        
        return key_findings
    
    def _generate_recommendations(self, overall_findings: Dict[str, Any]) -> List[str]:
        """Generate clinical recommendations based on findings"""
        recommendations = []
        
        try:
            total_pathologies = overall_findings.get('total_pathologies', 0)
            key_pathologies = overall_findings.get('key_pathologies_count', 0)
            
            if key_pathologies > 0:
                recommendations.append("Immediate clinical correlation required")
                recommendations.append("Consider contrast enhancement if not already performed")
                recommendations.append("Neurological consultation recommended")
                recommendations.append("Follow-up imaging in 3-6 months")
            elif total_pathologies > 0:
                recommendations.append("Clinical correlation recommended")
                recommendations.append("Follow-up as clinically indicated")
            else:
                recommendations.append("No acute pathology detected")
                recommendations.append("Clinical correlation as needed")
                recommendations.append("Follow-up per standard protocols")
            
            # Add specific recommendations based on findings
            if 'ischemic' in str(overall_findings).lower():
                recommendations.append("Consider stroke protocol imaging")
                recommendations.append("Neurological assessment for acute symptoms")
            
            if 'hemorrhagic' in str(overall_findings).lower():
                recommendations.append("Immediate neurosurgical consultation if acute")
                recommendations.append("Monitor for mass effect and herniation")
            
            if 'mass_lesions' in str(overall_findings).lower():
                recommendations.append("Contrast-enhanced imaging recommended")
                recommendations.append("Oncological consultation if primary tumor suspected")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations = ["Clinical correlation recommended", "Follow-up as clinically indicated"]
        
        return recommendations
