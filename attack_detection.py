import pandas as pd
from scapy.all import *

class AttackDetector:
    """Class for detecting various network attacks in flow data"""
    
    @staticmethod
    def detect_ntp_amplification(flow_data, packet_data):
        """
        Detect NTP amplification attacks in the flow data.
        
        Args:
            flow_data (pd.DataFrame): DataFrame containing flow data
            packet_data (pd.DataFrame): DataFrame containing packet data
            
        Returns:
            dict: Dictionary with detection results and details
        """
        # Filter for NTP traffic (UDP port 123)
        ntp_flows = flow_data[
            (flow_data['dst_port'] == 123) & 
            (flow_data['protocol'] == 'UDP')
        ]
        
        if ntp_flows.empty:
            return {
                'detected': False,
                'message': 'No NTP traffic detected',
                'flows': pd.DataFrame(),
                'packets': pd.DataFrame()
            }
        
        # Get NTP packets
        ntp_packets = packet_data[
            ((packet_data['src_port'] == 123) | (packet_data['dst_port'] == 123)) &
            (packet_data['protocol'] == 'UDP')
        ]
        
        # Calculate request/response ratios
        request_packets = ntp_packets[ntp_packets['dst_port'] == 123]
        response_packets = ntp_packets[ntp_packets['src_port'] == 123]
        
        # Check for potential amplification
        if len(request_packets) > 0 and len(response_packets) > 0:
            avg_request_size = request_packets['length'].mean()
            avg_response_size = response_packets['length'].mean()
            amplification_ratio = avg_response_size / avg_request_size if avg_request_size > 0 else 0
            
            if amplification_ratio > 10:  # Threshold for amplification
                return {
                    'detected': True,
                    'message': f'Potential NTP amplification attack detected (Amplification ratio: {amplification_ratio:.1f}x)',
                    'amplification_ratio': amplification_ratio,
                    'request_count': len(request_packets),
                    'response_count': len(response_packets),
                    'avg_request_size': avg_request_size,
                    'avg_response_size': avg_response_size,
                    'flows': ntp_flows,
                    'packets': ntp_packets
                }
        
        return {
            'detected': False,
            'message': 'No NTP amplification attack detected',
            'flows': ntp_flows,
            'packets': ntp_packets
        }
    
    @classmethod
    def detect_attacks(cls, flow_data, packet_data):
        """
        Run all attack detection methods.
        
        Args:
            flow_data (pd.DataFrame): Flow data
            packet_data (pd.DataFrame): Packet data
            
        Returns:
            dict: Dictionary with all detection results
        """
        results = {
            'ntp_amplification': cls.detect_ntp_amplification(flow_data, packet_data)
        }
        return results
