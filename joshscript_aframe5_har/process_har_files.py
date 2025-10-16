#!/usr/bin/env python3
"""
Process multiple HAR files for asBuilt DataColmap project.
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from har_analyzer import HARAnalyzer

def process_single_har(har_path: Path, output_dir: Path) -> bool:
    """
    Process a single HAR file.
    
    Args:
        har_path: Path to the HAR file
        output_dir: Output directory for results
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"PROCESSING: {har_path.name}")
    print(f"{'='*60}")
    
    analyzer = HARAnalyzer()
    
    # Load the HAR file
    if not analyzer.load_har_file(har_path):
        print(f"Failed to load {har_path.name}")
        return False
    
    # Create output filename
    output_name = har_path.stem.replace('.har', '') + '_analysis.json'
    output_path = output_dir / output_name
    
    # Export analysis
    if analyzer.export_summary(output_path):
        print(f"Analysis saved to: {output_path}")
        return True
    else:
        print(f"Failed to save analysis for {har_path.name}")
        return False

def process_har_directory(input_dir: Path, output_dir: Path, pattern: str = "*.har*") -> int:
    """
    Process all HAR files in a directory.
    
    Args:
        input_dir: Directory containing HAR files
        output_dir: Output directory for results
        pattern: File pattern to match (default: "*.har*")
        
    Returns:
        Number of files successfully processed
    """
    if not input_dir.exists():
        print(f"Input directory does not exist: {input_dir}")
        return 0
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find HAR files
    har_files = list(input_dir.glob(pattern))
    
    if not har_files:
        print(f"No HAR files found in {input_dir} with pattern '{pattern}'")
        return 0
    
    print(f"Found {len(har_files)} HAR files to process")
    print(f"Output directory: {output_dir}")
    
    # Process each file
    success_count = 0
    for har_file in har_files:
        try:
            if process_single_har(har_file, output_dir):
                success_count += 1
        except Exception as e:
            print(f"Error processing {har_file.name}: {e}")
    
    return success_count

def create_combined_analysis(output_dir: Path) -> bool:
    """
    Create a combined analysis of all processed HAR files.
    
    Args:
        output_dir: Directory containing individual analysis files
        
    Returns:
        True if successful, False otherwise
    """
    analysis_files = list(output_dir.glob("*_analysis.json"))
    
    if not analysis_files:
        print("No analysis files found to combine")
        return False
    
    print(f"\nCombining {len(analysis_files)} analysis files...")
    
    combined_data = {
        'timestamp': datetime.now().isoformat(),
        'total_files': len(analysis_files),
        'files': [],
        'summary': {
            'total_requests': 0,
            'total_api_requests': 0,
            'total_image_requests': 0,
            'unique_domains': set(),
            'unique_content_types': set(),
            'unique_user_agents': set()
        }
    }
    
    # Process each analysis file
    for analysis_file in analysis_files:
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Add file info
            file_info = {
                'filename': analysis_file.name,
                'file_info': data.get('file_info', {}),
                'total_entries': data.get('file_info', {}).get('total_entries', 0),
                'api_requests': data.get('api_requests', 0),
                'image_requests': data.get('image_requests', 0),
                'domains': data.get('domains', []),
                'content_types': data.get('content_types', []),
                'user_agents': data.get('user_agents', [])
            }
            combined_data['files'].append(file_info)
            
            # Update summary
            combined_data['summary']['total_requests'] += file_info['total_entries']
            combined_data['summary']['total_api_requests'] += file_info['api_requests']
            combined_data['summary']['total_image_requests'] += file_info['image_requests']
            combined_data['summary']['unique_domains'].update(file_info['domains'])
            combined_data['summary']['unique_content_types'].update(file_info['content_types'])
            combined_data['summary']['unique_user_agents'].update(file_info['user_agents'])
            
        except Exception as e:
            print(f"Error processing {analysis_file.name}: {e}")
    
    # Convert sets to lists for JSON serialization
    combined_data['summary']['unique_domains'] = sorted(list(combined_data['summary']['unique_domains']))
    combined_data['summary']['unique_content_types'] = sorted(list(combined_data['summary']['unique_content_types']))
    combined_data['summary']['unique_user_agents'] = sorted(list(combined_data['summary']['unique_user_agents']))
    
    # Save combined analysis
    combined_path = output_dir / 'combined_analysis.json'
    try:
        with open(combined_path, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
        print(f"Combined analysis saved to: {combined_path}")
        print(f"Summary:")
        print(f"  Total files: {combined_data['total_files']}")
        print(f"  Total requests: {combined_data['summary']['total_requests']}")
        print(f"  API requests: {combined_data['summary']['total_api_requests']}")
        print(f"  Image requests: {combined_data['summary']['total_image_requests']}")
        print(f"  Unique domains: {len(combined_data['summary']['unique_domains'])}")
        
        return True
        
    except Exception as e:
        print(f"Error saving combined analysis: {e}")
        return False

def main():
    """Main function for processing HAR files."""
    parser = argparse.ArgumentParser(description='Process HAR files for asBuilt DataColmap')
    parser.add_argument('--input-dir', '-i', required=True, help='Input directory containing HAR files')
    parser.add_argument('--output-dir', '-o', default='har_analysis_output', help='Output directory for analysis results')
    parser.add_argument('--pattern', '-p', default='*.har*', help='File pattern to match (default: *.har*)')
    parser.add_argument('--combine', '-c', action='store_true', help='Create combined analysis of all files')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    print("HAR File Processor for asBuilt DataColmap")
    print("=" * 50)
    
    # Process HAR files
    success_count = process_har_directory(input_dir, output_dir, args.pattern)
    
    if success_count > 0:
        print(f"\n{'='*50}")
        print(f"PROCESSING COMPLETE")
        print(f"{'='*50}")
        print(f"Successfully processed: {success_count} files")
        print(f"Output directory: {output_dir}")
        
        # Create combined analysis if requested
        if args.combine:
            create_combined_analysis(output_dir)
    else:
        print("No files were successfully processed.")

if __name__ == '__main__':
    main()


