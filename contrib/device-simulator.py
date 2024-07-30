import random
import socket
import time


def send_packet():
    # Define the packet data
    version = 1
    reporter_id = 123
    state_of_charge = random.randrange(10, 100)
    charging = random.choice([0, 1])
    temperature = random.randrange(15, 50)

    # Construct the packet
    packet = bytearray()
    packet.append(version)
    packet.extend(reporter_id.to_bytes(2, 'big'))
    packet.append(state_of_charge)
    packet.append(charging)
    packet.append(temperature if temperature >= 0 else (256 + temperature))

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Send the packet to localhost on port 1234
    sock.sendto(packet, ('localhost', 1234))

    # Close the socket
    sock.close()


if __name__ == '__main__':
    while True:
        send_packet()
        time.sleep(1)
