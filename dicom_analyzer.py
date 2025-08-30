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
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

class DICOMAnalyzer:
    """
    Advanced DICOM analyzer using OpenAI for accurate body part detection and analysis
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the DICOM analyzer with OpenAI client
        
        Args:
            api_key: OpenAI API key (if not provided, will use environment variable)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it to constructor.")
        
        # Initialize OpenAI client with legacy API format
        try:
            import openai
            openai.api_key = self.api_key
            self.client = openai
            logger.info("Using legacy OpenAI client (v0.28.1)")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise ValueError("Could not initialize OpenAI client")
        self.supported_modalities = ['CT', 'MR', 'XR', 'US', 'CR', 'DR', 'NM', 'PT']
        
    def load_dicom(self, file_path: str) -> pydicom.Dataset:
        """
        Load and validate DICOM file
        
        Args:
            file_path: Path to DICOM file
            
        Returns:
            pydicom.Dataset: Loaded DICOM dataset
        """
        try:
            dataset = pydicom.dcmread(file_path)
            
            # Validate essential DICOM tags
            required_tags = ['Modality', 'PatientName', 'PatientID']
            missing_tags = [tag for tag in required_tags if not hasattr(dataset, tag)]
            
            if missing_tags:
                raise ValueError(f"Missing required DICOM tags: {missing_tags}")
            
            return dataset
            
        except Exception as e:
            logger.error(f"Error loading DICOM file: {e}")
            raise
    
    def extract_metadata(self, dataset: pydicom.Dataset) -> DICOMMetadata:
        """
        Extract comprehensive metadata from DICOM dataset
        
        Args:
            dataset: pydicom.Dataset object
            
        Returns:
            DICOMMetadata: Extracted metadata
        """
        try:
            # Extract basic patient information
            patient_name = str(getattr(dataset, 'PatientName', 'Unknown'))
            patient_id = str(getattr(dataset, 'PatientID', 'Unknown'))
            study_date = str(getattr(dataset, 'StudyDate', 'Unknown'))
            modality = str(getattr(dataset, 'Modality', 'Unknown'))
            
            # Extract body part and study information
            body_part_examined = str(getattr(dataset, 'BodyPartExamined', 'Unknown'))
            study_description = str(getattr(dataset, 'StudyDescription', 'Unknown'))
            series_description = str(getattr(dataset, 'SeriesDescription', 'Unknown'))
            
            # Extract image properties
            rows = getattr(dataset, 'Rows', 0)
            columns = getattr(dataset, 'Columns', 0)
            image_size = (rows, columns)
            
            # Extract spatial information
            pixel_spacing = None
            if hasattr(dataset, 'PixelSpacing'):
                pixel_spacing = tuple(dataset.PixelSpacing)
            
            slice_thickness = getattr(dataset, 'SliceThickness', None)
            
            return DICOMMetadata(
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
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            raise
    
    def convert_to_image(self, dataset: pydicom.Dataset) -> Image.Image:
        """
        Convert DICOM pixel data to PIL Image with proper windowing
        
        Args:
            dataset: pydicom.Dataset object
            
        Returns:
            PIL.Image: Converted image
        """
        try:
            # Get pixel data
            pixel_array = dataset.pixel_array
            
            # Apply window/level if available
            if hasattr(dataset, 'WindowCenter') and hasattr(dataset, 'WindowWidth'):
                window_center = dataset.WindowCenter
                window_width = dataset.WindowWidth
                
                # Handle multiple window settings
                if isinstance(window_center, pydicom.multival.MultiValue):
                    window_center = window_center[0]
                if isinstance(window_width, pydicom.multival.MultiValue):
                    window_width = window_width[0]
                
                # Apply windowing
                min_val = window_center - window_width // 2
                max_val = window_center + window_width // 2
                pixel_array = np.clip(pixel_array, min_val, max_val)
            
            # Normalize to 0-255 range
            if pixel_array.max() > 0:
                pixel_array = ((pixel_array - pixel_array.min()) / 
                             (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
            
            # Convert to PIL Image
            image = Image.fromarray(pixel_array)
            
            # Apply LUT if available
            if hasattr(dataset, 'VOILUTSequence'):
                # Apply VOI LUT transformation
                pass  # Complex LUT application would go here
            
            return image
            
        except Exception as e:
            logger.error(f"Error converting DICOM to image: {e}")
            raise
    
    def encode_image_for_openai(self, image: Image.Image) -> str:
        """
        Encode PIL image to base64 string for OpenAI API
        
        Args:
            image: PIL Image object
            
        Returns:
            str: Base64 encoded image
        """
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (OpenAI has size limits)
            max_size = 1024
            if max(image.size) > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str
            
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            raise
    
    def analyze_with_openai(self, image_base64: str, metadata: DICOMMetadata) -> Dict[str, Any]:
        """
        Analyze DICOM image using OpenAI Vision API for accurate body part detection
        
        Args:
            image_base64: Base64 encoded image
            metadata: DICOM metadata
            
        Returns:
            Dict: Analysis results from OpenAI
        """
        try:
            # Create comprehensive prompt for medical image analysis
            system_prompt = """You are an expert medical imaging AI assistant specializing in DICOM image analysis. 
            Your task is to accurately identify and analyze medical images with the following requirements:
            
            1. **Body Part Identification**: Precisely identify the anatomical body part(s) shown in the image
            2. **Anatomical Landmarks**: Identify key anatomical structures and landmarks visible
            3. **Pathology Detection**: Look for any visible pathologies, abnormalities, or concerning findings
            4. **Image Quality Assessment**: Evaluate image quality, positioning, and technical factors
            5. **Clinical Context**: Provide clinical insights based on the imaging modality and findings
            
            IMPORTANT: Be extremely accurate in body part identification. Common body parts include:
            - Head/Brain, Neck, Chest, Abdomen, Pelvis, Spine, Extremities (arms/legs)
            - Specific regions: Thorax, Lumbar spine, Cervical spine, etc.
            
            Provide your analysis in the following JSON format:
            {
                "body_part": "specific anatomical region",
                "confidence": 0.95,
                "anatomical_landmarks": ["landmark1", "landmark2"],
                "pathologies": ["pathology1", "pathology2"],
                "image_quality": "assessment",
                "clinical_insights": "insights",
                "recommendations": ["rec1", "rec2"]
            }
            """
            
            user_prompt = f"""Analyze this medical image with the following DICOM metadata:
            
            Modality: {metadata.modality}
            Body Part Examined: {metadata.body_part_examined}
            Study Description: {metadata.study_description}
            Series Description: {metadata.series_description}
            Image Size: {metadata.image_size}
            
            Please provide a comprehensive analysis focusing on accurate body part identification and any clinical findings."""
            
            # Use legacy OpenAI client API
            response = self.client.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            content = response.choices[0].message.content
            
            # Parse the response
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    analysis_result = json.loads(json_str)
                else:
                    # Fallback: create structured response from text
                    analysis_result = {
                        "body_part": "Unknown",
                        "confidence": 0.0,
                        "anatomical_landmarks": [],
                        "pathologies": [],
                        "image_quality": "Unable to assess",
                        "clinical_insights": content,
                        "recommendations": []
                    }
            except json.JSONDecodeError:
                logger.warning("Could not parse JSON from OpenAI response, using fallback")
                analysis_result = {
                    "body_part": "Unknown",
                    "confidence": 0.0,
                    "anatomical_landmarks": [],
                    "pathologies": [],
                    "image_quality": "Unable to assess",
                    "clinical_insights": content,
                    "recommendations": []
                }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in OpenAI analysis: {e}")
            raise
    
    def analyze_dicom_file(self, file_path: str) -> BodyPartAnalysis:
        """
        Complete DICOM analysis pipeline
        
        Args:
            file_path: Path to DICOM file
            
        Returns:
            BodyPartAnalysis: Complete analysis results
        """
        try:
            logger.info(f"Starting analysis of DICOM file: {file_path}")
            
            # Load DICOM file
            dataset = self.load_dicom(file_path)
            
            # Extract metadata
            metadata = self.extract_metadata(dataset)
            logger.info(f"Extracted metadata for modality: {metadata.modality}")
            
            # Convert to image
            image = self.convert_to_image(dataset)
            logger.info(f"Converted DICOM to image: {image.size}")
            
            # Encode for OpenAI
            image_base64 = self.encode_image_for_openai(image)
            
            # Analyze with OpenAI
            openai_result = self.analyze_with_openai(image_base64, metadata)
            logger.info(f"OpenAI analysis completed")
            
            # Create comprehensive analysis result
            analysis = BodyPartAnalysis(
                body_part=openai_result.get('body_part', 'Unknown'),
                confidence=openai_result.get('confidence', 0.0),
                anatomical_landmarks=openai_result.get('anatomical_landmarks', []),
                pathologies=openai_result.get('pathologies', []),
                recommendations=openai_result.get('recommendations', []),
                modality=metadata.modality,
                study_description=metadata.study_description,
                patient_info={
                    'name': metadata.patient_name,
                    'id': metadata.patient_id,
                    'study_date': metadata.study_date
                }
            )
            
            logger.info(f"Analysis completed successfully for body part: {analysis.body_part}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in DICOM analysis pipeline: {e}")
            raise
    
    def validate_dicom_file(self, file_path: str) -> bool:
        """
        Validate if file is a valid DICOM file
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            bool: True if valid DICOM file
        """
        try:
            dataset = pydicom.dcmread(file_path)
            return hasattr(dataset, 'Modality')
        except:
            return False
    
    def get_supported_modalities(self) -> List[str]:
        """
        Get list of supported imaging modalities
        
        Returns:
            List[str]: Supported modalities
        """
        return self.supported_modalities.copy()
