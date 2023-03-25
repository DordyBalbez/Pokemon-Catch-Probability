import numpy as np
import ctypes
import win32process
import win32ui
import tkinter as tk
from ReadWriteMemory import ReadWriteMemory


class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("500x200")
        self.root.title('Pokémon Catch Probability Calculator')

        self.running = False

        self.label = tk.Label(self.root, text='', font=('Arial', 16))
        self.label.pack(pady=10)

        self.button = tk.Button(self.root, text="S'go", command=self.start)
        self.button.place(x = 50, y = 150)

        self.button = tk.Button(self.root, text="enough..", command=self.stop)
        self.button.place(x = 375, y = 150)

        self.root.after(500, self.task)
        self.root.mainloop()

    def task(self):
        if self.running:
            self.label.config(text='', font=('Arial', 16))
            self.label.config(text=self.sort())
        self.root.after(500, self.task)

    def start(self):
        self.running = True
        return self.running

    def stop(self):
        self.label.config(text='', font=('Arial', 16))
        self.running = False
        return self.running

    def sort(self):
        self.P = self.get_probability()
        ball = np.array(["Pokéball", "Greatball", "Ultraball"])
        sort_ball = np.argsort(-self.P)
        ball = ball[sort_ball]
        self.output = np.vstack([-np.sort(-self.P), ball])
        probs, balls = self.output
        p1, p2, p3 = probs
        b1, b2, b3 = balls
        self.output = str(b1) + ": " + str(p1) + "%\n" + str(b2) + ": " + str(p2) + "%\n" + str(b3) + ": " + str(p3) + "%"
        self.label.config(text=self.output)

    def get_probability(self):
        self.HP, self.HP_max, self.catch_rate, self.status = self.get_variables()
        balls = np.array([255, 200, 150])
        ball_modifier = np.array([12, 8, 12])
        self.P = (self.status + 1) / (balls + 1) + ((np.minimum(self.catch_rate + 1, balls - self.status)) * (
                1 + np.minimum(255, np.floor(
                    np.floor(255 * self.HP_max / ball_modifier) / max(1, np.floor(self.HP / 4)))))) / (
                                   256 * (balls + 1))
        self.P = np.round(100*self.P, 2)
        return self.P

    def get_variables(self):
        process_all_access = 0x1F0FFF
        hwnd, yellow, nihon = self.get_hwnd()
        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        process_handle = ctypes.windll.kernel32.OpenProcess(process_all_access, False, pid)
        base_address = win32process.EnumProcessModulesEx(process_handle, 0x02)[0]

        base_address = int((ctypes.c_int64(base_address).value + 0x2758E30))
        rwm = ReadWriteMemory()
        process = rwm.get_process_by_name("visualboyadvance-m.exe")
        process.open()
        if nihon:
            current_health_pointer = process.get_pointer(base_address, [0xFCE])
            max_health_pointer = process.get_pointer(base_address, [0xD25])
            catch_rate_pointer = process.get_pointer(base_address, [0xFD3])
            status_pointer = process.get_pointer(base_address, [0xFD0])
        else:
            if yellow:
                current_health_pointer = process.get_pointer(base_address, [0xFE6])
                max_health_pointer = process.get_pointer(base_address, [0xD24])
                catch_rate_pointer = process.get_pointer(base_address, [0xFEB])
                status_pointer = process.get_pointer(base_address, [0xFE8])
            else:
                current_health_pointer = process.get_pointer(base_address, [0xFE7])
                max_health_pointer = process.get_pointer(base_address, [0xD25])
                catch_rate_pointer = process.get_pointer(base_address, [0xFEC])
                status_pointer = process.get_pointer(base_address, [0xFE9])

        self.hp = process.read(current_health_pointer) & 0xffff
        self.hp_max = process.read(max_health_pointer) & 0xffff
        self.catch_rate = process.read(catch_rate_pointer) & 0xff
        self.status = process.read(status_pointer) & 0xff

        if self.status == 0:
            pass
        elif self.status in {0b1000, 0b10000, 0b1000000}:
            self.status = 12
        elif self.status in {0b1, 0b10, 0b100, 0b100000}:
            self.status = 25

        process.close()
        return self.hp, self.hp_max, self.catch_rate, self.status

    def get_hwnd(self):
        yellow = False
        nihon = False
        try:
            self.hwnd = win32ui.FindWindow(None, u"Pokemon Red - VisualBoyAdvance-M 2.1.5").GetSafeHwnd()
        except win32ui.error:
            pass
        try:
            self.hwnd = win32ui.FindWindow(None, u"Pokemon Blue - VisualBoyAdvance-M 2.1.5").GetSafeHwnd()
        except win32ui.error:
            pass
        try:
            self.hwnd = win32ui.FindWindow(None, u"Pokemon - Yellow Version - VisualBoyAdvance-M 2.1.5").GetSafeHwnd()
            yellow = True
        except win32ui.error:
            pass
        try:
            self.hwnd = win32ui.FindWindow(None, u"Pocket Monsters - Red Version - VisualBoyAdvance-M 2.1.5").GetSafeHwnd()
            nihon = True
        except win32ui.error:
            pass
        try:
            self.hwnd = win32ui.FindWindow(None, u"Pocket Monsters - Green Version - VisualBoyAdvance-M 2.1.5").GetSafeHwnd()
            nihon = True
        except win32ui.error:
            pass
        try:
            self.hwnd = win32ui.FindWindow(None, u"Pocket Monsters - Blue Version - VisualBoyAdvance-M 2.1.5").GetSafeHwnd()
            nihon = True
        except win32ui.error:
            pass
        return self.hwnd, yellow, nihon


GUI()
