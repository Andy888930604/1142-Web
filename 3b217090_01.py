def find_product(products: list, pid: int) -> dict:
    """根據 ID 查詢產品，回傳固定格式的 dict"""
    for p in products:
        if p.get("id") == pid:
            return {"success": True, "data": p}
    return {"success": False, "data": None}

def format_price(price: int) -> str:
    """將數字格式化為帶有千分位與貨幣符號的字串"""
    return f"${price:,}"

if __name__ == "__main__":
    products = [
        {"id": 1, "name": "Keyboard", "price": 1200},
        {"id": 2, "name": "Mouse", "price": 800},
        {"id": 3, "name": "Monitor", "price": 4500}
    ]

    
    print("=== 查詢 ID: 1 ===")
    result1 = find_product(products, 1)
    if result1["success"]:
        product = result1["data"]
        name = product["name"]
        price_str = format_price(product["price"])
        print(f"找到產品: {name}, 價格: {price_str}")
    else:
        print("=> 查無此產品")

    print("\n=== 查詢 ID: 99 ===")
    
    result2 = find_product(products, 99)
    if result2["success"]:
        product = result2["data"]
        print(f"找到產品: {product['name']}, 價格: {format_price(product['price'])}")
    else:
        print("=> 查無此產品")
