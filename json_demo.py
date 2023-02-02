import json

try:
    f = open(r"./user_data.json", "r", encoding="utf-8")
    user_json = json.loads(f.read())
    first_name = user_json["first_name"]
    last_name = user_json["last_name"]
    email = user_json["email"]
except:
    # 重写文件
    f = open('./user_data.json', 'w')
    print("用户信息初始化")
    first_name = input("请输入你的姓名: ")
    last_name = input("请输入你的姓氏：")
    email = input("请输入你的邮箱: ")

    data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email
    }
    json_data = json.dumps(data, indent=4, separators=(',', ': '))
    f.write(json_data)
