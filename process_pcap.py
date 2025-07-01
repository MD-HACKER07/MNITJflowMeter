import sys
import os
import csv
import math
import logging
from datetime import datetime
import scapy.all as scapy
from scapy.sendrecv import AsyncSniffer
from scapy.sessions import DefaultSession
from mnitjflowmeter.flow_session import generate_session_class

# Constants
EXPIRED_UPDATE = 40  # seconds

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('MNITJFlowMeter.log')
    ]
)
logger = logging.getLogger(__name__)

def format_flow_data(flow_data):
    """Format flow data to match command-line output format"""
    # Convert timestamp to readable format if it's a float
    if 'timestamp' in flow_data and isinstance(flow_data['timestamp'], (int, float)):
        try:
            flow_data['timestamp'] = datetime.fromtimestamp(flow_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            flow_data['timestamp'] = ''
    
    # Replace None with 0 for numeric fields
    for key, value in flow_data.items():
        if value is None or (isinstance(value, float) and math.isnan(value)):
            flow_data[key] = 0
        elif isinstance(value, float):
            # Format float to avoid scientific notation
            if value == 0 or (abs(value) > 1e-4 and abs(value) < 1e6):
                flow_data[key] = round(value, 6)
            else:
                flow_data[key] = f"{value:.6e}"
    
    return flow_data

def process_pcap(pcap_file, output_file):
    """Process a pcap file and generate flow statistics."""
    logger.info(f"Processing {pcap_file}...")
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Define the CSV header to match command-line output
        header = [
            'src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol', 'timestamp',
            'flow_duration', 'flow_byts_s', 'flow_pkts_s', 'fwd_pkts_s', 'bwd_pkts_s',
            'tot_fwd_pkts', 'tot_bwd_pkts', 'totlen_fwd_pkts', 'totlen_bwd_pkts',
            'fwd_pkt_len_max', 'fwd_pkt_len_min', 'fwd_pkt_len_mean', 'fwd_pkt_len_std',
            'bwd_pkt_len_max', 'bwd_pkt_len_min', 'bwd_pkt_len_mean', 'bwd_pkt_len_std',
            'pkt_len_max', 'pkt_len_min', 'pkt_len_mean', 'pkt_len_std', 'pkt_len_var',
            'fwd_header_len', 'bwd_header_len', 'fwd_seg_size_min', 'fwd_act_data_pkts',
            'flow_iat_mean', 'flow_iat_max', 'flow_iat_min', 'flow_iat_std',
            'fwd_iat_tot', 'fwd_iat_max', 'fwd_iat_min', 'fwd_iat_mean', 'fwd_iat_std',
            'bwd_iat_tot', 'bwd_iat_max', 'bwd_iat_min', 'bwd_iat_mean', 'bwd_iat_std',
            'fwd_psh_flags', 'bwd_psh_flags', 'fwd_urg_flags', 'bwd_urg_flags',
            'fin_flag_cnt', 'syn_flag_cnt', 'rst_flag_cnt', 'psh_flag_cnt', 'ack_flag_cnt',
            'urg_flag_cnt', 'ece_flag_cnt', 'down_up_ratio', 'pkt_size_avg',
            'init_fwd_win_byts', 'init_bwd_win_byts', 'active_max', 'active_min',
            'active_mean', 'active_std', 'idle_max', 'idle_min', 'idle_mean', 'idle_std',
            'fwd_byts_b_avg', 'fwd_pkts_b_avg', 'bwd_byts_b_avg', 'bwd_pkts_b_avg',
            'fwd_blk_rate_avg', 'bwd_blk_rate_avg', 'fwd_seg_size_avg', 'bwd_seg_size_avg',
            'cwr_flag_count', 'subflow_fwd_pkts', 'subflow_bwd_pkts', 'subflow_fwd_byts', 'subflow_bwd_byts'
        ]
        
        # Open the output file for writing
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=header, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
            writer.writeheader()
            
            # Generate a flow session class with a custom handler
            def flow_handler(flow_data):
                # Format the flow data to match command-line output
                formatted_data = format_flow_data(flow_data)
                
                # Ensure all fields are present in the output
                row = {}
                for field in header:
                    row[field] = formatted_data.get(field, 0)
                
                # Write the row
                writer.writerow(row)
                f.flush()
            
            # Generate the flow session class with our handler
            FlowSession = generate_session_class("flow", None, None)
            
            # Create an async sniffer to process the pcap file
            sniffer = AsyncSniffer(
                offline=pcap_file,
                filter="ip and (tcp or udp)",
                prn=None,
                session=FlowSession,
                store=False
            )
            
            # Start the sniffer
            logger.info("Starting packet processing...")
            sniffer.start()
            
            try:
                # Wait for the sniffer to finish
                sniffer.join()
            except KeyboardInterrupt:
                logger.warning("Process interrupted by user")
                sniffer.stop()
            except Exception as e:
                logger.error(f"Error during packet processing: {str(e)}")
                return False
            finally:
                sniffer.join()
        
        # Verify output file was created and has content
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            logger.info(f"Successfully processed {pcap_file}. Flow statistics saved to {output_file}")
            return True
        else:
            logger.error(f"Failed to generate output file or file is empty: {output_file}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing pcap file: {str(e)}")
        return False

if __name__ == "__main__":
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
    
    success = process_pcap(input_pcap, output_csv)
    
    if success:
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
            sys.exit(1)
    else:
        logger.error("Failed to process pcap file")
        sys.exit(1)


