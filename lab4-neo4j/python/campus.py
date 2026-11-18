"""CampusGraph: a course-prerequisite and friendship graph in Neo4j.

Usage:
    python campus.py setup     # (re)load the dataset, wipes the database first
    python campus.py check     # run every task and compare with the expected output
    python campus.py extra     # phần "Going further": credits_to_reach, phát hiện chu trình, gợi ý bạn có điểm
"""
import os
import sys

from neo4j import GraphDatabase

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "learnneo4j"))
driver = GraphDatabase.driver(URI, auth=AUTH)

# Giới hạn độ dài đường đi biến thiên (bài học khuyên luôn đặt cận trên).
# 20 bước là quá đủ cho một chương trình học; đường đi không lặp quan hệ nên không chạy vô hạn.
# Cypher không cho truyền độ dài đường đi bằng tham số, nên hằng số này được ghép vào chuỗi
# truy vấn. Đây là hằng số trong code, không phải dữ liệu người dùng, nên không có rủi ro injection.
MAX_DEPTH = 20

# ---------------------------------------------------------------- dataset
COURSES = [  # (code, title, credits)
    ("CS101", "Intro to Programming", 3), ("MATH101", "Calculus", 3),
    ("MATH102", "Linear Algebra", 3), ("STAT101", "Probability and Statistics", 3),
    ("CS102", "Data Structures", 3), ("DB201", "Databases", 3),
    ("VIZ201", "Data Visualization", 2), ("ML201", "Machine Learning", 4),
    ("DE301", "Data Engineering", 3), ("DB301", "NoSQL Databases", 3),
    ("DL301", "Deep Learning", 4), ("NLP401", "Natural Language Processing", 3),
    ("CAP401", "Capstone Project", 6),
]
REQUIRES = [  # (course, prerequisite)
    ("MATH102", "MATH101"), ("STAT101", "MATH101"), ("CS102", "CS101"),
    ("DB201", "CS102"), ("VIZ201", "CS101"), ("VIZ201", "STAT101"),
    ("ML201", "CS102"), ("ML201", "MATH102"), ("ML201", "STAT101"),
    ("DE301", "DB201"), ("DE301", "CS102"), ("DB301", "DB201"),
    ("DL301", "ML201"), ("NLP401", "DL301"), ("CAP401", "DB301"), ("CAP401", "ML201"),
]
STUDENTS = [  # (id, name, year)
    ("S01", "An", 3), ("S02", "Binh", 2), ("S03", "Chi", 3), ("S04", "Dung", 1),
    ("S05", "Giang", 2), ("S06", "Hoa", 3), ("S07", "Khoa", 2), ("S08", "Lan", 1),
    ("S09", "Minh", 3), ("S10", "Phuong", 2),
]
PASSED = {  # student -> {course: grade}
    "S01": {"CS101": 8.5, "MATH101": 7.0, "CS102": 8.0, "MATH102": 6.5, "STAT101": 7.5, "DB201": 9.0},
    "S02": {"CS101": 7.0, "MATH101": 8.0, "STAT101": 8.5, "VIZ201": 9.0},
    "S03": {"CS101": 9.0, "MATH101": 9.5, "MATH102": 9.0, "STAT101": 8.0, "CS102": 8.5, "ML201": 9.0, "DB201": 7.5},
    "S04": {"CS101": 6.5, "MATH101": 7.5},
    "S05": {"CS101": 8.0, "CS102": 7.5, "DB201": 8.0, "MATH101": 6.0},
    "S06": {"CS101": 9.5, "MATH101": 8.5, "MATH102": 8.0, "STAT101": 9.0, "CS102": 9.0, "DB201": 8.5, "DB301": 9.0, "ML201": 8.0},
    "S07": {"CS101": 7.5, "MATH101": 7.0, "STAT101": 6.5, "CS102": 7.0},
    "S08": {"CS101": 8.0},
    "S09": {"CS101": 8.0, "MATH101": 8.0, "MATH102": 7.5, "STAT101": 7.0, "CS102": 8.0, "DB201": 8.0, "ML201": 7.5, "DL301": 8.5, "VIZ201": 8.0},
    "S10": {"CS101": 9.0, "MATH101": 9.0, "STAT101": 8.0, "VIZ201": 8.5, "CS102": 7.5},
}
FRIENDS = [  # stored once; the friendship means both ways
    ("S01", "S02"), ("S01", "S05"), ("S02", "S04"), ("S04", "S08"), ("S05", "S07"),
    ("S07", "S10"), ("S03", "S06"), ("S03", "S09"), ("S06", "S09"), ("S09", "S10"),
    ("S08", "S10"),
]


def setup():
    """Wipe the database, create constraints and load the dataset in batches."""
    q = lambda cypher, **params: driver.execute_query(cypher, params)
    q("MATCH (n) DETACH DELETE n")
    q("CREATE CONSTRAINT student_id IF NOT EXISTS FOR (s:Student) REQUIRE s.id IS UNIQUE")
    q("CREATE CONSTRAINT course_code IF NOT EXISTS FOR (c:Course) REQUIRE c.code IS UNIQUE")
    q("""UNWIND $rows AS r
         MERGE (c:Course {code: r[0]}) SET c.title = r[1], c.credits = r[2]""",
      rows=[list(c) for c in COURSES])
    q("""UNWIND $rows AS r
         MATCH (c:Course {code: r[0]}), (p:Course {code: r[1]})
         MERGE (c)-[:REQUIRES]->(p)""", rows=[list(r) for r in REQUIRES])
    q("""UNWIND $rows AS r
         MERGE (s:Student {id: r[0]}) SET s.name = r[1], s.year = r[2]""",
      rows=[list(s) for s in STUDENTS])
    q("""UNWIND $rows AS r
         MATCH (s:Student {id: r.sid}), (c:Course {code: r.code})
         MERGE (s)-[p:PASSED]->(c) SET p.grade = r.grade""",
      rows=[{"sid": s, "code": c, "grade": g} for s, d in PASSED.items() for c, g in d.items()])
    q("""UNWIND $rows AS r
         MATCH (a:Student {id: r[0]}), (b:Student {id: r[1]})
         MERGE (a)-[:FRIEND]->(b)""", rows=[list(f) for f in FRIENDS])
    counts = driver.execute_query(
        "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY label").records
    print("loaded:", {r["label"]: r["n"] for r in counts})


# ---------------------------------------------------------------- tasks
# Mọi giá trị đều truyền bằng tham số ($sid, $code, ...), không dùng f-string.

def passed_courses(student_id):
    """Task 1. [(code, grade), ...] the student passed, best grade first, then by code."""
    records = driver.execute_query("""
        MATCH (:Student {id: $sid})-[p:PASSED]->(c:Course)
        RETURN c.code AS code, p.grade AS grade
        ORDER BY grade DESC, code""", sid=student_id).records
    return [(r["code"], r["grade"]) for r in records]


def prerequisite_chain(code):
    """Task 2. Every direct and indirect prerequisite of a course, as [(code, depth), ...].
    depth = the fewest REQUIRES hops from the course. Sort by depth, then code."""
    records = driver.execute_query(f"""
        MATCH path = (:Course {{code: $code}})-[:REQUIRES*1..{MAX_DEPTH}]->(pre:Course)
        RETURN pre.code AS code, min(length(path)) AS depth
        ORDER BY depth, code""", code=code).records
    return [(r["code"], r["depth"]) for r in records]


def eligible_courses(student_id):
    """Task 3. Codes of courses the student has NOT passed and whose direct
    prerequisites are ALL passed (a course without prerequisites counts). Sorted."""
    records = driver.execute_query("""
        MATCH (s:Student {id: $sid}), (c:Course)
        WHERE NOT (s)-[:PASSED]->(c)
          AND NOT EXISTS {
                (c)-[:REQUIRES]->(pre:Course)
                WHERE NOT (s)-[:PASSED]->(pre)
          }
        RETURN c.code AS code
        ORDER BY code""", sid=student_id).records
    return [r["code"] for r in records]


def suggest_friends(student_id, k=3):
    """Task 4. Students who are not yet friends (either direction), ranked by the number
    of courses both passed. [(name, shared), ...], shared desc then name, top k."""
    records = driver.execute_query("""
        MATCH (me:Student {id: $sid})-[:PASSED]->(c:Course)<-[:PASSED]-(other:Student)
        WHERE other <> me AND NOT (me)-[:FRIEND]-(other)
        RETURN other.name AS name, count(DISTINCT c) AS shared
        ORDER BY shared DESC, name
        LIMIT $k""", sid=student_id, k=k).records
    return [(r["name"], r["shared"]) for r in records]


def connection(a_id, b_id):
    """Task 5. Names along the shortest FRIEND path between two students (ignore direction)."""
    if a_id == b_id:   # shortestPath không cho điểm đầu trùng điểm cuối
        records = driver.execute_query(
            "MATCH (s:Student {id: $sid}) RETURN s.name AS name", sid=a_id).records
        return [r["name"] for r in records]
    records = driver.execute_query(f"""
        MATCH (a:Student {{id: $a}}), (b:Student {{id: $b}})
        MATCH p = shortestPath((a)-[:FRIEND*..{MAX_DEPTH}]-(b))
        RETURN [n IN nodes(p) | n.name] AS route""", a=a_id, b=b_id).records
    return records[0]["route"] if records else []


def bottleneck_courses(k=3):
    """Task 6. Courses that the most other courses depend on, directly or indirectly.
    [(code, dependents), ...], dependents desc then code, top k."""
    records = driver.execute_query(f"""
        MATCH (dep:Course)-[:REQUIRES*1..{MAX_DEPTH}]->(c:Course)
        RETURN c.code AS code, count(DISTINCT dep) AS dependents
        ORDER BY dependents DESC, code
        LIMIT $k""", k=k).records
    return [(r["code"], r["dependents"]) for r in records]


def _record_pass_tx(tx, student_id, code, grade):
    # Task 7: mọi truy vấn chạy trên tx nên cùng nằm trong MỘT transaction.
    # 1) Sinh viên và môn học phải tồn tại
    found = tx.run("""
        OPTIONAL MATCH (s:Student {id: $sid})
        OPTIONAL MATCH (c:Course {code: $code})
        RETURN s IS NOT NULL AS student_ok, c IS NOT NULL AS course_ok""",
        sid=student_id, code=code).single()
    if not (found["student_ok"] and found["course_ok"]):
        raise ValueError(f"unknown student or course: {student_id}, {code}")

    # 2) Các môn tiên quyết trực tiếp mà sinh viên chưa qua (đã sắp xếp)
    missing = tx.run("""
        MATCH (s:Student {id: $sid}), (:Course {code: $code})-[:REQUIRES]->(pre:Course)
        WHERE NOT (s)-[:PASSED]->(pre)
        RETURN pre.code AS code
        ORDER BY code""", sid=student_id, code=code).value()
    if missing:
        raise ValueError(f"missing prerequisites: {missing}")

    # 3) MERGE: ghi lần hai chỉ cập nhật điểm, không tạo quan hệ thứ hai
    tx.run("""
        MATCH (s:Student {id: $sid}), (c:Course {code: $code})
        MERGE (s)-[p:PASSED]->(c)
        SET p.grade = $grade""", sid=student_id, code=code, grade=grade)


def record_pass(student_id, code, grade):
    """Task 7. Record that a student passed a course, inside ONE write transaction.
    Raise ValueError (and write nothing) if the student or course does not exist or a
    direct prerequisite is missing. Recording the same pass twice must not duplicate it."""
    with driver.session() as session:
        session.execute_write(_record_pass_tx, student_id, code, grade)


# ---------------------------------------------------------------- going further

def credits_to_reach(student_id, code):
    """Tổng tín chỉ của mọi môn tiên quyết (trực tiếp và gián tiếp) mà sinh viên còn thiếu."""
    return driver.execute_query(f"""
        MATCH (s:Student {{id: $sid}}), (:Course {{code: $code}})-[:REQUIRES*1..{MAX_DEPTH}]->(pre:Course)
        WHERE NOT (s)-[:PASSED]->(pre)
        WITH DISTINCT pre
        RETURN coalesce(sum(pre.credits), 0) AS credits""",
        sid=student_id, code=code).records[0]["credits"]


def find_cycles():
    """Các môn tự yêu cầu chính nó (qua một hoặc nhiều bước)."""
    records = driver.execute_query(f"""
        MATCH p = (c:Course)-[:REQUIRES*1..{MAX_DEPTH}]->(c)
        RETURN c.code AS code, [n IN nodes(p) | n.code] AS cycle
        ORDER BY code""").records
    return [(r["code"], r["cycle"]) for r in records]


def suggest_friends_scored(student_id, k=3):
    """Gợi ý bạn với điểm = số môn chung + 2 * số bạn chung."""
    records = driver.execute_query("""
        MATCH (me:Student {id: $sid}), (other:Student)
        WHERE other <> me AND NOT (me)-[:FRIEND]-(other)
        WITH other,
             COUNT { (me)-[:PASSED]->(:Course)<-[:PASSED]-(other) } AS shared,
             COUNT { (me)-[:FRIEND]-(:Student)-[:FRIEND]-(other) } AS mutual
        RETURN other.name AS name, shared, mutual, shared + 2 * mutual AS score
        ORDER BY score DESC, name
        LIMIT $k""", sid=student_id, k=k).records
    return [(r["name"], r["shared"], r["mutual"], r["score"]) for r in records]


def extra():
    setup()
    print("\n--- credits_to_reach ---")
    for sid, code in [("S04", "ML201"), ("S08", "CAP401"), ("S06", "CAP401"), ("S01", "NLP401")]:
        print(f"credits_to_reach({sid!r}, {code!r}) = {credits_to_reach(sid, code)}")

    print("\n--- phát hiện chu trình ---")
    print("trước khi thêm quan hệ sai:", find_cycles())
    driver.execute_query("""MATCH (a:Course {code: "MATH101"}), (b:Course {code: "ML201"})
                            MERGE (a)-[:REQUIRES]->(b)""")
    for code, cycle in find_cycles():
        print(f"  {code}: {' -> '.join(cycle)}")
    driver.execute_query("""MATCH (:Course {code: "MATH101"})-[r:REQUIRES]->(:Course {code: "ML201"})
                            DELETE r""")
    print("sau khi xoá quan hệ sai:", find_cycles())

    print("\n--- suggest_friends có điểm (shared + 2 * mutual) ---")
    for sid in ["S02", "S08"]:
        print(f"{sid}: suggest_friends        = {suggest_friends(sid)}")
        print(f"{sid}: suggest_friends_scored = {suggest_friends_scored(sid)}  (name, shared, mutual, score)")


# ---------------------------------------------------------------- self-check

def check():
    setup()

    def expect_error(fn):
        try:
            fn()
        except ValueError as e:
            return str(e)
        return None

    def after_record():
        record_pass("S08", "CS102", 7.0)
        record_pass("S08", "CS102", 7.5)          # same pass again: update, not duplicate
        n = driver.execute_query("""
            MATCH (:Student {id: 'S08'})-[p:PASSED]->(:Course {code: 'CS102'})
            RETURN count(p) AS n, max(p.grade) AS g""").records[0]
        return (n["n"], n["g"], eligible_courses("S08"))

    tests = [
        ("1 passed_courses", lambda: passed_courses("S04"), [("MATH101", 7.5), ("CS101", 6.5)]),
        ("2 prerequisite_chain", lambda: prerequisite_chain("DE301"),
         [("CS102", 1), ("DB201", 1), ("CS101", 2)]),
        ("3 eligible_courses", lambda: eligible_courses("S01"), ["DB301", "DE301", "ML201", "VIZ201"]),
        ("4 suggest_friends", lambda: suggest_friends("S02"),
         [("Minh", 4), ("Phuong", 4), ("Chi", 3)]),
        ("5 connection", lambda: connection("S01", "S08"), ["An", "Binh", "Dung", "Lan"]),
        ("6 bottleneck_courses", lambda: bottleneck_courses(),
         [("CS101", 9), ("CS102", 7), ("MATH101", 7)]),
        ("7a record_pass refuses", lambda: expect_error(lambda: record_pass("S04", "ML201", 8.0)),
         "missing prerequisites: ['CS102', 'MATH102', 'STAT101']"),
        ("7b record_pass writes", after_record, (1, 7.5, ["DB201", "MATH101"])),
    ]
    for name, fn, expected in tests:
        try:
            got = fn()
        except NotImplementedError:
            print(f"TODO  {name}")
            continue
        except Exception as e:
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            continue
        status = "PASS " if got == expected else "FAIL "
        print(f"{status} {name}")
        if got != expected:
            print(f"        expected {expected}\n        got      {got}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    try:
        {"setup": setup, "check": check, "extra": extra}[cmd]()
    finally:
        driver.close()
