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
        """Create concise medical analysis prompt for Gemini (under 100 words)"""
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Extract modality if available
        modality = "Multiple modalities"
        if 'Modality:' in analysis_summary:
            try:
                modality = analysis_summary.split('Modality:')[1].split('\n')[0].strip()
            except:
                modality = "Multiple modalities"
        
        return f"""
You are Dr. AI Radiologist, an expert medical AI specialist. Generate a CONCISE medical summary (UNDER 100 WORDS) in professional doctor's report style.

ANALYSIS DATA:
{analysis_summary}

REQUIREMENTS:
- Maximum 100 words total
- Professional medical terminology
- Doctor's report writing style
- Focus on key pathological findings
- Include clinical significance
- Clear and actionable

FORMAT:
**CLINICAL SUMMARY:**
[Write a concise, professional medical summary under 100 words that includes:
- Key pathological findings
- Clinical significance
- Brief assessment
- Essential recommendations]

**REPORT PREPARED BY:**
Dr. AI Radiologist
Date: {current_date}

IMPORTANT: Keep the entire response under 100 words. Be concise but comprehensive. Use professional medical language.
"""
    
    def _parse_gemini_response(self, response_text: str, analysis_results: List[Dict[str, Any]]) -> GeminiAnalysis:
        """Parse Gemini response into structured analysis"""
        try:
            # For concise format, extract the clinical summary
            clinical_summary = self._extract_clinical_summary(response_text)
            
            # Count words to ensure it's under 100
            word_count = len(clinical_summary.split())
            if word_count > 100:
                # Truncate to 100 words
                words = clinical_summary.split()[:100]
                clinical_summary = ' '.join(words) + '...'
            
            return GeminiAnalysis(
                summary=clinical_summary,
                clinical_insights=[clinical_summary],  # Use summary as main insight
                differential_diagnosis=["Clinical correlation required"],
                recommendations=["Follow-up imaging recommended"],
                risk_assessment="Moderate",
                follow_up_plan="Standard follow-up recommended",
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
    
    def _extract_clinical_summary(self, response_text: str) -> str:
        """Extract clinical summary from concise Gemini response"""
        try:
            # Look for CLINICAL SUMMARY section
            if '**CLINICAL SUMMARY:**' in response_text:
                start_idx = response_text.find('**CLINICAL SUMMARY:**') + len('**CLINICAL SUMMARY:**')
                end_idx = response_text.find('**REPORT PREPARED BY:**')
                if end_idx == -1:
                    end_idx = len(response_text)
                
                summary = response_text[start_idx:end_idx].strip()
                # Clean up the summary
                summary = summary.replace('\n', ' ').replace('  ', ' ')
                return summary
            
            # Fallback: extract content between asterisks or after colons
            lines = response_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('**') and not line.startswith('REPORT PREPARED BY'):
                    return line
            
            # Final fallback
            return "Clinical analysis completed with findings requiring medical review."
            
        except Exception as e:
            logger.error(f"Error extracting clinical summary: {e}")
            return "Clinical analysis completed with findings requiring medical review."
    
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
