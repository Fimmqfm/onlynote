from werkzeug.security import generate_password_hash

# 数据库路径，一般保持默认
app_database = 'contact.db'

# 密钥，需改为随机字符，越长越安全
app_secret_key = 'example'
# 将password改为自己的密码。建议自行获取哈希值，避免明文保存
app_password_hash = generate_password_hash('password')

# 运行端口。如需被其他设备访问请修改为0.0.0.0
app_host = 'localhost'
# 运行端口
app_port = 8080
