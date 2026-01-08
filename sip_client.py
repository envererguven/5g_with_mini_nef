import socket
import sys
import time
import argparse
import threading

# Configuration
SMSC_IP = "172.18.4.30"
SMSC_PORT = 5060

def parse_args():
    parser = argparse.ArgumentParser(description="SIP Client for UERANSIM SMS Simulation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Register Command
    reg_parser = subparsers.add_parser("register", help="Register this UE with SMSC")
    reg_parser.add_argument("--sip-user", required=True, help="SIP URI User (e.g. msisdn)")
    reg_parser.add_argument("--local-ip", required=True, help="Local IP of this UE")
    reg_parser.add_argument("--local-port", type=int, default=5060, help="Local SIP Port")

    # Send Command
    send_parser = subparsers.add_parser("send", help="Send SMS (SIP MESSAGE)")
    send_parser.add_argument("--sip-user", required=True, help="Sender SIP URI User")
    send_parser.add_argument("--to", required=True, help="Recipient SIP URI User")
    send_parser.add_argument("--msg", required=True, help="Message Body")
    send_parser.add_argument("--local-port", type=int, default=5060, help="Local SIP Port")

    # Listen Command
    listen_parser = subparsers.add_parser("listen", help="Listen for incoming SIP messages")
    listen_parser.add_argument("--local-ip", required=True, help="Local IP to bind")
    listen_parser.add_argument("--local-port", type=int, default=5060, help="Local SIP Port")

    # Global arg for server IP (hacky insertion but works for verified structure)
    parser.add_argument("--server-ip", default="172.18.4.30", help="SMSC/SIP Server IP")

    return parser.parse_args()

def udp_send(data, ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data.encode('utf-8'), (ip, port))
    return sock

def cmd_register(args):
    # SIP REGISTER
    # Very basic packet construction
    call_id = f"reg-{time.time()}"
    sip_uri = f"sip:{args.sip_user}@free5gc.org"
    contact = f"<sip:{args.sip_user}@{args.local_ip}:{args.local_port}>"
    
    msg = (
        f"REGISTER sip:free5gc.org SIP/2.0\r\n"
        f"Via: SIP/2.0/UDP {args.local_ip}:{args.local_port};branch=z9hG4bK-reg\r\n"
        f"From: <{sip_uri}>;tag=1\r\n"
        f"To: <{sip_uri}>\r\n"
        f"Call-ID: {call_id}\r\n"
        f"CSeq: 1 REGISTER\r\n"
        f"Contact: {contact}\r\n"
        f"Content-Length: 0\r\n"
        f"\r\n"
    )
    print(f"Sending REGISTER for {args.sip_user}...")
    s = udp_send(msg, args.server_ip, SMSC_PORT)
    # Wait for response (short timeout)
    s.settimeout(2)
    try:
        data, _ = s.recvfrom(4096)
        print("Received Response:")
        print(data.decode('utf-8'))
    except socket.timeout:
        print("Timeout waiting for response.")

def cmd_send(args):
    # SIP MESSAGE
    call_id = f"msg-{time.time()}"
    sender_uri = f"sip:{args.sip_user}@free5gc.org"
    target_uri = f"sip:{args.to}@free5gc.org" # Sending to Proxy/SMSC, addressing User
    
    # We send packet TO the SMSC IP, but Request-URI is the target user
    
    body = args.msg
    msg = (
        f"MESSAGE {target_uri} SIP/2.0\r\n"
        f"Via: SIP/2.0/UDP {args.local_ip}:{args.local_port};branch=z9hG4bK-msg\r\n" # simplified IP
        f"From: <{sender_uri}>;tag=1\r\n"
        f"To: <{target_uri}>\r\n"
        f"Call-ID: {call_id}\r\n"
        f"CSeq: 1 MESSAGE\r\n"
        f"Content-Type: text/plain\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"\r\n"
        f"{body}"
    )
    print(f"Sending MESSAGE to {args.to}...")
    udp_send(msg, args.server_ip, SMSC_PORT)

def cmd_listen(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.local_ip, args.local_port))
    print(f"Listening on {args.local_ip}:{args.local_port}...")
    
    while True:
        data, addr = sock.recvfrom(4096)
        text = data.decode('utf-8')
        print(f"\n[Received from {addr}]:")
        print(text)
        
        # Simple auto-reply 200 OK for messages to stop retransmissions (simulated)
        if "MESSAGE" in text.splitlines()[0]:
             # Extract Call-ID etc to reply? Simplified: Just print for now.
             pass

if __name__ == "__main__":
    args = parse_args()
    if args.command == "register":
        cmd_register(args)
    elif args.command == "send":
        cmd_send(args)
    elif args.command == "listen":
        cmd_listen(args)
