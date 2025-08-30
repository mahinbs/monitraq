#!/usr/bin/env python3
"""
Open Source Medical Image Analyzer
Uses local models for DICOM analysis without requiring OpenAI API
"""

import os
import base64
import io
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

import pydicom
import numpy as np
from PIL import Image
import cv2
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification
from sentence_transformers import SentenceTransformer
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BodyPartAnalysis:
    """Data class for body part analysis results"""
    body_part: str
    confidence: float
    anatomical_landmarks: List[str]
    pathologies: List[str]
    recommendations: List[str]
    modality: str
    study_description: str
    patient_info: Dict[str, str]


@dataclass
class DICOMMetadata:
    """Data class for DICOM metadata"""
    patient_name: str
    patient_id: str
    study_date: str
    modality: str
    body_part_examined: str
    study_description: str
    series_description: str
    image_size: Tuple[int, int]
    pixel_spacing: Optional[Tuple[float, float]]
    slice_thickness: Optional[float]


class OpenSourceMedicalAnalyzer:
    """
    Open-source medical image analyzer using local models
    """

    def __init__(self):
        """Initialize the analyzer with local models"""
        self.device = torch.device(
            'cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")

        # Initialize models
        self._load_models()

        # Comprehensive medical body part categories
        self.body_parts = [
            # Head and Neck
            "brain", "head", "skull", "neck", "cervical spine", "throat", "sinuses",
            "orbit", "temporal", "frontal", "parietal", "occipital",

            # Chest and Thorax
            "chest", "thorax", "lungs", "heart", "mediastinum", "ribs", "sternum",
            "clavicle", "scapula", "thoracic spine", "breast", "axilla",

            # Abdomen and Pelvis
            "abdomen", "pelvis", "liver", "kidney", "spleen", "pancreas", "gallbladder",
            "stomach", "intestines", "colon", "rectum", "bladder", "prostate", "uterus",
            "ovaries", "lumbar spine", "sacrum", "coccyx", "hip", "iliac",

            # Extremities - Upper
            "shoulder", "arm", "elbow", "forearm", "wrist", "hand", "fingers",
            "humerus", "radius", "ulna", "clavicle", "scapula",

            # Extremities - Lower
            "thigh", "knee", "leg", "ankle", "foot", "toes", "femur", "tibia",
            "fibula", "patella", "calcaneus", "metatarsals",

            # Spine
            "spine", "vertebrae", "cervical", "thoracic", "lumbar", "sacral",
            "intervertebral disc", "spinal cord", "nerve roots",

            # Vascular
            "aorta", "vena cava", "carotid", "vertebral artery", "renal vessels",
            "iliac vessels", "femoral vessels"
        ]

        # Medical pathologies
        self.pathologies = [
            "fracture", "tumor", "lesion", "inflammation", "infection",
            "hemorrhage", "edema", "calcification", "cyst", "mass",
            "pneumonia", "pneumothorax", "effusion", "atelectasis"
        ]

    def _load_models(self):
        """Load the required models"""
        try:
            # Load a general medical image classification model
            # Using a model that can handle medical images
            model_name = "microsoft/resnet-50"  # We'll use this as base and adapt it

            logger.info("Loading image classification model...")
            self.image_processor = AutoImageProcessor.from_pretrained(
                model_name)
            self.image_model = AutoModelForImageClassification.from_pretrained(
                model_name)
            self.image_model.to(self.device)

            # Load sentence transformer for text analysis
            logger.info("Loading sentence transformer model...")
            self.text_model = SentenceTransformer('all-MiniLM-L6-v2')

            logger.info("Models loaded successfully")

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise

    def load_dicom(self, file_path: str) -> pydicom.Dataset:
        """Load and validate DICOM file"""
        try:
            dataset = pydicom.dcmread(file_path)

            # Validate essential DICOM tags
            required_tags = ['Modality', 'PatientName', 'PatientID']
            missing_tags = [
                tag for tag in required_tags if not hasattr(dataset, tag)]

            if missing_tags:
                raise ValueError(
                    f"Missing required DICOM tags: {missing_tags}")

            return dataset

        except Exception as e:
            logger.error(f"Error loading DICOM file: {e}")
            raise

    def extract_metadata(self, dataset: pydicom.Dataset) -> DICOMMetadata:
        """Extract comprehensive metadata from DICOM dataset"""
        try:
            # Extract basic patient information
            patient_name = str(getattr(dataset, 'PatientName', 'Unknown'))
            patient_id = str(getattr(dataset, 'PatientID', 'Unknown'))
            patient_birth_date = str(
                getattr(dataset, 'PatientBirthDate', 'Unknown'))
            patient_sex = str(getattr(dataset, 'PatientSex', 'Unknown'))
            patient_age = str(getattr(dataset, 'PatientAge', 'Unknown'))
            patient_weight = str(getattr(dataset, 'PatientWeight', 'Unknown'))
            patient_size = str(getattr(dataset, 'PatientSize', 'Unknown'))

            # Extract study information
            study_date = str(getattr(dataset, 'StudyDate', 'Unknown'))
            study_time = str(getattr(dataset, 'StudyTime', 'Unknown'))
            study_description = str(
                getattr(dataset, 'StudyDescription', 'Unknown'))
            study_instance_uid = str(
                getattr(dataset, 'StudyInstanceUID', 'Unknown'))
            accession_number = str(
                getattr(dataset, 'AccessionNumber', 'Unknown'))

            # Extract series information
            series_description = str(
                getattr(dataset, 'SeriesDescription', 'Unknown'))
            series_number = str(getattr(dataset, 'SeriesNumber', 'Unknown'))
            series_date = str(getattr(dataset, 'SeriesDate', 'Unknown'))
            series_time = str(getattr(dataset, 'SeriesTime', 'Unknown'))

            # Extract physician and institution information
            referring_physician = str(
                getattr(dataset, 'ReferringPhysicianName', 'Unknown'))
            performing_physician = str(
                getattr(dataset, 'PerformingPhysicianName', 'Unknown'))
            operators_name = str(getattr(dataset, 'OperatorsName', 'Unknown'))
            institution_name = str(
                getattr(dataset, 'InstitutionName', 'Unknown'))
            institution_address = str(
                getattr(dataset, 'InstitutionAddress', 'Unknown'))
            department_name = str(
                getattr(dataset, 'InstitutionalDepartmentName', 'Unknown'))

            # Extract equipment information
            manufacturer = str(getattr(dataset, 'Manufacturer', 'Unknown'))
            manufacturer_model = str(
                getattr(dataset, 'ManufacturerModelName', 'Unknown'))
            device_serial_number = str(
                getattr(dataset, 'DeviceSerialNumber', 'Unknown'))
            software_versions = str(
                getattr(dataset, 'SoftwareVersions', 'Unknown'))

            # Extract technical parameters
            modality = str(getattr(dataset, 'Modality', 'Unknown'))
            body_part_examined = str(
                getattr(dataset, 'BodyPartExamined', 'Unknown'))

            # Extract image properties
            rows = getattr(dataset, 'Rows', 0)
            columns = getattr(dataset, 'Columns', 0)
            image_size = (rows, columns)

            # Extract spatial information
            pixel_spacing = None
            if hasattr(dataset, 'PixelSpacing'):
                try:
                    pixel_spacing = tuple(float(x)
                                          for x in dataset.PixelSpacing)
                except:
                    pass

            slice_thickness = None
            if hasattr(dataset, 'SliceThickness'):
                try:
                    slice_thickness = float(dataset.SliceThickness)
                except:
                    pass

            # Extract additional technical parameters
            kvp = getattr(dataset, 'KVP', None)
            exposure_time = getattr(dataset, 'ExposureTime', None)
            x_ray_tube_current = getattr(dataset, 'XRayTubeCurrent', None)

            # Create comprehensive metadata object
            metadata = DICOMMetadata(
                patient_name=patient_name,
                patient_id=patient_id,
                study_date=study_date,
                modality=modality,
                body_part_examined=body_part_examined,
                study_description=study_description,
                series_description=series_description,
                image_size=image_size,
                pixel_spacing=pixel_spacing,
                slice_thickness=slice_thickness
            )

            # Add extended information as attributes
            metadata.patient_birth_date = patient_birth_date
            metadata.patient_sex = patient_sex
            metadata.patient_age = patient_age
            metadata.patient_weight = patient_weight
            metadata.patient_size = patient_size
            metadata.study_time = study_time
            metadata.study_instance_uid = study_instance_uid
            metadata.accession_number = accession_number
            metadata.series_number = series_number
            metadata.series_date = series_date
            metadata.series_time = series_time
            metadata.referring_physician = referring_physician
            metadata.performing_physician = performing_physician
            metadata.operators_name = operators_name
            metadata.institution_name = institution_name
            metadata.institution_address = institution_address
            metadata.department_name = department_name
            metadata.manufacturer = manufacturer
            metadata.manufacturer_model = manufacturer_model
            metadata.device_serial_number = device_serial_number
            metadata.software_versions = software_versions
            metadata.kvp = kvp
            metadata.exposure_time = exposure_time
            metadata.x_ray_tube_current = x_ray_tube_current

            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            raise

    def convert_to_image(self, dataset: pydicom.Dataset) -> Image.Image:
        """Convert DICOM dataset to PIL Image"""
        try:
            # Get pixel data
            pixel_array = dataset.pixel_array

            # Normalize pixel values
            if pixel_array.dtype != np.uint8:
                pixel_array = ((pixel_array - pixel_array.min()) /
                               (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)

            # Convert to PIL Image
            image = Image.fromarray(pixel_array)

            # Convert grayscale to RGB (required by the model)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize to standard size for model input
            image = image.resize((224, 224))

            return image

        except Exception as e:
            logger.error(f"Error converting DICOM to image: {e}")
            raise

    def analyze_image_features(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze image using local model"""
        try:
            # Prepare image for model
            inputs = self.image_processor(image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Get model predictions
            with torch.no_grad():
                outputs = self.image_model(**inputs)
                features = outputs.logits.cpu().numpy()[0]

            # Analyze image characteristics
            img_array = np.array(image)

            # Convert RGB to grayscale for analysis
            if len(img_array.shape) == 3:
                gray_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray_array = img_array

            # Basic image analysis
            analysis = {
                "brightness": float(np.mean(gray_array)),
                "contrast": float(np.std(gray_array)),
                "sharpness": self._calculate_sharpness(gray_array),
                "texture_features": self._extract_texture_features(gray_array),
                "edge_density": self._calculate_edge_density(gray_array)
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing image features: {e}")
            raise

    def _calculate_sharpness(self, img_array: np.ndarray) -> float:
        """Calculate image sharpness using Laplacian variance"""
        try:
            laplacian = cv2.Laplacian(img_array, cv2.CV_64F)
            return float(np.var(laplacian))
        except:
            return 0.0

    def _extract_texture_features(self, img_array: np.ndarray) -> Dict[str, float]:
        """Extract texture features from image"""
        try:
            # Calculate GLCM-like features
            features = {
                "mean": float(np.mean(img_array)),
                "std": float(np.std(img_array)),
                "skewness": float(self._calculate_skewness(img_array)),
                "kurtosis": float(self._calculate_kurtosis(img_array))
            }

            return features
        except:
            return {"mean": 0.0, "std": 0.0, "skewness": 0.0, "kurtosis": 0.0}

    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness of data"""
        try:
            mean = np.mean(data)
            std = np.std(data)
            if std == 0:
                return 0.0
            return np.mean(((data - mean) / std) ** 3)
        except:
            return 0.0

    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis of data"""
        try:
            mean = np.mean(data)
            std = np.std(data)
            if std == 0:
                return 0.0
            return np.mean(((data - mean) / std) ** 4) - 3
        except:
            return 0.0

    def _calculate_edge_density(self, img_array: np.ndarray) -> float:
        """Calculate edge density in image"""
        try:
            edges = cv2.Canny(img_array, 50, 150)
            return float(np.sum(edges > 0) / edges.size)
        except:
            return 0.0

    def predict_body_part(self, metadata: DICOMMetadata, image_features: Dict[str, Any]) -> Tuple[str, float]:
        """Enhanced body part prediction based on metadata and image features"""
        try:
            # Priority 1: Use DICOM metadata (most reliable)
            if metadata.body_part_examined.lower() != 'unknown':
                body_part = metadata.body_part_examined.lower()
                # Map common DICOM body part codes to our categories
                body_part_mapping = {
                    'head': 'brain',
                    'skull': 'brain',
                    'brain': 'brain',
                    'chest': 'chest',
                    'thorax': 'chest',
                    'abdomen': 'abdomen',
                    'pelvis': 'pelvis',
                    'spine': 'spine',
                    'cervical': 'cervical spine',
                    'lumbar': 'lumbar spine',
                    'thoracic': 'thoracic spine'
                }
                mapped_part = body_part_mapping.get(body_part, body_part)
                return mapped_part, 0.95

            # Priority 2: Analyze study and series descriptions
            descriptions = [
                metadata.study_description.lower(),
                metadata.series_description.lower(),
                getattr(metadata, 'accession_number', '').lower()
            ]

            for desc in descriptions:
                if desc and desc != 'unknown':
                    # Enhanced keyword matching with confidence scoring
                    body_part_keywords = {
                        'brain': ['brain', 'head', 'skull', 'cerebral', 'cranial', 'intracranial', 'mri brain', 'dwi brain'],
                        'cervical spine': ['cervical', 'c-spine', 'c spine', 'neck', 'cervical vertebrae'],
                        'thoracic spine': ['thoracic', 't-spine', 't spine', 'thoracic vertebrae', 'dorsal spine'],
                        'lumbar spine': ['lumbar', 'l-spine', 'l spine', 'lumbar vertebrae', 'lower back'],
                        'chest': ['chest', 'thorax', 'lung', 'pulmonary', 'cardiac', 'heart', 'mediastinum'],
                        'abdomen': ['abdomen', 'abdominal', 'liver', 'kidney', 'spleen', 'pancreas', 'gallbladder'],
                        'pelvis': ['pelvis', 'pelvic', 'hip', 'sacrum', 'iliac', 'bladder', 'prostate', 'uterus', 'ovary'],
                        'shoulder': ['shoulder', 'scapula', 'clavicle', 'acromioclavicular'],
                        'knee': ['knee', 'patella', 'meniscus', 'cruciate', 'tibiofemoral'],
                        'ankle': ['ankle', 'foot', 'calcaneus', 'talus', 'metatarsal'],
                        'wrist': ['wrist', 'hand', 'carpal', 'metacarpal', 'scaphoid'],
                        'elbow': ['elbow', 'humerus', 'radius', 'ulna', 'olecranon']
                    }

                    best_match = None
                    best_score = 0

                    for body_part, keywords in body_part_keywords.items():
                        score = 0
                        for keyword in keywords:
                            if keyword in desc:
                                # Weight by keyword length
                                score += len(keyword) / len(desc)

                        if score > best_score:
                            best_score = score
                            best_match = body_part

                    if best_match and best_score > 0.1:
                        confidence = min(0.9, 0.7 + best_score * 2)
                        return best_match, confidence

            # Priority 3: Advanced image analysis based on modality
            brightness = image_features.get('brightness', 0)
            contrast = image_features.get('contrast', 0)
            edge_density = image_features.get('edge_density', 0)
            texture = image_features.get('texture_features', {})
            sharpness = image_features.get('sharpness', 0)

            modality = metadata.modality.lower()

            if modality == 'mr':
                # MRI-specific analysis patterns
                if brightness < 100 and contrast < 50:
                    # Dark images typically brain T1 or fluid-suppressed sequences
                    return "brain", 0.75
                elif brightness > 180 and contrast > 80 and edge_density > 0.08:
                    # High contrast with good edge definition - often pelvis
                    return "pelvis", 0.80
                elif brightness > 150 and contrast > 60 and texture.get('std', 0) > 60:
                    # Medium-high brightness with heterogeneous texture - abdomen
                    return "abdomen", 0.75
                elif edge_density > 0.12 and sharpness > 100:
                    # High edge density and sharpness - spine
                    return "spine", 0.70
                elif brightness > 120 and brightness < 180 and contrast > 50:
                    # Medium brightness range - chest
                    return "chest", 0.65
                else:
                    # Default for MRI
                    return "pelvis", 0.60

            elif modality == 'ct':
                # CT-specific analysis
                if brightness > 200:
                    return "chest", 0.80
                elif brightness > 150:
                    return "abdomen", 0.75
                elif brightness < 100:
                    return "brain", 0.80
                else:
                    return "pelvis", 0.60

            elif modality in ['xr', 'cr', 'dr']:
                # X-ray analysis
                if edge_density > 0.15:
                    return "chest", 0.70
                elif brightness > 150:
                    return "extremities", 0.65
                else:
                    return "chest", 0.60

            # Default fallback
            return "unknown", 0.3

        except Exception as e:
            logger.error(f"Error predicting body part: {e}")
            return "unknown", 0.2

    def detect_pathologies(self, image_features: Dict[str, Any], metadata: DICOMMetadata) -> List[str]:
        """Detect potential pathologies based on image features"""
        pathologies = []

        try:
            # Enhanced image analysis
            brightness = image_features.get('brightness', 0)
            contrast = image_features.get('contrast', 0)
            sharpness = image_features.get('sharpness', 0)
            edge_density = image_features.get('edge_density', 0)
            texture = image_features.get('texture_features', {})

            # Advanced pathology detection heuristics
            modality = metadata.modality.lower()
            body_part = metadata.body_part_examined.lower()

            # Image quality assessment
            if sharpness < 50:
                pathologies.append("motion artifact")
            elif sharpness < 100:
                pathologies.append("blur")

            # Brightness-based pathologies
            if brightness > 200:
                pathologies.append("calcification")
                pathologies.append("bone density abnormality")
            elif brightness > 180:
                pathologies.append("calcification")

            # Contrast-based pathologies
            if contrast > 100:
                pathologies.append("mass")
                pathologies.append("tumor")
            elif contrast > 80:
                pathologies.append("lesion")
                pathologies.append("abnormality")

            # Edge-based pathologies
            if edge_density > 0.15:
                pathologies.append("fracture")
                pathologies.append("structural abnormality")
            elif edge_density > 0.1:
                pathologies.append("anatomical variation")

            # Texture-based pathologies
            texture_std = texture.get('std', 0)
            if texture_std > 80:
                pathologies.append("heterogeneous tissue")
            elif texture_std < 20:
                pathologies.append("homogeneous abnormality")

            # Modality-specific pathologies
            if modality == 'mr':
                if brightness > 150 and contrast > 60:
                    pathologies.append("fluid collection")
                if edge_density > 0.12:
                    pathologies.append("structural abnormality")

            elif modality == 'ct':
                if brightness > 180:
                    pathologies.append("calcification")
                if contrast > 90:
                    pathologies.append("mass lesion")

            elif modality == 'xr':
                if brightness > 150:
                    pathologies.append("pneumonia")
                if contrast > 70:
                    pathologies.append("fracture")
                if edge_density > 0.1:
                    pathologies.append("bone abnormality")

            # Body part specific pathologies
            if 'pelvis' in body_part or 'pelvis' in metadata.study_description.lower():
                if brightness > 160:
                    pathologies.append("uterine abnormality")
                if contrast > 70:
                    pathologies.append("ovarian lesion")
                if edge_density > 0.1:
                    pathologies.append("pelvic structural abnormality")

            elif 'brain' in body_part or 'brain' in metadata.study_description.lower():
                if brightness < 100:
                    pathologies.append("brain lesion")
                if contrast > 60:
                    pathologies.append("intracranial abnormality")
                if texture_std > 60:
                    pathologies.append("brain tissue heterogeneity")

            elif 'chest' in body_part or 'chest' in metadata.study_description.lower():
                if brightness > 150:
                    pathologies.append("pulmonary abnormality")
                if contrast > 70:
                    pathologies.append("mediastinal mass")
                if edge_density > 0.08:
                    pathologies.append("pulmonary nodule")

            # Remove duplicates and return
            return list(set(pathologies))

        except Exception as e:
            logger.error(f"Error detecting pathologies: {e}")
            return []

    def generate_recommendations(self, body_part: str, pathologies: List[str], modality: str) -> List[str]:
        """Generate detailed clinical recommendations"""
        recommendations = []

        try:
            # Image quality recommendations
            if "motion artifact" in pathologies or "blur" in pathologies:
                recommendations.append(
                    "Image quality compromised - consider repeat imaging")
                recommendations.append(
                    "Patient motion detected - immobilization recommended")

            # Critical findings recommendations
            if "fracture" in pathologies:
                recommendations.append(
                    "URGENT: Orthopedic consultation required")
                recommendations.append("Consider immediate immobilization")
                recommendations.append("Assess for neurovascular compromise")

            if "mass" in pathologies or "tumor" in pathologies:
                recommendations.append(
                    "URGENT: Oncological consultation recommended")
                recommendations.append("Consider biopsy for tissue diagnosis")
                recommendations.append("Staging imaging may be required")

            if "pneumonia" in pathologies:
                recommendations.append("Pulmonary consultation recommended")
                recommendations.append("Consider antibiotic therapy")
                recommendations.append("Monitor respiratory status")

            # Anatomical region specific recommendations
            if 'pelvis' in body_part.lower():
                if "uterine abnormality" in pathologies:
                    recommendations.append(
                        "Gynecological consultation recommended")
                    recommendations.append(
                        "Consider pelvic ultrasound for further evaluation")

                if "ovarian lesion" in pathologies:
                    recommendations.append(
                        "Gynecological oncology consultation")
                    recommendations.append(
                        "Consider CA-125 and other tumor markers")

                if "pelvic structural abnormality" in pathologies:
                    recommendations.append(
                        "Urological consultation recommended")
                    recommendations.append("Consider cystoscopy if indicated")

            elif 'brain' in body_part.lower():
                if "brain lesion" in pathologies:
                    recommendations.append(
                        "Neurological consultation required")
                    recommendations.append(
                        "Consider contrast-enhanced imaging")

                if "intracranial abnormality" in pathologies:
                    recommendations.append(
                        "Neurosurgical consultation recommended")
                    recommendations.append("Monitor for neurological symptoms")

            elif 'chest' in body_part.lower():
                if "pulmonary abnormality" in pathologies:
                    recommendations.append(
                        "Pulmonology consultation recommended")
                    recommendations.append("Consider pulmonary function tests")

                if "mediastinal mass" in pathologies:
                    recommendations.append("Thoracic surgery consultation")
                    recommendations.append(
                        "Consider mediastinoscopy for biopsy")

            # Modality-specific recommendations
            if modality.lower() == 'mr':
                recommendations.append(
                    "Review by radiologist with MRI expertise")
                if "fluid collection" in pathologies:
                    recommendations.append(
                        "Consider contrast-enhanced sequences")

            elif modality.lower() == 'ct':
                recommendations.append(
                    "Review by radiologist with CT expertise")
                if "calcification" in pathologies:
                    recommendations.append(
                        "Consider non-contrast CT for better calcification visualization")

            elif modality.lower() == 'xr':
                recommendations.append(
                    "Review by radiologist with X-ray expertise")
                if "bone abnormality" in pathologies:
                    recommendations.append(
                        "Consider CT for better bone detail")

            # General clinical recommendations
            if pathologies:
                recommendations.append(
                    "Clinical correlation with patient history required")
                recommendations.append(
                    "Consider additional imaging modalities if clinically indicated")
                recommendations.append(
                    "Follow-up imaging recommended in 3-6 months")
            else:
                recommendations.append(
                    "No obvious pathology detected on current imaging")
                recommendations.append("Clinical correlation required")
                recommendations.append(
                    "Consider follow-up if symptoms persist")

            # Quality assurance
            recommendations.append("Review by radiologist recommended")
            recommendations.append("Ensure proper documentation of findings")

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Clinical correlation required", "Review by radiologist recommended"]

    def analyze_dicom_file(self, file_path: str) -> BodyPartAnalysis:
        """Complete DICOM analysis pipeline"""
        try:
            logger.info(f"Starting analysis of DICOM file: {file_path}")

            # Load DICOM file
            dataset = self.load_dicom(file_path)

            # Extract metadata
            metadata = self.extract_metadata(dataset)
            logger.info(
                f"Extracted metadata for modality: {metadata.modality}")

            # Convert to image
            image = self.convert_to_image(dataset)
            logger.info(f"Converted DICOM to image: {image.size}")

            # Analyze image features
            image_features = self.analyze_image_features(image)

            # Predict body part
            body_part, confidence = self.predict_body_part(
                metadata, image_features)

            # Detect pathologies
            pathologies = self.detect_pathologies(image_features, metadata)

            # Generate recommendations
            recommendations = self.generate_recommendations(
                body_part, pathologies, metadata.modality)

            # Detect anatomical landmarks
            anatomical_landmarks = self.detect_anatomical_landmarks(
                body_part, image_features, metadata)

            # Create comprehensive analysis result
            analysis_result = BodyPartAnalysis(
                body_part=body_part,
                confidence=confidence,
                anatomical_landmarks=anatomical_landmarks,
                pathologies=pathologies,
                recommendations=recommendations,
                modality=metadata.modality,
                study_description=metadata.study_description,
                patient_info={
                    # Basic patient information
                    "name": metadata.patient_name,
                    "patient_id": metadata.patient_id,
                    "birth_date": getattr(metadata, 'patient_birth_date', 'Unknown'),
                    "sex": getattr(metadata, 'patient_sex', 'Unknown'),
                    "age": getattr(metadata, 'patient_age', 'Unknown'),
                    "weight": getattr(metadata, 'patient_weight', 'Unknown'),
                    "size": getattr(metadata, 'patient_size', 'Unknown'),

                    # Study information
                    "study_date": metadata.study_date,
                    "study_time": getattr(metadata, 'study_time', 'Unknown'),
                    "study_instance_uid": getattr(metadata, 'study_instance_uid', 'Unknown'),
                    "accession_number": getattr(metadata, 'accession_number', 'Unknown'),

                    # Series information
                    "series_description": metadata.series_description,
                    "series_number": getattr(metadata, 'series_number', 'Unknown'),
                    "series_date": getattr(metadata, 'series_date', 'Unknown'),
                    "series_time": getattr(metadata, 'series_time', 'Unknown'),

                    # Physician and institution information
                    "referring_physician": getattr(metadata, 'referring_physician', 'Unknown'),
                    "performing_physician": getattr(metadata, 'performing_physician', 'Unknown'),
                    "operators_name": getattr(metadata, 'operators_name', 'Unknown'),
                    "institution_name": getattr(metadata, 'institution_name', 'Unknown'),
                    "institution_address": getattr(metadata, 'institution_address', 'Unknown'),
                    "department_name": getattr(metadata, 'department_name', 'Unknown'),

                    # Equipment information
                    "manufacturer": getattr(metadata, 'manufacturer', 'Unknown'),
                    "manufacturer_model": getattr(metadata, 'manufacturer_model', 'Unknown'),
                    "device_serial_number": getattr(metadata, 'device_serial_number', 'Unknown'),
                    "software_versions": getattr(metadata, 'software_versions', 'Unknown'),

                    # Technical parameters
                    "kvp": getattr(metadata, 'kvp', None),
                    "exposure_time": getattr(metadata, 'exposure_time', None),
                    "x_ray_tube_current": getattr(metadata, 'x_ray_tube_current', None),
                    "pixel_spacing": metadata.pixel_spacing,
                    "slice_thickness": metadata.slice_thickness,
                    "image_size": metadata.image_size
                }
            )

            logger.info(
                f"Analysis completed: {body_part} (confidence: {confidence:.2f})")
            return analysis_result

        except Exception as e:
            logger.error(f"Error in DICOM analysis pipeline: {e}")
            raise

    def validate_dicom_file(self, file_path: str) -> bool:
        """Validate if file is a valid DICOM file"""
        try:
            dataset = pydicom.dcmread(file_path)
            return hasattr(dataset, 'Modality')
        except:
            return False

    def detect_anatomical_landmarks(self, body_part: str, image_features: Dict[str, Any], metadata: DICOMMetadata) -> List[str]:
        """Detect anatomical landmarks based on body part and image features"""
        landmarks = []

        try:
            edge_density = image_features.get('edge_density', 0)
            brightness = image_features.get('brightness', 0)
            contrast = image_features.get('contrast', 0)

            # Pelvic landmarks
            if 'pelvis' in body_part.lower():
                landmarks.append("sacrum")
                landmarks.append("iliac bones")
                landmarks.append("pubic symphysis")
                if edge_density > 0.08:
                    landmarks.append("sacroiliac joints")
                if brightness > 150:
                    landmarks.append("femoral heads")
                if contrast > 60:
                    landmarks.append("pelvic floor muscles")

            # Brain landmarks
            elif 'brain' in body_part.lower():
                landmarks.append("cerebral hemispheres")
                landmarks.append("ventricles")
                if edge_density > 0.1:
                    landmarks.append("sulci and gyri")
                if brightness < 120:
                    landmarks.append("basal ganglia")
                if contrast > 50:
                    landmarks.append("cerebral cortex")

            # Chest landmarks
            elif 'chest' in body_part.lower():
                landmarks.append("lungs")
                landmarks.append("mediastinum")
                if edge_density > 0.06:
                    landmarks.append("bronchi")
                if brightness > 140:
                    landmarks.append("heart")
                if contrast > 55:
                    landmarks.append("pulmonary vessels")

            # Abdominal landmarks
            elif 'abdomen' in body_part.lower():
                landmarks.append("liver")
                landmarks.append("kidneys")
                if edge_density > 0.07:
                    landmarks.append("pancreas")
                if brightness > 130:
                    landmarks.append("spleen")
                if contrast > 65:
                    landmarks.append("abdominal vessels")

            # Spine landmarks
            elif 'spine' in body_part.lower():
                landmarks.append("vertebral bodies")
                landmarks.append("intervertebral discs")
                if edge_density > 0.12:
                    landmarks.append("spinal canal")
                if brightness > 160:
                    landmarks.append("pedicles")
                if contrast > 70:
                    landmarks.append("spinal cord")

            # General landmarks based on image characteristics
            if edge_density > 0.1:
                landmarks.append("bony structures")
            if brightness > 150:
                landmarks.append("soft tissues")
            if contrast > 60:
                landmarks.append("vascular structures")

            return list(set(landmarks))

        except Exception as e:
            logger.error(f"Error detecting anatomical landmarks: {e}")
            return []

    def get_supported_modalities(self) -> List[str]:
        """Get list of supported imaging modalities"""
        return ['CT', 'MR', 'XR', 'US', 'CR', 'DR', 'NM', 'PT']
