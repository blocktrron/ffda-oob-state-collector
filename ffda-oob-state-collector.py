import argparse
import time

from prometheus_client import Gauge
from prometheus_client.twisted import MetricsResource
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol


class StateCollectorMetrics:
    def __init__(self):
        metric_labels = ['ip', 'host']
        self.soc = Gauge('soc', 'State of charge', metric_labels)
        self.charging = Gauge('charging', 'Charging status', metric_labels)
        self.temperature = Gauge('temperature', 'Temperature in celsius', metric_labels)
        self.last_contact = Gauge('last_contact', 'Last contact', metric_labels)


class StateReporterListener(DatagramProtocol):
    def __init__(self, state_collector_metrics: StateCollectorMetrics):
        self.metrics = state_collector_metrics

    def datagramReceived(self, data, address):
        # byte0: version
        # byte1-2: reporter-id
        # byte3: state-of-charge (unsigned)
        # byte4: (bit0: charging)
        # byte5: temp (celsius rounded signed int8)

        if len(data) < 1:
            print('Invalid data length')
            return

        # Extract data from bytes
        protocol_version = int.from_bytes(data[0:1], 'big', signed=False)

        if protocol_version == 1:
            host_id = int.from_bytes(data[1:3], 'big', signed=False)
            soc_value = int.from_bytes(data[3:4], 'big', signed=False)
            charging_value = data[1] & 1
            temperature_value = int.from_bytes(data[5:6], 'big', signed=True)
            last_contact_value = time.time()

            # Print the values
            print(
                f'SOC: {soc_value}, Charging: {charging_value}, Temperature: {temperature_value}, Last Contact: {last_contact_value}')

            # Set the values to Prometheus
            self.metrics.soc.labels(address[0], host_id).set(soc_value)
            self.metrics.charging.labels(address[0], host_id).set(charging_value)
            self.metrics.temperature.labels(address[0], host_id).set(temperature_value)
            self.metrics.last_contact.labels(address[0], host_id).set(last_contact_value)
        else:
            print('Unsupported protocol version')
            return


class StateCollector:
    def __init__(self, tcp_port: int = 9091, udp_port: int = 1234, tcp_listen_address: str = None,
                 udp_listen_address: str = None):
        self.last_contact = None
        self.temperature = None
        self.charging = None
        self.soc = None
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.tcp_listen_address = tcp_listen_address
        self.udp_listen_address = udp_listen_address

        self.metrics = StateCollectorMetrics()
        self.state_reporter_listener = StateReporterListener(self.metrics)

    def start_network(self):
        root = Resource()
        root.putChild(b'metrics', MetricsResource())

        # TCP HTTP metrics endpoint
        factory = Site(root)
        reactor.listenTCP(self.tcp_port, factory, interface=self.tcp_listen_address)

        # UDP state listener
        reactor.listenUDP(self.udp_port, self.state_reporter_listener, interface=self.udp_listen_address)
        reactor.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='ffda-oob-state-collector',
        description='Out-of-band state collector'
    )
    parser.add_argument('--tcp-listen-address', type=str, help='TCP listen address', default="")
    parser.add_argument('--udp-listen-address', type=str, help='UDP listen address', default="")
    parser.add_argument('--tcp-listen-port', type=int, help='TCP port', default=9091)
    parser.add_argument('--udp-listen-port', type=int, help='UDP port', default=1234)
    args = parser.parse_args()

    state_collector = StateCollector(
        udp_listen_address=args.udp_listen_address,
        tcp_listen_address=args.tcp_listen_address
    )
    state_collector.start_network()
