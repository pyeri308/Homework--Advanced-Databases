// Bài tập 1 — Thêm 5 đơn hàng có "hình dạng" khác nhau, rồi tìm các đơn chứa 1 sku
// Dùng collection riêng orders_ex để không ảnh hưởng dữ liệu bài học.
db = db.getSiblingDB("shop");
const c = db.orders_ex;
c.drop();

c.insertMany([
  { _id: 1, customer: { name: "An", city: "Hanoi" }, status: "paid",
    items: [{ sku: "BK-01", qty: 1, price: 12.5 }] },
  { _id: 2, customer: { name: "Binh", city: "Hue", phone: "0901234567" }, status: "shipped",
    items: [{ sku: "BK-03", qty: 1, price: 22.0 }, { sku: "BK-01", qty: 2, price: 12.5 }],
    tags: ["gift"] },
  { _id: 3, customer: { name: "Chi" }, status: "cancelled", items: [],
    note: "Khách huỷ đơn" },
  { _id: 4, customer: { name: "Dung", city: "HCMC" }, status: "paid",
    items: [{ sku: "BK-07", qty: 1, price: 18.0 }],
    coupon: "WELCOME10", shipping: { method: "express", fee: 3.5 } },
  { _id: 5, customer: { name: "Em", city: "Da Nang" }, status: "paid",
    items: [{ sku: "BK-01", qty: 3, price: 12.5, giftWrap: true }],
    paidAt: new Date() },
]);

const sku = "BK-01";
print(`=== Các đơn có sku ${sku} ===`);
printjson(c.find({ "items.sku": sku }, { _id: 1, "customer.name": 1, items: 1 }).toArray());
