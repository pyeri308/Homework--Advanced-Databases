// 01_insert.js — Create: thêm dữ liệu
// Script xoá collection trước nên chạy lại bao nhiêu lần cũng được (dùng để "reset" dữ liệu).
db = db.getSiblingDB("shop");
db.orders.drop();

db.orders.insertOne({
  _id: 1001,
  customer: { name: "Linh", city: "Hanoi" },
  status: "paid",
  items: [
    { sku: "BK-01", title: "Python Basics", qty: 2, price: 12.5 },
    { sku: "BK-07", title: "SQL in Practice", qty: 1, price: 18.0 },
  ],
});

db.orders.insertMany([
  { _id: 1002, customer: { name: "Nam", city: "Da Nang" }, status: "shipped",
    items: [{ sku: "BK-03", title: "Data Viz", qty: 1, price: 22.0 }] },
  { _id: 1003, customer: { name: "Mai", city: "Hanoi" }, status: "paid",
    items: [{ sku: "BK-01", title: "Python Basics", qty: 1, price: 12.5 }],
    coupon: "WELCOME10" },   // chỉ document này có field coupon
]);

print("Số đơn hàng:", db.orders.countDocuments());
printjson(db.orders.find().toArray());
