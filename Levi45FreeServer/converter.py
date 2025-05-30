class FreeServerToOscamConverter:
    def convert(self, server_lines):
        config = "# OSCam Server Configuration\n\n"
        
        for i, line in enumerate(server_lines, 1):
            parts = line.split()
            if len(parts) >= 4:
                host, port, user, password = parts[1], parts[2], parts[3], parts[4] if len(parts) > 4 else ""
                config += f"""[reader]
label = Server_{i}
protocol = cccam
device = {host},{port}
user = {user}
password = {password}
group = 1
cccversion = 2.1.2
ccckeepalive = 1

"""
        return config