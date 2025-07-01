import os
import sys
import csv
import logging
from scapy.all import *
from MNITJFlowMeter.flow_session import generate_session_class
from scapy.sendrecv import AsyncSniffer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FlowAnalyzer:
    def __init__(self, output_file):
        self.output_file = output_file
        self.flow_session = None
        self.sniffer = None
        self.flows = []
        
    def process_pcap(self, pcap_file):
        """Process a pcap file and generate flow statistics."""
        logger.info(f"Processing {pcap_file}...")
        
        # Create a custom flow session class
        FlowSession = generate_session_class("flow", self.output_file, None)
        
        # Create a sniffer to process the pcap file
        self.sniffer = AsyncSniffer(
            offline=pcap_file,
            filter="ip and (tcp or udp)",
            prn=None,
            session=FlowSession,
            store=False
        )
        
        # Start the sniffer
        logger.info("Starting packet processing...")
        self.sniffer.start()
        
        try:
            # Wait for the sniffer to finish
            self.sniffer.join()
            logger.info("Packet processing completed")
            return True
            
        except Exception as e:
            logger.error(f"Error during packet processing: {str(e)}")
            return False

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input_pcap> <output_csv>")
        sys.exit(1)
    
    input_pcap = sys.argv[1]
    output_csv = sys.argv[2]
    
    if not os.path.exists(input_pcap):
        logger.error(f"Input file '{input_pcap}' not found")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_csv)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Initialize and run the flow analyzer
    analyzer = FlowAnalyzer(output_csv)
    success = analyzer.process_pcap(input_pcap)
    
    if success:
        logger.info(f"Successfully processed {input_pcap}")
        if os.path.exists(output_csv) and os.path.getsize(output_csv) > 0:
            logger.info(f"Flow statistics saved to {output_csv}")
            
            # Print summary of the output file
            try:
                with open(output_csv, 'r') as f:
                    reader = csv.reader(f)
                    headers = next(reader, None)
                    row_count = sum(1 for row in reader)
                    
                    print("\nFlow Statistics Summary:")
                    print(f"- Output file: {output_csv}")
                    print(f"- Number of flows: {row_count}")
                    if headers:
                        print("\nAvailable features:")
                        print(", ".join(headers))
            except Exception as e:
                logger.error(f"Error reading output file: {str(e)}")
        else:
            logger.error("Output file was not created or is empty")
    else:
        logger.error(f"Failed to process pcap file: {input_pcap}")
        sys.exit(1)

if __name__ == "__main__":
    main()
