import json
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# --- 1. 自訂過濾器 ---

@app.template_filter('mask_phone')
def mask_phone(phone: str) -> str:
    """將電話號碼中間四碼遮罩，例如 0912345678 -> 0912****78"""
    if len(phone) == 10:
        return f"{phone[:4]}****{phone[8:]}"
    return phone

@app.template_filter('format_tw_date')
def format_tw_date(date_str: str) -> str:
    """將西元日期轉換為民國日期，例如 1990-01-01 -> 民國 79 年 01 月 01 日"""
    try:
        parts = date_str.split('-')
        year = int(parts[0]) - 1911
        return f"民國 {year} 年 {parts[1]} 月 {parts[2]} 日"
    except (IndexError, ValueError):
        return date_str

# --- 2. 輔助函式 ---

def init_json_file(file_path: str) -> None:
    """初始化 JSON 檔案，若不存在則建立預設 admin 資料"""
    if not os.path.exists(file_path):
        initial_data = {
            "users": [
                {
                    "username": "admin",
                    "email": "admin@example.com",
                    "password": "admin123",
                    "phone": "0912345678",
                    "birthdate": "1990-01-01"
                }
            ]
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=4, ensure_ascii=False)

def read_users(file_path: str) -> dict:
    """讀取會員資料"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": []}

def save_users(file_path: str, data: dict) -> bool:
    """儲存會員資料"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False

def validate_register(form_data: dict, users: list) -> dict:
    """驗證註冊資料"""
    u = form_data.get("username", "").strip()
    e = form_data.get("email", "").strip()
    p = form_data.get("password", "").strip()
    ph = form_data.get("phone", "").strip()
    b = form_data.get("birthdate", "").strip()

    # 必填檢查
    if not all([u, e, p, b]):
        return {"success": False, "error": "帳號、Email、密碼與生日為必填項目"}
    
    # Email 格式
    if "@" not in e or "." not in e:
        return {"success": False, "error": "Email 格式不正確"}
    
    # 密碼長度
    if not (6 <= len(p) <= 16):
        return {"success": False, "error": "密碼長度需介於 6~16 字元"}
    
    # 電話驗證 (選填)
    if ph and (not ph.isdigit() or len(ph) != 10 or not ph.startswith("09")):
        return {"success": False, "error": "電話需為 10 碼數字且以 09 開頭"}

    # 重複檢查
    for user in users:
        if user['username'] == u:
            return {"success": False, "error": "帳號已存在"}
        if user['email'] == e:
            return {"success": False, "error": "Email 已被註冊"}

    return {"success": True, "data": {"username": u, "email": e, "password": p, "phone": ph, "birthdate": b}}

def verify_login(email: str, password: str, users: list) -> dict:
    """驗證登入資料"""
    for user in users:
        if user['email'] == email and user['password'] == password:
            return {"success": True, "data": user}
    return {"success": False, "error": "Email 或密碼錯誤"}

# 初始化檔案 (模組層級執行)
USER_FILE = "users.json"
init_json_file(USER_FILE)

# --- 3. 路由實作 ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register_route():
    if request.method == "POST":
        all_data = read_users(USER_FILE)
        result = validate_register(request.form, all_data["users"])
        
        if result["success"]:
            all_data["users"].append(result["data"])
            save_users(USER_FILE, all_data)
            return redirect(url_for("login_route"))
        else:
            return redirect(url_for("error_route", message=result["error"]))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login_route():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        all_data = read_users(USER_FILE)
        
        result = verify_login(email, password, all_data["users"])
        if result["success"]:
            return redirect(url_for("welcome_route", username=result["data"]["username"]))
        else:
            return redirect(url_for("error_route", message=result["error"]))
    return render_template("login.html")

@app.route("/welcome/<username>")
def welcome_route(username):
    all_data = read_users(USER_FILE)
    user = next((u for u in all_data["users"] if u["username"] == username), None)
    if user:
        return render_template("welcome.html", user=user)
    return redirect(url_for("error_route", message="找不到該使用者"))

@app.route("/users")
def users_list_route():
    all_data = read_users(USER_FILE)
    return render_template("users.html", users=all_data["users"])

@app.route("/error")
def error_route():
    message = request.args.get("message", "發生未知錯誤")
    return render_template("error.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)
