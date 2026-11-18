// 01_shop_read.cypher — dữ liệu mẫu cửa hàng + các truy vấn đọc trong bài
// Chạy: docker compose exec -T neo4j cypher-shell -u neo4j -p learnneo4j -f /cypher/01_shop_read.cypher

MATCH (n) DETACH DELETE n;

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
       (mai)-[:BOUGHT {year: 2026}]->(viz);

RETURN "=== MATCH / WHERE / RETURN ===" AS section;
MATCH (p:Person {city: "Hanoi"}) RETURN p.name;
MATCH (p:Person)
WHERE p.city = "Hanoi" AND p.age >= 21
RETURN p.name, p.age
ORDER BY p.age DESC;
MATCH (:Person {name: "Linh"})-[b:BOUGHT]->(book:Book)
RETURN book.title, b.year;
MATCH (:Person {name: "Mai"})-[:FRIEND]-(f:Person)
RETURN f.name;

RETURN "=== OPTIONAL MATCH (Hung vẫn có mặt với 0 sách) ===" AS section;
MATCH (p:Person)
OPTIONAL MATCH (p)-[:BOUGHT]->(b:Book)
RETURN p.name, count(b) AS books;

RETURN "=== Aggregation + collect ===" AS section;
MATCH (p:Person)-[:BOUGHT]->(b:Book)
RETURN p.name AS person, count(b) AS books, sum(b.price) AS spent, collect(b.title) AS titles
ORDER BY spent DESC;

RETURN "=== WITH: mua nhiều hơn 1 sách trong 2026 ===" AS section;
MATCH (p:Person)-[r:BOUGHT]->(:Book)
WHERE r.year = 2026
WITH p, count(*) AS n
WHERE n > 1
RETURN p.name, n;

RETURN "=== Sách phổ biến nhất và người mua ===" AS section;
MATCH (b:Book)<-[:BOUGHT]-(p:Person)
WITH b, count(p) AS buyers
ORDER BY buyers DESC, b.title
LIMIT 1
MATCH (b)<-[:BOUGHT]-(p:Person)
RETURN b.title, collect(p.name) AS buyers;

RETURN "=== List / pattern comprehension ===" AS section;
MATCH (p:Person)
RETURN p.name,
       [(p)-[:BOUGHT]->(b) | b.title] AS books,
       [x IN range(1, 5) WHERE x % 2 = 1 | x * x] AS odd_squares;

RETURN "=== COUNT { } và NOT EXISTS { } ===" AS section;
MATCH (p:Person)
WHERE COUNT { (p)-[:FRIEND]-() } >= 2
RETURN p.name;
MATCH (b:Book)
WHERE NOT EXISTS { (b)<-[:BOUGHT]-(:Person {city: "Hanoi"}) }
RETURN b.title;

RETURN "=== Đường đi có độ dài thay đổi ===" AS section;
MATCH (:Person {name: "Linh"})-[:FRIEND*2]->(fof:Person)
RETURN fof.name;
MATCH path = (:Person {name: "Linh"})-[:FRIEND*1..3]->(other:Person)
RETURN other.name, length(path) AS hops, [n IN nodes(path) | n.name] AS route
ORDER BY hops;

RETURN "=== Shortest path ===" AS section;
MATCH (a:Person {name: "Linh"}), (b:Person {name: "Hung"}),
      p = shortestPath((a)-[:FRIEND*..10]-(b))
RETURN [n IN nodes(p) | n.name] AS route, length(p) AS hops;
MATCH p = SHORTEST 1 (:Person {name: "Linh"})-[:FRIEND]-+(:Person {name: "Hung"})
RETURN length(p);

RETURN "=== Gợi ý sách ===" AS section;
MATCH (me:Person {name: "Linh"})-[:FRIEND]-(friend)-[:BOUGHT]->(book:Book)
WHERE NOT (me)-[:BOUGHT]->(book)
RETURN book.title AS recommendation, count(*) AS friends_who_bought
ORDER BY friends_who_bought DESC;
MATCH (:Book {title: "Python Basics"})<-[:BOUGHT]-(p:Person)-[:BOUGHT]->(other:Book)
WHERE other.title <> "Python Basics"
RETURN other.title, count(DISTINCT p) AS also_bought
ORDER BY also_bought DESC, other.title;

RETURN "=== Thuật toán bằng Cypher thuần: degree, Jaccard ===" AS section;
MATCH (p:Person)
RETURN p.name, COUNT { (p)-[:FRIEND]-() } AS degree
ORDER BY degree DESC, p.name;
MATCH (a:Person {name: "Linh"})-[:BOUGHT]->(b:Book)
WITH a, collect(b) AS mine
MATCH (other:Person)-[:BOUGHT]->(b:Book) WHERE other <> a
WITH mine, other, collect(b) AS theirs
RETURN other.name,
       toFloat(size([x IN mine WHERE x IN theirs])) /
       size(mine + [x IN theirs WHERE NOT x IN mine]) AS jaccard
ORDER BY jaccard DESC;
