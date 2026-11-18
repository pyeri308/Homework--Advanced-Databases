"""Bước 1 tự động: kiểm tra quy tắc "node kế tiếp theo chiều kim đồng hồ".

Với từng sensor: lấy token (Murmur3), tìm token đầu tiên trên vòng >= token đó
(nếu lớn hơn mọi token thì quay vòng về token nhỏ nhất), so với nodetool getendpoints.
Chạy từ thư mục lab3-cassandra, sau khi đã tạo keyspace ring1 (RF=1).
"""
import os
import subprocess
import sys

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(*args):
    return subprocess.run(args, cwd=LAB, capture_output=True, text=True, check=True).stdout


def node_names():
    ids = sh("docker", "compose", "ps", "-q").split()
    out = sh("docker", "inspect", "-f",
             "{{.Name}} {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", *ids)
    names = {}
    for line in out.splitlines():
        name, ip = line.split()
        names[ip] = name.strip("/").split("-")[-2] if name.count("-") >= 2 else name.strip("/")
    return names


def ring():
    """[(token, ip)] sắp tăng dần từ nodetool ring."""
    pairs = []
    for line in sh("docker", "compose", "exec", "-T", "cass1", "nodetool", "ring").splitlines():
        parts = line.split()
        if parts and parts[0].count(".") == 3 and parts[-1].lstrip("-").isdigit():
            pairs.append((int(parts[-1]), parts[0]))
    return sorted(pairs)


def tokens(sensors):
    out = sh("docker", "compose", "exec", "-T", "cass1", "cqlsh", "-e",
             "SELECT DISTINCT sensor_id, token(sensor_id) FROM iot.readings_by_sensor;")
    result = {}
    for line in out.splitlines():
        if "|" in line:
            key, tok = [x.strip() for x in line.split("|")]
            if key in sensors:
                result[key] = int(tok)
    return result


def owner_by_rule(tok, ring_pairs):
    for t, ip in ring_pairs:
        if t >= tok:
            return ip, t
    return ring_pairs[0][1], ring_pairs[0][0]          # quay vòng


def main():
    sensors = sys.argv[1:] or [f"hn-{i:02d}" for i in range(1, 7)]
    names = node_names()
    rp = ring()
    toks = tokens(set(sensors))
    print(f"Vòng token có {len(rp)} token ({len(rp) // max(1, len(set(ip for _, ip in rp)))} vnode mỗi node)")
    print("Bảng IP -> container:", {ip: names.get(ip, "?") for ip in sorted(set(ip for _, ip in rp))})
    print()
    print(f"{'sensor':<7} {'token':>21}  {'token kế tiếp trên vòng':>23}  {'theo quy tắc':<20} {'getendpoints':<20} khớp?")
    all_ok = True
    for s in sensors:
        tok = toks[s]
        ip_rule, t_next = owner_by_rule(tok, rp)
        ip_real = sh("docker", "compose", "exec", "-T", "cass1", "nodetool",
                     "getendpoints", "ring1", "sensors", s).strip()
        ok = ip_rule == ip_real
        all_ok &= ok
        print(f"{s:<7} {tok:>21}  {t_next:>23}  {ip_rule + ' (' + names.get(ip_rule, '?') + ')':<20} "
              f"{ip_real + ' (' + names.get(ip_real, '?') + ')':<20} {'OK' if ok else 'KHÁC'}")
    print("\nKẾT LUẬN:", "quy tắc đúng với mọi sensor" if all_ok else "có sensor không khớp!")


if __name__ == "__main__":
    main()
