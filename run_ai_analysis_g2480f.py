#!/usr/bin/env python3
"""
AI Analysis Script for G2480F Folder (JAYANTI DAS)
This script runs the AI analysis on the correct patient data to see what it can actually detect.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

def run_ai_analysis_on_g2480f():
    """Run AI analysis on the G2480F folder containing JAYANTI DAS's actual images."""
    
    print("=" * 60)
    print("AI ANALYSIS ON G2480F FOLDER (JAYANTI DAS)")
    print("=" * 60)
    
    # Check if G2480F folder exists
    g2480f_path = os.path.expanduser("~/Desktop/G2480F")
    if not os.path.exists(g2480f_path):
        print(f"❌ Error: G2480F folder not found at {g2480f_path}")
        return None
    
    print(f"✅ Found G2480F folder: {g2480f_path}")
    
    # Count DICOM files
    dicom_files = [f for f in os.listdir(g2480f_path) if f.endswith('.dcm')]
    print(f"📁 Total DICOM files: {len(dicom_files)}")
    
    # Check if we have the AI analysis tools
    print("\n🔍 Checking AI analysis tools...")
    
    # Look for existing AI analysis scripts
    ai_scripts = [
        "dicom_analyzer.py",
        "real_dicom_analyzer.py", 
        "pelvis_test_analyzer.py",
        "brain_test_analyzer.py"
    ]
    
    available_scripts = []
    for script in ai_scripts:
        if os.path.exists(script):
            available_scripts.append(script)
            print(f"✅ Found: {script}")
    
    if not available_scripts:
        print("❌ No AI analysis scripts found!")
        return None
    
    # Try to run analysis with available scripts
    print(f"\n🚀 Attempting AI analysis with: {available_scripts[0]}")
    
    try:
        # Create a temporary analysis folder for G2480F
        analysis_output_dir = "g2480f_ai_analysis"
        if not os.path.exists(analysis_output_dir):
            os.makedirs(analysis_output_dir)
        
        # Copy G2480F files to analysis directory
        print(f"📋 Preparing analysis directory: {analysis_output_dir}")
        
        # Run the AI analysis
        print("\n🤖 Running AI analysis...")
        
        # Try to run the analysis script
        if available_scripts[0] == "dicom_analyzer.py":
            cmd = [sys.executable, "dicom_analyzer.py", g2480f_path, "--output", analysis_output_dir]
        elif available_scripts[0] == "real_dicom_analyzer.py":
            cmd = [sys.executable, "real_dicom_analyzer.py", g2480f_path, "--output", analysis_output_dir]
        elif available_scripts[0] == "pelvis_test_analyzer.py":
            cmd = [sys.executable, "pelvis_test_analyzer.py", g2480f_path, "--output", analysis_output_dir]
        else:
            cmd = [sys.executable, available_scripts[0], g2480f_path]
        
        print(f"Command: {' '.join(cmd)}")
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ AI analysis completed successfully!")
            print("Output:", result.stdout)
            
            # Look for output files
            output_files = os.listdir(analysis_output_dir) if os.path.exists(analysis_output_dir) else []
            if output_files:
                print(f"\n📄 Analysis output files:")
                for file in output_files:
                    print(f"  - {file}")
            
            return {
                "status": "success",
                "script": available_scripts[0],
                "output": result.stdout,
                "output_files": output_files
            }
            
        else:
            print("❌ AI analysis failed!")
            print("Error:", result.stderr)
            return {
                "status": "failed",
                "script": available_scripts[0],
                "error": result.stderr
            }
            
    except subprocess.TimeoutExpired:
        print("❌ AI analysis timed out after 5 minutes")
        return {"status": "timeout", "script": available_scripts[0]}
    except Exception as e:
        print(f"❌ Error running AI analysis: {e}")
        return {"status": "error", "script": available_scripts[0], "error": str(e)}

def analyze_dicom_metadata_g2480f():
    """Analyze DICOM metadata from G2480F folder to understand the study structure."""
    
    print("\n" + "=" * 60)
    print("DICOM METADATA ANALYSIS - G2480F FOLDER")
    print("=" * 60)
    
    g2480f_path = os.path.expanduser("~/Desktop/G2480F")
    
    try:
        # Import pydicom if available
        try:
            import pydicom
        except ImportError:
            print("Installing pydicom...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pydicom"])
            import pydicom
        
        # Analyze a few sample files
        dicom_files = [f for f in os.listdir(g2480f_path) if f.endswith('.dcm')]
        sample_files = dicom_files[:5]
        
        metadata_summary = {
            "total_files": len(dicom_files),
            "sample_analysis": [],
            "series_distribution": {},
            "modality_distribution": {},
            "patient_info": {}
        }
        
        print(f"📊 Analyzing {len(sample_files)} sample files...")
        
        for i, filename in enumerate(sample_files):
            file_path = os.path.join(g2480f_path, filename)
            try:
                dcm = pydicom.dcmread(file_path)
                
                # Extract key information
                file_info = {
                    "filename": filename,
                    "patient_name": str(getattr(dcm, 'PatientName', 'Unknown')),
                    "patient_id": str(getattr(dcm, 'PatientID', 'Unknown')),
                    "series_description": str(getattr(dcm, 'SeriesDescription', 'Unknown')),
                    "modality": str(getattr(dcm, 'Modality', 'Unknown')),
                    "body_part": str(getattr(dcm, 'BodyPartExamined', 'Unknown')),
                    "image_type": str(getattr(dcm, 'ImageType', 'Unknown')),
                    "slice_thickness": str(getattr(dcm, 'SliceThickness', 'Unknown')),
                    "pixel_spacing": str(getattr(dcm, 'PixelSpacing', 'Unknown'))
                }
                
                metadata_summary["sample_analysis"].append(file_info)
                
                # Count series
                series = file_info["series_description"]
                metadata_summary["series_distribution"][series] = metadata_summary["series_distribution"].get(series, 0) + 1
                
                # Count modalities
                modality = file_info["modality"]
                metadata_summary["modality_distribution"][modality] = metadata_summary["modality_distribution"].get(modality, 0) + 1
                
                # Store patient info from first file
                if i == 0:
                    metadata_summary["patient_info"] = {
                        "patient_name": file_info["patient_name"],
                        "patient_id": file_info["patient_id"],
                        "body_part": file_info["body_part"]
                    }
                
                print(f"  File {i+1}: {filename}")
                print(f"    Series: {series}")
                print(f"    Modality: {modality}")
                
            except Exception as e:
                print(f"  Error reading {filename}: {e}")
        
        # Save metadata summary
        output_file = "g2480f_metadata_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(metadata_summary, f, indent=2)
        
        print(f"\n✅ Metadata analysis saved to: {output_file}")
        return metadata_summary
        
    except Exception as e:
        print(f"❌ Error in metadata analysis: {e}")
        return None

def main():
    """Main function to run the complete analysis."""
    
    print("🚀 Starting AI Analysis on G2480F Folder (JAYANTI DAS)")
    print(f"⏰ Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # First, analyze DICOM metadata
    metadata_results = analyze_dicom_metadata_g2480f()
    
    # Then, attempt AI analysis
    ai_results = run_ai_analysis_on_g2480f()
    
    # Compile final results
    final_results = {
        "analysis_date": datetime.now().isoformat(),
        "patient": "JAYANTI DAS (G2480F)",
        "metadata_analysis": metadata_results,
        "ai_analysis": ai_results,
        "summary": {}
    }
    
    if metadata_results and ai_results:
        final_results["summary"] = {
            "metadata_analysis": "✅ Completed",
            "ai_analysis": ai_results["status"],
            "total_files_analyzed": metadata_results["total_files"] if metadata_results else 0,
            "ai_analysis_success": ai_results["status"] == "success"
        }
    
    # Save final results
    output_file = "g2480f_complete_analysis_results.json"
    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    print(f"\n📋 Complete analysis results saved to: {output_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    
    if metadata_results:
        print(f"📊 Metadata Analysis: ✅ Completed")
        print(f"   - Total DICOM files: {metadata_results['total_files']}")
        print(f"   - Patient: {metadata_results['patient_info'].get('patient_name', 'Unknown')}")
        print(f"   - Patient ID: {metadata_results['patient_info'].get('patient_id', 'Unknown')}")
        print(f"   - Body Part: {metadata_results['patient_info'].get('body_part', 'Unknown')}")
    
    if ai_results:
        print(f"🤖 AI Analysis: {ai_results['status'].upper()}")
        if ai_results['status'] == 'success':
            print(f"   - Script used: {ai_results['script']}")
            print(f"   - Output files: {len(ai_results.get('output_files', []))}")
        else:
            print(f"   - Error: {ai_results.get('error', 'Unknown error')}")
    
    print("\n🎯 Next Steps:")
    print("1. Review the analysis results")
    print("2. Compare AI findings with doctor's report")
    print("3. Assess AI system capabilities")
    print("4. Implement improvements based on findings")

if __name__ == "__main__":
    main()
