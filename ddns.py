import subprocess
import os
import time

import CloudFlare

SECOND = 1
MINUTE = 60 * SECOND

def get_external_IP():
    p = subprocess.Popen(["dig", "@resolver1.opendns.com", "ANY", "myip.opendns.com", "+short"],
                         stdout=subprocess.PIPE)
    return p.stdout.read().strip().decode("ascii")

def get_zone(cf:CloudFlare.CloudFlare, zone_name:str):
    zone_name = zone_name.lower()
    all_zones = cf.zones()
    for zone in all_zones:
        if zone["name"].lower() == zone_name:
            return zone
    raise ValueError("could not find zone with name '"+zone_name+"'")

def get_dns_record(cf:CloudFlare.CloudFlare, zone:dict, domain_name:str):
    domain_name = domain_name.lower()
    dns_records = cf.zones.dns_records(zone["id"])
    for dns in dns_records:
        if dns["name"].lower() == domain_name:
            return dns
    raise ValueError("could not find domain with name '"+zone_name+"'")


def update_DNS_IP(cf:CloudFlare.CloudFlare, dns:dict, IP:str, proxied=None):
    data = {
        "type": dns["type"],
        "name": dns["name"],
        "ttl": dns["ttl"],
        "content": IP,
        }
    if proxied is not None:
        data["proxied"] = bool(proxied)

    return cf.zones.dns_records.put(dns["zone_id"], dns["id"], data=data)
    
if __name__ == "__main__":
    # extract config from environment variables
    ZONE = os.environ["DDNS_ZONE"]
    SUBDOMAIN = os.environ["DDNS_SUBDOMAIN"]
    TOKEN = os.environ["CLOUDFLARE_TOKEN"]

    # connect APi
    cf = CloudFlare.CloudFlare(token=TOKEN)
    
    # get the zone
    zone = get_zone(cf, ZONE)

    # check the DNS record every 5 minutes to see
    # if it matches the current external IP
    while True:
        dns = get_dns_record(cf, zone, SUBDOMAIN)
        external_IP = get_external_IP()
        print("External IP:", external_IP, end="; ")
        print("DNS Record:", dns["content"])
        if dns["content"] != external_IP:
            print("Updating DNS record")
            update_DNS_IP(cf, dns, external_IP)
        print("Sleeping...")
        time.sleep(5 * MINUTE)
