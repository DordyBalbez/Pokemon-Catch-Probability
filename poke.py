import numpy as np
import ctypes
import win32process
import win32ui
from ctypes import *
import tkinter as tk
from ReadWriteMemory import ReadWriteMemory


class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("500x300")
        self.root.title('Pokémon Catch Probability Calculator')

        self.running = False

        self.label = tk.Label(self.root, text='', font=('Arial', 16))
        self.label.pack(pady=10)

        self.button = tk.Button(self.root, text="S'go", command=self.start)
        self.button.pack(pady=85)

        self.button = tk.Button(self.root, text="enough..", command=self.stop)
        self.button.pack()

        self.root.after(500, self.task)
        self.root.mainloop()

    def task(self):
        if self.running == True:
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
        ball = np.array(["Pokeball", "Greatball", "Ultraball"])
        sort_Ball = np.argsort(-self.P)
        ball = ball[sort_Ball]
        output = np.vstack([-np.sort(-self.P), ball])
        self.label.config(text=(output))

    def get_probability(self):
        self.HP, self.HP_max, self.C, self.S = self.get_variables()
        B = np.array([255, 200, 150])
        B_mod = np.array([12, 8, 12])
        self.P = np.round(((self.S + 1) / (B + 1) + ((np.minimum(self.C + 1, B - self.S)) * (
                1 + np.minimum(255, np.floor(np.floor(255 * self.HP_max / B_mod) / max(1, np.floor(self.HP / 4)))))) / (
                                   256 * (B + 1))), 2)
        return self.P

    def get_variables(self):
        PROCESS_ALL_ACCESS = 0x1F0FFF
        try:
            hwnd = win32ui.FindWindow(None, u"Pokemon Red - VisualBoyAdvance-M 2.1.5").GetSafeHwnd()
        except win32ui.error:
            hwnd = win32ui.FindWindow(None, u"Pokemon Blue - VisualBoyAdvance-M 2.1.5").GetSafeHwnd()
        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        processHandle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        BaseAddress = win32process.EnumProcessModules(processHandle)[0]

        base_address = int((c_int(BaseAddress).value + 0x39602E0))

        rwm = ReadWriteMemory()
        process = rwm.get_process_by_name("visualboyadvance-m.exe")
        process.open()

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


GUI()
