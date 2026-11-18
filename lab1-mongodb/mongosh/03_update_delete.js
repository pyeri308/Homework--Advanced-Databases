// 03_update_delete.js — Update và Delete
// Lưu ý: script này thay đổi dữ liệu (xoá đơn 1003). Muốn làm lại từ đầu thì chạy lại 01_insert.js.
db = db.getSiblingDB("shop");

function result(title, r) {
  print(`${title}: matched=${r.matchedCount}, modified=${r.modifiedCount}`);
}

result("1001 -> shipped", db.orders.updateOne({ _id: 1001 }, { $set: { status: "shipped" } }));
result("Mọi đơn paid -> reviewed=false", db.orders.updateMany({ status: "paid" }, { $set: { reviewed: false } }));
result("Thêm tag 'gift' vào 1002", db.orders.updateOne({ _id: 1002 }, { $push: { tags: "gift" } }));
result("Xoá field coupon của 1003", db.orders.updateOne({ _id: 1003 }, { $unset: { coupon: "" } }));

const d = db.orders.deleteOne({ _id: 1003 });
print("Xoá đơn 1003: deleted=" + d.deletedCount);

print("\n=== Dữ liệu sau khi cập nhật ===");
printjson(db.orders.find().toArray());
