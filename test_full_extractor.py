#!/usr/bin/env python3
"""
Test script for the full feature extractor.
This script demonstrates how to use the FullFlowExtractor class.
"""
import sys
import time
import pandas as pd
from gui_flow_extractor_full import FullFlowExtractor

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_full_extractor.py <pcap_file> [output_csv]")
        sys.exit(1)
    
    pcap_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'flow_features.csv'
    
    print(f"[+] Processing {pcap_file}...")
    start_time = time.time()
    
    # Create extractor instance
    extractor = FullFlowExtractor()
    
    # Progress callback function
    def progress_callback(current, total):
        elapsed = time.time() - start_time
        rate = current / elapsed if elapsed > 0 else 0
        print(f"\r[+] Processed {current:,} packets ({current/total*100:.1f}%) - "
              f"{rate:,.1f} pkt/s - {elapsed:.1f}s elapsed", end='')
    
    try:
        # Process the pcap file
        extractor.process_pcap(pcap_file, progress_callback)
        
        # Get the flow data as a DataFrame
        print("\n[+] Extracting flow features...")
        df = extractor.get_flow_dataframe()
        
        # Save to CSV
        df.to_csv(output_file, index=False)
        
        # Print some statistics
        print(f"\n[+] Extracted {len(df)} flow records")
        print(f"[+] Features extracted: {len(df.columns)}")
        print(f"[+] Output saved to {output_file}")
        print(f"[+] Total processing time: {time.time() - start_time:.2f} seconds")
        
        # Print the column names
        print("\nAvailable features:")
        print("-" * 80)
        for i, col in enumerate(sorted(df.columns), 1):
            print(f"{i:3}. {col}")
        
    except Exception as e:
        print(f"\n[!] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
