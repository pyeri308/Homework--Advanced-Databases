// Bài tập 2 — Doanh thu theo thành phố (chạy trên collection orders của bài học)
db = db.getSiblingDB("shop");

const rows = db.orders.aggregate([
  { $unwind: "$items" },
  { $group: {
      _id: "$customer.city",
      orderIds: { $addToSet: "$_id" },
      revenue: { $sum: { $multiply: ["$items.qty", "$items.price"] } },
  } },
  { $project: { _id: 0, city: "$_id", orders: { $size: "$orderIds" }, revenue: 1 } },
  { $sort: { revenue: -1 } },
]);

print("=== Doanh thu theo thành phố ===");
printjson(rows.toArray());
