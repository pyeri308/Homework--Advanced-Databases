// 03_exercises.cypher — bài tập 1–4 (bài 5 PROFILE nằm trong python/plan.py)
// Chạy: docker compose exec -T neo4j cypher-shell -u neo4j -p learnneo4j -f /cypher/03_exercises.cypher
// Tự dựng lại dữ liệu cửa hàng nên chạy độc lập được.

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

RETURN "=== Bài 1: thêm 5 người + quan hệ bạn bè, rồi tìm bạn của bạn của Linh ở Hanoi ===" AS section;
UNWIND [
  {name: "Tuan",  city: "Hanoi",   age: 22, friend: "Nam"},
  {name: "Vy",    city: "Can Tho", age: 21, friend: "Linh"},
  {name: "Quang", city: "Hanoi",   age: 23, friend: "Vy"},
  {name: "Thao",  city: "Hanoi",   age: 20, friend: "Linh"},
  {name: "Duc",   city: "Hue",     age: 24, friend: "Thao"}
] AS row
MERGE (p:Person {name: row.name}) SET p.city = row.city, p.age = row.age
WITH p, row
MATCH (f:Person {name: row.friend})
MERGE (f)-[:FRIEND {since: 2026}]->(p);
// Bạn của bạn (đúng 2 bước, không tính hướng), loại chính Linh và bạn trực tiếp của Linh
MATCH (linh:Person {name: "Linh"})-[:FRIEND*2]-(fof:Person)
WHERE fof <> linh AND NOT (linh)-[:FRIEND]-(fof) AND fof.city = "Hanoi"
RETURN DISTINCT fof.name AS friend_of_friend_in_hanoi
ORDER BY friend_of_friend_in_hanoi;

RETURN "=== Bài 2a: gợi ý sách cho Mai ===" AS section;
MATCH (me:Person {name: "Mai"})-[:FRIEND]-(friend)-[:BOUGHT]->(book:Book)
WHERE NOT (me)-[:BOUGHT]->(book)
RETURN book.title AS recommendation, count(*) AS friends_who_bought, collect(friend.name) AS via
ORDER BY friends_who_bought DESC, recommendation;

RETURN "=== Bài 2b: tổng tiền mỗi người đã chi (cả người chưa mua) ===" AS section;
MATCH (p:Person)
OPTIONAL MATCH (p)-[:BOUGHT]->(b:Book)
RETURN p.name AS person, coalesce(sum(b.price), 0) AS total_spent
ORDER BY total_spent DESC, person;

RETURN "=== Bài 3: mạng metro, tuyến ít ga nhất và tuyến ít phút nhất ===" AS section;
// Một đoạn tuyến Cát Linh – Hà Đông và một tuyến giả định cắt ngang
UNWIND [
  ["Cat Linh", "La Thanh", 2], ["La Thanh", "Thai Ha", 2], ["Thai Ha", "Lang", 3],
  ["Lang", "Thuong Dinh", 3], ["Thuong Dinh", "Vanh Dai 3", 2], ["Vanh Dai 3", "Phung Khoang", 3],
  ["Cat Linh", "Kim Ma", 4], ["Kim Ma", "Cau Giay", 5], ["Cau Giay", "Lang", 6],
  ["Thai Ha", "Nga Tu So", 4], ["Nga Tu So", "Phung Khoang", 9]
] AS seg
MERGE (a:Station {name: seg[0]})
MERGE (b:Station {name: seg[1]})
MERGE (a)-[:NEXT {minutes: seg[2]}]->(b);
// Ít ga nhất (đếm số chặng, đi được cả hai chiều)
MATCH (a:Station {name: "Kim Ma"}), (b:Station {name: "Phung Khoang"}),
      p = shortestPath((a)-[:NEXT*..20]-(b))
RETURN [s IN nodes(p) | s.name] AS fewest_stops, length(p) AS stops,
       reduce(t = 0, r IN relationships(p) | t + r.minutes) AS minutes;
// Ít phút nhất: liệt kê các tuyến có giới hạn độ dài rồi cộng phút (Dijkstra thật nằm trong GDS)
MATCH p = (:Station {name: "Kim Ma"})-[:NEXT*..10]-(:Station {name: "Phung Khoang"})
WITH p, reduce(t = 0, r IN relationships(p) | t + r.minutes) AS minutes
RETURN [s IN nodes(p) | s.name] AS route, length(p) AS stops, minutes
ORDER BY minutes, stops LIMIT 3;

RETURN "=== Bài 4: lịch sử làm việc theo 2 cách mô hình ===" AS section;
// Cách A: thuộc tính trên quan hệ
MERGE (p:Person {name: "Linh"})
MERGE (c1:Company {name: "FPT"})
MERGE (c2:Company {name: "Viettel"})
MERGE (p)-[:WORKED_AT {role: "Intern", start: date("2024-06-01"), end: date("2024-09-01")}]->(c1)
MERGE (p)-[:WORKED_AT {role: "Data Analyst", start: date("2025-01-01")}]->(c2);
// Cách B: node trung gian :Employment
MERGE (p:Person {name: "Nam"})
MERGE (c:Company {name: "FPT"})
MERGE (r:Role {title: "Data Engineer"})
MERGE (p)-[:HAD]->(e:Employment {start: date("2025-03-01")})-[:AT]->(c)
MERGE (e)-[:AS]->(r);
// A dễ: "Linh từng làm ở đâu, vai trò gì?" (một bước)
MATCH (:Person {name: "Linh"})-[w:WORKED_AT]->(c:Company)
RETURN c.name, w.role, w.start, w.end ORDER BY w.start;
// B dễ: "Ai từng làm Data Engineer ở bất kỳ công ty nào?" (role là node, đi qua được)
MATCH (p:Person)-[:HAD]->(:Employment)-[:AS]->(:Role {title: "Data Engineer"})
RETURN p.name;
// Ai từng làm ở FPT: mỗi mô hình cần một truy vấn riêng
MATCH (p:Person)-[w:WORKED_AT]->(:Company {name: "FPT"})
RETURN p.name AS person, w.role AS role, "A: quan hệ" AS model;
MATCH (p:Person)-[:HAD]->(e:Employment)-[:AT]->(:Company {name: "FPT"})
OPTIONAL MATCH (e)-[:AS]->(r:Role)
RETURN p.name AS person, r.title AS role, "B: node Employment" AS model;
