#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: Liu Jiang
# Python 3.5

"""
MyFtp服务器核心模块，实现了cd/dir/ls/mkdir/rm/du/get/put/help等功能。
"""
import os
import json
import shutil
import logging
import hashlib
import socketserver
from conf import settings


class MyServer(socketserver.BaseRequestHandler):
    """
    继承socketserver.BaseRequestHandler
    """
    def handle(self):
        """
        核心处理方法
        :return:
        """
        while True:
            try:
                # 接收客户端发来的信息，并加以分析
                cmd = self.request.recv(4096).decode()
                # 客户端正常断开
                if cmd in ["exit", "bye", "quit"]:
                    # 将用户名从已登陆列表内移除
                    LoginUser.del_user(self.current_user)
                    print("来自%s:%s的客户端主动断开连接..." % (self.client_address[0], self.client_address[1]))
                    # 添加日志
                    MyLogger.get_logout_instance("logout").info("%s  from %s:%s" %
                                                               (self.current_user, self.client_address[0],
                                                                self.client_address[1]))
                    break
                if not cmd:
                    print("客户端指令为空！")
                    break
                # 一切正常时，调用cmd_call方法
                self.cmd_call(cmd)
            except Exception as e:
                print(e)
                LoginUser.del_user(self.current_user)
                MyLogger.get_logout_instance("logout").info("%s  from %s:%s" %
                                                           (self.current_user, self.client_address[0],
                                                            self.client_address[1]))
                print("来自%s:%s的客户端主动断开连接..." % (self.client_address[0], self.client_address[1]))
                break

    def cmd_call(self, cmd_str):
        """
        指令分发机构，根据字符串反射相应的方法
        :param cmd_str: 命令参数
        :return:
        """
        # 对客户端发送过来的json数据进行解析
        cmd_dict = json.loads(cmd_str)
        # 获取命令动作
        command = cmd_dict["action"]
        if hasattr(self, command):
            func = getattr(self, command)
            # 调用对应的方法
            func(cmd_dict)
        else:
            print("错误的指令")

    def login(self, cmd_dict):
        """
        登录功能
        :param cmd_dict: 命令参数
        :return:
        """
        # 分析命令字典的数据
        name = cmd_dict["user_name"]
        password = cmd_dict["password"]
        if not os.path.exists(settings.USER_FILE):
            confirm = "201"
        else:
            if os.stat(settings.USER_FILE).st_size == 0:
                confirm = "201"
            else:
                with open(settings.USER_FILE) as f:
                    user_dict = json.load(f)
                # 过滤掉无效的用户、密码错误和已经登录三种状态
                if name not in user_dict:
                    confirm = "201"
                elif user_dict[name]["password"] != password:
                    confirm = "201"
                elif name in LoginUser.get_user():
                    confirm = "202"
                else:
                    # 当一切正常时，动态生成当前用户、用户磁盘配额、用户家目录三个属性
                    confirm = "200"
                    self.current_user = name
                    self.current_quota = user_dict[name]["quota"]
                    self.current_path = os.path.join(settings.USER_HOME_DIR, self.current_user)
                    self.base_path = os.path.join(settings.USER_HOME_DIR, self.current_user)
                    # 将用户加入已登陆列表，添加登陆日志
                    LoginUser.add_user(name)
                    MyLogger.get_login_instance("login").info("%s  from %s:%s" %
                                                    (self.current_user, self.client_address[0], self.client_address[1]))
        self.request.sendall(confirm.encode())

    def dir(self, cmd_dict):
        """
        查看目录
        :param cmd_dict: 命令参数
        :return:
        """
        # 进行路径拼接和分析判断，限制客户端不能访问家目录以外的目录
        base_path = os.path.join(settings.USER_HOME_DIR, self.current_user)
        if cmd_dict["path"].startswith("/"):
            path = os.path.join(base_path, cmd_dict["path"].lstrip("/"))
        else:
            path = os.path.join(self.current_path, cmd_dict["path"])
        path = os.path.abspath(path)
        if not path.startswith(base_path):
            self.request.sendall(json.dumps("401").encode())
            return
        if not os.path.exists(path):
            self.request.sendall(json.dumps("401").encode())
            return
        # 获得指定目录下的文件结构和文件大小，并以“d“和”f“的方式区分文件和目录
        dir_list = os.listdir(path)
        data_list = []
        for i in dir_list:
            file_path = os.path.join(path, i)
            list_1 = []
            if os.path.isdir(file_path):
                list_1.append("d")
                list_1.append(i)
                data_list.append(list_1)
            else:
                file_size = os.stat(file_path).st_size
                list_1.append("f")
                list_1.append(i)
                list_1.append(file_size)
                data_list.append(list_1)
        # 将生成的数据列表以json的格式发送给客户端
        json_str = json.dumps(data_list)
        self.request.sendall(json_str.encode())

    def cd(self, cmd_dict):
        """
        路径切换
        :param cmd_dict: 命令参数
        :return:
        """
        # 进行路径拼接和分析判断，限制客户端不能访问家目录以外的目录
        base_path = os.path.join(settings.USER_HOME_DIR, self.current_user)
        if cmd_dict["path"].startswith("/"):
            path = os.path.join(base_path, cmd_dict["path"].lstrip("/"))
        else:
            path = os.path.join(self.current_path, cmd_dict["path"])
        path = os.path.abspath(path)
        if not os.path.exists(path):
            self.request.sendall("401".encode())
            return
        if not path.startswith(base_path):
            self.request.sendall("401".encode())
            return
        # 修改当前目录
        self.current_path = path
        # 截取相对路径字符串，并将其发送给客户端
        relative_path = path.replace(base_path, "")
        if not relative_path:
            relative_path = os.sep
        self.request.sendall(relative_path.encode())

    def mkdir(self, cmd_dict):
        """
        新建目录
        :param cmd_dict: 命令参数
        :return:
        """
        # 进行路径拼接和分析判断，限制客户端不能访问家目录以外的目录
        if cmd_dict["path"].startswith("/"):
            dir_path = os.path.join(self.base_path, cmd_dict["path"].lstrip("/"))
        else:
            dir_path = os.path.join(self.current_path, cmd_dict["path"])
        dir_path = os.path.abspath(dir_path)
        if not dir_path.startswith(self.base_path):
            self.request.sendall("401".encode())
            return
        if os.path.exists(dir_path):
            self.request.sendall("305".encode())
            return
        os.makedirs(dir_path)
        self.request.sendall("308".encode())

    def du(self, cmd_dict):
        """
        查询磁盘配额使用情况
        :param cmd_dict:
        :return:
        """
        path = os.path.join(settings.USER_HOME_DIR, self.current_user)
        # 递归遍历家目录下的所有目录和文件，计算文件大小的总和
        size = 0
        for root, dirs, files in os.walk(path):
            size += sum([os.stat(os.path.join(root, name)).st_size for name in files])
        free_size = (int(self.current_quota)*1024**3 - size)/1024**2
        mb_size = size / 1024 / 1024
        msg = "当前已用空间：%.2f MB\n当前可用空间：%.2f MB\n用户磁盘限额： %sGB"\
              % (mb_size, free_size, self.current_quota)
        self.request.sendall(msg.encode())

    def get(self, cmd_dict):
        """
        下载文件，支持断点续传
        :param cmd_dict: 命令参数
        :return:
        """
        # 分析指令字典的内容，判断路径和文件的正确与否，存在与否
        src_path = cmd_dict["file_path"]
        if src_path.startswith("/"):
            file_path = os.path.join(self.base_path, src_path.lstrip("/"))
        else:
            file_path = os.path.join(self.current_path, src_path)
        if not os.path.isfile(file_path):
            self.request.sendall("404".encode())
            return
        if not file_path.startswith(self.base_path):
            self.request.sendall("401".encode())
            return
        # 获取文件大小和MD5码
        file_size = os.stat(file_path).st_size
        hash_obj = hashlib.md5()
        with open(file_path, "rb") as f:
            while True:
                data = f.read(4096)
                if not data:
                    break
                hash_obj.update(data)
        md5_str = hash_obj.hexdigest()
        print(md5_str)
        # 生成消息字典，发送给客户端，并等待回应
        file_info = {
            "file_size": file_size,
            "md5": md5_str
        }
        json_str = json.dumps(file_info)
        self.request.sendall(json_str.encode())
        confirm = self.request.recv(1024).decode()
        # 判断是否有未完成的任务
        transfered_data = 0
        if confirm.startswith("402"):
            print("发现未完成的任务，继续上次任务！")
            transfered_data = int(confirm.split(":")[1])
            confirm = self.request.recv(1024).decode()
        # 如果一切正常，开始发送文件
        if confirm == "301":
            with open(file_path, "rb") as f:
                f.seek(transfered_data)
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    self.request.sendall(data)
        # 确认文件发送成功
        confirm = self.request.recv(1024).decode()
        if confirm == "306":
            print(settings.RESPONSE_CODE["306"])
            # 添加日志
            MyLogger.get_download_instance("download").info(("%s  from %s:%s download %s" %
                                                     (self.current_user, self.client_address[0],
                                                      self.client_address[1], os.path.basename(file_path))))
        else:
            print(settings.RESPONSE_CODE["307"])

    def put(self, cmd_dict):
        # 分析指令字典的内容
        file_name = cmd_dict["file_name"]
        file_size = cmd_dict["size"]
        dst_path = cmd_dict["dst_path"]
        # 判断磁盘限额是否足够
        used_size = 0
        for root, dirs, files in os.walk(self.base_path):
            used_size += sum([os.stat(os.path.join(root, name)).st_size for name in files])
        if file_size > (int(self.current_quota)*1024**3 - used_size):
            print("磁盘容量不足，拒绝上传！")
            self.request.sendall("400".encode())
            return
        # 分析文件路径
        if not dst_path:
            file_path = os.path.join(self.current_path, file_name)
        elif dst_path.startswith("/"):
            file_path = os.path.join(self.base_path, dst_path.lstrip("/"))
            if os.path.exists(os.path.dirname(file_path)):
                if os.path.isdir(file_path):
                    file_path = os.path.join(file_path, file_name)
            else:
                self.request.sendall("401".encode())
                return
        else:
            file_path = os.path.join(self.current_path, dst_path)
            if os.path.exists(os.path.dirname(file_path)):
                if os.path.isdir(file_path):
                    file_path = os.path.join(file_path, file_name)
            else:
                self.request.sendall("401".encode())
                return
        file_path = os.path.abspath(file_path)
        if not file_path.startswith(self.base_path):
            self.request.sendall("401".encode())
            return
        # 判断目标文件是否存在
        if os.path.exists(file_path):
            self.request.sendall("304".encode())
            confirm = self.request.recv(1024).decode()
            if confirm == "abort":
                print("客户端放弃传输文件")
                return
        # 设定临时文件
        temp_home = os.path.join(self.base_path, ".tmp")
        if not os.path.exists(temp_home):
            os.makedirs(temp_home)
        temp_file = os.path.join(temp_home, cmd_dict["md5"])
        # 判断是否有未完成的上传任务
        if os.path.exists(temp_file):
            print("发现未完成的上传任务")
            temp_size = os.stat(temp_file).st_size
            file_size -= temp_size
            msg = "402:%s" % temp_size
            self.request.sendall(msg.encode())
        # 如果一切正常，开始接收文件
        self.request.sendall("303".encode())
        with open(temp_file, "ab") as w:
            recv_size = 0
            while recv_size < file_size:
                data = self.request.recv(4096)
                w.write(data)
                recv_size += len(data)
        # 生成MD5值
        hash_obj = hashlib.md5()
        with open(temp_file, "rb") as f:
            while True:
                data = f.read(4096)
                if not data:
                    break
                hash_obj.update(data)
        md5_str = hash_obj.hexdigest()
        print(md5_str)
        # 进行MD5值对比
        if md5_str == cmd_dict["md5"]:
            shutil.copyfile(temp_file, file_path)
            os.remove(temp_file)
            confirm = "306"
            print(settings.RESPONSE_CODE["306"])
            self.request.sendall(confirm.encode())
            MyLogger.get_upload_instance("upload").info(("%s  from %s:%s upload %s" %
                                                    (self.current_user, self.client_address[0],
                                                     self.client_address[1], os.path.basename(file_path))))
        else:
            confirm = "307"
            print(settings.RESPONSE_CODE["307"])
            self.request.sendall(confirm.encode())

    def rm(self, cmd_dict):
        # 对处理后的路径进行进一步过滤
        path = self.path_handler(cmd_dict["path"])
        if not path:
            return
        if path == self.base_path:
            print("不能删除家目录")
            self.request.sendall("401".encode())
            return
        # 删除指定的目录或文件
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        # 如果正好将当前路径也删除了
        if not os.path.exists(self.current_path):
            self.current_path = self.base_path
            self.request.sendall("311".encode())
            print("311", settings.RESPONSE_CODE["311"])
            return
        # 一切正常则返回310
        print("310", settings.RESPONSE_CODE["310"])
        self.request.sendall("310".encode())

    def path_handler(self, path):
        if path.startswith("/"):
            path = os.path.join(self.base_path, path.lstrip("/"))
        else:
            path = os.path.join(self.current_path, path)
        final_path = os.path.abspath(path)
        if not os.path.exists(final_path):
            self.request.sendall("404".encode())
            return
        if not final_path.startswith(self.base_path):
            self.request.sendall("401".encode())
            return
        return final_path


class LoginUser:
    """
    用于保存已登陆的用户名，防止重复登陆。
    """
    __login_user = []

    @staticmethod
    def add_user(name):
        LoginUser.__login_user.append(name)

    @staticmethod
    def del_user(name):
        LoginUser.__login_user.remove(name)

    @staticmethod
    def get_user():
        return LoginUser.__login_user


class MyLogger:
    """
    用于生成四种日志对象，每种只能有一个，即单例模式。
    """
    __login = None
    __logout = None
    __upload = None
    __download = None

    # 单例模式
    @classmethod
    def get_login_instance(cls, log_type):
        if cls.__login:
            return cls.__login
        else:
            obj = MyLogger.make_logger(log_type)
            cls.__login = obj
            return obj

    @classmethod
    def get_logout_instance(cls, log_type):
        if cls.__logout:
            return cls.__logout
        else:
            obj = MyLogger.make_logger(log_type)
            cls.__logout = obj
            return obj

    @classmethod
    def get_upload_instance(cls, log_type):
        if cls.__upload:
            return cls.__upload
        else:
            obj = MyLogger.make_logger(log_type)
            cls.__upload = obj
            return obj

    @classmethod
    def get_download_instance(cls, log_type):
        if cls.__download:
            return cls.__download
        else:
            obj = MyLogger.make_logger(log_type)
            cls.__download = obj
            return obj

    @staticmethod
    def make_logger(log_type):
        """
        创建日志对象的函数。
        :param log_type: 对象的名字
        :return: 日志对象
        """
        # 创建logger
        logger = logging.getLogger(log_type)
        logger.setLevel(settings.LOG_LEVEL)

        # 创建要针对屏幕的handler，并设置其日志等级
        sh = logging.StreamHandler()
        sh.setLevel(settings.LOG_LEVEL)

        # 创建要针对文件的handler，并设置其日志等级
        log_file = os.path.join(settings.LOG_DIR, settings.LOG_TYPES[log_type])
        fh = logging.FileHandler(log_file)
        fh.setLevel(settings.LOG_LEVEL)

        # 创建formatter格式
        formatter = logging.Formatter(settings.FORMATTER)

        # 为先前创建好的Handlers添加formatter格式
        sh.setFormatter(formatter)
        fh.setFormatter(formatter)

        # 为一开始创建的logger添加Handlers
        logger.addHandler(sh)
        logger.addHandler(fh)
        return logger