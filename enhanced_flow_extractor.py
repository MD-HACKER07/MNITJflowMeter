import os
import time
import pandas as pd
import numpy as np
from scapy.all import rdpcap, IP, TCP, UDP, ICMP, Raw, Ether
from scapy.packet import Packet
from collections import defaultdict, namedtuple, deque
from datetime import datetime
from enum import Enum, auto
import socket
import struct
import ipaddress
from typing import Dict, List, Tuple, Optional, Any

class PacketDirection(Enum):
    FORWARD = auto()
    REVERSE = auto()

class EnhancedFlowFeatures:
    """Enhanced flow feature extraction based on CICFlowMeter implementation"""
    
    def __init__(self, packet, direction):
        self.packets = [(packet, direction)]
        self.flow_interarrival_time = []
        self.active = []
        self.idle = []
        self.start_timestamp = packet.time
        self.latest_timestamp = packet.time
        self.protocol = packet[IP].proto if IP in packet else 0
        
        # Initialize flow key
        self.src_ip = packet[IP].src if IP in packet else '0.0.0.0'
        self.dst_ip = packet[IP].dst if IP in packet else '0.0.0.0'
        self.src_port = 0
        self.dst_port = 0
        
        # Initialize TCP/UDP ports
        if TCP in packet:
            self.src_port = packet[TCP].sport
            self.dst_port = packet[TCP].dport
        elif UDP in packet:
            self.src_port = packet[UDP].sport
            self.dst_port = packet[UDP].dport
            
        # Initialize bulk transfer tracking
        self._init_bulk_tracking()
        
        # Initialize window sizes
        self.init_window_size = {
            PacketDirection.FORWARD: packet[TCP].window if TCP in packet else 0,
            PacketDirection.REVERSE: 0
        }
        
        # Initialize packet counts and lengths
        self.packet_counts = {
            PacketDirection.FORWARD: 0,
            PacketDirection.REVERSE: 0
        }
        
        self.packet_lengths = {
            PacketDirection.FORWARD: [],
            PacketDirection.REVERSE: []
        }
        
        # Initialize flag counts
        self.flag_counts = {
            'FIN': 0, 'SYN': 0, 'RST': 0, 'PSH': 0,
            'ACK': 0, 'URG': 0, 'ECE': 0, 'CWR': 0
        }
        
        # Add first packet
        self.add_packet(packet, direction)
    
    def _init_bulk_tracking(self):
        """Initialize variables for bulk transfer tracking"""
        # Forward direction
        self.forward_bulk_last_timestamp = 0
        self.forward_bulk_start_tmp = 0
        self.forward_bulk_count = 0
        self.forward_bulk_count_tmp = 0
        self.forward_bulk_duration = 0
        self.forward_bulk_packet_count = 0
        self.forward_bulk_size = 0
        self.forward_bulk_size_tmp = 0
        
        # Backward direction
        self.backward_bulk_last_timestamp = 0
        self.backward_bulk_start_tmp = 0
        self.backward_bulk_count = 0
        self.backward_bulk_count_tmp = 0
        self.backward_bulk_duration = 0
        self.backward_bulk_packet_count = 0
        self.backward_bulk_size = 0
        self.backward_bulk_size_tmp = 0
    
    def add_packet(self, packet, direction):
        """Add a packet to the flow"""
        self.packets.append((packet, direction))
        
        # Update timestamps
        current_time = packet.time
        if self.latest_timestamp != 0:
            self.flow_interarrival_time.append(1e6 * (current_time - self.latest_timestamp))
        self.latest_timestamp = max([current_time, self.latest_timestamp])
        
        # Update packet counts
        self.packet_counts[direction] += 1
        
        # Update packet lengths
        packet_size = len(packet)
        self.packet_lengths[direction].append(packet_size)
        
        # Update TCP flags if present
        if TCP in packet:
            tcp = packet[TCP]
            if tcp.flags.F: self.flag_counts['FIN'] += 1
            if tcp.flags.S: self.flag_counts['SYN'] += 1
            if tcp.flags.R: self.flag_counts['RST'] += 1
            if tcp.flags.P: self.flag_counts['PSH'] += 1
            if tcp.flags.A: self.flag_counts['ACK'] += 1
            if tcp.flags.U: self.flag_counts['URG'] += 1
            if tcp.flags.E: self.flag_counts['ECE'] += 1
            if tcp.flags.C: self.flag_counts['CWR'] += 1
            
            # Update window size
            if direction == PacketDirection.FORWARD and self.init_window_size[direction] == 0:
                self.init_window_size[direction] = tcp.window
            elif direction == PacketDirection.REVERSE:
                self.init_window_size[direction] = tcp.window
        
        # Update bulk transfer stats
        self._update_flow_bulk(packet, direction)
    
    def _update_flow_bulk(self, packet, direction):
        """Update bulk transfer statistics"""
        payload_size = len(packet[Raw].load) if Raw in packet else 0
        if payload_size == 0:
            return
            
        # Constants for bulk transfer detection
        BULK_BOUND = 4
        CLUMP_TIMEOUT = 1.0  # seconds
        
        if direction == PacketDirection.FORWARD:
            if self.backward_bulk_last_timestamp > self.forward_bulk_start_tmp:
                self.forward_bulk_start_tmp = 0
                
            if self.forward_bulk_start_tmp == 0:
                self.forward_bulk_start_tmp = packet.time
                self.forward_bulk_last_timestamp = packet.time
                self.forward_bulk_count_tmp = 1
                self.forward_bulk_size_tmp = payload_size
            else:
                if (packet.time - self.forward_bulk_last_timestamp) > CLUMP_TIMEOUT:
                    self.forward_bulk_start_tmp = packet.time
                    self.forward_bulk_last_timestamp = packet.time
                    self.forward_bulk_count_tmp = 1
                    self.forward_bulk_size_tmp = payload_size
                else:
                    self.forward_bulk_count_tmp += 1
                    self.forward_bulk_size_tmp += payload_size
                    
                    if self.forward_bulk_count_tmp == BULK_BOUND:
                        self.forward_bulk_count += 1
                        self.forward_bulk_packet_count += self.forward_bulk_count_tmp
                        self.forward_bulk_size += self.forward_bulk_size_tmp
                        self.forward_bulk_duration += (packet.time - self.forward_bulk_start_tmp)
                    elif self.forward_bulk_count_tmp > BULK_BOUND:
                        self.forward_bulk_packet_count += 1
                        self.forward_bulk_size += payload_size
                        self.forward_bulk_duration += (packet.time - self.forward_bulk_last_timestamp)
                    
                    self.forward_bulk_last_timestamp = packet.time
        else:  # REVERSE direction
            if self.forward_bulk_last_timestamp > self.backward_bulk_start_tmp:
                self.backward_bulk_start_tmp = 0
                
            if self.backward_bulk_start_tmp == 0:
                self.backward_bulk_start_tmp = packet.time
                self.backward_bulk_last_timestamp = packet.time
                self.backward_bulk_count_tmp = 1
                self.backward_bulk_size_tmp = payload_size
            else:
                if (packet.time - self.backward_bulk_last_timestamp) > CLUMP_TIMEOUT:
                    self.backward_bulk_start_tmp = packet.time
                    self.backward_bulk_last_timestamp = packet.time
                    self.backward_bulk_count_tmp = 1
                    self.backward_bulk_size_tmp = payload_size
                else:
                    self.backward_bulk_count_tmp += 1
                    self.backward_bulk_size_tmp += payload_size
                    
                    if self.backward_bulk_count_tmp == BULK_BOUND:
                        self.backward_bulk_count += 1
                        self.backward_bulk_packet_count += self.backward_bulk_count_tmp
                        self.backward_bulk_size += self.backward_bulk_size_tmp
                        self.backward_bulk_duration += (packet.time - self.backward_bulk_start_tmp)
                    elif self.backward_bulk_count_tmp > BULK_BOUND:
                        self.backward_bulk_packet_count += 1
                        self.backward_bulk_size += payload_size
                        self.backward_bulk_duration += (packet.time - self.backward_bulk_last_timestamp)
                    
                    self.backward_bulk_last_timestamp = packet.time
    
    def get_flow_features(self):
        """Extract all flow features"""
        if not self.packets:
            return {}
            
        # Calculate basic statistics
        flow_duration = self.latest_timestamp - self.start_timestamp
        total_packets = sum(self.packet_counts.values())
        
        # Calculate packet length statistics
        def get_stats(values):
            if not values:
                return {'total': 0, 'mean': 0, 'std': 0, 'min': 0, 'max': 0}
            return {
                'total': sum(values),
                'mean': np.mean(values),
                'std': np.std(values) if len(values) > 1 else 0,
                'min': min(values),
                'max': max(values)
            }
        
        fwd_stats = get_stats(self.packet_lengths[PacketDirection.FORWARD])
        bwd_stats = get_stats(self.packet_lengths[PacketDirection.REVERSE])
        all_stats = get_stats(
            self.packet_lengths[PacketDirection.FORWARD] + 
            self.packet_lengths[PacketDirection.REVERSE]
        )
        
        # Calculate IAT statistics
        if len(self.flow_interarrival_time) > 0:
            iat_stats = {
                'mean': np.mean(self.flow_interarrival_time),
                'std': np.std(self.flow_interarrival_time),
                'min': min(self.flow_interarrival_time),
                'max': max(self.flow_interarrival_time)
            }
        else:
            iat_stats = {'mean': 0, 'std': 0, 'min': 0, 'max': 0}
        
        # Build feature dictionary
        features = {
            # Basic flow information
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'src_port': self.src_port,
            'dst_port': self.dst_port,
            'protocol': self.protocol,
            'timestamp': self.start_timestamp,
            'flow_duration': flow_duration * 1e6,  # Convert to microseconds
            
            # Packet count statistics
            'tot_fwd_pkts': self.packet_counts[PacketDirection.FORWARD],
            'tot_bwd_pkts': self.packet_counts[PacketDirection.REVERSE],
            'tot_pkts': total_packets,
            
            # Packet length statistics
            'totlen_fwd_pkts': fwd_stats['total'],
            'totlen_bwd_pkts': bwd_stats['total'],
            'fwd_pkt_len_max': float(fwd_stats['max']),
            'fwd_pkt_len_min': float(fwd_stats['min']),
            'fwd_pkt_len_mean': float(fwd_stats['mean']),
            'fwd_pkt_len_std': float(fwd_stats['std']),
            'bwd_pkt_len_max': float(bwd_stats['max']),
            'bwd_pkt_len_min': float(bwd_stats['min']),
            'bwd_pkt_len_mean': float(bwd_stats['mean']),
            'bwd_pkt_len_std': float(bwd_stats['std']),
            'pkt_len_max': float(all_stats['max']),
            'pkt_len_min': float(all_stats['min']),
            'pkt_len_mean': float(all_stats['mean']),
            'pkt_len_std': float(all_stats['std']),
            
            # Flow IAT statistics
            'flow_iat_mean': float(iat_stats['mean']),
            'flow_iat_std': float(iat_stats['std']),
            'flow_iat_max': float(iat_stats['max']),
            'flow_iat_min': float(iat_stats['min']),
            
            # TCP flags
            'fin_flag_cnt': self.flag_counts['FIN'],
            'syn_flag_cnt': self.flag_counts['SYN'],
            'rst_flag_cnt': self.flag_counts['RST'],
            'psh_flag_cnt': self.flag_counts['PSH'],
            'ack_flag_cnt': self.flag_counts['ACK'],
            'urg_flag_cnt': self.flag_counts['URG'],
            'ece_flag_cnt': self.flag_counts['ECE'],
            'cwr_flag_cnt': self.flag_counts['CWR'],
            
            # Window sizes
            'init_fwd_win_byts': self.init_window_size[PacketDirection.FORWARD],
            'init_bwd_win_byts': self.init_window_size[PacketDirection.REVERSE],
            
            # Bulk transfer statistics
            'fwd_bulk_packets': self.forward_bulk_packet_count,
            'fwd_bulk_size': self.forward_bulk_size,
            'fwd_bulk_duration': self.forward_bulk_duration,
            'bwd_bulk_packets': self.backward_bulk_packet_count,
            'bwd_bulk_size': self.backward_bulk_size,
            'bwd_bulk_duration': self.backward_bulk_duration,
        }
        
        # Calculate rates
        if flow_duration > 0:
            features.update({
                'flow_pkts_s': total_packets / flow_duration,
                'flow_byts_s': all_stats['total'] / flow_duration,
                'fwd_pkts_s': self.packet_counts[PacketDirection.FORWARD] / flow_duration,
                'bwd_pkts_s': self.packet_counts[PacketDirection.REVERSE] / flow_duration,
            })
        else:
            features.update({
                'flow_pkts_s': 0,
                'flow_byts_s': 0,
                'fwd_pkts_s': 0,
                'bwd_pkts_s': 0,
            })
            
        return features

class PacketFeatures:
    """Class to store and extract packet-level features"""
    
    @staticmethod
    def extract_packet_features(packet: Packet) -> Dict[str, Any]:
        """Extract features from a single packet"""
        features = {
            'frame_number': 0,
            'timestamp': packet.time,
            'frame_len': len(packet),
            'eth_src': packet[Ether].src if Ether in packet else '',
            'eth_dst': packet[Ether].dst if Ether in packet else '',
            'ip_src': packet[IP].src if IP in packet else '',
            'ip_dst': packet[IP].dst if IP in packet else '',
            'ip_version': packet[IP].version if IP in packet else 0,
            'ip_ttl': packet[IP].ttl if IP in packet else 0,
            'ip_len': packet[IP].len if IP in packet else 0,
            'ip_flags': packet[IP].flags if IP in packet else 0,
            'ip_proto': packet[IP].proto if IP in packet else 0,
            'tcp_sport': 0,
            'tcp_dport': 0,
            'tcp_flags': 0,
            'tcp_flags_str': '',
            'tcp_window': 0,
            'tcp_seq': 0,
            'tcp_ack': 0,
            'tcp_header_len': 0,
            'udp_sport': 0,
            'udp_dport': 0,
            'udp_len': 0,
            'protocol': '',
            'payload_len': 0,
            'is_malformed': 0
        }
        
        # Extract TCP features
        if TCP in packet:
            tcp = packet[TCP]
            features.update({
                'tcp_sport': tcp.sport,
                'tcp_dport': tcp.dport,
                'tcp_flags': tcp.flags,
                'tcp_flags_str': str(tcp.flags),
                'tcp_window': tcp.window,
                'tcp_seq': tcp.seq,
                'tcp_ack': tcp.ack,
                'tcp_header_len': tcp.dataofs * 4 if hasattr(tcp, 'dataofs') else 0,
                'protocol': 'TCP'
            })
        # Extract UDP features
        elif UDP in packet:
            udp = packet[UDP]
            features.update({
                'udp_sport': udp.sport,
                'udp_dport': udp.dport,
                'udp_len': udp.len,
                'protocol': 'UDP'
            })
        elif ICMP in packet:
            features['protocol'] = 'ICMP'
            
        # Calculate payload length
        if Raw in packet:
            features['payload_len'] = len(packet[Raw].load)
            
        return features


class EnhancedFlowExtractor:
    """Extracts network flows with enhanced feature extraction"""
    
    def __init__(self):
        self.flows = {}
        self.packets = []
        self.current_packet_number = 0
    
    def get_flow_key(self, packet: Packet, direction: PacketDirection) -> Optional[str]:
        """Generate a flow key based on 5-tuple, direction, and timestamp"""
        if IP not in packet:
            return None
            
        src = packet[IP].src
        dst = packet[IP].dst
        proto = packet[IP].proto
        
        # For TCP/UDP, use ports; for others, use 0
        sport, dport = 0, 0
        if TCP in packet:
            sport, dport = packet[TCP].sport, packet[TCP].dport
        elif UDP in packet:
            sport, dport = packet[UDP].sport, packet[UDP].dport
        
        # Include timestamp in the key to ensure each packet is a separate flow
        timestamp = int(packet.time * 1000000)  # Convert to microseconds for better precision
            
        # Create a unique key for each packet
        if direction == PacketDirection.FORWARD:
            return f"{src}_{sport}_{dst}_{dport}_{proto}_{timestamp}"
        return f"{dst}_{dport}_{src}_{sport}_{proto}_{timestamp}"
    
    def process_packet(self, packet: Packet, direction: PacketDirection) -> None:
        """Process a single packet and update flow information"""
        if IP not in packet:
            return
            
        # Extract packet features
        self.current_packet_number += 1
        packet_features = PacketFeatures.extract_packet_features(packet)
        packet_features['packet_number'] = self.current_packet_number
        packet_features['direction'] = 'forward' if direction == PacketDirection.FORWARD else 'backward'
        
        # Add to packet list
        self.packets.append(packet_features)
        
        # Update flow information
        flow_key = self.get_flow_key(packet, direction)
        if not flow_key:
            return
            
        if flow_key not in self.flows:
            self.flows[flow_key] = EnhancedFlowFeatures(packet, direction)
        else:
            self.flows[flow_key].add_packet(packet, direction)
    
    def process_pcap(self, pcap_file: str, progress_callback=None) -> None:
        """Process a pcap file and extract packet and flow information"""
        try:
            packets = rdpcap(pcap_file)
            total_packets = len(packets)
            
            for i, packet in enumerate(packets):
                if IP not in packet:
                    continue
                    
                # Process all IP packets in the forward direction
                # The flow key will include the timestamp to ensure each packet is unique
                self.process_packet(packet, PacketDirection.FORWARD)
                
                # Update progress if callback provided
                if progress_callback and (i % 100 == 0 or i == total_packets - 1):
                    if not progress_callback(i + 1, total_packets):
                        break
                        
        except Exception as e:
            print(f"Error processing pcap file: {e}")
            raise
    
    def get_packet_dataframe(self) -> pd.DataFrame:
        """Convert packets to a pandas DataFrame"""
        if not self.packets:
            return pd.DataFrame()
            
        # Convert packet timestamps to human-readable format
        df = pd.DataFrame(self.packets)
        if 'timestamp' in df.columns:
            df['time'] = pd.to_datetime(df['timestamp'], unit='s')
            df['time_str'] = df['time'].dt.strftime('%b %d, %Y %H:%M:%S.%f')
        
        return df
    
    def get_flow_dataframe(self) -> pd.DataFrame:
        """Convert flows to a pandas DataFrame"""
        flow_data = []
        
        for flow_key, flow in self.flows.items():
            flow_info = {
                'flow_id': flow_key,
                'src_ip': flow.src_ip,
                'src_port': flow.src_port,
                'dst_ip': flow.dst_ip,
                'dst_port': flow.dst_port,
                'protocol': flow.protocol,
                'start_time': flow.start_timestamp,
                'end_time': flow.latest_timestamp,
                'duration': flow.latest_timestamp - flow.start_timestamp,
                'fwd_pkts_tot': flow.packet_counts[PacketDirection.FORWARD],
                'bwd_pkts_tot': flow.packet_counts[PacketDirection.REVERSE],
                'fwd_byts_tot': sum(flow.packet_lengths[PacketDirection.FORWARD]),
                'bwd_byts_tot': sum(flow.packet_lengths[PacketDirection.REVERSE]),
                'flow_pkts_s': (flow.packet_counts[PacketDirection.FORWARD] + flow.packet_counts[PacketDirection.REVERSE]) / 
                              max(1, (flow.latest_timestamp - flow.start_timestamp)),
                'flow_byts_s': (sum(flow.packet_lengths[PacketDirection.FORWARD]) + 
                              sum(flow.packet_lengths[PacketDirection.REVERSE])) / 
                             max(1, (flow.latest_timestamp - flow.start_timestamp)),
                'fwd_pkts_s': flow.packet_counts[PacketDirection.FORWARD] / 
                             max(1, (flow.latest_timestamp - flow.start_timestamp)),
                'bwd_pkts_s': flow.packet_counts[PacketDirection.REVERSE] / 
                             max(1, (flow.latest_timestamp - flow.start_timestamp)),
                'fwd_iat_mean': np.mean(flow.forward_iat) if hasattr(flow, 'forward_iat') and flow.forward_iat else 0,
                'bwd_iat_mean': np.mean(flow.backward_iat) if hasattr(flow, 'backward_iat') and flow.backward_iat else 0,
                'active_mean': np.mean(flow.active) if hasattr(flow, 'active') and flow.active else 0,
                'idle_mean': np.mean(flow.idle) if hasattr(flow, 'idle') and flow.idle else 0,
            }
            flow_data.append(flow_info)
        
        return pd.DataFrame(flow_data)

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python enhanced_flow_extractor.py <pcap_file>")
        sys.exit(1)
    
    pcap_file = sys.argv[1]
    
    def progress_callback(current, total):
        print(f"Processing: {current}/{total} packets", end='\r')
        return True
    
    print(f"Processing {pcap_file}...")
    extractor = EnhancedFlowExtractor()
    extractor.process_pcap(pcap_file, progress_callback)
    
    print("\nExtracting features...")
    df = extractor.get_flow_dataframe()
    
    print("\nExtracted features:")
    print(f"Total flows: {len(df)}")
    print("\nFirst few flows:")
    print(df.head())
    
    # Save to CSV
    output_file = os.path.splitext(pcap_file)[0] + "_flows.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved flow data to {output_file}")
