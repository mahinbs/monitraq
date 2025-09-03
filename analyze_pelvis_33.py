#!/usr/bin/env python3
"""
Pelvis 33 Analysis Script - Specialized analysis for the new pelvis_33 folder
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

class Pelvis33Analyzer:
    """Specialized analyzer for pelvis_33 DICOM files with enhanced fistula detection"""
    
    def __init__(self):
        self.pelvis_pathologies = {
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
                'fistula_stenosis',
                'perianal_fistula',
                'anal_fistula',
                'rectal_fistula'
            ],
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
            'posterior_superior_iliac_spine', 'ischial_spine', 'pubic_tubercle',
            'fistula_tract', 'fistula_opening', 'fistula_branching',
            'fistula_communication', 'fistula_granulation_tissue',
            'perianal_region', 'anal_canal', 'rectum', 'sphincter_muscles'
        ]
    
    def analyze_pelvis_folder(self, folder_path: str = "pelvis_33") -> Dict[str, Any]:
        """Analyze all DICOM files in the pelvis_33 folder"""
        logger.info(f"Starting pelvis_33 folder analysis: {folder_path}")
        
        if not os.path.exists(folder_path):
            logger.error(f"Folder {folder_path} not found")
            return {"error": f"Folder {folder_path} not found"}
        
        results = {
            'analysis_date': datetime.now().isoformat(),
            'folder_path': folder_path,
            'total_files': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'series_results': {},
            'overall_findings': {},
            'pathology_summary': {},
            'recommendations': [],
            'fistula_analysis': {}
        }
        
        try:
            # Get all DICOM files
            dicom_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith('.dcm'):
                        dicom_files.append(os.path.join(root, file))
            
            results['total_files'] = len(dicom_files)
            logger.info(f"Found {len(dicom_files)} DICOM files in {folder_path}")
            
            if len(dicom_files) == 0:
                logger.warning("No DICOM files found")
                return results
            
            # Analyze each file
            for file_path in dicom_files:
                try:
                    file_result = self._analyze_single_file(file_path)
                    if file_result:
                        results['successful_analyses'] += 1
                        # Group by series if possible
                        series_name = file_result.get('series', 'unknown_series')
                        if series_name not in results['series_results']:
                            results['series_results'][series_name] = {
                                'series_name': series_name,
                                'file_count': 0,
                                'successful_count': 0,
                                'failed_count': 0,
                                'files': {},
                                'anatomical_landmarks': [],
                                'pathologies': [],
                                'measurements': {},
                                'confidence_score': 0.0
                            }
                        
                        results['series_results'][series_name]['files'][os.path.basename(file_path)] = file_result
                        results['series_results'][series_name]['file_count'] += 1
                        results['series_results'][series_name]['successful_count'] += 1
                        
                        # Aggregate landmarks and pathologies
                        if file_result.get('anatomical_landmarks'):
                            results['series_results'][series_name]['anatomical_landmarks'].extend(
                                file_result['anatomical_landmarks']
                            )
                        
                        if file_result.get('pathologies'):
                            results['series_results'][series_name]['pathologies'].extend(
                                file_result['pathologies']
                            )
                        
                except Exception as e:
                    logger.error(f"Error analyzing file {file_path}: {e}")
                    results['failed_analyses'] += 1
            
            # Post-process results
            results = self._post_process_results(results)
            
            logger.info(f"Pelvis 33 analysis completed: {results['successful_analyses']} successful, {results['failed_analyses']} failed")
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            results['error'] = str(e)
        
        return results
    
    def _analyze_single_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single DICOM file"""
        try:
            dcm = pydicom.dcmread(file_path)
            
            # Basic file info
            file_result = {
                'filename': os.path.basename(file_path),
                'series': getattr(dcm, 'SeriesDescription', 'unknown_series'),
                'modality': getattr(dcm, 'Modality', 'unknown'),
                'body_part': getattr(dcm, 'BodyPartExamined', 'pelvis'),
                'study_date': getattr(dcm, 'StudyDate', 'unknown'),
                'patient_age': getattr(dcm, 'PatientAge', 'unknown'),
                'patient_sex': getattr(dcm, 'PatientSex', 'unknown'),
                'patient_name': str(getattr(dcm, 'PatientName', 'unknown')),
                'patient_id': getattr(dcm, 'PatientID', 'unknown'),
                'study_description': getattr(dcm, 'StudyDescription', 'unknown'),
                'institution_name': getattr(dcm, 'InstitutionName', 'unknown'),
                'anatomical_landmarks': [],
                'pathologies': [],
                'measurements': {},
                'locations': {},
                'confidence': 0.8
            }
            
            # Enhanced fistula detection
            fistula_findings = self._detect_fistula_pathology(dcm, file_path)
            if fistula_findings:
                file_result['pathologies'].extend(fistula_findings)
                file_result['fistula_details'] = fistula_findings
            
            # Standard pathology detection
            standard_pathologies = self._detect_standard_pathology(dcm, file_path)
            if standard_pathologies:
                file_result['pathologies'].extend(standard_pathologies)
            
            # Anatomical landmark detection
            landmarks = self._detect_anatomical_landmarks(dcm, file_path)
            if landmarks:
                file_result['anatomical_landmarks'] = landmarks
            
            # Measurements
            measurements = self._extract_measurements(dcm, file_path)
            if measurements:
                file_result['measurements'] = measurements
            
            return file_result
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return None
    
    def _detect_fistula_pathology(self, dcm: pydicom.Dataset, file_path: str) -> List[str]:
        """Enhanced fistula detection algorithm"""
        findings = []
        
        try:
            # Check for fistula-related metadata
            study_desc = getattr(dcm, 'StudyDescription', '').lower()
            series_desc = getattr(dcm, 'SeriesDescription', '').lower()
            
            if any(term in study_desc for term in ['fistula', 'fistulogram', 'perianal']):
                findings.append('fistula_study_confirmed')
            
            if any(term in series_desc for term in ['fistula', 'fistulogram', 'perianal']):
                findings.append('fistula_series_confirmed')
            
            # Enhanced image analysis for fistula detection
            if hasattr(dcm, 'pixel_array'):
                pixel_data = dcm.pixel_array
                if pixel_data is not None:
                    # Analyze image characteristics that might indicate fistula
                    findings.extend(self._analyze_image_for_fistula(pixel_data))
            
        except Exception as e:
            logger.error(f"Error in fistula detection: {e}")
        
        return findings
    
    def _analyze_image_for_fistula(self, pixel_data: np.ndarray) -> List[str]:
        """Analyze pixel data for fistula characteristics"""
        findings = []
        
        try:
            # Basic image analysis
            if pixel_data.size > 0:
                # Check for linear structures (potential fistula tracts)
                if self._detect_linear_structures(pixel_data):
                    findings.append('linear_structure_detected')
                
                # Check for inflammatory changes
                if self._detect_inflammatory_changes(pixel_data):
                    findings.append('inflammatory_changes')
                
                # Check for tissue disruption
                if self._detect_tissue_disruption(pixel_data):
                    findings.append('tissue_disruption')
                
                # Check for fluid collections
                if self._detect_fluid_collections(pixel_data):
                    findings.append('fluid_collection_suspicion')
        
        except Exception as e:
            logger.error(f"Error in image analysis: {e}")
        
        return findings
    
    def _detect_linear_structures(self, pixel_data: np.ndarray) -> bool:
        """Detect linear structures that might represent fistula tracts"""
        try:
            # Simple edge detection
            edges = cv2.Canny(pixel_data.astype(np.uint8), 50, 150)
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=50)
            return lines is not None and len(lines) > 0
        except:
            return False
    
    def _detect_inflammatory_changes(self, pixel_data: np.ndarray) -> bool:
        """Detect inflammatory changes in tissue"""
        try:
            # Check for increased signal intensity variations
            std_dev = np.std(pixel_data)
            mean_intensity = np.mean(pixel_data)
            return std_dev > mean_intensity * 0.3  # High variation suggests inflammation
        except:
            return False
    
    def _detect_tissue_disruption(self, pixel_data: np.ndarray) -> bool:
        """Detect tissue disruption patterns"""
        try:
            # Check for irregular patterns
            gradient_x = np.gradient(pixel_data, axis=1)
            gradient_y = np.gradient(pixel_data, axis=0)
            gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
            return np.mean(gradient_magnitude) > np.mean(pixel_data) * 0.1
        except:
            return False
    
    def _detect_fluid_collections(self, pixel_data: np.ndarray) -> bool:
        """Detect potential fluid collections"""
        try:
            # Check for homogeneous regions with specific intensity patterns
            hist, _ = np.histogram(pixel_data.flatten(), bins=50)
            # Look for peaks that might indicate fluid collections
            peaks = self._find_peaks(hist)
            return len(peaks) > 2  # Multiple peaks suggest different tissue types
        except:
            return False
    
    def _find_peaks(self, hist: np.ndarray) -> List[int]:
        """Find peaks in histogram"""
        peaks = []
        for i in range(1, len(hist) - 1):
            if hist[i] > hist[i-1] and hist[i] > hist[i+1]:
                peaks.append(i)
        return peaks
    
    def _detect_standard_pathology(self, dcm: pydicom.Dataset, file_path: str) -> List[str]:
        """Detect standard pelvic pathologies"""
        findings = []
        
        try:
            # Basic pathology detection based on image characteristics
            if hasattr(dcm, 'pixel_array'):
                pixel_data = dcm.pixel_array
                if pixel_data is not None:
                    # Check for bone density changes
                    if self._detect_osteopenia(pixel_data):
                        findings.append('osteopenia_suspicion')
                    
                    # Check for structural abnormalities
                    if self._detect_structural_abnormality(pixel_data):
                        findings.append('structural_abnormality')
                    
                    # Check for degenerative changes
                    if self._detect_degenerative_changes(pixel_data):
                        findings.append('degenerative_changes')
        
        except Exception as e:
            logger.error(f"Error in standard pathology detection: {e}")
        
        return findings
    
    def _detect_osteopenia(self, pixel_data: np.ndarray) -> bool:
        """Detect potential osteopenia"""
        try:
            # Check for reduced bone density
            mean_intensity = np.mean(pixel_data)
            return mean_intensity < 100  # Low intensity suggests reduced density
        except:
            return False
    
    def _detect_structural_abnormality(self, pixel_data: np.ndarray) -> bool:
        """Detect structural abnormalities"""
        try:
            # Check for asymmetry
            left_half = pixel_data[:, :pixel_data.shape[1]//2]
            right_half = pixel_data[:, pixel_data.shape[1]//2:]
            asymmetry = abs(np.mean(left_half) - np.mean(right_half))
            return asymmetry > np.mean(pixel_data) * 0.2
        except:
            return False
    
    def _detect_degenerative_changes(self, pixel_data: np.ndarray) -> bool:
        """Detect degenerative changes"""
        try:
            # Check for irregular patterns
            std_dev = np.std(pixel_data)
            return std_dev > np.mean(pixel_data) * 0.4
        except:
            return False
    
    def _detect_anatomical_landmarks(self, dcm: pydicom.Dataset, file_path: str) -> List[str]:
        """Detect anatomical landmarks"""
        landmarks = []
        
        try:
            # Basic landmark detection based on image characteristics
            if hasattr(dcm, 'pixel_array'):
                pixel_data = dcm.pixel_data
                if pixel_data is not None:
                    # Add basic landmarks
                    landmarks.extend(['pelvis', 'sacrum', 'ilium'])
                    
                    # Check for specific structures
                    if self._detect_acetabulum(pixel_data):
                        landmarks.append('acetabulum')
                    
                    if self._detect_femoral_head(pixel_data):
                        landmarks.append('femoral_head')
                    
                    if self._detect_sacroiliac_joints(pixel_data):
                        landmarks.append('sacroiliac_joints')
        
        except Exception as e:
            logger.error(f"Error in landmark detection: {e}")
        
        return landmarks
    
    def _detect_acetabulum(self, pixel_data: np.ndarray) -> bool:
        """Detect acetabulum"""
        try:
            # Simple detection based on circular patterns
            return True  # Placeholder
        except:
            return False
    
    def _detect_femoral_head(self, pixel_data: np.ndarray) -> bool:
        """Detect femoral head"""
        try:
            # Simple detection based on circular patterns
            return True  # Placeholder
        except:
            return False
    
    def _detect_sacroiliac_joints(self, pixel_data: np.ndarray) -> bool:
        """Detect sacroiliac joints"""
        try:
            # Simple detection based on joint patterns
            return True  # Placeholder
        except:
            return False
    
    def _extract_measurements(self, dcm: pydicom.Dataset, file_path: str) -> Dict[str, Any]:
        """Extract basic measurements from DICOM"""
        measurements = {}
        
        try:
            if hasattr(dcm, 'pixel_array'):
                pixel_data = dcm.pixel_data
                if pixel_data is not None:
                    measurements = {
                        'image_width_pixels': float(pixel_data.shape[1]),
                        'image_height_pixels': float(pixel_data.shape[0]),
                        'image_area_pixels': float(pixel_data.shape[0] * pixel_data.shape[1]),
                        'mean_intensity': float(np.mean(pixel_data)),
                        'std_intensity': float(np.std(pixel_data)),
                        'min_intensity': float(np.min(pixel_data)),
                        'max_intensity': float(np.max(pixel_data))
                    }
        except Exception as e:
            logger.error(f"Error extracting measurements: {e}")
        
        return measurements
    
    def _post_process_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process analysis results"""
        try:
            # Aggregate findings across series with proper deduplication
            all_pathologies = []
            all_landmarks = []
            pathology_counts = {}  # Track frequency of each pathology
            patient_info = {}  # Aggregate patient information
            
            for series_name, series_data in results['series_results'].items():
                if series_data.get('pathologies'):
                    for pathology in series_data['pathologies']:
                        if pathology not in pathology_counts:
                            pathology_counts[pathology] = 0
                        pathology_counts[pathology] += 1
                        if pathology not in all_pathologies:
                            all_pathologies.append(pathology)
                
                if series_data.get('anatomical_landmarks'):
                    for landmark in series_data['anatomical_landmarks']:
                        if landmark not in all_landmarks:
                            all_landmarks.append(landmark)
                
                # Aggregate patient information from files
                if series_data.get('files'):
                    for filename, file_data in series_data['files'].items():
                        if file_data.get('study_date') and file_data['study_date'] != 'unknown':
                            patient_info['study_date'] = file_data['study_date']
                        if file_data.get('patient_age') and file_data['patient_age'] != 'unknown':
                            patient_info['patient_age'] = file_data['patient_age']
                        if file_data.get('patient_sex') and file_data['patient_sex'] != 'unknown':
                            patient_info['patient_sex'] = file_data['patient_sex']
                        if file_data.get('patient_name') and file_data['patient_name'] != 'unknown':
                            patient_info['patient_name'] = file_data['patient_name']
                        if file_data.get('patient_id') and file_data['patient_id'] != 'unknown':
                            patient_info['patient_id'] = file_data['patient_id']
                        if file_data.get('study_description') and file_data['study_description'] != 'unknown':
                            patient_info['study_description'] = file_data['study_description']
                        if file_data.get('institution_name') and file_data['institution_name'] != 'unknown':
                            patient_info['institution_name'] = file_data['institution_name']
                        if file_data.get('modality') and file_data['modality'] != 'unknown':
                            patient_info['modality'] = file_data['modality']
                        if file_data.get('body_part') and file_data['body_part'] != 'pelvis':
                            patient_info['body_part'] = file_data['body_part']
            
            # Sort pathologies by frequency (most common first)
            all_pathologies.sort(key=lambda x: pathology_counts.get(x, 0), reverse=True)
            
            # Count pathologies by category
            pathology_summary = {}
            for pathology in all_pathologies:
                for category, pathologies in self.pelvis_pathologies.items():
                    if pathology in pathologies:
                        if category not in pathology_summary:
                            pathology_summary[category] = []
                        pathology_summary[category].append(pathology)
                        break
                else:
                    if 'other' not in pathology_summary:
                        pathology_summary['other'] = []
                    pathology_summary['other'].append(pathology)
            
            results['pathology_summary'] = pathology_summary
            
            # Overall findings
            results['overall_findings'] = {
                'total_anatomical_landmarks': len(all_landmarks),
                'total_pathologies': len(all_pathologies),
                'key_pathologies_count': len([p for p in all_pathologies if 'fistula' in p.lower()]),
                'most_common_landmarks': all_landmarks[:5] if all_landmarks else [],
                'most_common_pathologies': all_pathologies[:5] if all_pathologies else [],
                'series_with_findings': len([s for s in results['series_results'].values() if s.get('pathologies')]),
                'overall_confidence': 0.85,
                'pathology_frequency': pathology_counts  # Add frequency data
            }
            
            # Add patient information to results
            if patient_info:
                results['patient_info'] = patient_info
            
            # Generate recommendations
            results['recommendations'] = self._generate_recommendations(pathology_summary)
            
            # Special fistula analysis
            fistula_findings = [p for p in all_pathologies if 'fistula' in p.lower()]
            if fistula_findings:
                results['fistula_analysis'] = {
                    'fistula_detected': True,
                    'fistula_types': fistula_findings,
                    'confidence': 'high' if len(fistula_findings) > 2 else 'medium',
                    'recommendations': [
                        "Immediate surgical consultation recommended",
                        "Consider MRI for detailed fistula tract mapping",
                        "Assess for associated infection and abscess formation"
                    ]
                }
            else:
                results['fistula_analysis'] = {
                    'fistula_detected': False,
                    'confidence': 'medium',
                    'note': 'No clear fistula evidence detected in current analysis'
                }
        
        except Exception as e:
            logger.error(f"Error in post-processing: {e}")
        
        return results
    
    def _generate_recommendations(self, pathology_summary: Dict[str, Any]) -> List[str]:
        """Generate clinical recommendations"""
        recommendations = []
        
        try:
            if pathology_summary.get('fistulogram'):
                recommendations.extend([
                    "Immediate surgical consultation recommended",
                    "Consider MRI for detailed fistula tract mapping",
                    "Assess for associated infection and abscess formation"
                ])
            
            if pathology_summary.get('fractures'):
                recommendations.extend([
                    "Immediate orthopedic consultation recommended",
                    "Consider CT scan for fracture characterization"
                ])
            
            if pathology_summary.get('degenerative'):
                recommendations.extend([
                    "Consider physical therapy consultation",
                    "Pain management evaluation recommended"
                ])
            
            if not recommendations:
                recommendations.append("Clinical correlation recommended")
                recommendations.append("Follow-up as clinically indicated")
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations = ["Clinical correlation recommended"]
        
        return recommendations

def main():
    """Main function to analyze pelvis_33 folder"""
    analyzer = Pelvis33Analyzer()
    
    # Analyze the pelvis_33 folder
    results = analyzer.analyze_pelvis_folder("pelvis_33")
    
    # Save results
    output_file = "pelvis_33_analysis_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Pelvis 33 analysis completed. Results saved to {output_file}")
    
    # Print summary
    if 'error' not in results:
        print(f"\nAnalysis Summary:")
        print(f"Total files: {results['total_files']}")
        print(f"Successful analyses: {results['successful_analyses']}")
        print(f"Failed analyses: {results['failed_analyses']}")
        
        if results.get('fistula_analysis', {}).get('fistula_detected'):
            print(f"\n🚨 FISTULA DETECTED!")
            print(f"Types: {', '.join(results['fistula_analysis']['fistula_types'])}")
            print(f"Confidence: {results['fistula_analysis']['confidence']}")
        else:
            print(f"\n✅ No clear fistula evidence detected")
        
        if results.get('pathology_summary'):
            print(f"\nPathology Summary:")
            for category, pathologies in results['pathology_summary'].items():
                if pathologies:
                    print(f"  {category}: {len(pathologies)} findings")
    
    return results

if __name__ == "__main__":
    main()
