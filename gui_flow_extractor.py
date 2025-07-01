import os
import time
import pandas as pd
from scapy.all import rdpcap, IP, TCP, UDP
from collections import defaultdict

class SimpleFlowExtractor:
    def __init__(self, output_file):
        """Initialize the flow extractor."""
        self.output_file = output_file
        self.flows = {}
        
    def process_pcap_gui(self, pcap_file, progress_callback=None):
        """Process a pcap file and extract flow statistics with progress updates.
        
        Args:
            pcap_file: Path to the pcap file
            progress_callback: Callback function that takes (current, total) as arguments
        """
        # Clear any existing flows
        self.flows = {}
        
        try:
            # Read the pcap file
            packets = rdpcap(pcap_file)
            total_packets = len(packets)
            
            # Process each packet
            for i, packet in enumerate(packets):
                try:
                    # Skip non-IP packets
                    if IP not in packet:
                        continue
                        
                    # Determine flow direction (simplified - in a real scenario, you'd track bidirectional flows)
                    direction = 'forward'  # Simplified for this example
                    
                    # Get flow key
                    flow_key = self.get_flow_key(packet, direction)
                    if not flow_key:
                        continue
                    
                    # Add packet to flow
                    if flow_key in self.flows:
                        flow = self.flows[flow_key]
                    else:
                        # Create a new flow
                        flow = self.Flow(packet, direction)
                        self.flows[flow_key] = flow
                    
                    # Add packet to flow
                    flow.add_packet(packet, direction)
                    
                    # Update progress more frequently but with throttling
                    if progress_callback and (i + 1) % 10 == 0:  # Update every 10 packets for better performance
                        try:
                            if callable(progress_callback):
                                progress_callback(i + 1, total_packets)
                        except Exception as e:
                            print(f"Error in progress callback: {e}")
                    
                except Exception as e:
                    print(f"Error processing packet {i + 1}: {str(e)}")
            
            # Final progress update
            if progress_callback and callable(progress_callback):
                try:
                    progress_callback(total_packets, total_packets)
                except Exception as e:
                    print(f"Error in final progress update: {e}")
                    
        except Exception as e:
            print(f"Error reading pcap file: {e}")
            if progress_callback and callable(progress_callback):
                try:
                    progress_callback(0, 1)  # Signal error by setting current=0
                except:
                    pass
            raise
    
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
        return None
    
    class Flow:
        """Class to represent a network flow."""
        
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
            
            # Extract protocol-specific information
            if TCP in packet:
                self.src_port = packet[TCP].sport
                self.dst_port = packet[TCP].dport
                self.protocol = "TCP"
            elif UDP in packet:
                self.src_port = packet[UDP].sport
                self.dst_port = packet[UDP].dport
                self.protocol = "UDP"
            
            # Add the first packet
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
            return self.end_time - self.start_time if hasattr(self, 'end_time') else 0
        
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
