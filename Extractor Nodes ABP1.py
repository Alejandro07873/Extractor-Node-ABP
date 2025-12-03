import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import scrolledtext
import json
import os
import re
import ctypes
import sys

import ScriptExtractor1  
if getattr(sys, "frozen", False):
    dnd_path = os.path.join(sys._MEIPASS, "tkinterdnd2")
    if os.path.exists(dnd_path):
        os.environ["TKDND_LIBRARY"] = os.path.join(dnd_path, "tkdnd2.8")


try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except Exception as e:
    print("⚠ Drag & Drop disabled:", e)
    DND_AVAILABLE = False


if getattr(sys, "frozen", False):

    BASE_DIR = os.path.dirname(sys.executable)
else:

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = ""
ICON_PATH = r"C:\Users\Admin\Documents\icon2.ico"


CONFIG_FILE = os.path.join(BASE_DIR, "output_config.txt")



def load_saved_output_dir():
    global OUTPUT_DIR
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = f.read().strip()
                if os.path.isdir(saved):
                    OUTPUT_DIR = saved
        except:
            pass


def save_output_dir(path):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(path)
    except:
        pass


CHAR_MAP = {
    "001": "Izuku", "002": "Bakugo", "003": "Uravity", "004": "Shoto", "005": "Ida",
    "006": "Froppy", "007": "Denki", "008": "Kirishima", "009": "Jiro", "010": "Momo",
    "011": "Tokoyami", "012": "All Might", "013": "Aizawa", "014": "Gran Torino",
    "015": "Shigaraki", "016": "All For One", "017": "Dabi", "018": "Toga", "019": "Stain",
    "020": "Muscular", "022": "Inasa Yoarashi", "023": "Endeavor", "024": "Mirio",
    "025": "Nejire", "026": "Tamaki", "027": "Mina", "028": "Mineta", "029": "Camie",
    "030": "Seiji", "031": "Nighteye", "032": "Gang Orca", "033": "FatGum",
    "034": "Overhaul", "036": "Rappa", "037": "Twice", "038": "Compress",
    "043": "Hawks", "044": "Gentle", "045": "Mei Hatsume", "046": "Kendo",
    "047": "Tetsutetsu", "093": "La Brava", "100": "Mount Lady", "101": "Cementoss",
    "102": "Ibara", "103": "Kurogiri", "104": "Monoma", "105": "Shinso",
    "109": "Present Mic", "110": "Sero", "111": "Mirko", "112": "Hood",
    "113": "Midnight", "115": "Lady Nagant", "201": "All For One New", "202": "Deku OFA",
    "501": "Masculine", "502": "Female", "503": "Kota"
}


def seleccionar_json():
    archivo = filedialog.askopenfilename(
        title="Select JSON file",
        filetypes=[("JSON Files", "*.json")]
    )
    if archivo:
        entry_json.delete(0, tk.END)
        entry_json.insert(0, archivo)


def elegir_carpeta_salida():
    global OUTPUT_DIR
    carpeta = filedialog.askdirectory(title="Select folder to save TXT")
    if carpeta:
        OUTPUT_DIR = carpeta
        save_output_dir(carpeta)
        lbl_output.config(text=f"Selected folder:\n{OUTPUT_DIR}")


def abrir_txt():
    if OUTPUT_DIR == "":
        messagebox.showerror("Error", "You haven't generated any file yet.")
        return

    archivo = filedialog.askopenfilename(initialdir=OUTPUT_DIR,
                                         filetypes=[("TXT", "*.txt")])
    if archivo:
        os.startfile(archivo)


def mostrar_ayuda():
    messagebox.showinfo(
        "Help",
        "How to use the extractor:\n\n"
        "1. Export an ABP from FModel.\n"
        "2. Save it as JSON.\n"
        "3. Drag the JSON into the app or browse it.\n"
        "4. Press 'Generate TXT'.\n"
        "5. The file will be saved with the character name.\n"
        "6. In Unreal → AnimBlueprint → AnimGraph → press CTRL + V.\n"
    )


def detectar_anim_class(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for obj in data:
            if isinstance(obj, dict) and "Outer" in obj:
                outer = obj["Outer"]
                if isinstance(outer, str) and outer.endswith("_C"):
                    return outer

    except Exception as e:
        print("Error detecting ABP:", e)

    return None

def ejecutar_script():
    global OUTPUT_DIR

    log_box.delete("1.0", "end")
    log_box.insert("end", "Processing JSON...\n","Processing")

    json_path = entry_json.get()
    if not json_path or not os.path.exists(json_path):
        messagebox.showerror("Error", "Select a valid JSON file.","error")
        return

    if OUTPUT_DIR == "":
        messagebox.showerror("Error", "Select a folder to save the TXT file.","error")
        return

    anim_bp_class = detectar_anim_class(json_path) or "ABP_Default_C"

    match = re.search(r"Ch(\d{3})", anim_bp_class or "")
    personaje = CHAR_MAP.get(match.group(1), "Custom Abp") if match else "Custom Abp"

    output_name = f"{personaje}.txt"
    output_path = os.path.join(OUTPUT_DIR, output_name).replace("\\", "/")

    log_box.insert("end", f"Detected character: ", "char")
    log_box.insert("end", personaje + "\n","Personaje")
    log_box.insert("end", f"ABP Class:", "aclass")
    log_box.insert("end", anim_bp_class + "\n","Class")
    log_box.insert("end", "Running script⚙️...\n", "running")

    try:
       
        ScriptExtractor1.run_extractor(json_path, output_path, anim_bp_class)

        log_box.insert("end", "✅ Export completed.\n", "success")
        log_box.insert("end", "Generated file 🖥️: ", "char")
        log_box.insert("end", output_path + "\n")

    except Exception as e:
        log_box.insert("end", f"❌ ERROR:\n{e}\n", "error")

    log_box.see("end")

root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
root.title("Extractor Nodes ABP Kota")
root.geometry("600x480")
root.configure(bg="#1e1e1e")

load_saved_output_dir()

try:
    root.iconbitmap(ICON_PATH)
except:
    pass

try:
    HWND = ctypes.windll.user32.GetParent(root.winfo_id())
    ctypes.windll.dwmapi.DwmSetWindowAttribute(HWND, 20, ctypes.byref(ctypes.c_int(1)), 4)
except:
    pass

tk.Label(root, text="Select or drag your (ABP_Ch00.json) : ",
         bg="#1e1e1e", fg="white").pack(pady=10)

entry_json = tk.Entry(root, width=60, bg="#2d2d2d",
                      fg="#007acc", insertbackground="#00ffcc")
entry_json.pack()

if DND_AVAILABLE:
    entry_json.drop_target_register(DND_FILES)

    def drop_archivo(event):
        archivo = event.data.strip("{}")
        if archivo.lower().endswith(".json"):
            entry_json.delete(0, tk.END)
            entry_json.insert(0, archivo)

    entry_json.dnd_bind("<<Drop>>", drop_archivo)

frame = tk.Frame(root, bg="#1e1e1e")
frame.pack(pady=10)

tk.Button(frame, text="📂 Browse JSON", command=seleccionar_json,
          bg="#3c3c3c", fg="white", width=18).grid(row=0, column=0, padx=8)
tk.Button(frame, text="📁 Select Folder", command=elegir_carpeta_salida,
          bg="#007acc", fg="Black", width=18).grid(row=0, column=1, padx=8)

tk.Button(root, text="⚙️ Generate TXT", command=ejecutar_script,
          bg="#007acc", fg="Black", width=20).pack(pady=10)
tk.Button(root, text="📄 Open Generated TXT", command=abrir_txt,
          bg="#444", fg="white", width=20).pack()

lbl_output = tk.Label(
    root,
    text=("Selected folder:\n" + OUTPUT_DIR) if OUTPUT_DIR else "No folder selected",
    bg="#1e1e1e",
    fg="#fcd53f"
)
lbl_output.pack(pady=5)

log_box = scrolledtext.ScrolledText(
    root,
    height=8,
    bg="#111111",
    fg="#007acc",
    insertbackground="#00ffcc",
    relief="flat",
    borderwidth=1
)
log_box.pack(fill="x", padx=20, pady=10)
log_box.insert("end", "Waiting for file 💽 ...\n")

log_box.tag_config("Processing",    foreground="#00FF2A")  
log_box.tag_config("info",    foreground="#00e5ff")  
log_box.tag_config("char",    foreground="#fcd53f")  
log_box.tag_config("aclass",  foreground="#ff6bff")  
log_box.tag_config("running", foreground="#22d3ee")  
log_box.tag_config("success", foreground="#39ff14")  
log_box.tag_config("error",   foreground="#ff4b4b")  
log_box.tag_config("Personaje",   foreground="#d9aa8f")
log_box.tag_config("Class",   foreground="#00aca3") 

tk.Button(root, text="❓ Help", command=mostrar_ayuda,
          bg="#555", fg="white", width=20).pack(pady=5)

tk.Label(root, text="Made by Alejandro (aweooppoe)",
         bg="#1e1e1e", fg="#007acc").pack(side="bottom", pady=10)

root.mainloop()
