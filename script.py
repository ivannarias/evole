#!/usr/bin/python
""Simple chat based on Ethernet.

""It requires sudo or CAP_NET_RAW capabilities in the python interpreter.


import argparse
import socket
import threading
import re

ETH_P_ALL = 0x0003

# chat commands /whisper <nickname> <mesage>
whisper = r"^/whisper\s+(?P<nickname>\S+)\s+(?P<message>.+)"


# Font Formatting
bold = "\033[1m"
bold_red = "\033[1;31m"
bold_blue = "\033[1;34m"
bold_purple = "\033[1;35m"
reset_font = "\033[0m"
start_line = "\033[F\033[K"


class EthernetChat:
    """Simple chat based on Ethernet."""

    # EtherType of the frames used by this chat
    chat_frame_type = bytes([0x12, 0x34])
    # Broadcast ethernet address
    broadcast_mac = bytes([0xff] * 6)
    # Chat users dictionary
    chat_users = {}

    def __init__(self, interface_name: str, local_mac: bytes, nickname: str):
        """
        Initialize and start an ethernet chat.
        :param interface_name: name of the network interface to use for communications.
        :param local_mac: mac address of the local interface.
        :param nickname: nickname of the local chat user.
        """
        assert nickname, "A non-empty nickname must be provided"
        self.interface_name: str = interface_name
        self.local_mac: bytes = local_mac
        self.nickname: str = nickname

        # This is a raw layer 2 socket (normally layer 4 sockets are used)
        self.socket: socket.socket = socket.socket(
            family=socket.AF_PACKET,
            type=socket.SOCK_RAW,
            proto=socket.ntohs(ETH_P_ALL))

        # Listen for packets on the network interface
        self.background_thread = threading.Thread(
            target=self.sniff_packets_background,
            daemon=True)
        self.background_thread.start()
        self.socket.bind((self.interface_name, 0))

    def sniff_packets_background(self):
        """Listen for packets on the network interface and call
        self.receive_frame every time a packet is detected.
        This function runs forever, it is meant to be run in the background.
        """
        while True:
            self.receive_frame(self.socket.recv(1514))

    def receive_frame(self, frame: bytes):
        """Receive and decode an Ethernet frame containing a Chat message.
        Frames of other types are simply discarded.

        Upon reception of a valid frame containing a chat message, 
        this method calls self.receive_chat_message with the appropriate parameters.
        """
        # Decapsulate the layer 2 frame
        if len(frame) < 14:
            # Bogus ethernet frame
            return

        destination_mac = frame[0:6]
        source_mac = frame[6:12]
        frame_type = frame[12:14]
        frame_payload = frame[14:]

        if frame_type != self.chat_frame_type:
            # The frame type does not mach the chat's EtherType
            return
        if destination_mac not in (self.local_mac, self.broadcast_mac):
            # We are not the recipients of this frame 
            return
        if len(frame_payload) == 0:
            # Empty frame
            return
        if source_mac == self.local_mac:
            # We are seeing a message we sent ourselves
            return
																			
        # Decapsulate the payload  (refer to the packet format for details)
        nickname_length = frame[14] # TODO: Extract the length of the nickname
        if nickname_length == 0 or len(frame_payload) < nickname_length + 2:
            return
        nickname = frame[15+nickname_length] # TODO: Use the extracted nickname_length to slice the payload and get the nickname
        message = frame[15+nickname_length:]  # TODO: Extract the message
																			
        # BONUS: Do you see any problem here? TIP: How would you prevent impersonation?
        self.chat_users[nickname] = source_mac

        self.receive_chat_packet(
            source_mac=source_mac,
            destination_mac=destination_mac,
            nickname=nickname,
            message=message)

    def receive_chat_packet(self, source_mac: bytes, destination_mac: bytes, nickname: str, message: str):
        """Process the reception of a chat message."""
        if destination_mac == self.broadcast_mac:
            print(f"{bold}{nickname} says: {reset_font}{message}")
        else:
            print(f"{bold_purple}{nickname} whispers to you:{reset_font} {message}")

    def send_chat_packet(self, destination_mac: bytes, message: str):
        """Send a chat message."""
        assert len(message) <= 255
																			
        # Handle /whisper command
        match = re.match(whisper, message)
        if match:
            dest_nickname, message = match.group("nickname"), match.group("message")
            destination_mac = self.chat_users[dest_nickname]  # TODO: Get the MAC address corresponding to a user from the self.chat_user dictionary
            if destination_mac is None:
                print(f"{start_line}{bold_red}User {dest_nickname} does not exist{reset_font}")
                return
        else:
            destination_mac = broadcast_mac  # TODO: What MAC could you use to reach everybody?

        ethernet_header = destination_mac + self.local_mac + chat_frame_type  # TODO: Assemble the Ethernet Header
        ethernet_payload = len(self.nickname).to_bytes(1, 'big') + self.nickname + message # TODO: Assemble the Payload
        self.send_frame(ethernet_header + ethernet_payload)
																			
        if destination_mac == self.broadcast_mac:
            print(f"{start_line}{bold_blue}You ({sellsf.nickname}) say:{reset_font} {message}")
        else:
            print(f"{start_line}{bold_purple}You ({self.nickname}) whisper to {dest_nickname}: {reset_font}{message}")

    def send_frame(self, frame: bytes):
        """Send an Ethernet frame."""
        assert len(frame) >= 14 and frame[12:14] == self.chat_frame_type, \
            f"Invalid frame: length {len(frame)}, type {frame[12:14] if len(frame) >= 14 else '-'}."

        self.socket.send(frame)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("nickname", help="Nickname to use in the chat.")
    parser.add_argument("local_mac", help="MAC address to use (eg, aa:bb:cc:dd:ee:ff).")
    parser.add_argument("interface", help="Interface name (eg, wlan0).")
    args = parser.parse_args()

    # Validate the MAC address format
    local_mac = bytes(int(x, base=16) for x in args.local_mac.split(":"))
    if len(local_mac) != 6:
        raise ValueError("Invalid MAC address format")

    chat = EthernetChat(
        nickname=args.nickname,
        local_mac=local_mac,
        interface_name=args.interface)

    print(f"{bold}{f' [ Welcome to the chat, {chat.nickname} ] ':-^50s}{reset_font}")
    while True:
        message = input("").strip()
        if not message:
            continue
        chat.send_chat_packet(destination_mac=chat.broadcast_mac, message=message)

