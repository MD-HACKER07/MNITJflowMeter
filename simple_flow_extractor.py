import sys
import os
import csv
from collections import defaultdict
from scapy.all import *
from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.l2 import Ether
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('flow_extractor.log')
    ]
)
logger = logging.getLogger(__name__)

class SimpleFlow:
    def __init__(self, packet, direction):
        """Initialize a new flow with the first packet."""
        self.packets = []
        self.start_time = packet.time
        self.end_time = packet.time
        self.src_ip = packet[IP].src
        self.dst_ip = packet[IP].dst
        self.src_port = None
        self.dst_port = None
        self.protocol = packet[IP].proto
        self.packet_count = 0
        self.byte_count = 0
        self.directions = set()
        
        if TCP in packet:
            self.src_port = packet[TCP].sport
            self.dst_port = packet[TCP].dport
            self.protocol = "TCP"
        elif UDP in packet:
            self.src_port = packet[UDP].sport
            self.dst_port = packet[UDP].dport
            self.protocol = "UDP"
        
        self.add_packet(packet, direction)
    
    def add_packet(self, packet, direction):
        """Add a packet to the flow."""
        self.packets.append((packet, direction))
        self.end_time = packet.time
        self.packet_count += 1
        self.byte_count += len(packet)
        self.directions.add(direction)
    
    def get_duration(self):
        """Get the duration of the flow in seconds."""
        return self.end_time - self.start_time
    
    def get_data(self):
        """Get flow data as a dictionary."""
        return {
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'src_port': self.src_port,
            'dst_port': self.dst_port,
            'protocol': self.protocol,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.get_duration(),
            'packet_count': self.packet_count,
            'byte_count': self.byte_count,
            'avg_packet_size': self.byte_count / self.packet_count if self.packet_count > 0 else 0,
            'packet_rate': self.packet_count / self.get_duration() if self.get_duration() > 0 else 0,
            'byte_rate': self.byte_count / self.get_duration() if self.get_duration() > 0 else 0,
            'directions': ','.join(sorted(self.directions))
        }

class SimpleFlowExtractor:
    def __init__(self, output_file):
        """Initialize the flow extractor."""
        self.output_file = output_file
        self.flows = {}
        self.flow_timeout = 60  # seconds
    
    def get_flow_key(self, packet, direction):
        """Generate a flow key based on packet 5-tuple and direction."""
        if TCP in packet:
            return (
                packet[IP].src, packet[IP].dst,
                packet[TCP].sport, packet[TCP].dport,
                'TCP', direction
            )
        elif UDP in packet:
            return (
                packet[IP].src, packet[IP].dst,
                packet[UDP].sport, packet[UDP].dport,
                'UDP', direction
            )
        else:
            return None
    
    def process_pcap(self, pcap_file):
        """Process a pcap file and extract flow statistics."""
        logger.info(f"Processing {pcap_file}...")
        
        # Read the pcap file
        packets = rdpcap(pcap_file)
        logger.info(f"Read {len(packets)} packets from {pcap_file}")
        
        # Process each packet
        for i, packet in enumerate(packets):
            try:
                if IP not in packet:
                    continue
                    
                # Determine direction (simplified - in a real scenario, you'd need to track flows bidirectionally)
                direction = 'forward'  # Simplified
                
                # Get flow key
                flow_key = self.get_flow_key(packet, direction)
                if not flow_key:
                    continue
                
                # Check if this packet belongs to an existing flow
                if flow_key in self.flows:
                    flow = self.flows[flow_key]
                else:
                    # Check for reverse flow
                    reverse_key = (
                        packet[IP].dst, packet[IP].src,
                        packet[TCP].dport if TCP in packet else packet[UDP].dport,
                        packet[TCP].sport if TCP in packet else packet[UDP].sport,
                        'TCP' if TCP in packet else 'UDP',
                        'reverse' if direction == 'forward' else 'forward'
                    )
                    
                    if reverse_key in self.flows:
                        flow = self.flows[reverse_key]
                    else:
                        # Create a new flow
                        flow = SimpleFlow(packet, direction)
                        self.flows[flow_key] = flow
                
                # Add packet to flow
                flow.add_packet(packet, direction)
                
                # Log progress
                if (i + 1) % 100 == 0:
                    logger.debug(f"Processed {i+1} packets")
                    
            except Exception as e:
                logger.error(f"Error processing packet {i+1}: {str(e)}")
        
        logger.info(f"Processing completed. Found {len(self.flows)} flows.")
        
        # Write flows to CSV
        self.write_flows_to_csv()
    
    def write_flows_to_csv(self):
        """Write flow statistics to a CSV file."""
        if not self.flows:
            logger.warning("No flows to write")
            return
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(self.output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Write flows to CSV
        try:
            with open(self.output_file, 'w', newline='') as f:
                writer = None
                for flow in self.flows.values():
                    data = flow.get_data()
                    if writer is None:
                        writer = csv.DictWriter(f, fieldnames=data.keys())
                        writer.writeheader()
                    writer.writerow(data)
            
            logger.info(f"Flow statistics written to {self.output_file}")
            
            # Print summary
            self.print_summary()
            
        except Exception as e:
            logger.error(f"Error writing flows to CSV: {str(e)}")
    
    def print_summary(self):
        """Print a summary of the extracted flows."""
        if not self.flows:
            print("No flows to summarize")
            return
        
        total_packets = sum(flow.packet_count for flow in self.flows.values())
        total_bytes = sum(flow.byte_count for flow in self.flows.values())
        avg_packet_size = total_bytes / total_packets if total_packets > 0 else 0
        
        print("\nFlow Statistics Summary:")
        print(f"- Total flows: {len(self.flows)}")
        print(f"- Total packets: {total_packets}")
        print(f"- Total bytes: {total_bytes}")
        print(f"- Average packet size: {avg_packet_size:.2f} bytes")
        
        # Print protocol distribution
        protocols = defaultdict(int)
        for flow in self.flows.values():
            protocols[flow.protocol] += 1
        
        print("\nProtocol distribution:")
        for proto, count in protocols.items():
            print(f"- {proto}: {count} flows ({(count / len(self.flows)) * 100:.1f}%)")
        
        # Print top talkers
        print("\nTop talkers by packet count:")
        sorted_flows = sorted(self.flows.values(), key=lambda x: x.packet_count, reverse=True)
        for flow in sorted_flows[:5]:
            print(f"- {flow.src_ip}:{flow.src_port} -> {flow.dst_ip}:{flow.dst_port} "
                  f"({flow.protocol}): {flow.packet_count} packets, {flow.byte_count} bytes")

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input_pcap> <output_csv>")
        sys.exit(1)
    
    input_pcap = sys.argv[1]
    output_csv = sys.argv[2]
    
    if not os.path.exists(input_pcap):
        logger.error(f"Input file '{input_pcap}' not found")
        sys.exit(1)
    
    # Initialize and run the flow extractor
    extractor = SimpleFlowExtractor(output_csv)
    extractor.process_pcap(input_pcap)

if __name__ == "__main__":
    main()
