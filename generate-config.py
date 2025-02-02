from piawg import piawg
from pick import pick
from getpass import getpass
from datetime import datetime
from os import path
import argparse
import pathlib

parser = argparse.ArgumentParser()
parser.add_argument(
    '-p', '--print',
    action='store_true',
    help='Print the generated config to stdout'
)
parser.add_argument(
    '-o', '--output-dir',
    type=pathlib.Path,
    default='/output',
    required=False,
    help='Directory to write the generated config. Only valid if `--print` is not True'
)
parser.add_argument(
    '-m', '--mask',
    action='store_true',
    help='Should the output config include the Interface mask in the output'
)
parser.add_argument(
    '--debug',
    action='store_true',
    help='Use dummy values and print argument information'
)
args = parser.parse_args()

DEBUG = args.debug is True
if DEBUG:
    print('Arguments: ', args)

print_to_std_out = args.print is True
include_address_mask = args.mask
output_path: str = args.output_dir

if print_to_std_out is False and not path.exists(output_path):
    print("Error: Path does not exist: '%s', did you map the volume?" % output_path)
    exit(1)

global pia
if DEBUG:
    pia = piawg(fetch_servers=False)
    pia.connection = {
        "peer_ip": '0.0.0.0',
        "dns_servers": ['dns1', 'dns2'],
        "server_key": 'server_key',
        "server_ip": '127.0.0.1',
    }
    pia.privatekey = 'private_key'
    pia.region = 'CA Montreal'
elif not DEBUG:
    pia = piawg()
    # Generate public and private key pair
    pia.generate_keys()

    # Select region
    title = 'Please choose a region: '
    options = sorted(list(pia.server_list.keys()))
    option, index = pick(options, title)
    pia.set_region(option)
    print("Selected '{}'".format(option))

    # Get token
    while True:
        username = input("\nEnter PIA username: ")
        password = getpass()
        if pia.get_token(username, password):
            print("Login successful!")
            break
        else:
            print("Error logging in, please try again...")

    # Add key
    status, response = pia.addkey()
    if status:
        print("Added key to server!")
    else:
        print("Error adding key to server")
        print(response)

# Build config
timestamp = int(datetime.now().timestamp())
location = pia.region.replace(' ', '-')
buffer = []
buffer.append('[Interface]\n')
buffer.append('Address = {}{}\n'.format(
    pia.connection['peer_ip'], '/32' if include_address_mask is True else ''))
buffer.append('PrivateKey = {}\n'.format(pia.privatekey))
buffer.append('DNS = {},{}\n'.format(
    pia.connection['dns_servers'][0], pia.connection['dns_servers'][1])
)
buffer.append('\n')
buffer.append('[Peer]\n')
buffer.append('PublicKey = {}\n'.format(pia.connection['server_key']))
buffer.append('Endpoint = {}:1337\n'.format(pia.connection['server_ip']))
buffer.append('AllowedIPs = 0.0.0.0/0\n')
buffer.append('PersistentKeepalive = 25\n')

if print_to_std_out is True:
    print(*map(lambda line: line.strip(), buffer), sep='\n')
else:
    config_file = '{}{}PIA-{}-{}.conf'.format(
        output_path, path.sep, location, timestamp)
    with open(config_file, 'w') as file:
        print("Saving configuration file {}".format(config_file))
        file.writelines(buffer)
