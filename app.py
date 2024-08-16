from flask import Flask, request, jsonify, render_template, session, redirect, url_for, Response
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import csv
from io import StringIO
import os
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
def setup_logging():
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    logFile = 'app.log'
    handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
    handler.setFormatter(log_formatter)
    handler.setLevel(logging.INFO)

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

app = Flask(__name__)
app.secret_key = 'example'  # 设置一个秘密密钥用于加密session

DATABASE = 'contact.db'
PASSWORD_HASH = generate_password_hash('password')  # 设置您的密码
BAN_IP_FILE = 'banip.txt'

# 存储IP地址和尝试次数的字典
login_attempts = {}


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS main (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT NOT NULL,
            contact TEXT NOT NULL,
            type INTEGER NOT NULL DEFAULT 0  -- 新增type字段，默认值为0
        )
    ''')
    conn.commit()
    conn.close()


def is_ip_banned(ip):
    if os.path.exists(BAN_IP_FILE):
        with open(BAN_IP_FILE, 'r') as file:
            banned_ips = file.read().splitlines()
            return ip in banned_ips
    return False


def ban_ip(ip):
    with open(BAN_IP_FILE, 'a') as file:
        file.write(ip + '\n')


@app.route('/login', methods=['GET', 'POST'])
def login():
    ip = request.remote_addr
    if is_ip_banned(ip):
        app.logger.warning(f'Banned IP {ip} attempted to login.')
        return '密码错误！', 403

    if request.method == 'POST':
        password = request.form['password']
        if check_password_hash(PASSWORD_HASH, password):
            session['logged_in'] = True
            login_attempts[ip] = 0  # 重置尝试次数
            app.logger.info(f'IP {ip} logged in successfully.')
            return redirect(url_for('index'))
        else:
            if ip not in login_attempts:
                login_attempts[ip] = 1
            else:
                login_attempts[ip] += 1

            app.logger.warning(f'IP {ip} attempted to login with incorrect password. Attempt {login_attempts[ip]}.')

            if login_attempts[ip] >= 3:
                ban_ip(ip)
                app.logger.warning(f'IP {ip} has been banned due to multiple failed login attempts.')
                return '密码错误！', 403

            return '密码错误！', 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/notes', methods=['GET'])
def get_notes():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    limit = request.args.get('limit', default=10, type=int)
    # 获取请求中的type参数，如果不存在则默认为None
    note_type = request.args.get('type', type=int)

    if limit not in [0, 5, 10, 20, 50]:
        limit = 10
    conn = get_db_connection()
    # 根据note_type是否存在构建不同的查询条件
    if note_type is None:
        notes = conn.execute('''
            SELECT * FROM main WHERE type IN (0, 1) ORDER BY id DESC LIMIT ?
        ''', (limit,)).fetchall()
    else:
        notes = conn.execute('''
            SELECT * FROM main WHERE type = ? ORDER BY id DESC LIMIT ?
        ''', (note_type, limit)).fetchall()
    conn.close()
    return jsonify([dict(note) for note in notes])

@app.route('/notes', methods=['POST'])
def add_note():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    new_contact = request.json.get('contact')
    note_type = request.json.get('type', 0)  # 从请求中获取type字段，默认为0
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    conn.execute('INSERT INTO main (time, contact, type) VALUES (?, ?, ?)',
                 (current_time, new_contact, note_type))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Note added successfully', 'time': current_time}), 201


@app.route('/export-notes', methods=['POST'])
def export_notes():
    if not session.get('logged_in'):
        app.logger.warning('Unauthorized access attempt to export notes.')
        return redirect(url_for('login'))

    data = request.get_json()
    start_date = data.get('start-date')
    end_date = data.get('end-date')
    note_type = data.get('type', None)  # 使用None作为默认值来表示导出所有类型

    if not start_date or not end_date:
        app.logger.error('Missing start-date or end-date for notes export.')
        return jsonify({'error': 'Missing start-date or end-date'}), 400

    try:
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        app.logger.error('Invalid date format for notes export.')
        return jsonify({'error': 'Invalid date format'}), 400

    end_date += " 23:59:59"

    conn = get_db_connection()
    cursor = conn.cursor()
    # 根据note_type是否为None或all来构建查询条件
    if note_type is None or note_type == 'all':
        cursor.execute('''
            SELECT * FROM main
            WHERE time BETWEEN ? AND ? AND type IN (0, 1)
            ORDER BY id DESC
        ''', (start_date, end_date))
    else:
        cursor.execute('''
            SELECT * FROM main
            WHERE time BETWEEN ? AND ? AND type = ?
            ORDER BY id DESC
        ''', (start_date, end_date, note_type))

    rows = cursor.fetchall()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['id', 'time', 'contact', 'type'])  # 写入表头
    for row in rows:
        cw.writerow(row)  # 写入数据
    
    app.logger.info(f'Exported notes between {start_date} and {end_date}.')

    return Response(si.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=notes.csv'})


if __name__ == '__main__':
    create_table()  # 首次运行创建表
    setup_logging()  # 配置日志
    app.run(host='localhost', port=8080, debug=False)
