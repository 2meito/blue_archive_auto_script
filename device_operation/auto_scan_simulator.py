import re
import psutil

from .bluestacks_module import get_bluestacks_nxt_adb_port_id, return_bluestacks_type
from .get_adb_address import get_simulator_port
from .simulator_native import process_native_api

# 模拟器列表定义为全局变量
SIMULATOR_LISTS = {
    'bluestacks_nxt': ['hd-player.exe'],
    'yeshen': ['nox.exe'],
    'mumu': ['mumuplayer.exe'],
    'leidian': ['dnplayer.exe'],
    'xiaoyao_nat': ['memu.exe']
    # 添加其他模拟器的名称和对应进程名
}


def get_running_processes():
    process_list = []

    for process in psutil.process_iter(['pid', 'name']):
        process_list.append(process.info)

    return process_list


def check_simulator(process_name, simulator_lists):
    for simulator, names in simulator_lists.items():
        if process_name.lower() in names:
            return simulator
    return None


def auto_scan_simulators():
    simulator_list = []
    running_processes = get_running_processes()

    for process in running_processes:
        process_name = process['name'].lower()
        simulator = check_simulator(process_name, SIMULATOR_LISTS)
        if simulator:
            if process_name == 'hd-player.exe':
                pid = process['pid']
                bluestacks_type = return_bluestacks_type(pid)
                if bluestacks_type:
                    simulator_list.append(bluestacks_type)
            else:
                simulator_list.append(simulator)
    return simulator_list
def auto_search_adb_address():
    
    # 正则表达式匹配模板
    regex_patterns = {
    'MEmu.exe': r'.*MEmu.exe\s+MEmu_(\w+)',
    'HD-Player.exe': r'.*HD-Player.exe\s+--instance\s+(\w+)',
    'dnplayer.exe': r'.*dnplayer.exe\s+index=(\w+)',
    'MuMuPlayer.exe': r'.*MuMuPlayer.exe\s+-v\s+(\w+)'
    }


    adb_addresses = []
    process_list = auto_scan_simulators()

    def bst_read_install_key(region):
        key_path = f"SOFTWARE\\BlueStacks_nxt{region}"
        value_name = "InstallDir"
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
                return value + 'HD-Player.exe'
        except:
            return None

    for process in process_list:
        for process_name in SIMULATOR_LISTS[process]:
            match = None
            cmdlines = process_native_api("get_command_line_name", process_name)
            for cmdline in cmdlines:
                cmdline_no_quotes = cmdline.replace('"', '')
                for simulator, pattern in regex_patterns.items():
                    cmdline = cmdline.replace('"', '')
                    match = re.search(pattern, cmdline_no_quotes)
                    if match:
                        multi_instance = match.group(1)
                        if process == 'bluestacks_nxt':
                            bst_cn_path = bst_read_install_key('_cn')
                            bst_path = bst_read_install_key('')
                            player_path = process_native_api("get_exe_path_name", "HD-Player.exe")

                            if bst_cn_path == player_path:
                                adb_address = f"""127.0.0.1:{get_bluestacks_nxt_adb_port_id(multi_instance, "_cn")}"""
                                adb_addresses.append(adb_address)
                                break
                            elif bst_path == player_path:
                                adb_address = f"""127.0.0.1:{get_bluestacks_nxt_adb_port_id(multi_instance)}""" # 获取并拼接
                                adb_addresses.append(adb_address)
                                break
                        else:
                            adb_address = get_simulator_port(process, multi_instance)
                        adb_addresses.append(adb_address)
                if match == None:
                    adb_address = get_simulator_port(process, None)
                    adb_addresses.append(adb_address)
            match = None
    def remove_duplicates(lst):
        pattern = re.compile(r'^[\d\[\]:.]+$')
        lst = [item for item in lst if pattern.match(item)]
        return list(dict.fromkeys(lst))

    return remove_duplicates(adb_addresses)
