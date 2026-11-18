"""Bước 8 + bài tập 5: đọc query plan bằng PROFILE (trước/sau khi có constraint).

    python plan.py
Chạy sau `python campus.py check` (cần dữ liệu CampusGraph).
"""
from campus import driver, setup

TASK3 = """
MATCH (s:Student {id: $sid}), (c:Course)
WHERE NOT (s)-[:PASSED]->(c)
  AND NOT EXISTS { (c)-[:REQUIRES]->(pre:Course) WHERE NOT (s)-[:PASSED]->(pre) }
RETURN c.code AS code ORDER BY code"""


def _get(node, *keys, default=0):
    for k in keys:
        if k in node:
            return node[k]
    return node.get("args", {}).get(keys[0][0].upper() + keys[0][1:], default)


def profile(query, **params):
    """Chạy PROFILE, trả về (cây plan dạng text, các operator lá, tổng db hits, số dòng)."""
    records, summary, _ = driver.execute_query("PROFILE " + query, params)
    lines, leaves, total = [], [], 0

    def walk(node, depth):
        nonlocal total
        op = _get(node, "operatorType", "operator_type", default="?").split("@")[0]
        hits = _get(node, "dbHits", "db_hits")
        rows = _get(node, "rows")
        total += hits
        lines.append(f"{'  ' * depth}{op:<34} rows={rows:<5} dbHits={hits}")
        children = node.get("children", [])
        if not children:
            leaves.append(op)
        for child in children:
            walk(child, depth + 1)

    walk(summary.profile, 0)
    return "\n".join(lines), leaves, total, len(records)


def show(title, query, **params):
    tree, leaves, total, n = profile(query, **params)
    print(f"\n--- {title} ---")
    print(tree)
    print(f"=> operator đầu tiên (lá): {', '.join(leaves)} | tổng db hits: {total} | {n} dòng kết quả")
    return leaves, total


print("=" * 70)
print("BƯỚC 8: PROFILE truy vấn Task 3 cho S01")
print("=" * 70)
setup()
show("Có constraint student_id", TASK3, sid="S01")
driver.execute_query("DROP CONSTRAINT student_id IF EXISTS")
show("Đã DROP constraint student_id", TASK3, sid="S01")
driver.execute_query("CREATE CONSTRAINT student_id IF NOT EXISTS FOR (s:Student) REQUIRE s.id IS UNIQUE")
driver.execute_query("CALL db.awaitIndexes(60)")
show("Tạo lại constraint", TASK3, sid="S01")

print("\n" + "=" * 70)
print("Mô phỏng 100.000 sinh viên: thêm sinh viên giả rồi PROFILE lại")
print("=" * 70)
# Ghi theo lô 10.000 dòng (execute_query chạy trong transaction có quản lý,
# nên không dùng CALL ... IN TRANSACTIONS được; chia lô ngay trong Python)
for start in range(1, 100_001, 10_000):
    driver.execute_query("""
        UNWIND range($a, $b) AS i
        CREATE (:Student {id: 'X' + toString(i), name: 'Fake ' + toString(i), year: 1})""",
        a=start, b=start + 9_999)
show("100.000+ sinh viên, có constraint", TASK3, sid="S01")
driver.execute_query("DROP CONSTRAINT student_id IF EXISTS")
show("100.000+ sinh viên, KHÔNG constraint", TASK3, sid="S01")
driver.execute_query("CREATE CONSTRAINT student_id IF NOT EXISTS FOR (s:Student) REQUIRE s.id IS UNIQUE")
driver.execute_query("CALL db.awaitIndexes(60)")
while driver.execute_query("""
        MATCH (s:Student) WHERE s.id STARTS WITH 'X'
        WITH s LIMIT 10000 DETACH DELETE s
        RETURN count(*) AS n""").records[0]["n"] > 0:
    pass

print("\n" + "=" * 70)
print("BÀI TẬP 5: PROFILE MATCH (p:Person {name: 'Linh'}) RETURN p")
print("=" * 70)
driver.execute_query("DROP CONSTRAINT person_name IF EXISTS")
driver.execute_query("""
    UNWIND range(1, 1000) AS i CREATE (:Person {name: 'person' + toString(i)})""")
driver.execute_query("MERGE (:Person {name: 'Linh', city: 'Hanoi'})")
q = "MATCH (p:Person {name: $name}) RETURN p"
show("Trước khi có constraint (1001 Person)", q, name="Linh")
driver.execute_query("CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE")
driver.execute_query("CALL db.awaitIndexes(60)")
show("Sau khi có constraint", q, name="Linh")
driver.execute_query("MATCH (p:Person) DETACH DELETE p")
driver.close()
