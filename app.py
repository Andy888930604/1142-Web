from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = 'super-secret-key-for-exam'
DB_PATH = 'users.json'

# --- 核心資料處理 ---
def load_db():
    if not os.path.exists(DB_PATH):
        # 初始化預設管理員
        admin = [{
            "username": "admin",
            "email": "admin@test.com",
            "password": "password123",
            "phone": "0912345678",
            "birthday": "1990-01-01",
            "is_admin": True
        }]
        save_db(admin)
        return admin
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(data):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- 題目要求過濾器 ---
@app.template_filter('mask_phone')
def mask_phone(p):
    if not p or len(p) != 10: return p
    return f"{p[:4]}***{p[7:]}"

@app.template_filter('format_tw_date')
def format_tw_date(d):
    if not d: return ""
    try:
        y, m, d = d.split('-')
        return f"民國 {int(y)-1911} 年 {m} 月 {d} 日"
    except:
        return d

# --- 全域權限攔截 (防止忘記檢查 Session) ---
@app.before_request
def auth_guard():
    # 白名單：不需要登入的頁面
    public_endpoints = ['index', 'login', 'register', 'error', 'static']
    if request.endpoint not in public_endpoints and 'username' not in session:
        return redirect(url_for('error', message="請先登入系統"))

# --- 路由實作 ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form.get('username')
        e = request.form.get('email')
        p = request.form.get('password')
        ph = request.form.get('phone', '')
        b = request.form.get('birthday')

        users = load_db()
        # 1. 驗證重複
        if any(x['username'] == u or x['email'] == e for x in users):
            return redirect(url_for('error', message="帳號或 Email 不可重複"))
        
        # 2. 驗證密碼長度
        if not (6 <= len(p) <= 16):
            return redirect(url_for('error', message="密碼長度需為 6 到 16 字元"))
        
        # 3. 驗證 Email 格式 (基礎檢查)
        if "@" not in e or "." not in e:
            return redirect(url_for('error', message="Email 格式不正確"))

        # 4. 驗證電話 (若填寫則需符合格式)
        if ph and (not ph.startswith('09') or len(ph) != 10):
            return redirect(url_for('error', message="電話需為 10 碼數字且以 09 開頭"))

        users.append({
            "username": u, "email": e, "password": p, 
            "phone": ph, "birthday": b, "is_admin": False
        })
        save_db(users)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        e = request.form.get('email')
        p = request.form.get('password')
        user = next((x for x in load_db() if x['email'] == e and x['password'] == p), None)
        
        if user:
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            return redirect(url_for('announcement'))
        return redirect(url_for('error', message="登入失敗，Email 或密碼錯誤"))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/announcement')
def announcement():
    return render_template('announcement.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    users = load_db()
    current_username = session.get('username')
    idx = next((i for i, x in enumerate(users) if x['username'] == current_username), None)

    if request.method == 'POST':
        new_email = request.form.get('email')
        
        # 檢查 Email 重複 (排除自己)
        if any(x['email'] == new_email and x['username'] != current_username for x in users):
            return redirect(url_for('error', message="此 Email 已被其他會員使用"))
        
        # 更新資料
        users[idx]['email'] = new_email
        users[idx]['phone'] = request.form.get('phone')
        users[idx]['birthday'] = request.form.get('birthday')
        
        pwd = request.form.get('password')
        if pwd: 
            users[idx]['password'] = pwd
            
        save_db(users)

        # --- 關鍵修改處 ---
        session.clear() # 清除目前登入狀態
        return redirect(url_for('login')) # 跳轉至登入頁面
        # ----------------
        
    return render_template('profile.html', user=users[idx])


@app.route('/users')
def user_management():
    # 後端二次驗證管理權限
    if not session.get('is_admin'):
        return redirect(url_for('error', message="權限不足，僅管理員可進入"))
    return render_template('users.html', users=load_db())

@app.route('/users/<target_username>/edit', methods=['GET', 'POST'])
def edit_user(target_username):
    if not session.get('is_admin'):
        return redirect(url_for('error', message="權限不足"))
    
    users = load_db()
    idx = next((i for i, x in enumerate(users) if x['username'] == target_username), None)
    
    if request.method == 'POST':
        users[idx]['phone'] = request.form.get('phone')
        users[idx]['birthday'] = request.form.get('birthday')
        pwd = request.form.get('password')
        if pwd: users[idx]['password'] = pwd
        save_db(users)
        return redirect(url_for('user_management'))
        
    return render_template('edit_user.html', user=users[idx])

@app.route('/users/<target_username>/delete', methods=['POST'])
def delete_user(target_username):
    if not session.get('is_admin'):
        return redirect(url_for('error', message="權限不足"))
    
    # 防止刪除 admin 或 自己
    if target_username == 'admin' or target_username == session.get('username'):
        return redirect(url_for('error', message="系統限制：不可刪除 admin 或目前的管理員帳號"))
    
    users = [x for x in load_db() if x['username'] != target_username]
    save_db(users)
    return redirect(url_for('user_management'))

@app.route('/error')
def error():
    msg = request.args.get('message', '系統發生錯誤')
    return render_template('error.html', message=msg)

if __name__ == '__main__':
    app.run(debug=True)
