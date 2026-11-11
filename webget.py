import socket
import sys
from pathlib import Path

# 我的GitHub 仓库：https://github.com/JRJerry0621/webget.py

# 读取命令行参数
# 参数格式：python webget.py host path [port]
# host：服务器地址；path：请求资源路径；port：服务器端口，默认为 80
if len(sys.argv) not in (3, 4):
    print("用法: python webget.py host path [port]")
    sys.exit(1)

host = sys.argv[1]
path = sys.argv[2]

try:
    port = int(sys.argv[3]) if len(sys.argv) == 4 else 80
except ValueError:
    print("错误：端口必须是整数")
    sys.exit(1)

# 创建 TCP Socket，并与 Web 服务器建立连接
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(10)

try:
    s.connect((host, port))

    # 构造 HTTP GET 请求
    # Host 指定服务器主机名
    # Connection: close 表示服务器发送完响应后关闭连接
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )

    # 发送完整的 HTTP 请求
    s.sendall(request.encode())

    # 循环接收完整的 HTTP 响应
    # TCP 是面向字节流的协议，一次 recv() 不一定能收到完整响应，
    # 因此需要循环接收，并将每次收到的数据拼接起来。
    response = b""
    recv_count = 0
    recv_sizes = []
    content_length = None
    header_checked = False

    while True:
        # 每次最多接收 4096 字节
        data = s.recv(4096)

        # 结束条件一：recv() 返回空字节串 b""，
        # 表示服务器已经关闭连接，没有更多数据可接收。
        if not data:
            break

        # 记录每次接收的数据量
        recv_count += 1
        recv_sizes.append(len(data))
        response += data

        # HTTP 响应头和正文之间使用 \r\n\r\n 分隔
        # 收到完整响应头后，提取 Content-Length 字段
        if not header_checked and b"\r\n\r\n" in response:
            headers = response.split(b"\r\n\r\n", 1)[0]

            for line in headers.split(b"\r\n")[1:]:
                if line.lower().startswith(b"content-length:"):
                    content_length = int(
                        line.split(b":", 1)[1].strip()
                    )
                    break

            header_checked = True

        # 结束条件二：如果响应头中包含 Content-Length，
        # 当已接收的正文长度达到指定值时，说明正文接收完成。
        if header_checked and content_length is not None:
            body = response.split(b"\r\n\r\n", 1)[1]

            if len(body) >= content_length:
                break

finally:
    # 无论连接是否正常完成，都关闭 Socket
    s.close()

# 检查 HTTP 响应头是否完整
if not header_checked:
    raise ValueError("HTTP 响应头不完整")

# 输出接收统计信息
print("recv_calls:", recv_count)
print("recv_sizes:", recv_sizes)
print("total_bytes:", len(response))

# 解析 HTTP 响应
# 根据分隔符将响应拆分为响应头和正文
header_data, body = response.split(b"\r\n\r\n", 1)

# 如果服务器提供 Content-Length，检查正文长度
# 防止连接提前关闭导致保存不完整的正文
if content_length is not None:
    if len(body) < content_length:
        raise ValueError("HTTP 响应正文接收不完整")

    # 去除可能多接收的字节，只保留指定长度的正文
    body = body[:content_length]

# 解析 HTTP 状态行和响应头
header_lines = header_data.decode("iso-8859-1").split("\r\n")
status_line = header_lines[0]
status_parts = status_line.split()

if len(status_parts) < 2:
    raise ValueError("HTTP 状态行格式错误")

status_code = status_parts[1]

print("\nHTTP Status:", status_code)
print("Status Line:", status_line)

print("\nHTTP Headers:")
for line in header_lines[1:]:
    print(line)

# 将响应正文以二进制形式保存
# 使用 wb 模式，避免图片等二进制文件的数据被编码破坏
output_file = Path.home() / "webget_body.bin"

with open(output_file, "wb") as f:
    f.write(body)

print("\nBody saved:", output_file)
print("Body size:", len(body))
