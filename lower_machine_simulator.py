import socket
import time
import random
import threading

# --- 下位机配置 ---
# 模拟下位机监听的IP地址和端口
# 请确保这个IP地址是您的电脑的IP，或者使用 '127.0.0.1' (本地回环地址)
# 如果使用 '127.0.0.1'，请确保您的Qt上位机连接时也使用 '127.0.0.1'。
# 端口号可以随意设置，但要和Qt上位机连接的端口号一致。
HOST = '127.0.0.1'  # 建议使用 '127.0.0.1' 进行本地测试
PORT = 12345        # 随意选择一个未被占用的端口，例如 12345

# --- 下位机内部状态和阈值 ---
# 初始阈值 (可由模拟的按键调整)
temperature_threshold = 28.0  # 默认温度报警阈值
humidity_threshold = 70.0     # 默认湿度报警阈值

# 设备状态
is_fan_on = False             # 风扇是否开启
is_ambient_light_led_on = False # 环境光LED是否开启
is_alarm_active = False       # 报警是否激活 (蜂鸣器和报警LED)

def simulate_sensor_readings():
    """模拟温湿度和光照传感器读取数据"""
    # 模拟温度在 20.0 到 35.0 之间波动
    temp = round(random.uniform(20.0, 35.0), 2)
    # 模拟湿度在 40.0 到 80.0 之间波动
    humidity = round(random.uniform(40.0, 80.0), 2)
    # 模拟光照强度 (0-1000，值越低越暗)
    light_level = random.randint(0, 1000)
    return temp, humidity, light_level

def lower_machine_logic(current_temp, current_humidity, current_light):
    """模拟下位机的控制逻辑"""
    global is_fan_on, is_ambient_light_led_on, is_alarm_active

    print(f"\n--- 下位机当前读数: 温度={current_temp}°C, 湿度={current_humidity}%, 光照={current_light} ---")

    # 1. 温湿度报警逻辑
    if current_temp > temperature_threshold or current_humidity > humidity_threshold:
        if not is_alarm_active:
            print("[下位机] !!! 报警激活: 温度或湿度超出阈值 !!!")
            print("[下位机] 蜂鸣器响! 报警LED闪烁!")
            # 根据文档，超出阈值时会“提醒开风扇”，这里模拟自动开启风扇
            if not is_fan_on:
                print("[下位机] 风扇因报警自动开启。")
                is_fan_on = True
            is_alarm_active = True
    else:
        if is_alarm_active:
            print("[下位机] 报警解除。")
        is_alarm_active = False

    # 2. 光照控制逻辑 (模拟白天/黑夜开关灯)
    if current_light < 200: # 假设光照强度低于200为黑暗
        if not is_ambient_light_led_on:
            print("[下位机] 环境黑暗。环境光LED开启。")
            is_ambient_light_led_on = True
    else:
        if is_ambient_light_led_on:
            print("[下位机] 环境明亮。环境光LED关闭。")
            is_ambient_light_led_on = False

    # 3. 模拟OLED显示 (打印到控制台)
    print("\n--- 下位机OLED显示 ---")
    print(f"温度: {current_temp}°C (阈值: {temperature_threshold}°C)")
    print(f"湿度: {current_humidity}% (阈值: {humidity_threshold}%)")
    print(f"风扇状态: {'开启' if is_fan_on else '关闭'}")
    print(f"环境光LED: {'开启' if is_ambient_light_led_on else '关闭'}")
    print(f"报警状态: {'激活' if is_alarm_active else '未激活'}")
    print("----------------------")


def user_input_handler():
    """处理用户输入，模拟按键操作"""
    global temperature_threshold, humidity_threshold, is_fan_on
    while True:
        try:
            cmd = input("\n输入命令 (t+ / t- / h+ / h- / fan_on / fan_off / exit): ").strip().lower()
            if cmd == 't+':
                temperature_threshold = round(temperature_threshold + 1.0, 1)
                print(f"[下位机] 温度阈值增加到 {temperature_threshold}°C")
            elif cmd == 't-':
                temperature_threshold = round(temperature_threshold - 1.0, 1)
                print(f"[下位机] 温度阈值减少到 {temperature_threshold}°C")
            elif cmd == 'h+':
                humidity_threshold = round(humidity_threshold + 1.0, 1)
                print(f"[下位机] 湿度阈值增加到 {humidity_threshold}%")
            elif cmd == 'h-':
                humidity_threshold = round(humidity_threshold - 1.0, 1)
                print(f"[下位机] 湿度阈值减少到 {humidity_threshold}%")
            elif cmd == 'fan_on':
                is_fan_on = True
                print("[下位机] 风扇手动开启。")
            elif cmd == 'fan_off':
                is_fan_on = False
                print("[下位机] 风扇手动关闭。")
            elif cmd == 'exit':
                print("退出用户输入处理。")
                break
            else:
                print("未知命令。请尝试 't+', 't-', 'h+', 'h-', 'fan_on', 'fan_off', 'exit'。")
        except Exception as e:
            print(f"输入错误: {e}")

def main_lower_machine_loop():
    """下位机主循环：读取传感器、执行逻辑、发送数据"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"下位机模拟程序正在监听 {HOST}:{PORT}...")
        print("请在您的Qt上位机中设置连接IP为 '127.0.0.1'，端口为 '12345'，然后点击连接。")

        conn = None
        addr = None
        while True:
            try:
                if conn is None: # Only accept new connection if not already connected
                    conn, addr = s.accept()
                    print(f"上位机已连接: {addr}")
                
                # 模拟传感器读取
                temp, humidity, light_level = simulate_sensor_readings()

                # 执行下位机逻辑
                lower_machine_logic(temp, humidity, light_level)

                # 准备发送给上位机的数据
                data_to_send = f"{temp}/{humidity}" # 格式：温度/湿度
                conn.sendall(data_to_send.encode('utf-8'))
                print(f"发送到上位机: '{data_to_send.strip()}'")

                time.sleep(2) # 每2秒发送一次数据

            except ConnectionResetError:
                print("上位机断开连接。等待新的连接...")
                conn = None
                addr = None
            except BrokenPipeError:
                print("与上位机的连接已断开。等待新的连接...")
                conn = None
                addr = None
            except Exception as e:
                print(f"发生错误: {e}")
                break

if __name__ == "__main__":
    # 启动一个线程来处理用户输入，模拟按键操作
    input_thread = threading.Thread(target=user_input_handler)
    input_thread.daemon = True # 设置为守护线程，主程序退出时它也会退出
    input_thread.start()

    # 启动下位机主循环
    main_lower_machine_loop()