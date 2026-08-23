import socket
import time

class RedisClone:
    def __init__(self):
        self.store = {}
        self.expires = {}

    def handle_command(self, cmd_bytes):
        parts = cmd_bytes.decode('utf-8').strip().split()
        if not parts:
            return b"-ERR empty command\r\n"
        
        cmd = parts[0].upper()
        if cmd == "SET":
            if len(parts) < 3: return b"-ERR wrong number of arguments\r\n"
            key, val = parts[1], parts[2]
            self.store[key] = val
            if len(parts) >= 5 and parts[3].upper() == "EX":
                ttl = int(parts[4])
                self.expires[key] = time.time() + ttl
            else:
                self.expires.pop(key, None)
            return b"+OK\r\n"
            
        elif cmd == "GET":
            if len(parts) < 2: return b"-ERR wrong number of arguments\r\n"
            key = parts[1]
            if key in self.expires and time.time() > self.expires[key]:
                self.store.pop(key, None)
                self.expires.pop(key, None)
                return b"$-1\r\n"
            if key not in self.store:
                return b"$-1\r\n"
            val = self.store[key]
            return f"${len(val)}\r\n{val}\r\n".encode()
            
        elif cmd == "DEL":
            if len(parts) < 2: return b"-ERR wrong number of arguments\r\n"
            count = 0
            for key in parts[1:]:
                if key in self.store:
                    self.store.pop(key, None)
                    self.expires.pop(key, None)
                    count += 1
            return f":{count}\r\n".encode()
            
        elif cmd == "TTL":
            if len(parts) < 2: return b"-ERR wrong number of arguments\r\n"
            key = parts[1]
            if key not in self.store: return b":-2\r\n"
            if key not in self.expires: return b":-1\r\n"
            remaining = int(self.expires[key] - time.time())
            if remaining < 0:
                self.store.pop(key, None)
                self.expires.pop(key, None)
                return b":-2\r\n"
            return f":{remaining}\r\n".encode()
            
        return b"-ERR unknown command\r\n"

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 6379))
    server.listen(5)
    print("Redis Clone listening on 127.0.0.1:6379...")
    
    db = RedisClone()
    try:
        while True:
            client, addr = server.accept()
            data = client.recv(1024)
            if data:
                response = db.handle_command(data)
                client.sendall(response)
            client.close()
    except KeyboardInterrupt:
        print("Stopping server.")

if __name__ == "__main__":
    main()
