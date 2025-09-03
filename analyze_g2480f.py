#!/usr/bin/env python3
"""
DICOM Analysis Script for G2480F Folder (JAYANTI DAS)
This script analyzes the DICOM files to understand the patient data and study structure.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

try:
    import pydicom
except ImportError:
    print("pydicom not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pydicom"])
    import pydicom

def analyze_dicom_file(file_path):
    """Analyze a single DICOM file and extract key information."""
    try:
        dcm = pydicom.dcmread(file_path)
        
        # Extract basic patient information
        patient_info = {
            "filename": os.path.basename(file_path),
            "patient_name": str(getattr(dcm, 'PatientName', 'Unknown')),
            "patient_id": str(getattr(dcm, 'PatientID', 'Unknown')),
            "patient_age": str(getattr(dcm, 'PatientAge', 'Unknown')),
            "patient_sex": str(getattr(dcm, 'PatientSex', 'Unknown')),
            "study_date": str(getattr(dcm, 'StudyDate', 'Unknown')),
            "modality": str(getattr(dcm, 'Modality', 'Unknown')),
            "body_part": str(getattr(dcm, 'BodyPartExamined', 'Unknown')),
            "study_description": str(getattr(dcm, 'StudyDescription', 'Unknown')),
            "institution_name": str(getattr(dcm, 'InstitutionName', 'Unknown')),
            "series_description": str(getattr(dcm, 'SeriesDescription', 'Unknown')),
            "image_type": str(getattr(dcm, 'ImageType', 'Unknown')),
            "pixel_spacing": str(getattr(dcm, 'PixelSpacing', 'Unknown')),
            "slice_thickness": str(getattr(dcm, 'SliceThickness', 'Unknown')),
            "file_size": os.path.getsize(file_path)
        }
        
        return patient_info
        
    except Exception as e:
        return {
            "filename": os.path.basename(file_path),
            "error": str(e)
        }

def analyze_g2480f_folder():
    """Analyze the G2480F folder containing JAYANTI DAS's DICOM files."""
    
    g2480f_path = os.path.expanduser("~/Desktop/G2480F")
    
    if not os.path.exists(g2480f_path):
        print(f"Error: G2480F folder not found at {g2480f_path}")
        return None
    
    print(f"Analyzing G2480F folder: {g2480f_path}")
    
    # Get all DICOM files
    dicom_files = []
    for file in os.listdir(g2480f_path):
        if file.endswith('.dcm'):
            dicom_files.append(os.path.join(g2480f_path, file))
    
    print(f"Found {len(dicom_files)} DICOM files")
    
    # Analyze first few files to get patient information
    sample_files = dicom_files[:5]
    sample_analysis = []
    
    for file_path in sample_files:
        print(f"Analyzing: {os.path.basename(file_path)}")
        analysis = analyze_dicom_file(file_path)
        sample_analysis.append(analysis)
    
    # Analyze all files for basic statistics
    all_files_analysis = []
    for i, file_path in enumerate(dicom_files):
        if i % 50 == 0:
            print(f"Progress: {i}/{len(dicom_files)} files analyzed")
        
        analysis = analyze_dicom_file(file_path)
        all_files_analysis.append(analysis)
    
    # Compile results
    results = {
        "analysis_date": datetime.now().isoformat(),
        "folder_path": g2480f_path,
        "total_files": len(dicom_files),
        "sample_analysis": sample_analysis,
        "file_size_distribution": {},
        "modality_distribution": {},
        "series_distribution": {},
        "patient_verification": {},
        "summary": {}
    }
    
    # Analyze file size distribution
    file_sizes = [f.get('file_size', 0) for f in all_files_analysis if 'file_size' in f]
    if file_sizes:
        results["file_size_distribution"] = {
            "min_size": min(file_sizes),
            "max_size": max(file_sizes),
            "avg_size": sum(file_sizes) / len(file_sizes),
            "total_size": sum(file_sizes)
        }
    
    # Analyze modality distribution
    modalities = [f.get('modality', 'Unknown') for f in all_files_analysis if 'modality' in f]
    modality_counts = {}
    for modality in modalities:
        modality_counts[modality] = modality_counts.get(modality, 0) + 1
    results["modality_distribution"] = modality_counts
    
    # Analyze series distribution
    series = [f.get('series_description', 'Unknown') for f in all_files_analysis if 'series_description' in f]
    series_counts = {}
    for series_name in series:
        series_counts[series_name] = series_counts.get(series_name, 0) + 1
    results["series_distribution"] = series_counts
    
    # Patient verification
    patient_ids = set(f.get('patient_id', 'Unknown') for f in all_files_analysis if 'patient_id' in f)
    patient_names = set(f.get('patient_name', 'Unknown') for f in all_files_analysis if 'patient_name' in f)
    
    results["patient_verification"] = {
        "patient_ids": list(patient_ids),
        "patient_names": list(patient_names),
        "consistent_patient": len(patient_ids) == 1 and len(patient_names) == 1
    }
    
    # Summary
    results["summary"] = {
        "folder_contains_jayanti_das": any("JAYANTI" in name.upper() for name in patient_names),
        "patient_id_matches": "G2480F" in patient_ids,
        "total_data_size_gb": sum(file_sizes) / (1024**3) if file_sizes else 0,
        "analysis_complete": True
    }
    
    return results

def main():
    """Main function to run the analysis."""
    print("Starting G2480F folder analysis...")
    print("=" * 50)
    
    results = analyze_g2480f_folder()
    
    if results:
        # Save results to file
        output_file = "g2480f_analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nAnalysis complete! Results saved to: {output_file}")
        print("\nSummary:")
        print(f"- Total DICOM files: {results['total_files']}")
        print(f"- Patient IDs found: {results['patient_verification']['patient_ids']}")
        print(f"- Patient names found: {results['patient_verification']['patient_names']}")
        print(f"- Contains JAYANTI DAS: {results['summary']['folder_contains_jayanti_das']}")
        print(f"- Patient ID matches G2480F: {results['summary']['patient_id_matches']}")
        print(f"- Total data size: {results['summary']['total_data_size_gb']:.2f} GB")
        
        # Display sample analysis
        print("\nSample file analysis:")
        for i, sample in enumerate(results['sample_analysis'][:3]):
            print(f"\nFile {i+1}: {sample['filename']}")
            print(f"  Patient: {sample.get('patient_name', 'Unknown')}")
            print(f"  ID: {sample.get('patient_id', 'Unknown')}")
            print(f"  Modality: {sample.get('modality', 'Unknown')}")
            print(f"  Body Part: {sample.get('body_part', 'Unknown')}")
            
    else:
        print("Analysis failed!")

if __name__ == "__main__":
    main()
