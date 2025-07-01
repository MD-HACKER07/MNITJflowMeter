from scapy.all import *
import random

def create_test_pcap(filename, num_packets=10):
    packets = []
    
    for i in range(num_packets):
        # Create Ethernet frame with random MACs
        eth = Ether(src=f"00:11:22:33:44:{random.randint(10, 99):02d}",
                   dst=f"aa:bb:cc:dd:ee:{random.randint(10, 99):02d}")
        
        # Create IP packet with random source and destination
        ip = IP(src=f"192.168.1.{random.randint(1, 10)}",
                dst=f"10.0.0.{random.randint(1, 10)}")
        
        # Randomly choose between TCP and UDP
        if random.choice([True, False]):
            transport = TCP(sport=random.randint(1024, 65535),
                           dport=random.choice([80, 443, 22, 53]))
        else:
            transport = UDP(sport=random.randint(1024, 65535),
                           dport=random.choice([53, 67, 68, 123]))
        
        # Create the packet
        packet = eth / ip / transport / ("Test packet %d" % i).encode()
        packets.append(packet)
    
    # Write packets to pcap file
    wrpcap(filename, packets)
    print(f"Created {filename} with {len(packets)} packets")

if __name__ == "__main__":
    create_test_pcap("test_traffic.pcap", num_packets=100)
