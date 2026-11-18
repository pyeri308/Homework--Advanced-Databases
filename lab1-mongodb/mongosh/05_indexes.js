// 05_indexes.js — Index và explain()
db = db.getSiblingDB("shop");

// Tóm tắt kết quả explain cho dễ đọc (output gốc rất dài)
function planSummary(ex) {
  const plan = JSON.stringify(ex.queryPlanner.winningPlan);
  const s = ex.executionStats;
  return {
    stage: plan.includes("IXSCAN") ? "IXSCAN (dùng index)"
         : plan.includes("COLLSCAN") ? "COLLSCAN (quét toàn bộ)" : "khác",
    nReturned: s.nReturned,
    totalDocsExamined: s.totalDocsExamined,
    totalKeysExamined: s.totalKeysExamined,
    executionTimeMillis: s.executionTimeMillis,
  };
}

const filter = { "customer.city": "Hanoi", status: "paid" };

// Xoá index cũ (nếu có) để chạy lại script vẫn thấy được "trước" và "sau"
try { db.orders.dropIndex("customer.city_1_status_1"); } catch (e) {}

print("=== Trước khi tạo index ===");
printjson(planSummary(db.orders.find(filter).explain("executionStats")));

db.orders.createIndex({ "customer.city": 1, status: 1 });

print("\n=== Sau khi tạo index ===");
printjson(planSummary(db.orders.find(filter).explain("executionStats")));

print("\n=== Danh sách index ===");
printjson(db.orders.getIndexes());
