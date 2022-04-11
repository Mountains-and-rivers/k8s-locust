__author__ = "Alex Li"

import paramiko

private_key = paramiko.RSAKey.from_private_key_file('id_rsa31.txt')

# 创建SSH对象
ssh = paramiko.SSHClient()
# 允许连接不在know_hosts文件中的主机
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# 连接服务器
ssh.connect(hostname='10.0.0.41', port=52113, username='gongli', pkey=private_key)

# 执行命令
stdin, stdout, stderr = ssh.exec_command('df')
result = stdout.read()
print(result.decode())
stdin, stdout2, stderr = ssh.exec_command('ifconfig')
# 获取命令结果
result2 = stdout2.read()
print(result2.decode())

# 关闭连接
ssh.close()