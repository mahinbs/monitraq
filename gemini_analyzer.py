import google.generativeai as genai
import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class GeminiAnalysis:
    """Results from Gemini AI analysis"""
    summary: str
    clinical_insights: List[str]
    differential_diagnosis: List[str]
    recommendations: List[str]
    risk_assessment: str
    follow_up_plan: str
    ai_confidence: float

class GeminiAnalyzer:
    """Gemini AI-powered medical image analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini AI analyzer"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning("No Gemini API key provided. Set GEMINI_API_KEY environment variable.")
            self.client = None
        else:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini AI analyzer initialized successfully")
    
    def analyze_dicom_data(self, analysis_results: List[Dict[str, Any]], patient_data: Dict[str, Any] = None) -> GeminiAnalysis:
        """Analyze DICOM data using Gemini AI"""
        if not self.client:
            return self._generate_fallback_analysis(analysis_results)
        
        try:
            # Prepare comprehensive data for Gemini
            analysis_summary = self._prepare_analysis_summary(analysis_results)
            
            # Create detailed prompt for medical analysis
            prompt = self._create_medical_analysis_prompt(analysis_summary, patient_data)
            
            # Get Gemini response
            response = self.client.generate_content(prompt)
            
            # Parse and structure the response
            return self._parse_gemini_response(response.text, analysis_results)
            
        except Exception as e:
            logger.error(f"Error in Gemini analysis: {e}")
            return self._generate_fallback_analysis(analysis_results)
    
    def _prepare_analysis_summary(self, analysis_results: List[Dict[str, Any]]) -> str:
        """Prepare comprehensive summary of all analysis results"""
        summary_parts = []
        
        # Group by body part
        body_part_groups = {}
        for result in analysis_results:
            body_part = result.get('body_part', 'unknown')
            if body_part not in body_part_groups:
                body_part_groups[body_part] = []
            body_part_groups[body_part].append(result)
        
        summary_parts.append(f"Total DICOM files analyzed: {len(analysis_results)}")
        
        for body_part, results in body_part_groups.items():
            summary_parts.append(f"\n{body_part.upper()} ANALYSIS ({len(results)} files):")
            
            # Collect all pathologies
            all_pathologies = []
            all_landmarks = []
            modalities = set()
            confidences = []
            
            for result in results:
                pathologies = result.get('pathologies', [])
                landmarks = result.get('anatomical_landmarks', [])
                modality = result.get('modality', 'unknown')
                confidence = result.get('confidence', 0)
                
                all_pathologies.extend(pathologies)
                all_landmarks.extend(landmarks)
                modalities.add(modality)
                confidences.append(confidence)
            
            # Remove duplicates and count
            pathology_counts = {}
            for pathology in all_pathologies:
                pathology_counts[pathology] = pathology_counts.get(pathology, 0) + 1
            
            landmark_counts = {}
            for landmark in all_landmarks:
                landmark_counts[landmark] = landmark_counts.get(landmark, 0) + 1
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            summary_parts.append(f"  - Modality: {', '.join(modalities)}")
            summary_parts.append(f"  - Average confidence: {avg_confidence:.2f}")
            
            if pathology_counts:
                summary_parts.append(f"  - Pathologies detected:")
                for pathology, count in pathology_counts.items():
                    summary_parts.append(f"    * {pathology} ({count} files)")
            
            if landmark_counts:
                summary_parts.append(f"  - Anatomical landmarks:")
                for landmark, count in landmark_counts.items():
                    summary_parts.append(f"    * {landmark} ({count} files)")
        
        return "\n".join(summary_parts)
    
    def _create_medical_analysis_prompt(self, analysis_summary: str, patient_data: Dict[str, Any] = None) -> str:
        """Create detailed medical analysis prompt for Gemini AI - comprehensive doctor report"""
        current_date = datetime.now().strftime('%B %d, %Y at %H:%M')
        
        # Extract patient information
        patient_name = patient_data.get('patient_name', 'UNKNOWN') if patient_data else 'UNKNOWN'
        patient_id = patient_data.get('patient_id', 'N/A') if patient_data else 'N/A'
        patient_sex = patient_data.get('patient_sex', 'Unknown') if patient_data else 'Unknown'
        patient_age = patient_data.get('patient_age', 'Unknown') if patient_data else 'Unknown'
        study_date = patient_data.get('study_date', 'Unknown') if patient_data else 'Unknown'
        doctor_name = patient_data.get('doctor_name', 'DR. RADIOLOGIST') if patient_data else 'DR. RADIOLOGIST'
        modality = patient_data.get('modality', 'Unknown') if patient_data else 'Unknown'
        
        return f"""
You are {doctor_name}, an expert radiologist with 20+ years of experience. Generate a COMPREHENSIVE, DETAILED medical radiology report in professional doctor's format with multiple paragraphs.

PATIENT INFORMATION:
- Name: {patient_name}
- ID: {patient_id}
- Sex: {patient_sex}
- Age: {patient_age}
- Study Date: {study_date}
- Modality: {modality}

ANALYSIS DATA:
{analysis_summary}

REQUIREMENTS:
- Write as a detailed, professional radiologist report
- Use proper medical terminology and clinical language
- Organize in clear sections with detailed paragraphs
- Include comprehensive findings, assessment, and recommendations
- Write in first person as the reporting radiologist
- Provide detailed explanations for each finding
- Include clinical correlations and differential diagnoses

FORMAT (Write detailed paragraphs for each section):

**CLINICAL INDICATION:**
[Write a detailed paragraph about the clinical indication and reason for the study]

**TECHNIQUE:**
[Describe the imaging technique and technical parameters in a professional paragraph]

**FINDINGS:**
[Write 2-3 detailed paragraphs describing all imaging findings in comprehensive detail. Include:
- Detailed anatomical observations
- Specific measurements where relevant
- Comparison with normal anatomy
- Description of any abnormalities or pathologies
- Detailed characterization of each finding]

**IMPRESSION:**
[Write a detailed paragraph with:
- Clear summary of key findings
- Primary diagnosis or differential diagnoses
- Clinical significance of findings
- Degree of confidence in findings]

**RECOMMENDATIONS:**
[Write a detailed paragraph with:
- Specific clinical recommendations
- Follow-up imaging suggestions
- Clinical correlation needs
- Further workup if indicated]

**REPORTED BY:**
{doctor_name}
Board-Certified Radiologist
Report Date: {current_date}

IMPORTANT: Write in detailed, comprehensive paragraphs using professional medical language. Each section should be substantial and informative, not brief summaries.
"""
    
    def _parse_gemini_response(self, response_text: str, analysis_results: List[Dict[str, Any]]) -> GeminiAnalysis:
        """Parse Gemini response into structured analysis"""
        try:
            # Extract sections from the detailed report
            sections = self._extract_report_sections(response_text)
            
            # Create comprehensive summary from all sections
            full_report = response_text.strip()
            
            # Extract specific sections for structured data
            clinical_insights = []
            if sections.get('findings'):
                clinical_insights.append(sections['findings'])
            if sections.get('impression'):
                clinical_insights.append(sections['impression'])
                
            differential_diagnosis = []
            if sections.get('impression'):
                # Extract potential diagnoses from impression
                impression_text = sections['impression'].lower()
                if 'differential' in impression_text or 'diagnosis' in impression_text:
                    differential_diagnosis.append(sections['impression'])
                else:
                    differential_diagnosis.append("Clinical correlation required for definitive diagnosis")
            
            recommendations = []
            if sections.get('recommendations'):
                recommendations.append(sections['recommendations'])
            else:
                recommendations.append("Follow-up imaging and clinical correlation recommended")
            
            risk_assessment = "Moderate risk level" 
            if sections.get('impression'):
                impression_lower = sections['impression'].lower()
                if any(word in impression_lower for word in ['severe', 'critical', 'urgent', 'emergent']):
                    risk_assessment = "High risk - requires immediate attention"
                elif any(word in impression_lower for word in ['mild', 'minor', 'stable', 'benign']):
                    risk_assessment = "Low risk - routine follow-up"
            
            follow_up_plan = sections.get('recommendations', "Standard follow-up imaging recommended")
            
            return GeminiAnalysis(
                summary=full_report,  # Use the entire detailed report
                clinical_insights=clinical_insights,
                differential_diagnosis=differential_diagnosis,
                recommendations=recommendations,
                risk_assessment=risk_assessment,
                follow_up_plan=follow_up_plan,
                ai_confidence=0.90  # High confidence for detailed Gemini analysis
            )
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return self._generate_fallback_analysis(analysis_results)
    
    def _extract_from_raw_response(self, response_text: str) -> Dict[str, Any]:
        """Extract content from raw Gemini response when structured parsing fails"""
        sections = {}
        
        # Split into lines and look for content
        lines = response_text.split('\n')
        
        # Extract differential diagnosis
        diff_diagnosis = []
        in_diff_section = False
        for line in lines:
            line = line.strip()
            if 'DIFFERENTIAL DIAGNOSIS' in line.upper() or 'DIAGNOSIS' in line.upper():
                in_diff_section = True
                continue
            elif in_diff_section and line and len(line) > 20:
                if any(keyword in line.upper() for keyword in ['RECOMMENDATIONS', 'RISK', 'FOLLOW', 'CLINICAL']):
                    break
                # Clean up the line
                clean_line = line.replace('**', '').strip()
                if clean_line and len(clean_line) > 10:
                    diff_diagnosis.append(clean_line)
        
        # Extract recommendations
        recommendations = []
        in_rec_section = False
        for line in lines:
            line = line.strip()
            if 'RECOMMENDATIONS' in line.upper() or 'TREATMENT' in line.upper():
                in_rec_section = True
                continue
            elif in_rec_section and line and len(line) > 20:
                if any(keyword in line.upper() for keyword in ['RISK', 'FOLLOW', 'CLINICAL', 'IMPRESSION']):
                    break
                # Clean up the line
                clean_line = line.replace('**', '').strip()
                if clean_line and len(clean_line) > 10:
                    recommendations.append(clean_line)
        
        # Extract risk assessment
        risk_text = ""
        for line in lines:
            if 'RISK' in line.upper() and 'ASSESSMENT' in line.upper():
                risk_text = line
                break
        
        # Extract follow-up plan
        follow_up_text = ""
        for line in lines:
            if 'FOLLOW' in line.upper() and 'PLAN' in line.upper():
                follow_up_text = line
                break
        
        # Create a summary from the content
        summary_parts = []
        if diff_diagnosis:
            summary_parts.append(f"Analysis identified {len(diff_diagnosis)} potential diagnoses.")
        if recommendations:
            summary_parts.append(f"Generated {len(recommendations)} clinical recommendations.")
        
        sections = {
            'summary': ' '.join(summary_parts) if summary_parts else 'Comprehensive medical analysis completed with detailed findings and recommendations.',
            'clinical_insights': [],
            'differential_diagnosis': diff_diagnosis[:5],  # Limit to 5
            'recommendations': recommendations[:5],  # Limit to 5
            'risk_assessment': risk_text if risk_text else 'Moderate risk level identified.',
            'follow_up_plan': follow_up_text if follow_up_text else 'Follow-up imaging and clinical correlation recommended.'
        }
        
        return sections
    
    def _extract_report_sections(self, response_text: str) -> Dict[str, str]:
        """Extract detailed report sections from Gemini response"""
        sections = {}
        
        try:
            # Define section markers
            section_markers = [
                ('clinical_indication', '**CLINICAL INDICATION:**'),
                ('technique', '**TECHNIQUE:**'),
                ('findings', '**FINDINGS:**'),
                ('impression', '**IMPRESSION:**'),
                ('recommendations', '**RECOMMENDATIONS:**')
            ]
            
            # Extract each section
            for i, (section_name, marker) in enumerate(section_markers):
                if marker in response_text:
                    start_idx = response_text.find(marker) + len(marker)
                    
                    # Find the end of this section (start of next section or end of text)
                    end_idx = len(response_text)
                    for j in range(i + 1, len(section_markers)):
                        next_marker = section_markers[j][1]
                        if next_marker in response_text:
                            next_start = response_text.find(next_marker)
                            if next_start > start_idx:
                                end_idx = next_start
                                break
                    
                    # Also check for REPORTED BY section
                    reported_by_idx = response_text.find('**REPORTED BY:**')
                    if reported_by_idx != -1 and reported_by_idx < end_idx and reported_by_idx > start_idx:
                        end_idx = reported_by_idx
                    
                    section_content = response_text[start_idx:end_idx].strip()
                    # Clean up the content
                    section_content = section_content.replace('\n\n', '\n').strip()
                    if section_content:
                        sections[section_name] = section_content
            
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting report sections: {e}")
            return {}
    
    def _generate_fallback_analysis(self, analysis_results: List[Dict[str, Any]]) -> GeminiAnalysis:
        """Generate concise fallback analysis when Gemini is not available"""
        total_files = len(analysis_results)
        
        # Collect all pathologies
        all_pathologies = []
        for result in analysis_results:
            all_pathologies.extend(result.get('pathologies', []))
        
        pathology_counts = {}
        for pathology in all_pathologies:
            pathology_counts[pathology] = pathology_counts.get(pathology, 0) + 1
        
        # Generate concise summary (under 100 words)
        if pathology_counts:
            most_common = max(pathology_counts, key=pathology_counts.get)
            summary = f"Analysis of {total_files} DICOM files reveals {len(pathology_counts)} pathology types. Primary finding: {most_common}. Clinical correlation required. Follow-up imaging recommended."
        else:
            summary = f"Analysis of {total_files} DICOM files completed. No significant pathologies detected. Standard follow-up recommended."
        
        return GeminiAnalysis(
            summary=summary,
            clinical_insights=[summary],
            differential_diagnosis=["Clinical correlation required"],
            recommendations=["Follow-up imaging recommended"],
            risk_assessment="Moderate",
            follow_up_plan="Standard follow-up recommended",
            ai_confidence=0.75
        )
    
    def is_available(self) -> bool:
        """Check if Gemini AI is available"""
        return self.client is not None
    
    def generate_clear_human_analysis(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate clear human analysis (wrapper for compatibility)"""
        return self.generate_detailed_human_analysis(analysis_result)
    
    def generate_detailed_human_analysis(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed human-readable analysis for a single analysis result"""
        if not self.client:
            return self._generate_fallback_human_analysis(analysis_result)
        
        try:
            # Extract patient demographics from analysis result
            patient_data = self._extract_patient_demographics(analysis_result)
            
            # Prepare analysis data for Gemini
            analysis_summary = self._prepare_single_analysis_summary(analysis_result)
            
            # Create detailed prompt
            prompt = self._create_medical_analysis_prompt(analysis_summary, patient_data)
            
            # Get Gemini response
            response = self.client.generate_content(prompt)
            
            # Parse the detailed response
            sections = self._extract_report_sections(response.text)
            
            return {
                'executive_summary': response.text.strip(),
                'detailed_findings': sections.get('findings', 'Detailed findings analysis completed'),
                'clinical_indication': sections.get('clinical_indication', 'Radiological evaluation'),
                'technique': sections.get('technique', 'Advanced medical imaging analysis'),
                'impression': sections.get('impression', 'Clinical correlation recommended'),
                'recommendations': sections.get('recommendations', 'Follow-up as clinically indicated'),
                'confidence_level': 'High (90%)',
                'follow_up_plan': sections.get('recommendations', 'Standard follow-up recommended'),
                'patient_demographics': patient_data,
                'report_generated_by': patient_data.get('doctor_name', 'DR. RADIOLOGIST'),
                'report_date': datetime.now().strftime('%B %d, %Y at %H:%M'),
                'enhanced': True
            }
            
        except Exception as e:
            logger.error(f"Error in detailed human analysis: {e}")
            return self._generate_fallback_human_analysis(analysis_result)
    
    def _extract_patient_demographics(self, analysis_result: Dict[str, Any]) -> Dict[str, str]:
        """Extract patient demographics from analysis result with enhanced parsing"""
        # Get patient info from analysis result
        patient_info = analysis_result.get('patient_info', {})
        
        # Extract patient name and clean it
        raw_name = patient_info.get('name', analysis_result.get('patient_name', 'UNKNOWN'))
        clean_name, doctor_name = self._parse_patient_and_doctor_name(raw_name)
        
        # Extract demographics with enhanced parsing
        patient_sex = self._extract_patient_sex(patient_info, analysis_result)
        patient_age = self._extract_patient_age(patient_info, analysis_result)
        
        return {
            'patient_name': clean_name,
            'patient_id': patient_info.get('id', patient_info.get('patient_id', analysis_result.get('patient_id', 'N/A'))),
            'patient_sex': patient_sex,
            'patient_age': patient_age,
            'study_date': patient_info.get('study_date', analysis_result.get('study_date', 'Unknown')),
            'doctor_name': doctor_name,
            'modality': analysis_result.get('modality', 'Unknown'),
            'institution': patient_info.get('institution_name', 'Medical Imaging Center'),
            'study_description': analysis_result.get('study_description', patient_info.get('series_description', 'Medical Imaging Study'))
        }
    
    def _parse_patient_and_doctor_name(self, raw_name: str) -> tuple:
        """Parse patient name and extract doctor name"""
        if not raw_name or raw_name.upper() == 'UNKNOWN':
            return 'UNKNOWN PATIENT', 'DR. RADIOLOGIST'
        
        # Clean the name
        raw_name = str(raw_name).strip()
        
        # Look for doctor name patterns
        doctor_name = 'DR. RADIOLOGIST'  # Default
        clean_patient_name = raw_name
        
        # Pattern 1: "PATIENT NAME DR.DOCTOR NAME"
        if ' DR.' in raw_name.upper():
            parts = raw_name.upper().split(' DR.')
            if len(parts) >= 2:
                clean_patient_name = parts[0].strip()
                doctor_part = parts[1].strip()
                if doctor_part:
                    doctor_name = f'DR.{doctor_part}'
        
        # Pattern 2: "PATIENT NAME DR DOCTOR NAME"
        elif ' DR ' in raw_name.upper():
            parts = raw_name.upper().split(' DR ')
            if len(parts) >= 2:
                clean_patient_name = parts[0].strip()
                doctor_part = parts[1].strip()
                if doctor_part:
                    doctor_name = f'DR {doctor_part}'
        
        return clean_patient_name, doctor_name
    
    def _extract_patient_sex(self, patient_info: Dict, analysis_result: Dict) -> str:
        """Extract patient sex with enhanced parsing"""
        # Try multiple field names
        sex_fields = ['sex', 'gender', 'patient_sex', 'PatientSex']
        
        for field in sex_fields:
            value = patient_info.get(field) or analysis_result.get(field)
            if value and str(value).strip().upper() != 'UNKNOWN':
                sex_value = str(value).strip().upper()
                # Normalize sex values
                if sex_value in ['M', 'MALE', 'MAN']:
                    return 'Male'
                elif sex_value in ['F', 'FEMALE', 'WOMAN']:
                    return 'Female'
                elif sex_value in ['O', 'OTHER']:
                    return 'Other'
        
        return 'Unknown'
    
    def _extract_patient_age(self, patient_info: Dict, analysis_result: Dict) -> str:
        """Extract patient age with enhanced parsing"""
        # Try multiple field names
        age_fields = ['age', 'patient_age', 'PatientAge']
        
        for field in age_fields:
            value = patient_info.get(field) or analysis_result.get(field)
            if value and str(value).strip().upper() != 'UNKNOWN':
                age_str = str(value).strip()
                # Handle different age formats: "25Y", "025Y", "25", "25 years"
                if 'Y' in age_str.upper():
                    # Extract numeric part
                    numeric_part = ''.join(filter(str.isdigit, age_str))
                    if numeric_part:
                        return f"{int(numeric_part)} years"
                elif age_str.isdigit():
                    return f"{age_str} years"
                elif 'year' in age_str.lower():
                    return age_str
        
        return 'Unknown'
    
    def _prepare_single_analysis_summary(self, analysis_result: Dict[str, Any]) -> str:
        """Prepare analysis summary for a single result"""
        summary_parts = []
        
        # Basic information
        body_part = analysis_result.get('body_part', 'Unknown')
        modality = analysis_result.get('modality', 'Unknown')
        confidence = analysis_result.get('confidence', 0)
        
        summary_parts.append(f"IMAGING STUDY: {body_part.upper()} - {modality}")
        summary_parts.append(f"Analysis Confidence: {confidence:.2f}")
        
        # Anatomical landmarks
        landmarks = analysis_result.get('anatomical_landmarks', [])
        if landmarks:
            summary_parts.append(f"\nANATOMICAL LANDMARKS IDENTIFIED ({len(landmarks)}):")
            for landmark in landmarks[:10]:  # Limit to top 10
                summary_parts.append(f"  - {landmark}")
        
        # Pathologies
        pathologies = analysis_result.get('pathologies', [])
        if pathologies:
            summary_parts.append(f"\nPATHOLOGICAL FINDINGS ({len(pathologies)}):")
            for pathology in pathologies:
                summary_parts.append(f"  - {pathology}")
        else:
            summary_parts.append("\nPATHOLOGICAL FINDINGS: No obvious abnormalities detected")
        
        # Measurements
        measurements = analysis_result.get('measurements', {})
        if measurements:
            summary_parts.append(f"\nMEASUREMENTS:")
            for key, value in measurements.items():
                summary_parts.append(f"  - {key}: {value}")
        
        # Technical parameters
        image_size = analysis_result.get('image_size', [])
        if image_size:
            summary_parts.append(f"\nTECHNICAL PARAMETERS:")
            summary_parts.append(f"  - Image dimensions: {' x '.join(map(str, image_size))}")
        
        pixel_spacing = analysis_result.get('pixel_spacing', [])
        if pixel_spacing:
            summary_parts.append(f"  - Pixel spacing: {' x '.join(map(str, pixel_spacing))} mm")
        
        return "\n".join(summary_parts)
    
    def _generate_fallback_human_analysis(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback analysis when Gemini is not available"""
        patient_data = self._extract_patient_demographics(analysis_result)
        
        body_part = analysis_result.get('body_part', 'Unknown')
        pathologies = analysis_result.get('pathologies', [])
        
        if pathologies:
            findings_summary = f"Analysis of {body_part} imaging reveals {len(pathologies)} significant findings requiring clinical attention."
        else:
            findings_summary = f"Analysis of {body_part} imaging completed. No significant abnormalities detected in the current study."
        
        return {
            'executive_summary': f"""**RADIOLOGY REPORT**

Patient: {patient_data['patient_name']}
ID: {patient_data['patient_id']}
Age: {patient_data['patient_age']}
Sex: {patient_data['patient_sex']}

**CLINICAL INDICATION:**
Radiological evaluation of {body_part} for diagnostic assessment.

**FINDINGS:**
{findings_summary}

**IMPRESSION:**
Clinical correlation recommended for optimal patient care.

**RECOMMENDATIONS:**
Follow-up imaging as clinically indicated.

**REPORTED BY:**
{patient_data['doctor_name']}
Board-Certified Radiologist""",
            'detailed_findings': findings_summary,
            'clinical_indication': f'Radiological evaluation of {body_part}',
            'technique': 'Advanced medical imaging analysis',
            'impression': 'Clinical correlation recommended',
            'recommendations': 'Follow-up as clinically indicated',
            'confidence_level': 'Moderate (75%)',
            'follow_up_plan': 'Standard follow-up recommended',
            'patient_demographics': patient_data,
            'report_generated_by': patient_data['doctor_name'],
            'report_date': datetime.now().strftime('%B %d, %Y at %H:%M'),
            'enhanced': False
        }
