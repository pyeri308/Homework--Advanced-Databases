"""Neo4j từ Python (phần lý thuyết): execute_query, DataFrame, UNWIND theo lô, transaction.

    python shop.py
Tự dựng lại dữ liệu cửa hàng mẫu nên chạy độc lập được.
"""
import os

import neo4j
from neo4j import GraphDatabase

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "learnneo4j"))

driver = GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()

driver.execute_query("MATCH (n) WHERE n:Person OR n:Book DETACH DELETE n")
driver.execute_query("""
CREATE (linh:Person {name: "Linh", city: "Hanoi", age: 21}),
       (nam:Person  {name: "Nam",  city: "Da Nang", age: 22}),
       (mai:Person  {name: "Mai",  city: "Hanoi", age: 20}),
       (hung:Person {name: "Hung", city: "Hue", age: 23}),
       (py:Book  {title: "Python Basics", price: 120000}),
       (sql:Book {title: "SQL in Practice", price: 150000}),
       (viz:Book {title: "Data Viz", price: 135000}),
       (linh)-[:FRIEND {since: 2023}]->(nam),
       (nam)-[:FRIEND {since: 2024}]->(mai),
       (mai)-[:FRIEND {since: 2025}]->(hung),
       (linh)-[:BOUGHT {year: 2026}]->(py),
       (linh)-[:BOUGHT {year: 2026}]->(sql),
       (nam)-[:BOUGHT {year: 2025}]->(sql),
       (nam)-[:BOUGHT {year: 2026}]->(viz),
       (mai)-[:BOUGHT {year: 2026}]->(py),
       (mai)-[:BOUGHT {year: 2026}]->(viz)""")

print("=== execute_query: gợi ý sách cho Linh ===")
QUERY = """
MATCH (me:Person {name: $name})-[:FRIEND]-(friend)-[:BOUGHT]->(book:Book)
WHERE NOT (me)-[:BOUGHT]->(book)
RETURN book.title AS title, count(*) AS score
ORDER BY score DESC
"""
records, summary, keys = driver.execute_query(QUERY, name="Linh")
for record in records:
    print(record["title"], record["score"])
print(f"{summary.result_available_after} ms")

print("\n=== Kết quả dạng pandas DataFrame: tuổi trung bình theo thành phố ===")
df = driver.execute_query(
    "MATCH (p:Person) RETURN p.name AS name, p.city AS city, p.age AS age",
    result_transformer_=neo4j.Result.to_df,
)
print(df.groupby("city")["age"].mean())

print("\n=== Ghi theo lô với UNWIND: 10.000 người trong 1 truy vấn ===")
people = [{"name": f"user{i}", "city": "Hanoi"} for i in range(10_000)]
_, summary, _ = driver.execute_query("""
    UNWIND $rows AS row
    MERGE (p:Person {name: row.name})
    SET p.city = row.city
""", rows=people)
print("nodes created:", summary.counters.nodes_created,
      "| thời gian:", summary.result_available_after + summary.result_consumed_after, "ms")
driver.execute_query("MATCH (p:Person) WHERE p.name STARTS WITH 'user' DETACH DELETE p")


print("\n=== Nhiều truy vấn trong một transaction ===")
def transfer_friend(tx, person, old_friend, new_friend):
    tx.run("""MATCH (:Person {name: $p})-[f:FRIEND]-(:Person {name: $o}) DELETE f""",
           p=person, o=old_friend)
    tx.run("""MATCH (a:Person {name: $p}), (b:Person {name: $n})
              MERGE (a)-[:FRIEND]->(b)""", p=person, n=new_friend)


def friends_of(name):
    return driver.execute_query("""MATCH (:Person {name: $n})-[:FRIEND]-(f) RETURN f.name AS f ORDER BY f""",
                                n=name).records


print("Bạn của Linh trước:", [r["f"] for r in friends_of("Linh")])
with driver.session(database="neo4j") as session:
    session.execute_write(transfer_friend, "Linh", "Nam", "Mai")
print("Bạn của Linh sau  :", [r["f"] for r in friends_of("Linh")])

driver.close()
