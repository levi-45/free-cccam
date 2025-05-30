import re
import requests
import threading
from queue import Queue

class FreeServerDownloader:
    def __init__(self):
        self.sources = [
            "https://raw.githubusercontent.com/levi-45/free-cccam/main/servers.txt"
        ]
        self.timeout = 15
        self.stop_flag = False

    def download_sync(self):
        self.stop_flag = False
        result_queue = Queue()
        threads = []

        for url in self.sources:
            if self.stop_flag:
                break
            thread = threading.Thread(target=self._fetch_servers, args=(url, result_queue))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join(timeout=30)

        servers = []
        while not result_queue.empty():
            servers.extend(result_queue.get())

        return servers  # Return all valid servers without filtering duplicates

    def _fetch_servers(self, url, queue):
        try:
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                servers = self._parse_servers(response.text)
                if servers:
                    queue.put(servers)
        except:
            pass

    def _parse_servers(self, text):
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        lines = [line.split('#')[0].strip() for line in text.split('\n') if line.strip()]
        
        servers = []
        for line in lines:
            server = self._parse_server_line(line)
            if server:
                servers.append(server)
        return servers

    def _parse_server_line(self, line):
        patterns = [
            r'^(?:C:|c:)?\s*([^\s]+)[:\s]+(\d{2,5})\s+([^\s]+)\s+([^\s]+)',
            r'^([^\s:]+):(\d{2,5})\s+([^\s]+)\s+([^\s]+)',
            r'^([^\s]+)\s+(\d{2,5})\s+([^\s]+)\s+([^\s]+)'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                host, port, user, pwd = match.groups()
                if self._is_valid_server(host, port):
                    return f"C: {host} {port} {user} {pwd}"
        return None

    def _is_valid_server(self, host, port):
        if not host or not port:
            return False
        if not port.isdigit() or not 1000 <= int(port) <= 65535:
            return False
        if any(x in host.lower() for x in ['example', 'test', 'dummy']):
            return False
        return True

    def stop_download(self):
        self.stop_flag = True