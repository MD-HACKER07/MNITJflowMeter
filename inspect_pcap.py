from scapy.all import *
import sys

def inspect_pcap(pcap_file):
    print(f"Inspecting {pcap_file}...")
    
    # Read the pcap file
    packets = rdpcap(pcap_file)
    
    print(f"Total packets: {len(packets)}")
    
    # Print details of the first few packets
    for i, pkt in enumerate(packets[:5]):
        print(f"\n--- Packet {i+1} ---")
        print(f"Layers: {pkt.layers()}")
        print(f"Summary: {pkt.summary()}")
        
        # Print available fields for each layer
        for layer in pkt.layers():
            print(f"\nLayer: {layer.__name__}")
            print(f"Fields: {layer.fields_desc}")
            
            # Print field values
            if hasattr(pkt, layer.__name__):
                layer_obj = getattr(pkt, layer.__name__)
                for field in layer.fields_desc:
                    if hasattr(layer_obj, field.name):
                        print(f"  {field.name}: {getattr(layer_obj, field.name)}")
        
        # Print raw packet data
        print("\nRaw packet data:")
        hexdump(pkt)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input_pcap>")
        sys.exit(1)
    
    input_pcap = sys.argv[1]
    inspect_pcap(input_pcap)
