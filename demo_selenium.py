import json
import time
import typing

from selenium.common.exceptions import (
    ElementNotInteractableException,
    ElementClickInterceptedException, ElementNotVisibleException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.support.wait import WebDriverWait

import hcaptcha_challenger as solver
from hcaptcha_challenger import HolyChallenger
from hcaptcha_challenger.exceptions import ChallengePassed
from selenium.webdriver.support.select import Select

# Existing user data
headless = False
# 你的信息获取
try:
    f = open(r"./user_data.json", "r", encoding="utf-8")
    user_json = json.loads(f.read())
    first_name = user_json["first_name"]
    last_name = user_json["last_name"]
    email = user_json["email"]
    alternate_name = user_json['alternate_name']
    password = user_json['password']
    customer_type = user_json['customer_type']
    company_name = user_json['company_name']
    company_name_en = user_json['company_name_en']
    cloud_account = user_json['cloud_account']
    area = user_json['area']
    is_full_registration = user_json['is_full_registration']
    email_account = user_json['email_account']
    email_password = user_json['email_password']
    address_1 = user_json['address_1']
    address_2 = user_json['address_2']
    city = user_json['city']
    province = user_json['province']
    postal_code = user_json['postal_code']
    tel = user_json['tel']
    card_type = user_json['card_type']
    card_number = user_json['card_number']
    expiration_year = user_json['expiration_year']
    expiration_month = user_json['expiration_month']
    cvn = user_json['cvn']
except:
    # 重写文件
    f = open('./user_data.json', 'w')
    print("用户信息初始化,第一次进入程序是需要输入你的相关信息的")
    print("接收甲骨文邮箱暂时只支持163邮箱,其他邮箱看情况要不要开通支持")
    email_account = input("请输入你的163邮箱账号:")
    email_password = input("请输入你的163邮箱账号密码:")
    first_name = input("请输入你的姓名: ")
    last_name = input("请输入你的姓氏：")
    email = email_account + "@163.com"
    is_full_registration = input(
        "是否只获取邮箱:   0:程序只到获取邮箱就停止运行,并且返回甲骨文发送的邮件地址     1:程序会获取邮箱,并且需要你的信用卡等信息来完成完整的注册完整的甲骨文步骤")

    # 判断输入你的公司名称
    if is_full_registration == "1":
        alternate_name = input("请输入你的备用姓名：")
        password = input("请输入你的密码：")
        customer_type = input("请输入你的公司类型：  0:有公司   1:没有公司")

        # 判断输入你的公司名称
        if "0" == customer_type:
            customer_type = True
            company_name = input("请输入你的公司中文名：")
            company_name_en = input("请输入你的公司英文名：")
        else:
            customer_type = False
            company_name = ""
            company_name_en = ""

        cloud_account = input("请输入你的cloud账户名:    如果没输入,则取默认")
        area = input("请输入你需要注册的甲骨文區域:")
        address_1 = input("请输入你的地址1:")
        address_2 = input("默认为空  请输入你的地址2:")
        city = input("请输入你的城市:")
        province = input("请输入你的省份:")
        postal_code = input("请输入你的邮政编码:")
        tel = input("请输入你的手机号码:")
        card_type = input("请输入你的信用卡类型:")
        card_number = input("请输入你的信用卡号:")
        expiration_year = input("请输入你的信用卡到期年份  例如2030:")
        expiration_month = input("请输入你的信用到期月份呢  例如 05:")
        cvn = input("请输入你的信用cvn:")

    data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "alternate_name": alternate_name if len(alternate_name) else "",
        "password": password if len(password) else "",
        "customer_type": customer_type,
        "company_name": company_name,
        "company_name_en": company_name_en,
        "cloud_account": cloud_account if len(cloud_account) else "",
        "area": area if len(area) else "",
        "is_full_registration": is_full_registration,
        "email_account": email_account,
        "email_password": email_password,
        "address_1": address_1 if len(address_1) else "",
        "address_2": address_2 if len(address_2) else "",
        "city": city if len(city) else "",
        "province": province if len(province) else "",
        "postal_code": postal_code if len(postal_code) else "",
        "tel": tel if len(tel) else "",
        "card_type": card_type if len(card_type) else "",
        "card_number": card_number if len(card_number) else "",
        "expiration_year": expiration_year if len(expiration_year) else "",
        "expiration_month": expiration_month if len(expiration_month) else "",
        "cvn": cvn if len(cvn) else ""
    }
    json_data = json.dumps(data, indent=4, separators=(',', ': '))
    f.write(json_data)

# Init local-side of the ModelHub
solver.install()


# 拒绝cookie弹窗元素
def close_cookie(ctx):
    try:
        WebDriverWait(ctx, 2, ignored_exceptions=(ElementNotVisibleException,)).until(
            EC.frame_to_be_available_and_switch_to_it(
                (By.XPATH, "//iframe[@class='truste_popframe']")
            )
        )
        print("识别到cookie弹窗，开始尝试拒绝cookie")

        # [👻] 点击拒绝cookie
        WebDriverWait(ctx, 8).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[8]/div[1]/div/div[3]/a[2]"))).click()

        # [👻] 点击关闭
        WebDriverWait(ctx, 8).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='gwt-debug-close_id']"))).click()
    except:
        print("关闭Cookie处理完成")


def hit_challenge(ctx, challenger: HolyChallenger, retries: int = 10) -> typing.Optional[str]:
    """
    Use `anti_checkbox()` `anti_hcaptcha()` to be flexible to challenges
    :param ctx:
    :param challenger:
    :param retries:
    :return:
    """
    if challenger.utils.face_the_checkbox(ctx):
        challenger.anti_checkbox(ctx)
        if res := challenger.utils.get_hcaptcha_response(ctx):
            return res

    for _ in range(retries):
        try:
            if (resp := challenger.anti_hcaptcha(ctx)) is None:
                continue
            if resp == challenger.CHALLENGE_SUCCESS:
                return challenger.utils.get_hcaptcha_response(ctx)
        except ChallengePassed:
            return challenger.utils.get_hcaptcha_response(ctx)
        challenger.utils.refresh(ctx)
        time.sleep(1)


def bytedance():
    # New Challenger
    challenger = solver.new_challenger(screenshot=True, debug=True)

    # Replace selenium.webdriver.Chrome with CTX
    ctx = solver.get_challenge_ctx(silence=headless)
    ctx.get("https://www.oracle.com/cn/cloud/free/")
    try:
        # 甲骨文云点击发送邮箱
        registration(ctx)

        # 处理验证
        print("开始处理验证码部分，使用ai自动跳过，报错请在这部分使用vpn    验证无障碍模式待开发")
        hit_challenge(ctx=ctx, challenger=challenger)
        # 点击 验证我的电子邮件
        print("点击  验证我的电子邮件")
        WebDriverWait(ctx, 5, ignored_exceptions=(ElementClickInterceptedException,)).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='verifyMyEmail']"))
        ).click()

        # 等待发送成功
        print("等待发送成功")
        try:
            WebDriverWait(ctx, 20, ignored_exceptions=(ElementClickInterceptedException,)).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//*[@id='main']/div/div[2]/div/div[2]/div[1]/form/fieldset/div[4]/div[1]/div[1]/h4"))
            )
        except:
            print("发送邮件失败")
            return "发送邮件失败"

        # 163邮件获取
        print("邮件获取甲骨文地址中...")
        email_url = get_email(ctx)

        print("恭喜获取甲骨文注册地址,甲骨文注册地址为:", email_url)

        # 打开甲骨文地址
        ctx.get(email_url)
        # 甲骨文信用卡注册
        registration_oracle(ctx)

        ctx.save_screenshot(f"datas/bytedance{' - headless' if headless else ''}.png")
    finally:
        ctx.quit()


# 163邮件获取   不通过api获取邮件
def get_email(ctx):
    ctx.get("https://mail.163.com/")

    # 获取url来判断是否已经登录进去
    email_url = ctx.current_url
    if email_url.__len__() < 35:
        # 进入到frame元素
        ctx.switch_to.frame(0)
        # 账号
        ctx.find_element(By.NAME, "email").clear()
        ctx.find_element(By.NAME, "email").send_keys(email_account)
        # 密码输入
        ctx.find_element(By.NAME, "password").clear()
        ctx.find_element(By.NAME, "password").send_keys(email_password)
        ctx.find_element(By.ID, "dologin").click()

    # 获取提示
    WebDriverWait(ctx, timeout=200).until(
        lambda d: d.find_element(By.XPATH, '//*[@id="dvNavTree"]'))
    # 点击未读邮件
    ctx.find_element(By.XPATH,
                     '//*[@id="dvNavTree"]/ul/li[1]/div').click()

    # 获取到收件箱的未读甲骨文信息
    WebDriverWait(ctx, timeout=200).until(
        lambda d: d.find_element(By.XPATH, '//*[@id="_dvModuleContainer_mbox.ListModule_0"]/div/div/div/div[3]'))

    for i in range(40):
        # 找到甲骨文邮件
        try:
            email_info = ctx.find_element(By.XPATH,
                                          '//*[@id="_dvModuleContainer_mbox.ListModule_0"]/div/div/div/div/div[@class="rF0 kw0 nui-txt-flag0"]/div/div[1]/div[2 and span="Oracle Cloud"]')
        except:
            time.sleep(5)
            # 刷该页面
            ctx.refresh()
            print("每隔5s刷新一次从页面,总共刷新40次,刷新第 ", i + 1, " 次")
            continue
        email_info.click()
        break

        # 获取甲骨文url
    WebDriverWait(ctx, 2, ignored_exceptions=(ElementNotVisibleException,)).until(
        EC.frame_to_be_available_and_switch_to_it(
            (By.XPATH, "//iframe[@class='oD0']")
        )
    )
    oracle_url = WebDriverWait(ctx, 100, ignored_exceptions=(ElementClickInterceptedException,)).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@id='content']/div[1]/div/table/tbody/tr[2]/td/p[2]/a"))
    ).get_attribute("href")
    return oracle_url


# 注册甲骨文云
def registration(ctx):
    # 通过get方法发送网址
    print("打开甲骨文地址")
    ctx.get("https://www.oracle.com/cn/cloud/free/")
    # 拒绝cookie弹窗元素
    close_cookie(ctx)
    # 点击立即免费使用
    print("点击立即免费使用")
    WebDriverWait(ctx, 5, ignored_exceptions=(ElementClickInterceptedException,)).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/section[2]/div[3]/div/div[1]/div/div[1]/a"))
    ).click()

    # 获取全部标签页
    window = ctx.window_handles
    # 将激活标签页设置为最新的一项(按自己业务改)
    ctx.switch_to.window(window.pop())

    # 判断字符是中文还是英文
    language_text = ctx.find_element(By.XPATH,
                                     '//*[@id="main"]/div/div[2]/div/div[2]/div[1]/form/fieldset/div[3]/label/span').text
    is_en = language_text.isalnum()
    # 点击下拉框选择国家
    print("点击下拉框选择国家")
    WebDriverWait(ctx, 5, ignored_exceptions=(ElementClickInterceptedException,)).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='main']/div/div[2]/div/div[2]/div[1]/form/fieldset/div[1]/label/div/div/div[1]"))
    ).click()

    # 选择中国
    if is_en:
        WebDriverWait(ctx, 5, ignored_exceptions=(ElementClickInterceptedException,)).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "//*[@id='main']/div/div[2]/div/div[2]/div[1]/form/fieldset/div[1]/label/div/div[2]/div/div[text()='China']"))
        ).click()
    else:
        WebDriverWait(ctx, 5, ignored_exceptions=(ElementClickInterceptedException,)).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "//*[@id='main']/div/div[2]/div/div[2]/div[1]/form/fieldset/div[1]/label/div/div[2]/div/div[text()='中国']"))
        ).click()
        # ctx.find_element(By.XPATH,
        #                  "//*[@id='react-select-2-option-3']").click()
    # 名字
    print("名字输入")
    WebDriverWait(ctx, 15, ignored_exceptions=(ElementNotInteractableException,)).until(
        EC.presence_of_element_located((By.ID, "firstName"))
    ).send_keys(first_name)

    # 姓氏
    print("姓氏输入")
    WebDriverWait(ctx, 15, ignored_exceptions=(ElementNotInteractableException,)).until(
        EC.presence_of_element_located((By.ID, "lastName"))
    ).send_keys(last_name)

    # 电子邮箱
    print("电子邮箱输入")
    WebDriverWait(ctx, 15, ignored_exceptions=(ElementNotInteractableException,)).until(
        EC.presence_of_element_located((By.ID, "email"))
    ).send_keys(email)


# 甲骨文信用卡注册
def registration_oracle(ctx):
    # 备用姓名
    print("备用姓名输入")
    WebDriverWait(ctx, 10, ignored_exceptions=(ElementClickInterceptedException,)).until(
        EC.visibility_of_element_located(
            (By.XPATH,
             "//*[@id='alternateName']"))
    ).send_keys(alternate_name)

    # 密码
    print("密码输入")
    ctx.find_element(By.XPATH,
                     "//*[@id='main']/div/div[2]/div/div[2]/div[1]/form/fieldset/div[4]/label/div[1]/input").send_keys(
        password)
    # 确认密码
    print("确认密码输入")
    ctx.find_element(By.XPATH,
                     "//*[@id='main']/div/div[2]/div/div[2]/div[1]/form/fieldset/div[5]/label/input").send_keys(
        password)
    # 公司名称
    print("公司名称输入")
    ctx.find_element(By.XPATH,
                     "//*[@id='main']/div/div[2]/div/div[2]/div[1]/form/fieldset/div[7]/div[1]/div/label/input").send_keys(
        company_name)
    # 公司名称英文
    print("公司名称英文输入")
    ctx.find_element(By.XPATH,
                     "//*[@id='main']/div/div[2]/div/div[2]/div[1]/form/fieldset/div[7]/div[2]/div/label/input").send_keys(
        company_name_en)
    # Cloud账户名
    if len(cloud_account) > 0:
        ctx.find_element(By.XPATH,
                         "//*[@id='main']/div/div[2]/div/div[2]/div[1]/form/fieldset/div[7]/div[2]/div/label/input").send_keys(
            cloud_account)
    # 处理主区域
    WebDriverWait(ctx, 5, ignored_exceptions=(ElementClickInterceptedException,)).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='main']/div/div[2]/div/div[2]/div[1]/form/fieldset/div[9]/label/div/div"))
    ).click()
    # 選擇區域
    print("選擇區域处理")
    WebDriverWait(ctx, 5, ignored_exceptions=(ElementClickInterceptedException,)).until(
        EC.element_to_be_clickable(
            (By.XPATH,
             "//*[@id='main']/div/div[2]/div/div[2]/div[1]/form/fieldset/div[9]/label/div/div[2]/div/div/div[2]/div[text()='" + area + "']"))
    ).click()

    # 点击继续
    print("点击继续")
    WebDriverWait(ctx, 5, ignored_exceptions=(ElementClickInterceptedException,)).until(
        EC.element_to_be_clickable(
            (By.XPATH,
             "//*[@id='main']/div/div[2]/div/div[2]/div[2]/button"))
    ).click()

    # 地址1
    print("地址1输入")
    WebDriverWait(ctx, 5, ignored_exceptions=(ElementClickInterceptedException,)).until(
        EC.visibility_of_element_located(
            (By.XPATH,
             "//*[@id='address1']"))
    ).send_keys(address_1)
    # 地址2
    print("地址2输入")
    ctx.find_element(By.XPATH,
                     "//*[@id='address2']").send_keys(
        address_2)

    # 城市
    print("城市输入")
    ctx.find_element(By.XPATH,
                     "//*[@id='city']").send_keys(
        city)

    # 省份
    print("省份输入")
    ctx.find_element(By.XPATH,
                     "//*[@id='province']").send_keys(
        province)

    # 邮政编码
    print("邮政编码输入")
    ctx.find_element(By.XPATH,
                     "//*[@id='postalcode']").send_keys(
        postal_code)
    # 手机号输入
    print("手机号输入")
    ctx.find_element(By.XPATH,
                     "//*[@id='phoneNumber']").send_keys(
        tel)

    # 点击继续
    print("点击继续")
    WebDriverWait(ctx, 2).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='main']/div/div[2]/div[2]/div[1]/div/div[1]/div[2]/form/button"))).click()

    # 点击添加付款验证方式
    print("点击添加付款验证方式")
    WebDriverWait(ctx, 2).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='main']/div/div[2]/div[2]/div[1]/div/div[2]/div[2]/button"))).click()
    # pay获取弹窗支付卡
    print("pay获取弹窗支付卡")
    WebDriverWait(ctx, 10, ignored_exceptions=(ElementNotVisibleException,)).until(
        EC.frame_to_be_available_and_switch_to_it(
            (By.XPATH, "//iframe[@id='opayifrm']")
        )
    )
    # [👻] 点击支付卡
    print("点击支付卡")
    WebDriverWait(ctx, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@id='ps-cc-button']/div"))).click()

    # 有时候会出问题，不知道为啥，因此在这里延迟3s，然后在出现弹窗
    print("为避免未知错误，等待5s")
    time.sleep(5)

    # pay获取弹窗支付卡
    print("pay获取弹窗支付卡")
    WebDriverWait(ctx, 20, ignored_exceptions=(ElementNotVisibleException,)).until(
        EC.frame_to_be_available_and_switch_to_it(
            (By.XPATH, "//iframe[@data-testid='paymentGateway']")
        )
    )

    try:
        # 卡号
        print("卡号输入")
        WebDriverWait(ctx, 10, ignored_exceptions=(ElementClickInterceptedException,)).until(
            EC.visibility_of_element_located(
                (By.XPATH,
                 "//*[@id='card_number']"))
        ).send_keys(card_number)
    except:
        print("弹窗是空白的")

    # pay点击信用卡类型
    print("pay点击信用卡类型选择")
    locate_with_src = locate_with(By.TAG_NAME, "input").to_left_of(
        {By.XPATH: "//*[@id='card_type_selection']/div/label[text()='" + card_type + "']"})
    ctx.find_element(locate_with_src).click()

    # 信用卡年份选择
    print("信用卡年份选择")
    Select(ctx.find_element(By.XPATH, "//*[@id='card_expiry_year']")).select_by_value(expiration_year)
    # 信用卡月份选择
    print("信用卡月份选择")
    Select(ctx.find_element(By.XPATH, "//*[@id='card_expiry_month']")).select_by_value(
        expiration_month)
    # cvn填写
    print("cvn填写")
    ctx.find_element(By.XPATH,
                     "//*[@id='card_cvn']").send_keys(
        cvn)

    # 有时候会出问题，不知道为啥，因此在这里延迟3s，然后在出现弹窗
    print("为避免未知错误，等待5s")
    time.sleep(5)

    # 提交信用卡信息
    print("提交信用卡信息")
    ctx.find_element(By.XPATH,
                     "//*[@id='payment_details']/input").click()

    # 有时候会出问题，不知道为啥，因此在这里延迟3s，然后在出现弹窗
    print("为避免未知错误，等待5s")
    time.sleep(5)

    # pay获取弹窗
    print("pay获取弹窗")
    WebDriverWait(ctx, 10, ignored_exceptions=(ElementNotVisibleException,)).until(
        EC.frame_to_be_available_and_switch_to_it(
            (By.XPATH, "//iframe[@id='opayifrm']")
        )
    )

    # 点击Close
    print("关闭信息填写窗口")
    WebDriverWait(ctx, 10, ignored_exceptions=(ElementNotVisibleException,)).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='ps-success-close-button']")
        )
    ).click()

    # 有时候会出问题，不知道为啥，因此在这里延迟3s，然后在出现弹窗
    print("为避免未知错误，等待5s")
    time.sleep(5)

    # 点击协议
    WebDriverWait(ctx, 5, ignored_exceptions=(ElementNotVisibleException,)).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='main']/div/div[2]/div[2]/div[2]/label/div")
        )
    ).click()
    # 点击开始我的免费试用
    WebDriverWait(ctx, 10, ignored_exceptions=(ElementNotVisibleException,)).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='startMyTrialBtn' and not(@disabled)]")
        )
    ).click()

    # 有时候会出问题，不知道为啥，因此在这里延迟3s，然后在出现弹窗
    print("为避免未知错误，等待5s")
    time.sleep(5)

    # 获取提示信息  abc等
    try:
        WebDriverWait(ctx, 10, ignored_exceptions=(ElementNotVisibleException,)).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[@id='main']/div/div[2]/div[2]/div/div/div[2]/div[2]/div[3]/div[1]/div[1]/h4")
            )
        ).click()
    except:
        print("成功注册")


if __name__ == "__main__":
    bytedance()
