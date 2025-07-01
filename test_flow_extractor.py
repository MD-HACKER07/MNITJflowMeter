import sys
import pandas as pd
from flow_session_integration import FlowSessionExtractor

def test_pcap_processing(pcap_file):
    print(f"Testing PCAP file: {pcap_file}")
    
    # Initialize the extractor
    extractor = FlowSessionExtractor()
    
    # Process the PCAP file
    print("Processing PCAP file...")
    success = extractor.process_pcap(pcap_file)
    
    if not success:
        print("Failed to process PCAP file")
        return
    
    # Get flow data
    print("\nFlow Data:")
    flow_df = extractor.get_flow_dataframe()
    if flow_df is not None and not flow_df.empty:
        print(f"Extracted {len(flow_df)} flow records")
        print("\nFlow data columns:", flow_df.columns.tolist())
        print("\nFirst few flow records:")
        print(flow_df.head().to_string())
    else:
        print("No flow data extracted")
    
    # Get packet data
    print("\nPacket Data:")
    packet_df = extractor.get_packet_dataframe()
    if packet_df is not None and not packet_df.empty:
        print(f"Extracted {len(packet_df)} packet records")
        print("\nPacket data columns:", packet_df.columns.tolist())
        print("\nFirst few packet records:")
        print(packet_df.head().to_string())
    else:
        print("No packet data extracted")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_pcap_processing(sys.argv[1])
    else:
        print("Please provide a PCAP file path as an argument")
