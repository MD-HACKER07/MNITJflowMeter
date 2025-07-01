import os
import time
import pandas as pd
import numpy as np
import psutil
import gc
from scapy.all import PcapReader, IP, TCP, UDP, ICMP
from scapy.packet import Packet
from collections import defaultdict, namedtuple
from datetime import datetime
from multiprocessing import Pool, cpu_count
from functools import partial
import warnings

# Suppress Scapy warnings
warnings.filterwarnings("ignore", category=UserWarning, module='scapy')

# Memory management
def get_memory_usage():
    """Get current process memory usage in MB"""
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)  # Convert to MB

class FlowFeatures:
    """Class to calculate and store flow features"""
    
    def __init__(self, packet, direction):
        """Initialize flow with first packet"""
        self.packets = [(packet, direction)]
        self.timestamps = [packet.time]
        self.directions = [direction]
        self.packet_sizes = [len(packet)]
        self.tcp_flags = set()
        
        # Initialize all features
        self._init_features(packet, direction)
    
    def _init_features(self, packet, direction):
        """Initialize all flow features"""
        # Basic flow information
        self.src_ip = packet[IP].src if IP in packet else '0.0.0.0'
        self.dst_ip = packet[IP].dst if IP in packet else '0.0.0.0'
        self.protocol = packet[IP].proto if IP in packet else 0
        self.src_port = 0
        self.dst_port = 0
        
        # Initialize last packet times
        self.last_fwd_time = float(packet.time) if direction == 'forward' else 0.0
        self.last_bwd_time = float(packet.time) if direction == 'backward' else 0.0
        
        # Ports based on protocol
        if TCP in packet:
            self.src_port = packet[TCP].sport
            self.dst_port = packet[TCP].dport
            self._extract_tcp_flags(packet[TCP])
        elif UDP in packet:
            self.src_port = packet[UDP].sport
            self.dst_port = packet[UDP].dport
        
        # Initialize flow attributes with explicit float conversion
        self.flow_start_time = float(packet.time)
        self.flow_last_seen = float(packet.time)
        self.flow_duration = 0.0
        self.flow_id = f"{self.src_ip}_{self.src_port}_{self.dst_ip}_{self.dst_port}_{int(packet.time)}"
        
        # Initialize packet and byte counters
        self.fwd_packets = 1 if direction == 'forward' else 0
        self.bwd_packets = 1 if direction == 'backward' else 0
        self.fwd_bytes = int(len(packet)) if direction == 'forward' else 0
        self.bwd_bytes = int(len(packet)) if direction == 'backward' else 0
        
        # Initialize TCP flags
        self.tcp_flags = set()
        
        # Initialize lists for statistical calculations
        pkt_len = int(len(packet))
        self.fwd_packet_sizes = [pkt_len] if direction == 'forward' else []
        self.bwd_packet_sizes = [pkt_len] if direction == 'backward' else []
        self.fwd_iat = []  # Forward inter-arrival times
        self.bwd_iat = []  # Backward inter-arrival times
        self.flow_iat = []  # All inter-arrival times
        self.packet_sizes = [pkt_len]  # All packet sizes
        self.timestamps = [self.flow_start_time]  # All packet timestamps
        
        # TCP specific
        self.fin_flag_count = 1 if TCP in packet and packet[TCP].flags.F else 0
        self.syn_flag_count = 1 if TCP in packet and packet[TCP].flags.S else 0
        self.rst_flag_count = 1 if TCP in packet and packet[TCP].flags.R else 0
        self.psh_flag_count = 1 if TCP in packet and packet[TCP].flags.P else 0
        self.ack_flag_count = 1 if TCP in packet and packet[TCP].flags.A else 0
        self.urg_flag_count = 1 if TCP in packet and packet[TCP].flags.U else 0
        self.cwr_flag_count = 1 if TCP in packet and packet[TCP].flags.C else 0
        self.ece_flag_count = 1 if TCP in packet and packet[TCP].flags.E else 0
        
        # Window sizes
        self.init_fwd_win_size = packet[TCP].window if TCP in packet else 0
        self.init_bwd_win_size = 0  # Will be updated with backward packet
        
        # Initialize other features
        self.flow_byts_s = 0
        self.flow_pkts_s = 0
        self.fwd_pkts_s = 0
        self.bwd_pkts_s = 0
        
    def _extract_tcp_flags(self, tcp_layer):
        """Extract TCP flags"""
        if tcp_layer.flags.F: self.tcp_flags.add('FIN')
        if tcp_layer.flags.S: self.tcp_flags.add('SYN')
        if tcp_layer.flags.R: self.tcp_flags.add('RST')
        if tcp_layer.flags.P: self.tcp_flags.add('PSH')
        if tcp_layer.flags.A: self.tcp_flags.add('ACK')
        if tcp_layer.flags.U: self.tcp_flags.add('URG')
        if tcp_layer.flags.E: self.tcp_flags.add('ECE')
        if tcp_layer.flags.C: self.tcp_flags.add('CWR')
    
    def add_packet(self, packet, direction):
        """Add a packet to the flow with optimized memory usage"""
        try:
            # Get current timestamp and packet size with proper type conversion
            current_time = float(packet.time)
            packet_size = int(len(packet))
            
            # Initialize flow times if not set
            if not hasattr(self, 'flow_start_time'):
                self.flow_start_time = current_time
            if not hasattr(self, 'flow_last_seen'):
                self.flow_last_seen = current_time
            
            # Update timestamps
            self.flow_last_seen = current_time
            self.flow_duration = current_time - self.flow_start_time
            
            # Initialize packet lists if not exists (using more memory-efficient structures)
            if not hasattr(self, 'timestamps'):
                self.timestamps = []
            if not hasattr(self, 'fwd_packet_sizes'):
                self.fwd_packet_sizes = []
            if not hasattr(self, 'bwd_packet_sizes'):
                self.bwd_packet_sizes = []
            if not hasattr(self, 'fwd_iat'):
                self.fwd_iat = []
            if not hasattr(self, 'bwd_iat'):
                self.bwd_iat = []
            if not hasattr(self, 'flow_iat'):
                self.flow_iat = []
            
            # Store packet timestamp (with reduced precision to save memory)
            self.timestamps.append(round(current_time, 6))
            
            # Initialize counters if not exists
            if not hasattr(self, 'fwd_packets'):
                self.fwd_packets = 0
            if not hasattr(self, 'bwd_packets'):
                self.bwd_packets = 0
            if not hasattr(self, 'fwd_bytes'):
                self.fwd_bytes = 0
            if not hasattr(self, 'bwd_bytes'):
                self.bwd_bytes = 0
            
            # Update packet and byte counts based on direction
            if direction == 'forward':
                self.fwd_packets += 1
                self.fwd_bytes += packet_size
                self.fwd_packet_sizes.append(packet_size)
                
                # Initialize last_fwd_time if not exists
                if not hasattr(self, 'last_fwd_time'):
                    self.last_fwd_time = current_time
                
                # Calculate IAT for forward packets
                if self.fwd_packets > 1 and hasattr(self, 'last_fwd_time'):
                    iat = current_time - self.last_fwd_time
                    self.fwd_iat.append(round(iat, 6))  # Reduced precision to save memory
                    self.flow_iat.append(round(iat, 6))
                self.last_fwd_time = current_time
                
            else:  # backward
                self.bwd_packets += 1
                self.bwd_bytes += packet_size
                self.bwd_packet_sizes.append(packet_size)
                
                # Initialize last_bwd_time if not exists
                if not hasattr(self, 'last_bwd_time'):
                    self.last_bwd_time = current_time
                
                # Calculate IAT for backward packets
                if self.bwd_packets > 1 and hasattr(self, 'last_bwd_time'):
                    iat = current_time - self.last_bwd_time
                    self.bwd_iat.append(round(iat, 6))  # Reduced precision to save memory
                    self.flow_iat.append(round(iat, 6))
                self.last_bwd_time = current_time
                
            # Add to packet sizes list (with reduced precision if needed)
            self.packet_sizes.append(packet_size)
            
            # Periodically clean up large lists to save memory
            if len(self.timestamps) > 1000 and len(self.timestamps) % 500 == 0:
                # Keep only the last 1000 timestamps
                self.timestamps = self.timestamps[-1000:]
                self.packet_sizes = self.packet_sizes[-1000:]
                if hasattr(self, 'fwd_packet_sizes') and len(self.fwd_packet_sizes) > 1000:
                    self.fwd_packet_sizes = self.fwd_packet_sizes[-1000:]
                if hasattr(self, 'bwd_packet_sizes') and len(self.bwd_packet_sizes) > 1000:
                    self.bwd_packet_sizes = self.bwd_packet_sizes[-1000:]
                    
        except Exception as e:
            print(f"Error adding packet to flow: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Update TCP flags
        if TCP in packet:
            tcp = packet[TCP]
            self.fin_flag_count += 1 if tcp.flags.F else 0
            self.syn_flag_count += 1 if tcp.flags.S else 0
            self.rst_flag_count += 1 if tcp.flags.R else 0
            self.psh_flag_count += 1 if tcp.flags.P else 0
            self.ack_flag_count += 1 if tcp.flags.A else 0
            self.urg_flag_count += 1 if tcp.flags.U else 0
            self.cwr_flag_count += 1 if tcp.flags.C else 0
            self.ece_flag_count += 1 if tcp.flags.E else 0
            
            # Update window sizes
            if direction == 'backward' and self.init_bwd_win_size == 0:
                self.init_bwd_win_size = tcp.window
        
        # Store packet info
        self.packets.append((packet, direction))
        self.timestamps.append(packet.time)
        self.directions.append(direction)
        self.packet_sizes.append(packet_size)
    
    def _safe_statistics(self, values, default=0.0):
        """Safely calculate statistics for a list of values, handling empty lists and NaN values"""
        if not values or len(values) == 0:
            return {
                'max': default,
                'min': default,
                'mean': default,
                'std': default,
                'var': default,
                'sum': default
            }
            
        try:
            # Convert all values to float and filter out any potential None or NaN values
            clean_values = [float(v) for v in values if v is not None and not np.isnan(float(v))]
            if not clean_values:
                return {
                    'max': default,
                    'min': default,
                    'mean': default,
                    'std': default,
                    'var': default,
                    'sum': default
                }
                
            return {
                'max': float(np.nanmax(clean_values)),
                'min': float(np.nanmin(clean_values)),
                'mean': float(np.nanmean(clean_values)),
                'std': float(np.nanstd(clean_values)) if len(clean_values) > 1 else default,
                'var': float(np.nanvar(clean_values)) if len(clean_values) > 1 else default,
                'sum': float(np.nansum(clean_values))
            }
        except (ValueError, TypeError, RuntimeWarning):
            return {
                'max': default,
                'min': default,
                'mean': default,
                'std': default,
                'var': default,
                'sum': default
            }
    
    def calculate_features(self):
        """Calculate all flow features with NaN handling"""
        # Initialize with default values to avoid KeyError
        total_packets = getattr(self, 'fwd_packets', 0) + getattr(self, 'bwd_packets', 0)
        total_bytes = getattr(self, 'fwd_bytes', 0) + getattr(self, 'bwd_bytes', 0)
        
        # Initialize TCP flags with default values if not set
        tcp_flags = {
            'fin': getattr(self, 'fin_flag_count', 0),
            'syn': getattr(self, 'syn_flag_count', 0),
            'rst': getattr(self, 'rst_flag_count', 0),
            'psh': getattr(self, 'psh_flag_count', 0),
            'ack': getattr(self, 'ack_flag_count', 0),
            'urg': getattr(self, 'urg_flag_count', 0),
            'cwr': getattr(self, 'cwr_flag_count', 0),
            'ece': getattr(self, 'ece_flag_count', 0)
        }
        
        # Basic flow features with safe attribute access
        features = {
            'flow_id': getattr(self, 'flow_id', ''),
            'src_ip': getattr(self, 'src_ip', '0.0.0.0'),
            'src_port': getattr(self, 'src_port', 0),
            'dst_ip': getattr(self, 'dst_ip', '0.0.0.0'),
            'dst_port': getattr(self, 'dst_port', 0),
            'protocol': getattr(self, 'protocol', 0),
            'timestamp': float(getattr(self, 'flow_start_time', 0.0)),
            'flow_duration': float(getattr(self, 'flow_duration', 0.0)),
            'tot_fwd_pkts': getattr(self, 'fwd_packets', 0),
            'tot_bwd_pkts': getattr(self, 'bwd_packets', 0),
            'totlen_fwd_pkts': getattr(self, 'fwd_bytes', 0),
            'totlen_bwd_pkts': getattr(self, 'bwd_bytes', 0),
            'fin_flag_cnt': tcp_flags['fin'],
            'syn_flag_cnt': tcp_flags['syn'],
            'rst_flag_cnt': tcp_flags['rst'],
            'psh_flag_cnt': tcp_flags['psh'],
            'ack_flag_cnt': tcp_flags['ack'],
            'urg_flag_cnt': tcp_flags['urg'],
            'cwr_flag_count': tcp_flags['cwr'],
            'ece_flag_count': tcp_flags['ece'],
            'init_fwd_win_byts': getattr(self, 'init_fwd_win_size', 0),
            'init_bwd_win_byts': getattr(self, 'init_bwd_win_size', 0)
        }
        
        # Calculate rates with safe division
        flow_dur = float(getattr(self, 'flow_duration', 0.0))
        safe_flow_dur = max(flow_dur, 1e-10)  # Avoid division by zero
        
        # Calculate rates with safe division and NaN handling
        rates = {
            'flow_byts_s': float(total_bytes) / safe_flow_dur if safe_flow_dur > 0 else 0.0,
            'flow_pkts_s': float(total_packets) / safe_flow_dur if safe_flow_dur > 0 else 0.0,
            'fwd_pkts_s': float(getattr(self, 'fwd_packets', 0)) / safe_flow_dur if safe_flow_dur > 0 else 0.0,
            'bwd_pkts_s': float(getattr(self, 'bwd_packets', 0)) / safe_flow_dur if safe_flow_dur > 0 else 0.0,
            'fwd_avg_bytes_per_bulk': 0.0,  # Placeholder for future implementation
            'fwd_avg_packets_per_bulk': 0.0,  # Placeholder for future implementation
            'fwd_avg_bulk_rate': 0.0,  # Placeholder for future implementation
            'bwd_avg_bytes_per_bulk': 0.0,  # Placeholder for future implementation
            'bwd_avg_packets_per_bulk': 0.0,  # Placeholder for future implementation
            'bwd_avg_bulk_rate': 0.0,  # Placeholder for future implementation
            'fwd_avg_bytes_per_sec': float(getattr(self, 'fwd_bytes', 0)) / safe_flow_dur if safe_flow_dur > 0 else 0.0,
            'bwd_avg_bytes_per_sec': float(getattr(self, 'bwd_bytes', 0)) / safe_flow_dur if safe_flow_dur > 0 else 0.0,
            'flow_avg_bytes_per_sec': float(total_bytes) / safe_flow_dur if safe_flow_dur > 0 else 0.0
        }
        
        # Update features with rates, ensuring no NaN or inf values
        for k, v in rates.items():
            features[k] = 0.0 if v != v or abs(v) == float('inf') else float(v)
        
        # Calculate packet length statistics using safe_statistics
        fwd_stats = self._safe_statistics(getattr(self, 'fwd_packet_sizes', []))
        features.update({
            'fwd_pkt_len_max': fwd_stats['max'],
            'fwd_pkt_len_min': fwd_stats['min'],
            'fwd_pkt_len_mean': fwd_stats['mean'],
            'fwd_pkt_len_std': fwd_stats['std'],
            'fwd_pkt_len_var': fwd_stats['var'],
            'fwd_pkt_len_total': fwd_stats['sum']
        })
        
        bwd_stats = self._safe_statistics(getattr(self, 'bwd_packet_sizes', []))
        features.update({
            'bwd_pkt_len_max': bwd_stats['max'],
            'bwd_pkt_len_min': bwd_stats['min'],
            'bwd_pkt_len_mean': bwd_stats['mean'],
            'bwd_pkt_len_std': bwd_stats['std'],
            'bwd_pkt_len_var': bwd_stats['var'],
            'bwd_pkt_len_total': bwd_stats['sum']
        })
        
        # Calculate IAT statistics using safe_statistics
        flow_iat_stats = self._safe_statistics(getattr(self, 'flow_iat', []))
        features.update({
            'flow_iat_mean': flow_iat_stats['mean'],
            'flow_iat_max': flow_iat_stats['max'],
            'flow_iat_min': flow_iat_stats['min'],
            'flow_iat_std': flow_iat_stats['std'],
            'flow_iat_var': flow_iat_stats['var'],
            'flow_iat_total': flow_iat_stats['sum']
        })
        
        fwd_iat_stats = self._safe_statistics(getattr(self, 'fwd_iat', []))
        features.update({
            'fwd_iat_tot': fwd_iat_stats['sum'],
            'fwd_iat_max': fwd_iat_stats['max'],
            'fwd_iat_min': fwd_iat_stats['min'],
            'fwd_iat_mean': fwd_iat_stats['mean'],
            'fwd_iat_std': fwd_iat_stats['std'],
            'fwd_iat_var': fwd_iat_stats['var']
        })
        
        bwd_iat_stats = self._safe_statistics(getattr(self, 'bwd_iat', []))
        features.update({
            'bwd_iat_tot': bwd_iat_stats['sum'],
            'bwd_iat_max': bwd_iat_stats['max'],
            'bwd_iat_min': bwd_iat_stats['min'],
            'bwd_iat_mean': bwd_iat_stats['mean'],
            'bwd_iat_std': bwd_iat_stats['std'],
            'bwd_iat_var': bwd_iat_stats['var']
        })
        
        # Calculate packet size statistics using safe_statistics
        pkt_stats = self._safe_statistics(getattr(self, 'packet_sizes', []))
        features.update({
            'pkt_len_max': pkt_stats['max'],
            'pkt_len_min': pkt_stats['min'],
            'pkt_len_mean': pkt_stats['mean'],
            'pkt_len_std': pkt_stats['std'],
            'pkt_len_var': pkt_stats['var'],
            'pkt_len_total': pkt_stats['sum']
        })
        
        # Calculate down/up ratio with safe division
        bwd_pkts = getattr(self, 'bwd_packets', 0)
        fwd_pkts = getattr(self, 'fwd_packets', 0)
        features['down_up_ratio'] = (
            float(fwd_pkts) / float(bwd_pkts) 
            if bwd_pkts > 0 else 0.0
        )
        
        # Calculate average packet size with safe division
        features['pkt_size_avg'] = (
            float(total_bytes) / float(total_packets) 
            if total_packets > 0 else 0.0
        )
        
        # Calculate active/idle stats using timestamps
        timestamps = getattr(self, 'timestamps', [])
        if timestamps and len(timestamps) > 1:
            try:
                # Convert timestamps to float and sort to ensure increasing order
                times = sorted([float(t) for t in timestamps if t is not None])
                if len(times) > 1:
                    iats = np.diff(times)
                    iat_stats = self._safe_statistics(iats)
                    
                    # Active stats (same as IAT stats for now)
                    features.update({
                        'active_max': iat_stats['max'],
                        'active_min': iat_stats['min'],
                        'active_mean': iat_stats['mean'],
                        'active_std': iat_stats['std'],
                        'active_var': iat_stats['var'],
                        'active_total': iat_stats['sum']
                    })
                    
                    # For idle stats, we could implement more sophisticated logic
                    # For now, using the same as active
                    features.update({
                        'idle_max': iat_stats['max'],
                        'idle_min': iat_stats['min'],
                        'idle_mean': iat_stats['mean'],
                        'idle_std': iat_stats['std'],
                        'idle_var': iat_stats['var'],
                        'idle_total': iat_stats['sum']
                    })
            except (ValueError, TypeError) as e:
                # If there's any error in timestamp processing, set defaults
                features.update({
                    'active_max': 0.0, 'active_min': 0.0, 'active_mean': 0.0,
                    'active_std': 0.0, 'active_var': 0.0, 'active_total': 0.0,
                    'idle_max': 0.0, 'idle_min': 0.0, 'idle_mean': 0.0,
                    'idle_std': 0.0, 'idle_var': 0.0, 'idle_total': 0.0
                })
        
        # Add subflow information (simplified)
        features.update({
            'subflow_fwd_pkts': self.fwd_packets,
            'subflow_bwd_pkts': self.bwd_packets,
            'subflow_fwd_byts': self.fwd_bytes,
            'subflow_bwd_byts': self.bwd_bytes,
        })
        
        return features

class FullFlowExtractor:
    """Extracts network flows with full feature set"""
    
    def __init__(self):
        self.flows = {}
    
    def get_flow_key(self, packet, direction):
        """Generate a flow key based on 5-tuple and direction"""
        if IP not in packet:
            return None
            
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        
        # Determine source and destination ports based on protocol
        src_port = 0
        dst_port = 0
        
        if TCP in packet:
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
            protocol = 'TCP'
        elif UDP in packet:
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport
            protocol = 'UDP'
        elif ICMP in packet:
            protocol = 'ICMP'
        else:
            protocol = packet[IP].proto
        
        # Create a bidirectional flow key (same flow in both directions)
        if direction == 'forward':
            return (src_ip, dst_ip, src_port, dst_port, protocol)
        else:
            return (dst_ip, src_ip, dst_port, src_port, protocol)
    
    def _process_packet_batch(self, packets_batch):
        """Process a batch of packets and return flow updates"""
        batch_flows = {}
        for packet in packets_batch:
            if IP not in packet:
                continue
                
            # Determine direction (simplified - in reality, you'd need to know your network)
            direction = 'forward'  # Default
            
            # Get flow key
            flow_key = self.get_flow_key(packet, direction)
            if not flow_key:
                continue
            
            # Add packet to flow in batch
            if flow_key in batch_flows:
                batch_flows[flow_key].add_packet(packet, direction)
            else:
                # New flow in this batch
                batch_flows[flow_key] = FlowFeatures(packet, direction)
        
        return batch_flows

    def process_pcap(self, pcap_file, progress_callback=None):
        """Process a pcap file and extract flows with full features using chunked processing"""
        try:
            start_time = time.time()
            print(f"Starting PCAP processing: {pcap_file}")
            
            # Get total packets for progress tracking
            total_packets = 0
            with PcapReader(pcap_file) as pcap_reader:
                total_packets = sum(1 for _ in pcap_reader)
            
            print(f"Total packets to process: {total_packets}")
            
            # Process packets in chunks
            chunk_size = 100000  # Adjust based on available memory
            processed_packets = 0
            
            with PcapReader(pcap_file) as pcap_reader:
                while True:
                    # Read a chunk of packets
                    packets_chunk = []
                    try:
                        for _ in range(chunk_size):
                            packet = next(pcap_reader)
                            packets_chunk.append(packet)
                    except StopIteration:
                        pass  # End of file
                    
                    if not packets_chunk:
                        break  # No more packets
                    
                    # Process the chunk
                    chunk_start = time.time()
                    batch_flows = self._process_packet_batch(packets_chunk)
                    
                    # Merge batch flows into main flows
                    for flow_key, flow in batch_flows.items():
                        if flow_key in self.flows:
                            # For existing flows, we need to merge the statistics
                            # This is a simplified merge - in a real implementation, 
                            # you'd want to properly merge the flow statistics
                            self.flows[flow_key].packets.extend(flow.packets)
                            self.flows[flow_key].timestamps.extend(flow.timestamps)
                            self.flows[flow_key].packet_sizes.extend(flow.packet_sizes)
                            # Update other statistics...
                        else:
                            # New flow
                            self.flows[flow_key] = flow
                    
                    # Update progress
                    processed_packets += len(packets_chunk)
                    if progress_callback:
                        progress_callback(processed_packets, total_packets, 
                                        time.time() - start_time, 
                                        get_memory_usage())
                    
                    # Print progress
                    chunk_time = time.time() - chunk_start
                    print(f"Processed {processed_packets}/{total_packets} packets "
                          f"({processed_packets/total_packets*100:.1f}%) - "
                          f"{len(packets_chunk)/chunk_time:.1f} pkt/s - "
                          f"{get_memory_usage():.1f} MB")
                    
                    # Force garbage collection
                    del packets_chunk
                    del batch_flows
                    gc.collect()
            
            # Final progress update
            if progress_callback:
                progress_callback(total_packets, total_packets, 
                                time.time() - start_time,
                                get_memory_usage())
            
            print(f"PCAP processing completed in {time.time() - start_time:.2f} seconds")
            print(f"Memory usage: {get_memory_usage():.1f} MB")
            
        except Exception as e:
            print(f"Error processing pcap: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_flow_dataframe(self):
        """Convert flows to a pandas DataFrame"""
        flow_data = []
        for flow in self.flows.values():
            flow_data.append(flow.calculate_features())
        return pd.DataFrame(flow_data)

# Example usage:
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python full_flow_extractor.py <pcap_file> [output_csv]")
        sys.exit(1)
    
    pcap_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'flow_features.csv'
    
    print(f"Processing {pcap_file}...")
    extractor = FullFlowExtractor()
    
    def progress_callback(current, total):
        print(f"\rProcessed {current}/{total} packets ({current/total*100:.1f}%)", end='')
    
    extractor.process_pcap(pcap_file, progress_callback)
    print("\nExtracting features...")
    
    df = extractor.get_flow_dataframe()
    df.to_csv(output_file, index=False)
    print(f"Saved {len(df)} flow records to {output_file}")
