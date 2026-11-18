// 02_queries.js — Read: truy vấn với find(filter, projection)
db = db.getSiblingDB("shop");

function show(title, cursor) {
  print("\n=== " + title + " ===");
  printjson(cursor.toArray());
}

show("WHERE status = 'paid'", db.orders.find({ status: "paid" }));
show("Dot notation: customer.city = Hanoi", db.orders.find({ "customer.city": "Hanoi" }));
show("Tìm trong mảng: items.sku = BK-01", db.orders.find({ "items.sku": "BK-01" }));
show("paid và có field coupon", db.orders.find({ status: "paid", coupon: { $exists: true } }));
show("Có item giá > 20", db.orders.find({ "items.price": { $gt: 20 } }));
show(
  "paid/shipped, chỉ lấy _id + status, sắp xếp _id giảm dần, lấy 2",
  db.orders
    .find({ status: { $in: ["paid", "shipped"] } }, { _id: 1, status: 1 })
    .sort({ _id: -1 })
    .limit(2)
);
