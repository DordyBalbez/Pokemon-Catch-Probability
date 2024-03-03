import numpy as np
import pandas as pd
import ctypes
import win32process
import win32gui
import ctypes.wintypes
from pywintypes import error
import tkinter as tk

def get_hwnd() -> tuple:
    read = pd.read_csv("Pokeman.csv", delimiter=",")
    hwnds = []
    try:
        for i in read.columns:
            hwnds.append(win32gui.FindwindowsEx(None, None, None, i))
        idx = int=(np.nonzero(hwnds)[0])
    except TypeError:                       # TODO find t for root.after(t) s.t. I dont need the exception
        while True:
            for i in read.columns:
                hwnds.append(win32gui.FindWindowEx(None, None, None, i))
            if len(np.nonzero(hwnds)[0]) == 1:
                idx = int(np.nonzero(hwnds)[0])
                hwnd = hwnds[idx]
                break
    else:
        offsets = []
        for j in range(4):
            x = read[read.columns[idx]][j]
            offsets.append(eval(x))
        exe = read[read.columns[idx]][4]
        offsetOS = eval(read[read.columns[idx]][5])
        genBool = eval(read[read.columns[idx]][6])
    return hwnd, offsets, exe, offsetOS, genBool

def readAddr(Addr: int, handle: int) -> ctypes.c_uint64:
    readBuffer = ctypes.c_uint64()
    lpBuffer = ctypes.byref(readBuffer)
    nSize = ctypes.sizeof(readBuffer)
    lpNumBytes = ctypes.c_ulong(0)
    ctypes.windll.kernel32.ReadProcessMemory(handle, ctypes.c_void_p(Addr), lpBuffer,
                                                nSize, lpNumBytes)
    return readBuffer.value

def getVars() -> tuple:
    vipAccess = 0x1F0FFF
    hwnd, offsets, exe, offsetOS, genBool = get_hwnd()
    pid = win32process.GetWindowThreadProcessID(hwnd)[1]
    processHandle = ctypes.windll.kernel32.OpenProcess(vipAccess, False, pid)
    baseAddr = win32process.EnumProcessModulesEx(processHandle, 0x02)[0]
    baseAddr = int((ctypes.c_int64(baseAddr).value + offsetOS))
    tempAddr = readAddr(baseAddr, processHandle)
    vars = []
    for offset in offsets:
        ptr = int(str(tempAddr), 0) + int(str(offset), 0)
        tempAddr = read(ptr, processHandle)
        var = tempAddr
        vars.append(var)
    hp, hpMax, catchRate, status = vars
    ctypes.windll.kernel32.CloseHandle(processHandle)
    return hp & 0xFFFF, hpMax & 0xFFFF, catchRate & 0xFF, status & 0xFF, genBool 

def calcProbs(hp: int, hpMax: int, catchRate: int, status: int, genBool: tuple) -> np.ndarray:
    gen1, gen2 = genBool
    if gen1:
        if status == 0:
            pass
        elif status in {0b1000, 0b10000, 0b1000000}:
            status = 12
        elif status in {0b1, 0b10, 0b100, 0b100000}:
            status = 25
        balls = np.array([255, 200, 150])
        ballMod = np.array([12, 8, 12])
        probs = (status + 1) / (balls + 1) + ((np.minimum(catchRate + 1, balls - status)) * (
                1 + np.minimum(255, np.floor(
            np.floor(255 * hpMax / ballMod) / max(1, np.floor(hp / 4)))))) / (
                            256 * (balls + 1))
        probs = np.round(100 * probs, 2)
    elif gen2:
        denom = 3 * hpMax
        numTerm = 2 * hp
        if hpMax > 85:
            denom = np.floor(0.5 * np.floor(0.5 * denom))
            numTerm = np.floor(0.5 * np.floor(0.5 * numTerm))
        if hpMax == 0:
            hpMax = 1
        if status == 0:
            pass
        elif status in {0b1, 0b10, 0b100000}:
            status = 10
        balls = np.array([catchRate, 1.5 * catchRate, 2 * catchRate])
        calc = np.floor(((3 * hpMax - numTerm) * balls) / denom)
        probs = np.minimum((np.maximum(calc, 1) + status), 255)
        probs = 100 * np.round(probs, 2)
    return probs

def sortProbs() -> None:
    hp, hpMax, catchRate, status, genBool = getVars()
    probArray = calcProbs(hp, hpMax, catchRate, status, genBool)
    ballArray = np.array(["Pokéball", "Greatball", "Ultraball"])
    sortBall = np.argsort(-probs)
    ballArray = ballArray[sortBall]
    output = np.vstack([-np.sort(-probArray), ballArray])
    probs, balls = output
    p1, p2, p3 = probs
    b1, b2, b3 = balls
    outputStr = f"""
    {b1}: {p1}%\n
    {b2}: {p2}%\n
    {b3}: {p3}%
    """
    label.config(text=outputStr)

def start() -> bool:
    running = True
    return running

def stop() -> bool:
    running = False
    return running

def task() -> None:
    if running:
        label.config(text="", font=("Arial", 16))
        try:
            label.config(text=sortProbs())
        except(error, NameError):
            running = False
    root.after(500, task)

root = tk.Tk()
root.geometry("500x200")
root.title("Pokémon Catch Probability Calculator")
running = False
label = tk.Label(root, text="", font=("Arial", 16))
label.pack(pady=10)
button = tk.Button(root, text="S'go", command=start)
button.place(x=50, y=150)
button=tk.Button(root, text="Thats enough.", command=stop)
button.place(x=375, y=150)
root.after(500, task)
root.mainloop()
