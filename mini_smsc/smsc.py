import socket
import threading
import time
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Configuration
SIP_IP = "0.0.0.0"
SIP_PORT = 5060
API_PORT = 9091

# Storage (In-memory for prototype)
# Map: sip_uri -> (ip, port)
registered_users = {}
# Map: sip_uri -> [messages]
message_store = {}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SIP_IP, SIP_PORT))

def parse_sip(data):
    """Simple SIP parser for REGISTER and MESSAGE"""
    lines = data.split('\r\n')
    request_line = lines[0].split(' ')
    method = request_line[0]
    uri = request_line[1]
    headers = {}
    body = ""
    
    is_body = False
    for line in lines[1:]:
        if line == "":
            is_body = True
            continue
        if is_body:
            body += line + "\n"
        else:
            if ": " in line:
                k, v = line.split(": ", 1)
                headers[k] = v
    
    return method, uri, headers, body.strip()

def handle_sip():
    print(f"[*] SIP Listener started on {SIP_IP}:{SIP_PORT}")
    while True:
        data, addr = sock.recvfrom(4096)
        try:
            msg = data.decode('utf-8')
            method, uri, headers, body = parse_sip(msg)
            
            sender = headers.get('From', '').split(';')[0].replace('<', '').replace('>', '')
            recipient = headers.get('To', '').split(';')[0].replace('<', '').replace('>', '')
            call_id = headers.get('Call-ID', '12345')
            cseq = headers.get('CSeq', '1 REGISTER')
            
            print(f"[SIP] Received {method} from {sender} ({addr})")

            if method == 'REGISTER':
                # Map user to the source IP/Port of the UDP packet
                registered_users[sender] = addr
                print(f"[+] Registered {sender} at {addr}")
                
                # Send 200 OK
                response = f"SIP/2.0 200 OK\r\nVia: {headers.get('Via')}\r\nFrom: {headers.get('From')}\r\nTo: {headers.get('To')}\r\nCall-ID: {call_id}\r\nCSeq: {cseq}\r\nContent-Length: 0\r\n\r\n"
                sock.sendto(response.encode('utf-8'), addr)

            elif method == 'MESSAGE':
                # P2P SMS
                print(f"[>] Message: '{body}' from {sender} to {recipient}")
                
                # Store message
                if recipient not in message_store:
                    message_store[recipient] = []
                message_store[recipient].append({"from": sender, "body": body, "time": time.ctime()})
                
                # Send 200 OK to Sender
                response = f"SIP/2.0 200 OK\r\nVia: {headers.get('Via')}\r\nFrom: {headers.get('From')}\r\nTo: {headers.get('To')}\r\nCall-ID: {call_id}\r\nCSeq: {cseq}\r\nContent-Length: 0\r\n\r\n"
                sock.sendto(response.encode('utf-8'), addr)
                
                # Forward to Recipient if online
                if recipient in registered_users:
                    target_addr = registered_users[recipient]
                    print(f"[>>] Forwarding to {target_addr}")
                    
                    # Construct Forward Message
                    # Note: Simplified forwarding. Real proxying involves Via headers etc.
                    # We act as a B2BUA (Back-to-Back User Agent) effectively re-originating.
                    fwd_msg = f"MESSAGE {recipient} SIP/2.0\r\nVia: SIP/2.0/UDP {SIP_IP}:{SIP_PORT};branch=z9hG4bK-fwd\r\nFrom: {sender}\r\nTo: {recipient}\r\nCall-ID: fwd-{call_id}\r\nCSeq: 1 MESSAGE\r\nContent-Type: text/plain\r\nContent-Length: {len(body)}\r\n\r\n{body}"
                    sock.sendto(fwd_msg.encode('utf-8'), target_addr)
                else:
                    print(f"[!] Recipient {recipient} not registered. Stored offline.")

        except Exception as e:
            print(f"[!] SIP Error: {e}")

# Start SIP thread
threading.Thread(target=handle_sip, daemon=True).start()

@app.route('/sms/send', methods=['POST'])
def send_marketing_sms():
    data = request.json
    recipient = data.get('to') # sip:msisdn@domain
    body = data.get('body')
    sender_name = data.get('from', 'sip:marketing@smsc')

    if not recipient or not body:
         return jsonify({"error": "Missing 'to' or 'body'"}), 400

    print(f"[API] Sending A2P to {recipient}: {body}")
    
    # Check registration
    if recipient in registered_users:
        target_addr = registered_users[recipient]
        msg = f"MESSAGE {recipient} SIP/2.0\r\nVia: SIP/2.0/UDP {SIP_IP}:{SIP_PORT};branch=z9hG4bK-a2p\r\nFrom: {sender_name}\r\nTo: {recipient}\r\nCall-ID: a2p-{time.time()}\r\nCSeq: 1 MESSAGE\r\nContent-Type: text/plain\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        sock.sendto(msg.encode('utf-8'), target_addr)
        return jsonify({"status": "Sent", "target": str(target_addr)})
    else:
        return jsonify({"status": "Failed", "error": "Recipient offline"}), 404

@app.route('/sms/messages', methods=['GET'])
def get_messages():
    return jsonify(message_store)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=API_PORT)
