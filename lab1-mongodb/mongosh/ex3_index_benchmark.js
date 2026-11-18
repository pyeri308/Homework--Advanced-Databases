// Bài tập 3 — Sinh 10.000 document, so sánh explain() trước và sau khi tạo index
db = db.getSiblingDB("shop");
const big = db.orders_big;
big.drop();

const cities = ["Hanoi", "Da Nang", "Hue", "HCMC", "Hai Phong", "Can Tho"];
const statuses = ["paid", "shipped", "cancelled"];
const books = [
  { sku: "BK-01", title: "Python Basics", price: 12.5 },
  { sku: "BK-03", title: "Data Viz", price: 22.0 },
  { sku: "BK-07", title: "SQL in Practice", price: 18.0 },
  { sku: "BK-09", title: "NoSQL Intro", price: 15.0 },
];
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

const docs = [];
for (let i = 1; i <= 10000; i++) {
  const nItems = 1 + Math.floor(Math.random() * 3);
  const items = [];
  for (let k = 0; k < nItems; k++) {
    const b = pick(books);
    items.push({ ...b, qty: 1 + Math.floor(Math.random() * 3) });
  }
  docs.push({ _id: i, customer: { name: "KH" + i, city: pick(cities) },
              status: pick(statuses), items });
}
big.insertMany(docs);
print("Đã tạo", big.countDocuments(), "document trong orders_big");

function planSummary(ex) {
  const plan = JSON.stringify(ex.queryPlanner.winningPlan);
  const s = ex.executionStats;
  return {
    stage: plan.includes("IXSCAN") ? "IXSCAN" : plan.includes("COLLSCAN") ? "COLLSCAN" : "khác",
    nReturned: s.nReturned,
    totalDocsExamined: s.totalDocsExamined,
    totalKeysExamined: s.totalKeysExamined,
    executionTimeMillis: s.executionTimeMillis,
  };
}

const filter = { "customer.city": "Hanoi", status: "paid" };

print("\n=== Trước khi có index ===");
printjson(planSummary(big.find(filter).explain("executionStats")));

big.createIndex({ "customer.city": 1, status: 1 });

print("\n=== Sau khi có index ===");
printjson(planSummary(big.find(filter).explain("executionStats")));
