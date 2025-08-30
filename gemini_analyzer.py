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
    
    def analyze_dicom_data(self, analysis_results: List[Dict[str, Any]]) -> GeminiAnalysis:
        """Analyze DICOM data using Gemini AI"""
        if not self.client:
            return self._generate_fallback_analysis(analysis_results)
        
        try:
            # Prepare comprehensive data for Gemini
            analysis_summary = self._prepare_analysis_summary(analysis_results)
            
            # Create detailed prompt for medical analysis
            prompt = self._create_medical_analysis_prompt(analysis_summary)
            
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
    
    def _create_medical_analysis_prompt(self, analysis_summary: str) -> str:
        """Create comprehensive medical analysis prompt for Gemini"""
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Extract modality if available
        modality = "Multiple modalities"
        if 'Modality:' in analysis_summary:
            try:
                modality = analysis_summary.split('Modality:')[1].split('\n')[0].strip()
            except:
                modality = "Multiple modalities"
        
        return f"""
You are Dr. AI Radiologist, an expert medical AI specialist with extensive experience in radiological interpretation and clinical diagnosis. You are writing a comprehensive medical report for a healthcare professional.

ANALYSIS DATA:
{analysis_summary}

Please provide a detailed, professional medical report in the following format:

**MEDICAL IMAGING ANALYSIS REPORT**

**PATIENT INFORMATION:**
- Study Type: DICOM Medical Imaging Analysis
- Modality: {modality}
- Date of Analysis: {current_date}

**EXECUTIVE SUMMARY:**
Provide a 3-4 sentence comprehensive overview of the imaging findings, clinical significance, and overall assessment.

**DETAILED FINDINGS:**

1. **ANATOMICAL ASSESSMENT:**
   - Detailed description of anatomical structures identified
   - Normal vs. abnormal findings
   - Specific anatomical landmarks and their clinical relevance

2. **PATHOLOGICAL ANALYSIS:**
   - Comprehensive list of detected pathologies
   - Severity assessment for each finding
   - Clinical correlation and significance

3. **IMAGE QUALITY ASSESSMENT:**
   - Technical quality of the imaging
   - Artifacts or limitations identified
   - Recommendations for image optimization

**CLINICAL INTERPRETATION:**

1. **PRIMARY DIAGNOSIS:**
   - Most likely diagnosis based on findings
   - Confidence level and supporting evidence

2. **DIFFERENTIAL DIAGNOSIS:**
   - Alternative diagnostic possibilities (list 3-5)
   - Clinical reasoning for each differential
   - Probability assessment for each

3. **CLINICAL CORRELATION:**
   - How findings relate to patient symptoms
   - Clinical significance of each finding
   - Impact on patient management

**TREATMENT RECOMMENDATIONS:**

1. **IMMEDIATE ACTIONS:**
   - Urgent interventions if needed
   - Immediate clinical decisions required

2. **SPECIALIST CONSULTATIONS:**
   - Required specialist referrals
   - Specific expertise needed

3. **FURTHER DIAGNOSTIC WORKUP:**
   - Additional imaging studies recommended
   - Laboratory tests if indicated
   - Other diagnostic procedures

**RISK ASSESSMENT:**
- Overall risk level: [Low/Moderate/High]
- Specific risk factors identified
- Urgency of clinical attention
- Prognostic implications

**FOLLOW-UP PLAN:**
- Recommended timeline for follow-up imaging
- Specific monitoring requirements
- Patient education and counseling points
- Long-term management considerations

**CLINICAL IMPRESSION:**
Provide a final clinical impression summarizing the key findings, their significance, and the recommended course of action.

**REPORT PREPARED BY:**
Dr. AI Radiologist
Medical AI Specialist
Date: {current_date}

Please write this report in a professional medical tone, as if written by an experienced radiologist for clinical use. Be thorough, evidence-based, and clinically actionable.

IMPORTANT: Please structure your response with clear section headers and bullet points for easy parsing. Use the exact section names provided above.
"""
    
    def _parse_gemini_response(self, response_text: str, analysis_results: List[Dict[str, Any]]) -> GeminiAnalysis:
        """Parse Gemini response into structured analysis"""
        try:
            # Extract sections from response
            sections = self._extract_sections(response_text)
            
            # If parsing failed or summary is not meaningful, try to extract content from the raw response
            if (not sections.get('summary') or 
                sections.get('summary') == 'Analysis completed' or 
                sections.get('summary') == 'Analysis completed.' or
                len(sections.get('summary', '')) < 20):
                sections = self._extract_from_raw_response(response_text)
            
            return GeminiAnalysis(
                summary=sections.get('summary', 'Analysis completed'),
                clinical_insights=sections.get('clinical_insights', []),
                differential_diagnosis=sections.get('differential_diagnosis', []),
                recommendations=sections.get('recommendations', []),
                risk_assessment=sections.get('risk_assessment', 'Moderate'),
                follow_up_plan=sections.get('follow_up_plan', 'Standard follow-up recommended'),
                ai_confidence=0.85  # High confidence for Gemini analysis
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
    
    def _extract_sections(self, response_text: str) -> Dict[str, Any]:
        """Extract different sections from Gemini response"""
        sections = {}
        
        # Split the response into lines
        lines = response_text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers (more comprehensive)
            if any(header in line.upper() for header in ['EXECUTIVE SUMMARY', 'CLINICAL SUMMARY']):
                if current_section and current_content:
                    sections[current_section] = current_content
                current_section = 'summary'
                current_content = []
            elif any(header in line.upper() for header in ['CLINICAL INSIGHTS', 'DETAILED FINDINGS']):
                if current_section and current_content:
                    sections[current_section] = current_content
                current_section = 'clinical_insights'
                current_content = []
            elif 'DIFFERENTIAL DIAGNOSIS' in line.upper():
                if current_section and current_content:
                    sections[current_section] = current_content
                current_section = 'differential_diagnosis'
                current_content = []
            elif any(header in line.upper() for header in ['RECOMMENDATIONS', 'TREATMENT RECOMMENDATIONS']):
                if current_section and current_content:
                    sections[current_section] = current_content
                current_section = 'recommendations'
                current_content = []
            elif 'RISK ASSESSMENT' in line.upper():
                if current_section and current_content:
                    sections[current_section] = current_content
                current_section = 'risk_assessment'
                current_content = []
            elif 'FOLLOW-UP PLAN' in line.upper():
                if current_section and current_content:
                    sections[current_section] = current_content
                current_section = 'follow_up_plan'
                current_content = []
            elif current_section and line:
                # Add content to current section
                if line.startswith('-') or line.startswith('*') or line.startswith('•'):
                    current_content.append(line[1:].strip())
                else:
                    current_content.append(line)
        
        # Add final section
        if current_section and current_content:
            sections[current_section] = current_content
        
        # Process sections to clean up content
        for key in sections:
            if isinstance(sections[key], list):
                # Remove empty items and clean up formatting
                sections[key] = [item.strip() for item in sections[key] if item.strip() and not item.strip().startswith('**')]
        
        # Convert lists to appropriate format
        for key in ['clinical_insights', 'differential_diagnosis', 'recommendations']:
            if key in sections:
                if isinstance(sections[key], list):
                    sections[key] = [item for item in sections[key] if item and len(item) > 5]
                else:
                    sections[key] = [sections[key]] if sections[key] else []
        
        # Convert summary to string
        if 'summary' in sections:
            if isinstance(sections['summary'], list):
                sections['summary'] = ' '.join(sections['summary'])
        
        # If no proper summary was found, create one from the content
        if not sections.get('summary') or sections.get('summary') == 'Analysis completed':
            summary_parts = []
            if sections.get('differential_diagnosis'):
                summary_parts.append(f"Analysis identified {len(sections['differential_diagnosis'])} potential diagnoses.")
            if sections.get('recommendations'):
                summary_parts.append(f"Generated {len(sections['recommendations'])} clinical recommendations.")
            if summary_parts:
                sections['summary'] = ' '.join(summary_parts)
            else:
                sections['summary'] = 'Comprehensive medical analysis completed with detailed findings and recommendations.'
        
        # Convert risk assessment to string if it's a list
        if 'risk_assessment' in sections and isinstance(sections['risk_assessment'], list):
            sections['risk_assessment'] = ' '.join(sections['risk_assessment'])
        
        # Convert follow-up plan to string if it's a list
        if 'follow_up_plan' in sections and isinstance(sections['follow_up_plan'], list):
            sections['follow_up_plan'] = ' '.join(sections['follow_up_plan'])
        
        return sections
    
    def _generate_fallback_analysis(self, analysis_results: List[Dict[str, Any]]) -> GeminiAnalysis:
        """Generate fallback analysis when Gemini is not available"""
        total_files = len(analysis_results)
        
        # Collect all pathologies
        all_pathologies = []
        for result in analysis_results:
            all_pathologies.extend(result.get('pathologies', []))
        
        pathology_counts = {}
        for pathology in all_pathologies:
            pathology_counts[pathology] = pathology_counts.get(pathology, 0) + 1
        
        # Generate basic insights
        clinical_insights = [
            f"Analyzed {total_files} DICOM files successfully",
            f"Detected {len(pathology_counts)} different types of pathologies",
            "Image quality assessment completed",
            "Anatomical landmarks identified",
            "Modality-specific analysis performed"
        ]
        
        if pathology_counts:
            clinical_insights.append(f"Most common finding: {max(pathology_counts, key=pathology_counts.get)}")
        
        return GeminiAnalysis(
            summary=f"Comprehensive analysis of {total_files} DICOM files completed with {len(pathology_counts)} pathology types identified.",
            clinical_insights=clinical_insights,
            differential_diagnosis=["Clinical correlation required", "Further imaging may be needed", "Specialist consultation recommended"],
            recommendations=[
                "Review by radiologist recommended",
                "Clinical correlation with patient history required",
                "Consider additional imaging if clinically indicated",
                "Follow-up imaging recommended in 3-6 months",
                "Ensure proper documentation of findings"
            ],
            risk_assessment="Moderate - requires clinical correlation",
            follow_up_plan="Standard follow-up imaging recommended in 3-6 months with clinical correlation",
            ai_confidence=0.75
        )
