import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
from PIL import Image, ImageTk
import serial
import serial.tools.list_ports
import time
import threading
import sys
import os

puerto = None
WIDTH, HEIGHT = 240, 135
SCALE = 3
WINDOW_WIDTH = WIDTH*SCALE + 40
WINDOW_HEIGHT = HEIGHT*SCALE + 100

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def center_window(window, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

def list_com_ports():
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]

def connect_com(port_name):
    global puerto
    try:
        puerto = serial.Serial(port_name, 115200, timeout=1)
        time.sleep(2)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir {port_name}\n{e}")
        return False

def send_to_esp(data):
    global puerto
    if puerto:
        puerto.write(data.encode())

def send_image(path):
    global puerto
    if not puerto:
        messagebox.showerror("Error", "No hay conexión con el ESP32")
        return

    try:
        img = Image.open(path).resize((WIDTH, HEIGHT)).convert("RGB")
        send_to_esp("IMG_START\n")
        time.sleep(0.2)

        total_pixels = WIDTH * HEIGHT
        sent = 0

        progress = tk.Toplevel()
        progress.title("Enviando imagen...")
        center_window(progress)
        label = tk.Label(progress, text="Enviando 0%")
        label.pack(padx=20, pady=20)

        for y in range(HEIGHT):
            for x in range(WIDTH):
                r, g, b = img.getpixel((x, y))
                color = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                puerto.write(color.to_bytes(2, 'big'))
                sent += 1
                if sent % 1000 == 0:
                    percent = int(sent / total_pixels * 100)
                    label.config(text=f"Enviando {percent}%")
                    progress.update_idletasks()

        send_to_esp("IMG_END\n")
        label.config(text="Imagen enviada correctamente")
        time.sleep(1)
        progress.destroy()

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo enviar la imagen\n{e}")

def open_image_mode():
    file = filedialog.askopenfilename(
        title="Selecciona una imagen",
        filetypes=[("Archivos de imagen", "*.jpg *.png *.bmp *.jpeg")]
    )
    if file:
        threading.Thread(target=send_image, args=(file,)).start()

def open_paint_window():
    menu_window.withdraw()
    send_to_esp("WHITE\n")
    time.sleep(0.2)
    send_to_esp("CLEAR\n")

    paint_window = tk.Toplevel()
    paint_window.title("Mini Paint")
    paint_window.resizable(False, False)
    center_window(paint_window)

    canvas = tk.Canvas(paint_window, width=WIDTH*SCALE, height=HEIGHT*SCALE, bg="white")
    canvas.pack(padx=10, pady=10)

    current_color = tk.StringVar(value="black")
    pen_size = tk.IntVar(value=2)
    last_x, last_y = None, None

    def draw(event):
        nonlocal last_x, last_y
        x_real = event.x // SCALE
        y_real = event.y // SCALE
        if last_x is not None and last_y is not None:
            canvas.create_line(last_x*SCALE, last_y*SCALE, x_real*SCALE, y_real*SCALE,
                               fill=current_color.get(), width=pen_size.get()*SCALE)
            send_to_esp(f"{x_real},{y_real},{current_color.get()},{pen_size.get()}\n")
        last_x, last_y = x_real, y_real

    def reset(event):
        nonlocal last_x, last_y
        last_x, last_y = None, None

    canvas.bind("<B1-Motion>", draw)
    canvas.bind("<ButtonRelease-1>", reset)

    control_frame = tk.Frame(paint_window)
    control_frame.pack(pady=5)

    def choose_color():
        color_code = colorchooser.askcolor(title="Selecciona color")[1]
        if color_code:
            current_color.set(color_code)

    tk.Label(control_frame, text="Color:").pack(side=tk.LEFT)
    tk.Button(control_frame, text="", command=choose_color).pack(side=tk.LEFT, padx=5)
    tk.Label(control_frame, text="Grosor:").pack(side=tk.LEFT, padx=(10, 0))
    tk.Scale(control_frame, from_=1, to=10, orient=tk.HORIZONTAL, variable=pen_size, length=100).pack(side=tk.LEFT)

    frame_buttons = tk.Frame(paint_window)
    frame_buttons.pack(pady=5)

    def clear_canvas():
        canvas.delete("all")
        send_to_esp("CLEAR\n")

    def modo_oscuro():
        canvas.config(bg="black")
        send_to_esp("BLACK\n")

    def back_to_menu():
        paint_window.destroy()
        menu_window.deiconify()
        center_window(menu_window)

    tk.Button(frame_buttons, text="Borrar todo", command=clear_canvas).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_buttons, text="Modo Oscuro", command=modo_oscuro).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_buttons, text="Volver al menú", command=back_to_menu).pack(side=tk.LEFT, padx=5)

menu_window = tk.Tk()
menu_window.title("ESP32 Paint")
menu_window.resizable(False, False)
center_window(menu_window)

title_logo_frame = tk.Frame(menu_window)
title_logo_frame.pack(pady=10)
logo_path = resource_path("logo4.png")  # Usa resource_path para .exe
logo_pil = Image.open(logo_path).resize((200, 200))
logo_img = ImageTk.PhotoImage(logo_pil)
tk.Label(title_logo_frame, text="Paint ESP32", font=("Arial", 20)).pack(side=tk.LEFT, padx=10)
tk.Label(title_logo_frame, image=logo_img).pack(side=tk.LEFT)

com_frame = tk.Frame(menu_window)
com_frame.pack(pady=10)
tk.Label(com_frame, text="Puerto COM:").pack(side=tk.LEFT)
com_var = tk.StringVar()
com_box = ttk.Combobox(com_frame, textvariable=com_var, width=10)
com_box['values'] = list_com_ports()
if com_box['values']:
    com_box.current(0)
com_box.pack(side=tk.LEFT, padx=5)

buttons_frame = tk.Frame(menu_window)
buttons_frame.pack(pady=10)
btn_connect = tk.Button(buttons_frame, text="Conectar", command=lambda: on_connect())
btn_connect.pack(side=tk.LEFT, padx=5)
btn_refresh = tk.Button(buttons_frame, text="Actualizar puertos", command=lambda: com_box.config(values=list_com_ports()))
btn_refresh.pack(side=tk.LEFT, padx=5)
btn_paint = tk.Button(buttons_frame, text="Modo Paint", state="disabled", command=open_paint_window)
btn_paint.pack(side=tk.LEFT, padx=5)
btn_image = tk.Button(buttons_frame, text="Modo Imagen", state="disabled", command=open_image_mode)
btn_image.pack(side=tk.LEFT, padx=5)

def on_connect():
    port = com_var.get()
    if not port:
        messagebox.showwarning("Atención", "Selecciona un puerto COM")
        return
    if connect_com(port):
        btn_paint.config(state="normal")
        btn_image.config(state="normal")
        messagebox.showinfo("Conectado", f"Conectado a {port}")

menu_window.mainloop()

if puerto:
    puerto.close()
