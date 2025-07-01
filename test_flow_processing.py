import sys
import os
from scapy.all import *
from MNITJFlowMeter.flow_session import generate_session_class
from scapy.sendrecv import AsyncSniffer
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('flow_processing.log')
    ]
)
logger = logging.getLogger(__name__)

class TestFlowSession:
    def __init__(self, output_file):
        self.output_file = output_file
        self.flows = {}
        self.csv_line = 0
        self.csv_writer = None
        
        # Open the output file for writing
        self.output = open(self.output_file, 'w')
        self.csv_writer = csv.writer(self.output)
        
        # Initialize counters
        self.packets_count = 0
        
    def process_pcap(self, pcap_file):
        """Process a pcap file and generate flow statistics."""
        logger.info(f"Processing {pcap_file}...")
        
        # Read the pcap file
        packets = rdpcap(pcap_file)
        logger.info(f"Read {len(packets)} packets from {pcap_file}")
        
        # Process each packet
        for i, packet in enumerate(packets):
            try:
                self.on_packet_received(packet)
                if (i + 1) % 100 == 0:
                    logger.debug(f"Processed {i+1} packets")
            except Exception as e:
                logger.error(f"Error processing packet {i+1}: {str(e)}")
        
        # Final garbage collection to process remaining flows
        self.garbage_collect(None)
        
        # Close the output file
        self.output.close()
        
        logger.info(f"Processing completed. Output written to {self.output_file}")
    
    def on_packet_received(self, packet):
        """Process a single packet."""
        from MNITJFlowMeter.features.context.packet_direction import PacketDirection
        from MNITJFlowMeter.features.context.packet_flow_key import get_packet_flow_key
        
        count = 0
        direction = PacketDirection.FORWARD
        
        # Skip non-IP packets
        if 'IP' not in packet:
            logger.debug("Skipping non-IP packet")
            return
            
        # Skip packets without TCP or UDP
        if 'TCP' not in packet and 'UDP' not in packet:
            logger.debug("Skipping non-TCP/UDP packet")
            return
        
        self.packets_count += 1
        
        try:
            # Get the flow key
            packet_flow_key = get_packet_flow_key(packet, direction)
            flow = self.flows.get((packet_flow_key, count))
            
            # If no flow exists, create a new one
            if flow is None:
                from MNITJFlowMeter.flow import Flow
                flow = Flow(packet, direction)
                self.flows[(packet_flow_key, count)] = flow
                logger.debug(f"Created new flow: {packet_flow_key}")
            
            # Add the packet to the flow
            flow.add_packet(packet, direction)
            logger.debug(f"Added packet to flow: {packet_flow_key}")
            
            # Periodically clean up old flows
            if self.packets_count % 100 == 0:
                self.garbage_collect(packet.time)
                
        except Exception as e:
            logger.error(f"Error processing packet: {str(e)}")
    
    def garbage_collect(self, latest_time):
        """Clean up old flows and write them to the output file."""
        logger.debug(f"Garbage collection started. Current flows: {len(self.flows)}")
        
        keys = list(self.flows.keys())
        for k in keys:
            flow = self.flows.get(k)
            
            # If it's time to collect this flow
            if latest_time is None or (latest_time - flow.latest_timestamp) > 10:  # 10 second timeout
                try:
                    # Get flow data
                    data = flow.get_data()
                    
                    # Write header if this is the first flow
                    if self.csv_line == 0:
                        self.csv_writer.writerow(data.keys())
                    
                    # Write flow data
                    self.csv_writer.writerow(data.values())
                    self.csv_line += 1
                    
                    logger.debug(f"Wrote flow data to CSV: {k}")
                    
                    # Remove the flow
                    del self.flows[k]
                    
                except Exception as e:
                    logger.error(f"Error processing flow {k}: {str(e)}")
        
        logger.debug(f"Garbage collection finished. Remaining flows: {len(self.flows)}")

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
    analyzer = TestFlowSession(output_csv)
    analyzer.process_pcap(input_pcap)
    
    # Print summary
    if os.path.exists(output_csv) and os.path.getsize(output_csv) > 0:
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
    else:
        logger.error("No flow data was generated")
        sys.exit(1)

if __name__ == "__main__":
    import csv
    main()
