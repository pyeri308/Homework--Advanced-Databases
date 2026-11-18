// 02_shop_write.cypher — ghi dữ liệu, MERGE, LOAD CSV, constraint/index (chạy sau 01)
// Chạy: docker compose exec -T neo4j cypher-shell -u neo4j -p learnneo4j -f /cypher/02_shop_write.cypher

RETURN "=== CREATE / SET / REMOVE / DELETE ===" AS section;
CREATE (:Person {name: "Tuan", city: "Hanoi"});
MATCH (p:Person {name: "Hung"}) SET p.city = "Hanoi";
MATCH (p:Person {name: "Hung"}) SET p += {age: 24, job: "QA"};
MATCH (p:Person {name: "Hung"}) SET p:Student;
MATCH (p:Person {name: "Hung"}) RETURN p.name, p.city, p.age, p.job, labels(p);
MATCH (p:Person {name: "Hung"}) REMOVE p.job, p:Student;
MATCH (p:Person {name: "Hung"}) RETURN p.name, p.job, labels(p);
MATCH (p:Person {name: "Tuan"}) DETACH DELETE p;

RETURN "=== MERGE: chạy 2 lần vẫn chỉ 1 node ===" AS section;
MERGE (p:Person {name: "Linh"})
ON CREATE SET p.createdAt = datetime()
ON MATCH  SET p.lastSeen  = datetime();
MERGE (p:Person {name: "Linh"})
ON CREATE SET p.createdAt = datetime()
ON MATCH  SET p.lastSeen  = datetime();
MATCH (p:Person {name: "Linh"}) RETURN count(p) AS so_node_Linh, p.lastSeen IS NOT NULL AS co_lastSeen;

RETURN "=== MERGE an toàn: node trước, quan hệ sau ===" AS section;
MERGE (a:Person {name: "Linh"})
MERGE (b:Person {name: "Tuan"})
MERGE (a)-[:FRIEND]->(b);
MATCH (p:Person {name: "Linh"}) RETURN count(p) AS so_node_Linh;

RETURN "=== UNWIND ===" AS section;
UNWIND [
  {name: "Tuan", city: "Hanoi"},
  {name: "Vy",   city: "Can Tho"}
] AS row
MERGE (p:Person {name: row.name})
SET p.city = row.city;

RETURN "=== LOAD CSV (theo lô) ===" AS section;
LOAD CSV WITH HEADERS FROM "file:///people.csv" AS row
CALL (row) {
  MERGE (p:Person {name: row.name})
  SET p.city = row.city, p.age = toInteger(row.age)
} IN TRANSACTIONS OF 1000 ROWS;
MATCH (p:Person) WHERE p.name IN ["Tuan", "Vy"] RETURN p.name, p.city, p.age ORDER BY p.name;

RETURN "=== Constraint, index, full-text ===" AS section;
CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE;
CREATE INDEX person_city IF NOT EXISTS FOR (p:Person) ON (p.city);
CREATE FULLTEXT INDEX book_titles IF NOT EXISTS FOR (b:Book) ON EACH [b.title];
CALL db.awaitIndexes(60);
CALL db.index.fulltext.queryNodes("book_titles", "viz~") YIELD node, score
RETURN node.title, score;
SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties;
SHOW INDEXES YIELD name, type, labelsOrTypes, properties;
