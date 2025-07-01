#!/usr/bin/env python3
import sys
import pandas as pd
from scapy.all import rdpcap
from flow_session_integration import FlowSessionExtractor

def export_packets_to_csv(pcap_file, output_file=None):
    """
    Extract packets from a PCAP file and export to CSV
    
    Args:
        pcap_file (str): Path to the input PCAP file
        output_file (str, optional): Path to the output CSV file. 
                                   If not provided, will use the input filename with .csv extension
    """
    if not output_file:
        output_file = pcap_file.rsplit('.', 1)[0] + '_packets.csv'
    
    print(f"Processing {pcap_file}...")
    
    # Initialize the extractor
    extractor = FlowSessionExtractor()
    
    # Process the PCAP file
    extractor.process_pcap(pcap_file)
    
    # Get packet data as DataFrame
    packet_df = extractor.get_packet_dataframe()
    
    if packet_df is not None and not packet_df.empty:
        # Save to CSV
        packet_df.to_csv(output_file, index=False)
        print(f"Successfully exported {len(packet_df)} packets to {output_file}")
        return output_file
    else:
        print("No packet data found in the PCAP file")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_packets.py <pcap_file> [output_file]")
        sys.exit(1)
    
    pcap_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    export_packets_to_csv(pcap_file, output_file)
