import numpy as np
import pandas as pd
import ctypes
import win32process
import win32gui
import ctypes.wintypes
import pywintypes
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
        self.button.place(x=50, y=150)

        self.button = tk.Button(self.root, text="enough..", command=self.stop)
        self.button.place(x=375, y=150)

        self.root.after(500, self.task)
        self.root.mainloop()

    def task(self):
        if self.running:
            self.label.config(text='', font=('Arial', 16))
            try:
                self.label.config(text=self.sort())
            except (pywintypes.error, NameError):
                self.running = False
        self.root.after(500, self.task)

    def start(self):
        self.running = True
        return self.running

    def stop(self):
        self.label.config(text='', font=('Arial', 16))
        self.running = False
        return self.running

    def sort(self):
        probability = self.get_probability()
        ball = np.array(["Pokéball", "Greatball", "Ultraball"])
        sort_ball = np.argsort(-probability)
        ball = ball[sort_ball]
        output = np.vstack([-np.sort(-probability), ball])
        probs, balls = output
        p1, p2, p3 = probs
        b1, b2, b3 = balls
        output = str(b1) + ": " + str(p1) + "%\n" + str(b2) + ": " + str(p2) + "%\n" + str(b3) + ": " + str(p3) + "%"
        self.label.config(text=output)

    def get_probability(self):
        hp, hp_max, catch_rate, status = self.get_variables()
        balls = np.array([255, 200, 150])
        ball_modifier = np.array([12, 8, 12])
        probability = (status + 1) / (balls + 1) + ((np.minimum(catch_rate + 1, balls - status)) * (
                1 + np.minimum(255, np.floor(
            np.floor(255 * hp_max / ball_modifier) / max(1, np.floor(hp / 4)))))) / (
                              256 * (balls + 1))
        probability = np.round(100 * probability, 2)
        return probability

    def get_variables(self):
        process_all_access = 0x1F0FFF
        buffer = 0x2758E30

        hwnd, offsets = self.get_hwnd()

        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        process_handle = ctypes.windll.kernel32.OpenProcess(process_all_access, False, pid)
        base_address = win32process.EnumProcessModulesEx(process_handle, 0x02)[0]

        base_address = int((ctypes.c_int64(base_address).value + buffer))
        rwm = ReadWriteMemory()
        process = rwm.get_process_by_name("visualboyadvance-m.exe")
        process.open()

        variables = []
        for k in range(len(offsets)):
            pointer = process.get_pointer(base_address, offsets[k])
            variables.append(process.read(pointer))

        hp, hp_max, catch_rate, status = variables

        if status & 0xFF == 0:
            pass
        elif status & 0xFF in {0b1000, 0b10000, 0b1000000}:
            status = 12
        elif status & 0xFF in {0b1, 0b10, 0b100, 0b100000}:
            status = 25

        process.close()
        return hp & 0xFFFF, hp_max & 0xFFFF, catch_rate & 0xFF, status & 0xFF

    def get_hwnd(self):
        global hwnd
        global offsets
        read = pd.read_csv('Pokeman.csv')
        hwnds = []
        try:
            for i in read.columns:
                hwnds.append(win32gui.FindWindowEx(None, None, None, i))
            index = int(np.nonzero(hwnds)[0])
            hwnd = hwnds[index]
        except TypeError:
            self.running = False
        else:
            offsets = []
            for j in range(4):
                a = read[read.columns[index]][j]
                offsets.append(eval(a))
        if hwnd == 0:
            self.running = False
        return hwnd, offsets


GUI()
