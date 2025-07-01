import os
import time
import pandas as pd
import numpy as np
from scapy.all import rdpcap, PcapReader
from scapy.layers.inet import IP, TCP, UDP, ICMP
from collections import defaultdict, namedtuple
from datetime import datetime
from multiprocessing import Pool, cpu_count
from functools import partial
import pickle
import tempfile

class OptimizedFlowFeatures:
    """Optimized flow feature extraction with reduced memory usage"""
    
    __slots__ = [
        'src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol', 'packet_count',
        'flow_start_time', 'flow_last_seen', 'flow_duration', 'packet_sizes',
        'inter_arrival_times', 'tcp_flags', 'fwd_packets', 'bwd_packets',
        'fwd_bytes', 'bwd_bytes', 'fwd_header_bytes', 'bwd_header_bytes',
        'fwd_iat', 'bwd_iat', 'fwd_psh_flags', 'bwd_psh_flags', 'fwd_urg_flags',
        'bwd_urg_flags', 'fwd_urgent_packets', 'bwd_urgent_packets',
        'fwd_avg_packet_size', 'bwd_avg_packet_size', 'fwd_avg_iat', 'bwd_avg_iat'
    ]
    
    def __init__(self, packet, direction):
        """Initialize flow with first packet"""
        # Basic flow information
        self.src_ip = packet[IP].src if IP in packet else '0.0.0.0'
        self.dst_ip = packet[IP].dst if IP in packet else '0.0.0.0'
        self.protocol = packet[IP].proto if IP in packet else 0
        self.src_port = 0
        self.dst_port = 0
        
        # Ports based on protocol
        if TCP in packet:
            self.src_port = packet[TCP].sport
            self.dst_port = packet[TCP].dport
            self.tcp_flags = {packet[TCP].flags}
        elif UDP in packet:
            self.src_port = packet[UDP].sport
            self.dst_port = packet[UDP].dport
            self.tcp_flags = set()
        else:
            self.tcp_flags = set()
        
        # Initialize flow timing
        timestamp = float(packet.time)
        self.flow_start_time = timestamp
        self.flow_last_seen = timestamp
        self.flow_duration = 0.0
        
        # Initialize packet tracking
        self.packet_count = 1
        self.packet_sizes = [len(packet)]
        self.inter_arrival_times = []
        
        # Initialize direction-specific counters
        self.fwd_packets = 1 if direction == 'forward' else 0
        self.bwd_packets = 1 if direction == 'backward' else 0
        self.fwd_bytes = len(packet) if direction == 'forward' else 0
        self.bwd_bytes = len(packet) if direction == 'backward' else 0
        self.fwd_header_bytes = len(packet[IP].payload) if IP in packet and direction == 'forward' else 0
        self.bwd_header_bytes = len(packet[IP].payload) if IP in packet and direction == 'backward' else 0
        
        # Initialize timing stats
        self.fwd_iat = []
        self.bwd_iat = []
        
        # Flag tracking
        self.fwd_psh_flags = 1 if TCP in packet and packet[TCP].flags.PSH and direction == 'forward' else 0
        self.bwd_psh_flags = 1 if TCP in packet and packet[TCP].flags.PSH and direction == 'backward' else 0
        self.fwd_urg_flags = 1 if TCP in packet and packet[TCP].flags.URG and direction == 'forward' else 0
        self.bwd_urg_flags = 1 if TCP in packet and packet[TCP].flags.URG and direction == 'backward' else 0
        self.fwd_urgent_packets = 1 if TCP in packet and packet[TCP].flags.URG and direction == 'forward' else 0
        self.bwd_urgent_packets = 1 if TCP in packet and packet[TCP].flags.URG and direction == 'backward' else 0
        
        # Initialize averages
        self.fwd_avg_packet_size = len(packet) if direction == 'forward' else 0.0
        self.bwd_avg_packet_size = len(packet) if direction == 'backward' else 0.0
        self.fwd_avg_iat = 0.0
        self.bwd_avg_iat = 0.0
    
    def update(self, packet, direction):
        """Update flow with new packet"""
        timestamp = float(packet.time)
        packet_size = len(packet)
        
        # Update flow timing
        self.flow_duration = timestamp - self.flow_start_time
        self.flow_last_seen = timestamp
        
        # Update packet tracking
        self.packet_count += 1
        self.packet_sizes.append(packet_size)
        
        # Update direction-specific counters
        if direction == 'forward':
            self.fwd_packets += 1
            self.fwd_bytes += packet_size
            if IP in packet:
                self.fwd_header_bytes += len(packet[IP].payload)
            if len(self.fwd_iat) > 0:
                self.fwd_iat.append(timestamp - self.flow_last_seen)
        else:
            self.bwd_packets += 1
            self.bwd_bytes += packet_size
            if IP in packet:
                self.bwd_header_bytes += len(packet[IP].payload)
            if len(self.bwd_iat) > 0:
                self.bwd_iat.append(timestamp - self.flow_last_seen)
        
        # Update TCP flags if applicable
        if TCP in packet:
            self.tcp_flags.add(packet[TCP].flags)
            if packet[TCP].flags.PSH:
                if direction == 'forward':
                    self.fwd_psh_flags += 1
                else:
                    self.bwd_psh_flags += 1
            if packet[TCP].flags.URG:
                if direction == 'forward':
                    self.fwd_urg_flags += 1
                    self.fwd_urgent_packets += 1
                else:
                    self.bwd_urg_flags += 1
                    self.bwd_urgent_packets += 1
        
        # Update inter-arrival times
        if len(self.packet_sizes) > 1:
            self.inter_arrival_times.append(timestamp - self.flow_last_seen)
        
        # Update averages
        if self.fwd_packets > 0:
            self.fwd_avg_packet_size = self.fwd_bytes / self.fwd_packets
        if self.bwd_packets > 0:
            self.bwd_avg_packet_size = self.bwd_bytes / self.bwd_packets
        
        if self.fwd_iat:
            self.fwd_avg_iat = sum(self.fwd_iat) / len(self.fwd_iat)
        if self.bwd_iat:
            self.bwd_avg_iat = sum(self.bwd_iat) / len(self.bwd_iat)
    
    def to_dict(self):
        """Convert flow to dictionary for DataFrame conversion"""
        return {
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'src_port': self.src_port,
            'dst_port': self.dst_port,
            'protocol': self.protocol,
            'flow_duration': self.flow_duration,
            'fwd_packets': self.fwd_packets,
            'bwd_packets': self.bwd_packets,
            'fwd_bytes': self.fwd_bytes,
            'bwd_bytes': self.bwd_bytes,
            'fwd_header_bytes': self.fwd_header_bytes,
            'bwd_header_bytes': self.bwd_header_bytes,
            'fwd_avg_packet_size': self.fwd_avg_packet_size,
            'bwd_avg_packet_size': self.bwd_avg_packet_size,
            'fwd_avg_iat': self.fwd_avg_iat,
            'bwd_avg_iat': self.bwd_avg_iat,
            'fwd_psh_flags': self.fwd_psh_flags,
            'bwd_psh_flags': self.bwd_psh_flags,
            'fwd_urg_flags': self.fwd_urg_flags,
            'bwd_urg_flags': self.bwd_urg_flags,
            'fwd_urgent_packets': self.fwd_urgent_packets,
            'bwd_urgent_packets': self.bwd_urgent_packets,
            'total_packets': self.fwd_packets + self.bwd_packets,
            'total_bytes': self.fwd_bytes + self.bwd_bytes,
        }

class OptimizedFlowExtractor:
    """Optimized flow extractor with memory efficiency and parallel processing"""
    
    def __init__(self, max_memory_mb=1024, chunk_size=10000, max_flows=100000):
        self.flows = {}
        self.max_memory_mb = max_memory_mb
        self.chunk_size = chunk_size
        self.max_flows = max_flows
        self.temp_dir = tempfile.mkdtemp(prefix='mntj_flows_')
        self.flow_files = []
    
    def _get_flow_key(self, packet, direction):
        """Generate a flow key based on 5-tuple and direction"""
        if IP not in packet:
            return None
            
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        protocol = packet[IP].proto
        
        # Determine ports based on protocol
        src_port = 0
        dst_port = 0
        
        if TCP in packet:
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
        elif UDP in packet:
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport
        
        # Create consistent flow key regardless of direction
        if direction == 'forward':
            return (src_ip, dst_ip, src_port, dst_port, protocol)
        else:
            return (dst_ip, src_ip, dst_port, src_port, protocol)
    
    def _process_packet_chunk(self, packets, progress_callback=None):
        """Process a chunk of packets"""
        chunk_flows = {}
        
        for i, packet in enumerate(packets):
            try:
                if IP not in packet:
                    continue
                    
                # Determine direction
                direction = 'forward'  # Default direction
                
                # Get flow key
                flow_key = self._get_flow_key(packet, direction)
                if not flow_key:
                    continue
                
                # Add reverse direction flow key
                rev_flow_key = self._get_flow_key(packet, 'backward')
                
                # Check if this is actually a reply (backward) packet
                if flow_key in self.flows or flow_key in chunk_flows:
                    # Existing forward flow
                    flow = self.flows.get(flow_key) or chunk_flows.get(flow_key)
                    flow.update(packet, 'forward')
                elif rev_flow_key in self.flows or rev_flow_key in chunk_flows:
                    # This is a reply packet for an existing flow
                    flow = self.flows.get(rev_flow_key) or chunk_flows.get(rev_flow_key)
                    flow.update(packet, 'backward')
                    flow_key = rev_flow_key  # Use the reverse key for storage
                else:
                    # New flow
                    flow = OptimizedFlowFeatures(packet, direction)
                    chunk_flows[flow_key] = flow
                
                # Periodically save flows to disk to manage memory
                if len(chunk_flows) >= self.max_flows:
                    self._save_flows_to_disk(chunk_flows)
                    chunk_flows = {}
                
                # Update progress if callback provided
                if progress_callback and i % 1000 == 0:
                    progress_callback(i, len(packets))
                    
            except Exception as e:
                print(f"Error processing packet: {e}")
                continue
        
        return chunk_flows
    
    def _save_flows_to_disk(self, flows):
        """Save flows to disk and clear memory"""
        if not flows:
            return
            
        # Create a temporary file for this chunk
        fd, temp_file = tempfile.mkstemp(suffix='.pkl', dir=self.temp_dir)
        os.close(fd)
        
        # Convert flows to dict and save
        with open(temp_file, 'wb') as f:
            pickle.dump({k: v.to_dict() for k, v in flows.items()}, f)
        
        self.flow_files.append(temp_file)
        flows.clear()
    
    def process_pcap(self, pcap_file, progress_callback=None):
        """Process PCAP file in chunks for memory efficiency"""
        print(f"Processing {pcap_file} in chunks...")
        
        # Reset state
        self.flows = {}
        self.flow_files = []
        
        try:
            # First pass: count total packets for progress
            print("Counting packets...")
            total_packets = 0
            with PcapReader(pcap_file) as pcap_reader:
                for _ in pcap_reader:
                    total_packets += 1
            
            print(f"Found {total_packets} packets")
            
            # Process in chunks
            processed_packets = 0
            chunk = []
            
            with PcapReader(pcap_file) as pcap_reader:
                for packet in pcap_reader:
                    chunk.append(packet)
                    
                    if len(chunk) >= self.chunk_size:
                        chunk_flows = self._process_packet_chunk(chunk, progress_callback)
                        self.flows.update(chunk_flows)
                        processed_packets += len(chunk)
                        chunk = []
                        
                        # Update progress
                        if progress_callback:
                            progress_callback(processed_packets, total_packets)
            
            # Process remaining packets in the last chunk
            if chunk:
                chunk_flows = self._process_packet_chunk(chunk, progress_callback)
                self.flows.update(chunk_flows)
                processed_packets += len(chunk)
                
                if progress_callback:
                    progress_callback(processed_packets, total_packets)
            
            # Save any remaining flows to disk
            if self.flows:
                self._save_flows_to_disk(self.flows)
                self.flows = {}
            
            print("Finished processing PCAP file")
            
        except Exception as e:
            print(f"Error processing PCAP file: {e}")
            raise
    
    def get_flow_dataframe(self):
        """Combine flows from memory and disk into a single DataFrame"""
        all_flows = []
        
        # Add in-memory flows
        for flow in self.flows.values():
            all_flows.append(flow.to_dict())
        
        # Add flows from disk
        for flow_file in self.flow_files:
            try:
                with open(flow_file, 'rb') as f:
                    flows = pickle.load(f)
                    all_flows.extend(flows.values())
            except Exception as e:
                print(f"Error loading flows from {flow_file}: {e}")
        
        # Clean up temporary files
        self._cleanup_temp_files()
        
        # Create and return DataFrame
        if not all_flows:
            return pd.DataFrame()
            
        return pd.DataFrame(all_flows)
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        for flow_file in self.flow_files:
            try:
                if os.path.exists(flow_file):
                    os.remove(flow_file)
            except Exception as e:
                print(f"Error removing temp file {flow_file}: {e}")
        
        try:
            if os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
        except Exception as e:
            print(f"Error removing temp directory {self.temp_dir}: {e}")
        
        self.flow_files = []
    
    def __del__(self):
        """Cleanup on object destruction"""
        self._cleanup_temp_files()

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python optimized_flow_extractor.py <pcap_file>")
        sys.exit(1)
    
    pcap_file = sys.argv[1]
    
    def progress_callback(current, total):
        if total > 0:
            progress = (current / total) * 100
            print(f"\rProgress: {progress:.2f}% ({current}/{total} packets)", end="")
    
    print(f"Processing {pcap_file}...")
    extractor = OptimizedFlowExtractor()
    extractor.process_pcap(pcap_file, progress_callback)
    
    print("\nExtracting features...")
    df = extractor.get_flow_dataframe()
    
    print(f"\nExtracted {len(df)} flows")
    print("\nSample of extracted features:")
    print(df.head())
