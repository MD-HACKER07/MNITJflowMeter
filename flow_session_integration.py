import os
import pandas as pd
from scapy.all import rdpcap
from scapy.layers.inet import IP, TCP, UDP
from collections import defaultdict
from datetime import datetime
import csv

# Import flow session components
from need.flow_session import FlowSession
from need.flow import Flow
from need.features.context.packet_direction import PacketDirection

# Define constants
GARBAGE_COLLECT_PACKETS = 100

class CustomFlowSession(FlowSession):
    """Custom flow session class that collects flows and packets"""
    
    def __init__(self, *args, **kwargs):
        # Set required attributes before parent's __init__ is called
        self.output_mode = "flow"
        self.output_file = "temp_flow.csv"
        self.url_model = None  # Disable URL model functionality
        
        # Initialize parent class
        super().__init__(*args, **kwargs)
        
        # Initialize our custom attributes
        self.flows = {}
        self.packets = []
        self.packets_count = 0
        self._flows = {}  # Store flows from parent class
    
    def on_packet_received(self, packet):
        """Process each packet and extract flow information"""
        if IP not in packet:
            return
            
        try:
            # Process the packet in the parent class
            super().on_packet_received(packet)
            
            # Store the packet
            self.packets.append(packet)
            self.packets_count += 1
            
            # Update flows from parent class
            self.flows = getattr(self, '_flows', {})
            
            # Garbage collection
            if self.packets_count % GARBAGE_COLLECT_PACKETS == 0:
                self.garbage_collect(packet.time)
                
        except Exception as e:
            print(f"Error in on_packet_received: {str(e)}")
            import traceback
            traceback.print_exc()

class FlowSessionExtractor:
    """Wrapper around FlowSession to integrate with our GUI"""
    
    def __init__(self):
        self.flows = {}
        self.packets = []
        self.current_packet_number = 0
    
    def process_pcap(self, pcap_file, progress_callback=None):
        """Process a pcap file using the flow session implementation"""
        try:
            # Create a custom flow session
            session = CustomFlowSession()
            
            # Read packets
            packets = rdpcap(pcap_file)
            total_packets = len(packets)
            
            # Process each packet
            for i, packet in enumerate(packets):
                if IP not in packet:
                    continue
                
                # Process packet in the session
                session.on_packet_received(packet)
                
                # Update progress
                if progress_callback and (i % 100 == 0 or i == total_packets - 1):
                    if not progress_callback(i + 1, total_packets):
                        break
            
            # Store flows and packets from the session
            self.flows = session.flows
            self.packets = session.packets
            
            return True
            
        except Exception as e:
            print(f"Error in process_pcap: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_flow_dataframe(self):
        """Convert flows to a pandas DataFrame"""
        flow_data = []
        
        for flow_key, flow in self.flows.items():
            try:
                # Extract flow information safely with defaults
                flow_info = {
                    'flow_id': str(flow_key),
                    'src_ip': getattr(flow, 'src_ip', ''),
                    'src_port': getattr(flow, 'sport', 0),
                    'dst_ip': getattr(flow, 'dst_ip', ''),
                    'dst_port': getattr(flow, 'dport', 0),
                    'protocol': getattr(flow, 'proto', 'unknown'),
                    'timestamp': getattr(flow, 'timestamp', 0),
                    'packets': len(getattr(flow, 'packets', [])),
                    'bytes': sum(len(p) for p in getattr(flow, 'packets', [])),
                }
                
                # Add timing information if available
                if hasattr(flow, 'start_time') and hasattr(flow, 'end_time'):
                    flow_info['duration'] = flow.end_time - flow.start_time
                    flow_info['start_time'] = flow.start_time
                    flow_info['end_time'] = flow.end_time
                
                # Add TCP flags if available
                if hasattr(flow, 'tcp_flags'):
                    flow_info.update({
                        'tcp_flags': flow.tcp_flags,
                        'syn_count': getattr(flow, 'syn_count', 0),
                        'ack_count': getattr(flow, 'ack_count', 0),
                        'fin_count': getattr(flow, 'fin_count', 0),
                        'rst_count': getattr(flow, 'rst_count', 0),
                    })
                
                # Add packet-level statistics
                packets = getattr(flow, 'packets', [])
                if packets:
                    lengths = [len(p) for p in packets]
                    flow_info.update({
                        'avg_packet_size': sum(lengths) / len(lengths) if lengths else 0,
                        'min_packet_size': min(lengths) if lengths else 0,
                        'max_packet_size': max(lengths) if lengths else 0,
                    })
                
                flow_data.append(flow_info)
                
            except Exception as e:
                print(f"Error processing flow {flow_key}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        return pd.DataFrame(flow_data) if flow_data else pd.DataFrame()
    
    def get_packet_dataframe(self):
        """Convert packets to a pandas DataFrame"""
        if not hasattr(self, 'packets') or not self.packets:
            return pd.DataFrame()
            
        packet_data = []
        
        for i, packet in enumerate(self.packets):
            try:
                if IP not in packet:
                    continue
                    
                pkt_info = {
                    'packet_number': i,
                    'timestamp': packet.time,
                    'src_ip': packet[IP].src,
                    'dst_ip': packet[IP].dst,
                    'protocol': packet[IP].proto,
                    'length': len(packet),
                }
                
                # Add transport layer info
                if TCP in packet:
                    pkt_info.update({
                        'src_port': packet[TCP].sport,
                        'dst_port': packet[TCP].dport,
                        'tcp_flags': str(packet[TCP].flags),
                        'tcp_window': packet[TCP].window,
                    })
                elif UDP in packet:
                    pkt_info.update({
                        'src_port': packet[UDP].sport,
                        'dst_port': packet[UDP].dport,
                    })
                else:
                    pkt_info.update({
                        'src_port': 0,
                        'dst_port': 0,
                    })
                
                packet_data.append(pkt_info)
                
            except Exception as e:
                print(f"Error processing packet {i}: {str(e)}")
                continue
                
        return pd.DataFrame(packet_data) if packet_data else pd.DataFrame()
