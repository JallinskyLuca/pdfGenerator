import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import json, os, webbrowser, csv
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- IMPORTANTE: pdf_generator.py debe estar en la misma carpeta ---
try:
    from pdf_generator import generar_presupuesto_moderno
except ImportError:
    messagebox.showerror("Error", "No se encontró el archivo pdf_generator.py en la misma carpeta.")
    exit()

# Archivos de base de datos
NUM_FILE = "config_presupuesto.json"
CLIENTES_FILE = "clientes.json"
PRODUCTOS_FILE = "productos.json"
HISTORIAL_FILE = "historial.json"

# --- FUNCIONES DE PERSISTENCIA ---
def cargar_datos(archivo):
    if os.path.exists(archivo):
        with open(archivo, 'r') as f:
            try: return json.load(f)
            except: return {}
    return {}

def guardar_datos(archivo, clave, valor):
    datos = cargar_datos(archivo)
    datos[clave.lower()] = valor
    with open(archivo, 'w') as f:
        json.dump(datos, f, indent=4)

def get_num():
    num = 0
    if os.path.exists(NUM_FILE):
        with open(NUM_FILE, 'r') as f:
            try: num = json.load(f).get("last", 0)
            except: num = 0
    num += 1
    with open(NUM_FILE, 'w') as f:
        json.dump({"last": num}, f)
    return num

def registrar_en_historial(num, cliente, total, items_detalle):
    hist = []
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, 'r') as f:
            try: hist = json.load(f)
            except: hist = []
    
    hist.append({
        "num": num,
        "fecha": datetime.now().strftime("%d/%m/%Y"),
        "cliente": cliente,
        "total": total,
        "items": items_detalle
    })
    with open(HISTORIAL_FILE, 'w') as f:
        json.dump(hist, f, indent=4)

class AppFinalMasterV9:
    def __init__(self, root):
        self.root = root
        self.root.title("SISTEMA DE GESTIÓN TOTAL - v9 Pesos")
        self.root.geometry("950x950")
        self.root.configure(bg="#F4F6F7")
        self.items_data = []

        # --- MENÚ SUPERIOR ---
        menu_bar = tk.Frame(root, bg="#2C3E50", pady=10)
        menu_bar.pack(fill="x")
        
        tk.Button(menu_bar, text="📊 DASHBOARD", bg="#E67E22", fg="white", font=("Arial", 9, "bold"), command=self.abrir_dashboard, relief="flat", padx=20).pack(side="left", padx=10)
        tk.Button(menu_bar, text="⚙️ GESTIONAR DATOS", bg="#7F8C8D", fg="white", font=("Arial", 9, "bold"), command=self.abrir_gestor_datos, relief="flat", padx=20).pack(side="left", padx=5)
        tk.Button(menu_bar, text="📥 EXPORTAR", bg="#27AE60", fg="white", font=("Arial", 9, "bold"), command=self.exportar_csv, relief="flat", padx=20).pack(side="left", padx=5)

        main_container = tk.Frame(root, bg="#F4F6F7")
        main_container.pack(fill="both", expand=True, padx=25, pady=10)

        # --- SECCIÓN CLIENTE ---
        client_frame = tk.LabelFrame(main_container, text=" Información del Cliente ", font=("Arial", 10, "bold"), bg="white", padx=15, pady=10)
        client_frame.pack(fill="x", pady=5)

        tk.Label(client_frame, text="Buscar Cliente Registrado:", bg="white", fg="gray").grid(row=0, column=1, sticky="w")
        self.combo_clientes = ttk.Combobox(client_frame, values=list(cargar_datos(CLIENTES_FILE).keys()), state="readonly")
        self.combo_clientes.grid(row=1, column=1, sticky="ew", pady=(0, 10))
        self.combo_clientes.bind("<<ComboboxSelected>>", self.rellenar_cliente)

        fields = [("Nombre:", "ent_cliente"), ("Dirección:", "ent_dir"), ("Email:", "ent_mail"), ("Teléfono:", "ent_tel")]
        for i, (label, attr) in enumerate(fields):
            tk.Label(client_frame, text=label, bg="white").grid(row=i+2, column=0, sticky="w")
            ent = tk.Entry(client_frame)
            ent.grid(row=i+2, column=1, sticky="ew", pady=2)
            setattr(self, attr, ent)

        tk.Label(client_frame, text="Método Pago:", bg="white").grid(row=6, column=0, sticky="w")
        self.combo_pago = ttk.Combobox(client_frame, values=["Transferencia", "Efectivo", "Débito", "Crédito"], state="readonly")
        self.combo_pago.set("Transferencia")
        self.combo_pago.grid(row=6, column=1, sticky="ew", pady=2)
        client_frame.columnconfigure(1, weight=1)

        # --- SECCIÓN PRODUCTOS ---
        prod_frame = tk.LabelFrame(main_container, text=" Detalle del Presupuesto ", font=("Arial", 10, "bold"), bg="white", padx=15, pady=10)
        prod_frame.pack(fill="x", pady=10)

        tk.Label(prod_frame, text="Producto Guardado:", bg="white", fg="gray").grid(row=0, column=1, sticky="w")
        self.combo_prods = ttk.Combobox(prod_frame, values=list(cargar_datos(PRODUCTOS_FILE).keys()), state="readonly")
        self.combo_prods.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(0,10))
        self.combo_prods.bind("<<ComboboxSelected>>", self.rellenar_producto)

        tk.Label(prod_frame, text="Cant.", bg="white").grid(row=2, column=0)
        tk.Label(prod_frame, text="Descripción", bg="white").grid(row=2, column=1)
        tk.Label(prod_frame, text="Precio ($)", bg="white").grid(row=2, column=2)

        self.ent_cant = tk.Entry(prod_frame, width=8, justify="center"); self.ent_cant.grid(row=3, column=0)
        self.ent_desc = tk.Entry(prod_frame, width=40); self.ent_desc.grid(row=3, column=1, padx=5)
        self.ent_prec = tk.Entry(prod_frame, width=15); self.ent_prec.grid(row=3, column=2)
        
        tk.Button(prod_frame, text="➕ AGREGAR", command=self.add_item, bg="#27AE60", fg="white", font=("Arial", 9, "bold")).grid(row=3, column=3, padx=5)
        prod_frame.columnconfigure(1, weight=1)

        # --- TABLA ---
        self.tree = ttk.Treeview(main_container, columns=("c1", "c2", "c3", "c4"), show="headings", height=8)
        self.tree.heading("c1", text="Cant"); self.tree.heading("c2", text="Descripción"); self.tree.heading("c3", text="P. Unit"); self.tree.heading("c4", text="Subtotal")
        self.tree.column("c1", width=70, anchor="center"); self.tree.column("c2", width=400); self.tree.column("c3", width=120, anchor="e"); self.tree.column("c4", width=120, anchor="e")
        self.tree.pack(fill="x", pady=5)

        tk.Label(main_container, text="Notas para el PDF:", bg="#F4F6F7").pack(anchor="w")
        self.ent_coment = tk.Entry(main_container); self.ent_coment.pack(fill="x", pady=5)

        tk.Button(root, text="🚀 GENERAR Y NOTIFICAR", bg="#3498DB", fg="white", font=("Arial", 12, "bold"), command=self.finalizar, pady=15).pack(fill="x", padx=25, pady=10)

    # --- LÓGICA ---
    def rellenar_cliente(self, e):
        d = cargar_datos(CLIENTES_FILE).get(self.combo_clientes.get().lower())
        if d:
            self.ent_cliente.delete(0, tk.END); self.ent_cliente.insert(0, d["nombre"])
            self.ent_dir.delete(0, tk.END); self.ent_dir.insert(0, d.get("direccion", ""))
            self.ent_mail.delete(0, tk.END); self.ent_mail.insert(0, d.get("mail", ""))
            self.ent_tel.delete(0, tk.END); self.ent_tel.insert(0, d.get("tel", ""))

    def rellenar_producto(self, e):
        p = cargar_datos(PRODUCTOS_FILE).get(self.combo_prods.get().lower())
        if p:
            self.ent_desc.delete(0, tk.END); self.ent_desc.insert(0, p["desc"])
            self.ent_prec.delete(0, tk.END); self.ent_prec.insert(0, str(p["precio"]))

    def add_item(self):
        try:
            c, d, p = float(self.ent_cant.get()), self.ent_desc.get(), float(self.ent_prec.get())
            if d:
                self.items_data.append({"cant": c, "desc": d, "precio": p})
                self.tree.insert("", "end", values=(c, d, f"$ {p:,.2f}", f"$ {c*p:,.2f}"))
                guardar_datos(PRODUCTOS_FILE, d, {"desc": d, "precio": p})
                self.ent_cant.delete(0, tk.END); self.ent_desc.delete(0, tk.END); self.ent_prec.delete(0, tk.END)
                self.combo_prods['values'] = list(cargar_datos(PRODUCTOS_FILE).keys())
        except: messagebox.showerror("Error", "Revisar cantidad y precio.")

    def abrir_gestor_datos(self):
        v = tk.Toplevel(self.root); v.title("Gestor de Bases de Datos"); v.geometry("600x650")
        tabs = ttk.Notebook(v); tabs.pack(expand=1, fill="both")
        
        # Pestaña Clientes
        t_c = tk.Frame(tabs); tabs.add(t_c, text="Clientes")
        lb_c = tk.Listbox(t_c); lb_c.pack(fill="both", expand=1, padx=10, pady=10)
        for c in cargar_datos(CLIENTES_FILE).values(): lb_c.insert("end", c["nombre"])
        
        f_btn_c = tk.Frame(t_c); f_btn_c.pack(pady=10)
        tk.Button(f_btn_c, text="✎ EDITAR CLIENTE", bg="#F1C40F", command=lambda: self.editar_item(CLIENTES_FILE, lb_c)).pack(side="left", padx=5)
        tk.Button(f_btn_c, text="🗑️ BORRAR", bg="#E74C3C", fg="white", command=lambda: self.borrar_item(CLIENTES_FILE, lb_c)).pack(side="left", padx=5)

        # Pestaña Productos
        t_p = tk.Frame(tabs); tabs.add(t_p, text="Productos")
        lb_p = tk.Listbox(t_p); lb_p.pack(fill="both", expand=1, padx=10, pady=10)
        for p in cargar_datos(PRODUCTOS_FILE).values(): lb_p.insert("end", f"{p['desc']} - $ {p['precio']}")
        
        f_btn_p = tk.Frame(t_p); f_btn_p.pack(pady=10)
        tk.Button(f_btn_p, text="✎ EDITAR PRODUCTO", bg="#F1C40F", command=lambda: self.editar_item(PRODUCTOS_FILE, lb_p)).pack(side="left", padx=5)
        tk.Button(f_btn_p, text="🗑️ BORRAR", bg="#E74C3C", fg="white", command=lambda: self.borrar_item(PRODUCTOS_FILE, lb_p)).pack(side="left", padx=5)
        tk.Button(t_p, text="📈 AUMENTO % MASIVO", bg="#8E44AD", fg="white", command=self.actualizar_masiva).pack(pady=5)

    def actualizar_masiva(self):
        porc = simpledialog.askfloat("Aumento", "Porcentaje de aumento masivo:")
        if porc:
            datos = cargar_datos(PRODUCTOS_FILE)
            for k in datos: datos[k]["precio"] *= (1 + (porc / 100))
            with open(PRODUCTOS_FILE, 'w') as f: json.dump(datos, f, indent=4)
            messagebox.showinfo("Éxito", "Precios actualizados."); self.root.destroy()

    def editar_item(self, archivo, lista):
        idx = lista.curselection()
        if not idx: return
        key = lista.get(idx).split(" - ")[0].lower()
        datos = cargar_datos(archivo); item = datos[key]
        edit_v = tk.Toplevel(self.root); edit_v.title("Editar Registro")
        entries = {}
        for i, (k, v) in enumerate(item.items()):
            tk.Label(edit_v, text=k).grid(row=i, column=0, padx=10, pady=5)
            e = tk.Entry(edit_v); e.insert(0, str(v)); e.grid(row=i, column=1, padx=10, pady=5)
            entries[k] = e
        def save():
            new = {k: ent.get() for k, ent in entries.items()}
            if "precio" in new: new["precio"] = float(new["precio"])
            datos[key] = new
            with open(archivo, 'w') as f: json.dump(datos, f, indent=4)
            edit_v.destroy(); self.root.destroy()
        tk.Button(edit_v, text="GUARDAR CAMBIOS", bg="#27AE60", fg="white", command=save).grid(row=len(item), columnspan=2, pady=10)

    def borrar_item(self, archivo, lista):
        idx = lista.curselection()
        if not idx: return
        key = lista.get(idx).split(" - ")[0].lower()
        datos = cargar_datos(archivo)
        if key in datos:
            if messagebox.askyesno("Confirmar", f"¿Eliminar {key}?"):
                del datos[key]
                with open(archivo, 'w') as f: json.dump(datos, f, indent=4)
                lista.delete(idx)

    def abrir_dashboard(self):
        dash = tk.Toplevel(self.root); dash.title("Análisis Detallado"); dash.geometry("900x750")
        hist = cargar_datos(HISTORIAL_FILE)
        if not hist: return
        prod_stats = {}
        for h in hist:
            for i in h.get("items", []):
                d = i["desc"]; prod_stats[d] = prod_stats.get(d, {"c":0, "t":0})
                prod_stats[d]["c"] += i["cant"]; prod_stats[d]["t"] += i["cant"] * i["precio"]

        tree = ttk.Treeview(dash, columns=("P", "U", "R"), show="headings", height=10)
        tree.heading("P", text="Producto"); tree.heading("U", text="Unidades"); tree.heading("R", text="Recaudación")
        tree.pack(fill="x", padx=20, pady=10)
        for p, s in prod_stats.items(): tree.insert("", "end", values=(p, f"{s['c']:.0f}", f"$ {s['t']:,.2f}"))

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.bar(list(prod_stats.keys())[:5], [v["t"] for v in list(prod_stats.values())[:5]], color="#3498DB")
        ax.set_title("Ventas por Producto ($)")
        FigureCanvasTkAgg(fig, master=dash).get_tk_widget().pack(fill="both", expand=True)

    def exportar_csv(self):
        hist = cargar_datos(HISTORIAL_FILE)
        if not hist: return
        f = f"Reporte_{datetime.now().strftime('%Y%m%d')}.csv"
        with open(f, 'w', newline='', encoding='utf-8') as file:
            w = csv.writer(file); w.writerow(["Nro", "Fecha", "Cliente", "Total"])
            for h in hist: w.writerow([h['num'], h['fecha'], h['cliente'], f"{h['total']:.2f}"])
        messagebox.showinfo("Éxito", f"Archivo: {f}"); os.startfile(os.getcwd())

    def finalizar(self):
        nombre = self.ent_cliente.get()
        if not nombre or not self.items_data: return
        num = get_num(); tot = sum(i['cant'] * i['precio'] for i in self.items_data)
        
        registrar_en_historial(num, nombre, tot, self.items_data)
        guardar_datos(CLIENTES_FILE, nombre, {
            "nombre": nombre, "direccion": self.ent_dir.get(), 
            "mail": self.ent_mail.get(), "tel": self.ent_tel.get()
        })
        
        generar_presupuesto_moderno(num, datetime.now().strftime("%d/%m/%Y"), nombre, self.ent_dir.get(), self.ent_mail.get(), self.combo_pago.get(), self.items_data, self.ent_coment.get())
        
        os.startfile(os.getcwd())
        tel = self.ent_tel.get().replace("+", "").replace(" ", "")
        
        # --- MODIFICACIÓN DE WHATSAPP ---
        if tel:
            mensaje = f"Hola {nombre}! Te envío el presupuesto N°{num}. Quedo atento a tus comentarios!"
            webbrowser.open(f"https://wa.me/{tel}?text={mensaje.replace(' ', '%20')}")
        
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk(); AppFinalMasterV9(root); root.mainloop()