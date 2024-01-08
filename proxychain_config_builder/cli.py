import click


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

@click.command()
@click.argument('proxy_list_path', type=click.Path(exists=True))
@click.option('--template', 'template_path', type=click.Path(exists=True), default=None)
@click.option('--type', 'proxy_type', type=click.Choice(['http', 'socks4', 'socks5'], case_sensitive=False), default='http')
@click.option('--output', 'output_path', type=click.Path(), default=None)
def main(proxy_list_path, template_path, proxy_type, output_path):
    # Load the base template
    if template_path:
        with open(template_path, 'r') as file:
            template = file.read()
    else:
        template = DEFAULT_TEMPLATE

    # Load proxies from the provided file
    with open(proxy_list_path, 'r') as file:
        proxy_list = file.read()

    # Convert the proxy list into proxychains configuration format
    config_format = template
    for line in proxy_list.strip().split('\n'):
        ip_port = line.strip().split(':')
        if len(ip_port) == 2:
            ip, port = ip_port
            config_line = f"{proxy_type} {ip} {port}"
            config_format += config_line + '\n'

    # Output the final configuration
    if output_path:
        with open(output_path, 'w') as file:
            file.write(config_format)
        print(f"Proxychains configuration written to {output_path}")
    else:
        print(config_format)


if __name__ == '__main__':
    main()
