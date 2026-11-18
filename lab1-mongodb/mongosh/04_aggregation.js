// 04_aggregation.js — Aggregation pipeline (GROUP BY của MongoDB)
db = db.getSiblingDB("shop");

const top = db.orders.aggregate([
  { $match: { status: { $in: ["paid", "shipped"] } } },          // WHERE
  { $unwind: "$items" },                                         // mỗi item thành 1 document
  { $group: {                                                    // GROUP BY sku
      _id: "$items.sku",
      units: { $sum: "$items.qty" },
      revenue: { $sum: { $multiply: ["$items.qty", "$items.price"] } },
  } },
  { $sort: { revenue: -1 } },                                    // ORDER BY
  { $limit: 5 },
]);

print("=== Top sản phẩm theo doanh thu ===");
printjson(top.toArray());
