#!/usr/bin/env python3
"""
HAR (HTTP Archive) file analyzer for asBuilt DataColmap project.
"""

import json
import gzip
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

class HARAnalyzer:
    """Analyzes HAR files to extract relevant data."""
    
    def __init__(self):
        self.entries = []
        self.pages = []
        self.creator = {}
        self.browser = {}
        self.version = ""
        
    def load_har_file(self, har_path: Path) -> bool:
        """
        Load a HAR file from disk.
        
        Args:
            har_path: Path to the HAR file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Handle both regular and gzipped HAR files
            if har_path.suffix == '.gz':
                with gzip.open(har_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(har_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Parse HAR structure
            self.log = data.get('log', {})
            self.version = self.log.get('version', '')
            self.creator = self.log.get('creator', {})
            self.browser = self.log.get('browser', {})
            self.pages = self.log.get('pages', [])
            self.entries = self.log.get('entries', [])
            
            print(f"Loaded HAR file: {har_path.name}")
            print(f"  Version: {self.version}")
            print(f"  Creator: {self.creator.get('name', 'Unknown')} {self.creator.get('version', '')}")
            print(f"  Browser: {self.browser.get('name', 'Unknown')} {self.browser.get('version', '')}")
            print(f"  Pages: {len(self.pages)}")
            print(f"  Entries: {len(self.entries)}")
            
            return True
            
        except Exception as e:
            print(f"Error loading HAR file {har_path}: {e}")
            return False
    
    def get_requests_by_domain(self, domain: str = None) -> List[Dict]:
        """
        Get all requests filtered by domain.
        
        Args:
            domain: Domain to filter by (e.g., 'asbuiltvault.com')
            
        Returns:
            List of request entries
        """
        if not domain:
            return self.entries
        
        filtered_entries = []
        for entry in self.entries:
            request = entry.get('request', {})
            url = request.get('url', '')
            if domain in url:
                filtered_entries.append(entry)
        
        return filtered_entries
    
    def get_requests_by_type(self, content_type: str = None) -> List[Dict]:
        """
        Get all requests filtered by content type.
        
        Args:
            content_type: Content type to filter by (e.g., 'application/json')
            
        Returns:
            List of request entries
        """
        if not content_type:
            return self.entries
        
        filtered_entries = []
        for entry in self.entries:
            response = entry.get('response', {})
            headers = response.get('headers', [])
            
            # Check content-type header
            for header in headers:
                if header.get('name', '').lower() == 'content-type':
                    if content_type in header.get('value', ''):
                        filtered_entries.append(entry)
                    break
        
        return filtered_entries
    
    def get_api_requests(self) -> List[Dict]:
        """
        Get all API requests (typically JSON responses).
        
        Returns:
            List of API request entries
        """
        return self.get_requests_by_type('application/json')
    
    def get_image_requests(self) -> List[Dict]:
        """
        Get all image requests.
        
        Returns:
            List of image request entries
        """
        image_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']
        filtered_entries = []
        
        for entry in self.entries:
            response = entry.get('response', {})
            headers = response.get('headers', [])
            
            for header in headers:
                if header.get('name', '').lower() == 'content-type':
                    content_type = header.get('value', '')
                    if any(img_type in content_type for img_type in image_types):
                        filtered_entries.append(entry)
                    break
        
        return filtered_entries
    
    def extract_urls(self, domain: str = None) -> List[str]:
        """
        Extract all unique URLs from the HAR file.
        
        Args:
            domain: Optional domain filter
            
        Returns:
            List of unique URLs
        """
        urls = set()
        
        for entry in self.entries:
            request = entry.get('request', {})
            url = request.get('url', '')
            if url and (not domain or domain in url):
                urls.add(url)
        
        return sorted(list(urls))
    
    def extract_headers(self, header_name: str) -> List[str]:
        """
        Extract all values for a specific header name.
        
        Args:
            header_name: Name of the header to extract
            
        Returns:
            List of header values
        """
        values = set()
        
        for entry in self.entries:
            request = entry.get('request', {})
            response = entry.get('response', {})
            
            # Check request headers
            for header in request.get('headers', []):
                if header.get('name', '').lower() == header_name.lower():
                    values.add(header.get('value', ''))
            
            # Check response headers
            for header in response.get('headers', []):
                if header.get('name', '').lower() == header_name.lower():
                    values.add(header.get('value', ''))
        
        return sorted(list(values))
    
    def get_timing_stats(self) -> Dict[str, Any]:
        """
        Get timing statistics for all requests.
        
        Returns:
            Dictionary with timing statistics
        """
        timings = []
        
        for entry in self.entries:
            timings_data = entry.get('timings', {})
            if timings_data:
                timings.append(timings_data)
        
        if not timings:
            return {}
        
        # Calculate statistics
        total_times = [t.get('_totalTime', 0) for t in timings if t.get('_totalTime')]
        dns_times = [t.get('dns', 0) for t in timings if t.get('dns')]
        connect_times = [t.get('connect', 0) for t in timings if t.get('connect')]
        send_times = [t.get('send', 0) for t in timings if t.get('send')]
        wait_times = [t.get('wait', 0) for t in timings if t.get('wait')]
        receive_times = [t.get('receive', 0) for t in timings if t.get('receive')]
        
        def safe_stats(values):
            if not values:
                return {'min': 0, 'max': 0, 'avg': 0, 'count': 0}
            return {
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'count': len(values)
            }
        
        return {
            'total_time': safe_stats(total_times),
            'dns': safe_stats(dns_times),
            'connect': safe_stats(connect_times),
            'send': safe_stats(send_times),
            'wait': safe_stats(wait_times),
            'receive': safe_stats(receive_times)
        }
    
    def export_summary(self, output_path: Path) -> bool:
        """
        Export a summary of the HAR file analysis.
        
        Args:
            output_path: Path to save the summary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            summary = {
                'file_info': {
                    'version': self.version,
                    'creator': self.creator,
                    'browser': self.browser,
                    'total_pages': len(self.pages),
                    'total_entries': len(self.entries)
                },
                'urls': self.extract_urls(),
                'domains': list(set(url.split('/')[2] for url in self.extract_urls() if '://' in url)),
                'content_types': self.extract_headers('content-type'),
                'user_agents': self.extract_headers('user-agent'),
                'timing_stats': self.get_timing_stats(),
                'api_requests': len(self.get_api_requests()),
                'image_requests': len(self.get_image_requests())
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            print(f"Summary exported to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting summary: {e}")
            return False

def main():
    """Example usage of HARAnalyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze HAR files')
    parser.add_argument('har_file', help='Path to HAR file')
    parser.add_argument('--output', '-o', help='Output summary file')
    parser.add_argument('--domain', help='Filter by domain')
    
    args = parser.parse_args()
    
    analyzer = HARAnalyzer()
    
    if analyzer.load_har_file(Path(args.har_file)):
        print("\n=== Analysis Results ===")
        
        # Show basic stats
        print(f"Total requests: {len(analyzer.entries)}")
        print(f"API requests: {len(analyzer.get_api_requests())}")
        print(f"Image requests: {len(analyzer.get_image_requests())}")
        
        # Show domains
        domains = list(set(url.split('/')[2] for url in analyzer.extract_urls() if '://' in url))
        print(f"Domains: {', '.join(domains[:5])}{'...' if len(domains) > 5 else ''}")
        
        # Export summary if requested
        if args.output:
            analyzer.export_summary(Path(args.output))

if __name__ == '__main__':
    main()


