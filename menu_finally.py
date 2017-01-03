#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: Liu Jiang
# Python 3.5
"""
通过递归调用和栈的方法，实现N级菜单。
可接收json格式的字典为原始数据。
对非法和无效选择进行了处理，确保脚本健壮性。
可以很简单的改写为类的结构。
"""

menu_dict = {
    '北京':{
        '朝阳区':{
            '建外':{"赛特":1,
                  "建国饭店":2
                  },
            '三里屯':2,
            '亚运村':3
        },
        '海淀区':{'中关村':1,'清华园':2,'白石桥':3},
        '丰台区':{'北大地':1,'花乡桥':2,'长辛店':3},
    },
    '上海': {
        '静安区': {'江宁':1,'静安寺':2,'南京西路':3 },
        '徐汇区': {'徐家汇':1, '湖南路':2, '虹梅路':3},
        '长宁区': {'江苏路':1, '天山路':2, '华阳路':3},
    },
    '江西': {
        '南昌市': {'东湖区':1, '西湖区':2, '青云谱区':3},
        '宜春市': {'丰城市':1, '高安市':2, '樟树市':3},
        '九江市': {'庐山区':1, '瑞昌市':2, '永修县':3},
    },
    '河北': {
        '石家庄': {'正定': 1, '桥西': 2, '桥东': 3},
        '承德': {'丰宁': 1, '隆化': 2, '滦平': 3},
        '张家口': {'张北': 1, '宣化': 2, '万全': 3},
    },
}

# 保存着上一级字典的栈
choice_list = []


def print_menu(current_dict):
    # 保存本级字典键值的栈
    stack = []
    try:
        for order, key in enumerate(current_dict, 1):
            stack.append(key)
            print(order, key)
    except TypeError as ex:
        print("已经是最底层！")
        temp = choice_list.pop()
        print_menu(temp)

    choice = input("请按数字进行选择（[b]返回上级，[q]退出）： ").strip()

    if choice == "q":
        exit("bye!")
    elif choice.isdigit():
        choice = int(choice)
        if 0 < choice <= len(stack):
            choice_list.append(current_dict)
            new_dict = current_dict[stack[choice-1]]
            # 递归调用
            print_menu(new_dict)
        else:
            print("无效的选择！")
            print_menu(current_dict)
    elif choice == "b":
        if not choice_list:
            print("已经到顶层了，不可以再回退！")
            print_menu(menu_dict)
        else:
            temp = choice_list.pop()
            print_menu(temp)
    else:
        print("无效的选择！")
        print_menu(current_dict)


if __name__ == '__main__':

    print_menu(menu_dict)