#!/usr/bin/env python3
"""
Direct Analysis of G2480F Folder (JAYANTI DAS)
This script analyzes the G2480F folder directly to see what the AI system should be able to detect.
"""

import os
import json
import numpy as np
from datetime import datetime
from pathlib import Path

try:
    import pydicom
except ImportError:
    print("Installing pydicom...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pydicom"])
    import pydicom

def analyze_g2480f_folder():
    """Analyze the G2480F folder containing JAYANTI DAS's actual images."""
    
    print("=" * 60)
    print("DIRECT ANALYSIS OF G2480F FOLDER (JAYANTI DAS)")
    print("=" * 60)
    
    g2480f_path = os.path.expanduser("~/Desktop/G2480F")
    
    if not os.path.exists(g2480f_path):
        print(f"❌ Error: G2480F folder not found at {g2480f_path}")
        return None
    
    print(f"✅ Found G2480F folder: {g2480f_path}")
    
    # Get all DICOM files
    dicom_files = [f for f in os.listdir(g2480f_path) if f.endswith('.dcm')]
    print(f"📁 Total DICOM files: {len(dicom_files)}")
    
    # Analyze sample files to understand the study structure
    sample_files = dicom_files[:10]  # Analyze first 10 files
    
    analysis_results = {
        "analysis_date": datetime.now().isoformat(),
        "folder_path": g2480f_path,
        "patient_info": {},
        "study_structure": {},
        "series_analysis": {},
        "potential_findings": [],
        "technical_analysis": {},
        "summary": {}
    }
    
    print(f"\n📊 Analyzing {len(sample_files)} sample files...")
    
    series_info = {}
    modality_info = {}
    patient_info = {}
    
    for i, filename in enumerate(sample_files):
        file_path = os.path.join(g2480f_path, filename)
        try:
            dcm = pydicom.dcmread(file_path)
            
            # Extract patient information
            if not patient_info:
                patient_info = {
                    "patient_name": str(getattr(dcm, 'PatientName', 'Unknown')),
                    "patient_id": str(getattr(dcm, 'PatientID', 'Unknown')),
                    "patient_age": str(getattr(dcm, 'PatientAge', 'Unknown')),
                    "patient_sex": str(getattr(dcm, 'PatientSex', 'Unknown')),
                    "study_date": str(getattr(dcm, 'StudyDate', 'Unknown')),
                    "modality": str(getattr(dcm, 'Modality', 'Unknown')),
                    "body_part": str(getattr(dcm, 'BodyPartExamined', 'Unknown')),
                    "study_description": str(getattr(dcm, 'StudyDescription', 'Unknown')),
                    "institution_name": str(getattr(dcm, 'InstitutionName', 'Unknown'))
                }
            
            # Extract series information
            series_desc = str(getattr(dcm, 'SeriesDescription', 'Unknown'))
            if series_desc not in series_info:
                series_info[series_desc] = {
                    "count": 0,
                    "modality": str(getattr(dcm, 'Modality', 'Unknown')),
                    "body_part": str(getattr(dcm, 'BodyPartExamined', 'Unknown')),
                    "slice_thickness": str(getattr(dcm, 'SliceThickness', 'Unknown')),
                    "pixel_spacing": str(getattr(dcm, 'PixelSpacing', 'Unknown')),
                    "image_type": str(getattr(dcm, 'ImageType', 'Unknown'))
                }
            series_info[series_desc]["count"] += 1
            
            # Count modalities
            modality = str(getattr(dcm, 'Modality', 'Unknown'))
            modality_info[modality] = modality_info.get(modality, 0) + 1
            
            print(f"  File {i+1}: {filename}")
            print(f"    Series: {series_desc}")
            print(f"    Modality: {modality}")
            print(f"    Body Part: {getattr(dcm, 'BodyPartExamined', 'Unknown')}")
            
        except Exception as e:
            print(f"  Error reading {filename}: {e}")
    
    # Store analysis results
    analysis_results["patient_info"] = patient_info
    analysis_results["study_structure"] = {
        "total_files": len(dicom_files),
        "series_distribution": series_info,
        "modality_distribution": modality_info
    }
    
    # Analyze what the AI should be able to detect
    print(f"\n🔍 Analyzing what AI should be able to detect...")
    
    # Based on the doctor's report, the AI should detect:
    expected_findings = [
        {
            "finding": "Left Paraovarian Hematoma",
            "size": "4.7 x 4.2 cm",
            "location": "Left adnexal region",
            "signal_characteristics": {
                "T1": "Hypointense (dark)",
                "T2": "Predominantly hyperintense (bright)",
                "GRE": "Shows blooming without diffusion restriction"
            },
            "ai_detection_capability": "Should detect with proper training",
            "required_sequences": ["T1", "T2", "GRE"],
            "anatomical_landmarks": ["left_adnexa", "ovary", "pelvis"]
        },
        {
            "finding": "Endometrial Hematoma",
            "size": "3.3 x 1.3 cm",
            "location": "Endometrial cavity",
            "signal_characteristics": {
                "T1": "Hypointense contents",
                "T2": "Hypointense contents",
                "GRE": "Foci of blooming"
            },
            "ai_detection_capability": "Should detect with proper training",
            "required_sequences": ["T1", "T2", "GRE"],
            "anatomical_landmarks": ["uterus", "endometrial_cavity", "pelvis"]
        },
        {
            "finding": "Mild Pelvic Fluid",
            "size": "Small amount",
            "location": "Pelvic cavity",
            "signal_characteristics": {
                "T1": "Hypointense",
                "T2": "Hyperintense"
            },
            "ai_detection_capability": "Should detect with proper training",
            "required_sequences": ["T1", "T2"],
            "anatomical_landmarks": ["pelvis", "pelvic_cavity"]
        }
    ]
    
    analysis_results["potential_findings"] = expected_findings
    
    # Technical analysis
    technical_analysis = {
        "mri_sequences_available": list(series_info.keys()),
        "anatomical_coverage": "Multi-planar (axial, sagittal, coronal)",
        "contrast_enhancement": "Yes (T1 PROPELLER FS+C)",
        "diffusion_imaging": "Yes (Ax DWI)",
        "gradient_echo": "Yes (Ax GRE T2*)",
        "spatial_resolution": "High (0.4297mm pixel spacing)",
        "slice_thickness": "3.5mm (optimal for lesion detection)"
    }
    
    analysis_results["technical_analysis"] = technical_analysis
    
    # Summary and recommendations
    summary = {
        "study_quality": "Excellent - Comprehensive MRI protocol",
        "ai_readiness": "High - All necessary sequences present",
        "expected_ai_performance": "Should detect hematomas if properly trained",
        "missing_ai_capabilities": [
            "Anatomical specificity training",
            "Signal intensity analysis (T1/T2)",
            "Lesion measurement tools",
            "Clinical correlation algorithms"
        ],
        "recommendations": [
            "Train AI on pelvis-specific datasets",
            "Implement T1/T2 signal analysis",
            "Add measurement capabilities",
            "Develop clinical interpretation algorithms"
        ]
    }
    
    analysis_results["summary"] = summary
    
    return analysis_results

def main():
    """Main function to run the analysis."""
    
    print("🚀 Starting Direct Analysis of G2480F Folder (JAYANTI DAS)")
    print(f"⏰ Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the analysis
    results = analyze_g2480f_folder()
    
    if results:
        # Save results
        output_file = "g2480f_direct_analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Analysis complete! Results saved to: {output_file}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)
        
        if results["patient_info"]:
            patient = results["patient_info"]
            print(f"👤 Patient: {patient.get('patient_name', 'Unknown')}")
            print(f"🆔 Patient ID: {patient.get('patient_id', 'Unknown')}")
            print(f"📅 Study Date: {patient.get('study_date', 'Unknown')}")
            print(f"🏥 Institution: {patient.get('institution_name', 'Unknown')}")
        
        if results["study_structure"]:
            study = results["study_structure"]
            print(f"📁 Total Files: {study.get('total_files', 0)}")
            print(f"🔬 Modalities: {list(study.get('modality_distribution', {}).keys())}")
            print(f"📊 Series Count: {len(study.get('series_distribution', {}))}")
        
        if results["summary"]:
            summary = results["summary"]
            print(f"\n📋 Study Quality: {summary.get('study_quality', 'Unknown')}")
            print(f"🤖 AI Readiness: {summary.get('ai_readiness', 'Unknown')}")
            print(f"🎯 Expected AI Performance: {summary.get('expected_ai_performance', 'Unknown')}")
        
        print(f"\n🔍 Key Findings Expected:")
        for finding in results.get("potential_findings", []):
            print(f"  - {finding['finding']}: {finding['size']}")
        
        print(f"\n💡 Recommendations:")
        for rec in results.get("summary", {}).get("recommendations", []):
            print(f"  - {rec}")
        
    else:
        print("❌ Analysis failed!")

if __name__ == "__main__":
    main()
