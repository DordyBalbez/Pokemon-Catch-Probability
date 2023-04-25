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
        hp, hp_max, catch_rate, status, bool = self.get_variables()
        gen1, gen2 = bool
        if gen1:
            probability = self.get_probability_gen1(hp, hp_max, catch_rate, status)
        elif gen2:
            probability = self.get_probability_gen2(hp, hp_max, catch_rate, status)
        ball = np.array(["Pokéball", "Greatball", "Ultraball"])
        sort_ball = np.argsort(-probability)
        ball = ball[sort_ball]
        output = np.vstack([-np.sort(-probability), ball])
        probs, balls = output
        p1, p2, p3 = probs
        b1, b2, b3 = balls
        output = str(b1) + ": " + str(p1) + "%\n" + str(b2) + ": " + str(p2) + "%\n" + str(b3) + ": " + str(p3) + "%"
        self.label.config(text=output)

    def get_probability_gen1(self, hp, hp_max, catch_rate, status):

        if status == 0:
            pass
        elif status in {0b1000, 0b10000, 0b1000000}:
            status = 12
        elif status in {0b1, 0b10, 0b100, 0b100000}:
            status = 25

        balls = np.array([255, 200, 150])
        ball_modifier = np.array([12, 8, 12])
        probability = (status + 1) / (balls + 1) + ((np.minimum(catch_rate + 1, balls - status)) * (
                1 + np.minimum(255, np.floor(
            np.floor(255 * hp_max / ball_modifier) / max(1, np.floor(hp / 4)))))) / (
                              256 * (balls + 1))
        probability = np.round(100 * probability, 2)
        return probability

    def get_probability_gen2(self, hp, hp_max, catch_rate, status):
        denom = 3 * hp_max
        num_term = 2 * hp

        if hp_max > 85:
            denom = np.floor(.5 * np.floor(.5 * denom))
            num_term = np.floor(.5 * np.floor(.5 * num_term))

        if hp_max == 0:
            hp_max = 1

        if status == 0:
            pass
        elif status in {0b1, 0b10, 0b100000}:
            status = 10

        balls = np.array([catch_rate, 1.5 * catch_rate, 2 * catch_rate])
        calc = np.floor(((3 * hp_max - num_term) * balls) / denom)
        probability = np.minimum((np.maximum(calc, 1) + status), 255)
        probability = (probability + 1) / 256
        probability = 100 * np.round(probability, 2)
        return probability



    def get_variables(self):
        process_all_access = 0x1F0FFF

        hwnd, offsets, executable, offset_os, bool = self.get_hwnd()

        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        process_handle = ctypes.windll.kernel32.OpenProcess(process_all_access, False, pid)
        base_address = win32process.EnumProcessModulesEx(process_handle, 0x02)[0]

        base_address = int((ctypes.c_int64(base_address).value + offset_os))
        rwm = ReadWriteMemory()
        process = rwm.get_process_by_name(executable)
        process.open()

        variables = []
        for k in range(len(offsets)):
            pointer = process.get_pointer(base_address, offsets[k])
            variables.append(process.read(pointer))

        hp, hp_max, catch_rate, status = variables

        process.close()
        return hp & 0xFFFF, hp_max & 0xFFFF, catch_rate & 0xFF, status & 0xFF, bool

    def get_hwnd(self):
        global hwnd
        global offsets
        global executable
        global offset_os
        global bool
        read = pd.read_csv('Pokeman.csv', delimiter=',')
        hwnds = []

        try:
            for i in read.columns:
                hwnds.append(win32gui.FindWindowEx(None, None, None, i))
            index = int(np.nonzero(hwnds)[0])
            hwnd = hwnds[index]
        except TypeError:
            while True:
                for i in read.columns:
                    hwnds.append(win32gui.FindWindowEx(None, None, None, i))
                if len(np.nonzero(hwnds)[0]) == 1:
                    index = int(np.nonzero(hwnds)[0])
                    hwnd = hwnds[index]
                    break
        else:
            offsets = []
            for j in range(4):
                a = read[read.columns[index]][j]
                offsets.append(eval(a))
            executable = read[read.columns[index]][4]
            offset_os = eval(read[read.columns[index]][5])
            bool = eval(read[read.columns[index]][6])
        return hwnd, offsets, executable, offset_os, bool

GUI()
