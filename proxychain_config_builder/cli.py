import click
import requests
import time
import logging
import socket
import socks
import concurrent.futures
from rich.console import Console
from rich.logging import RichHandler

# Setting up Rich for logging
logging.basicConfig(level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
logger = logging.getLogger("rich")

console = Console()

# Default proxychains template
DEFAULT_TEMPLATE = """
# proxychains.conf  VER 4.x
# HTTP, SOCKS4, SOCKS5 tunneling proxifier with DNS.

dynamic_chain
#quiet_mode
proxy_dns
tcp_read_time_out 15000
tcp_connect_time_out 8000

[ProxyList]
"""

def test_proxy(proxy_url, proxy_type, threshold=300):
    """
    Test a proxy for functionality and response speed.
    """
    test_url = 'http://worldtimeapi.org/api/timezone/Europe/London'
    if proxy_type in ['socks4', 'socks5']:
        _, host_port = proxy_url.split('://')
        host, port = host_port.split(':')
        port = int(port)
        socks.set_default_proxy(socks.SOCKS5 if proxy_type == 'socks5' else socks.SOCKS4, host, port)
        socket.socket = socks.socksocket
    else:
        proxies = {'http': proxy_url, 'https': proxy_url}

    try:
        start_time = time.time()
        if proxy_type in ['socks4', 'socks5']:
            response = requests.get(test_url, timeout=10, verify=False)
        else:
            response = requests.get(test_url, proxies=proxies, timeout=10, verify=False)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000

        if response.status_code == 200 and response_time < threshold:
            logger.info(f"Proxy {proxy_url} passed with response time {response_time}ms.")
            return proxy_url
    except Exception as e:
        logger.error(f"Error with proxy {proxy_url}: {e}")
    finally:
        # Resetting the socket to its default state if necessary
        # socket.socket = socket.SocketType  # Uncomment if needed
        pass

    return None

@click.command()
@click.argument('proxy_list_path', type=click.Path(exists=True))
@click.option('--template', 'template_path', type=click.Path(exists=True), default=None)
@click.option('--type', 'proxy_type', type=click.Choice(['http', 'socks4', 'socks5'], case_sensitive=False), default='http')
@click.option('--output', 'output_path', type=click.Path(), default=None)
def main(proxy_list_path, template_path, proxy_type, output_path):
    if template_path:
        with open(template_path, 'r') as file:
            template = file.read()
    else:
        template = DEFAULT_TEMPLATE

    # Load proxies and setup multithreading
    with open(proxy_list_path, 'r') as file:
        proxies = file.read().splitlines()

    logger.info("Starting proxy testing...")
    valid_proxies = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_proxy = {executor.submit(test_proxy, f"{proxy_type}://{proxy}", proxy_type): proxy for proxy in proxies}
        for future in concurrent.futures.as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            result = future.result()
            if result:
                valid_proxies.append(proxy)

    # Generate the proxychains configuration
    config_format = template
    for proxy in valid_proxies:
        host, port = proxy.split(':')
        config_line = f"{proxy_type} {host} {port}\n"
        config_format += config_line

    # Output the final configuration
    if output_path:
        with open(output_path, 'w') as file:
            file.write(config_format)
        logger.info(f"Proxychains configuration written to {output_path}")
    else:
        logger.info("Proxychains configuration:")
        print(config_format)

if __name__ == '__main__':
    main()
