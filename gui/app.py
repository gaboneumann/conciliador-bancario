"""
gui/app.py — Interfaz gráfica del Conciliador Bancario v1.0

Tecnología : customtkinter (dark mode)
Threading  : el pipeline corre en un thread separado — UI nunca se congela
Estados    : Idle → Ejecutando → Éxito / Error

Uso:
    python gui/app.py
"""
import queue
import threading
import subprocess
from pathlib import Path
import sys
import logging
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import customtkinter as ctk
from tkinter import filedialog

from main import run
from utils.exceptions import ConciliadorError

# ─── Tema ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ─── Constantes visuales ──────────────────────────────────────────────────────
VENTANA_ANCHO_PCT = 0.52
VENTANA_ALTO_PCT  = 0.88
VENTANA_ANCHO_MAX = 800
VENTANA_ALTO_MAX  = 700
FONT_TITULO    = ("Segoe UI", 20, "bold")
FONT_LABEL     = ("Segoe UI", 13)
FONT_SMALL     = ("Segoe UI", 11)
FONT_LOG       = ("Consolas", 11)
FONT_METRICA   = ("Segoe UI", 13, "bold")

COLOR_EXITO    = "#2ecc71"
COLOR_ERROR    = "#e74c3c"
COLOR_NEUTRO   = "#a0a0a0"
COLOR_NARANJA  = "#e67e22"

PASOS = [
    "[1/6] Leyendo archivos de entrada...",
    "[2/6] Normalizando datos...",
    "[3/6] Ejecutando matching...",
    "[4/6] Clasificando resultados...",
    "[5/6] Calculando diferencia de saldo...",
    "[6/6] Escribiendo archivos de salida...",
]

# ─── Handler de logging para la GUI ──────────────────────────────────────────

class GUILogHandler(logging.Handler):
    """
    Handler personalizado que redirige los mensajes del logger
    al CTkTextbox de la GUI de forma thread-safe.
    """
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def emit(self, record):
        mensaje = self.format(record)
        self.callback(mensaje)

class ConciliadorApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Conciliador Bancario v2")
        self.update_idletasks()
        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla  = self.winfo_screenheight()
        ancho_ventana  = min(int(ancho_pantalla * VENTANA_ANCHO_PCT), VENTANA_ANCHO_MAX)
        alto_ventana   = min(int(alto_pantalla  * VENTANA_ALTO_PCT),  VENTANA_ALTO_MAX)

        self.geometry(f"{ancho_ventana}x{alto_ventana}")
        self.resizable(True, True)
        self.minsize(600, 500)

        self.path_cartola = ctk.StringVar()
        self.path_libro   = ctk.StringVar()
        
        self._queue = queue.Queue()

        self._construir_ui()

        # — Conectar logger a la GUI —
        self._gui_handler = GUILogHandler(
            callback=lambda msg: self.after(0, self._escribir_log, msg)
        )
        self._gui_handler.setLevel(logging.INFO)
        self._gui_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s",
                              datefmt="%H:%M:%S")
        )

        # Agregar directamente a cada logger del pipeline
        # (propagate=False impide que lleguen al root logger)
        for nombre in [
            "main",
            "ingestion.reader",
            "ingestion.normalizer",
            "conciliation.matcher",
            "conciliation.classifier",
            "reporting.writer",
        ]:
            logging.getLogger(nombre).addHandler(self._gui_handler)
        
        self.after(50, self._procesar_queue)


    # ─── Construcción de UI ───────────────────────────────────────────────────

    def _construir_ui(self):

        # — Título —
        ctk.CTkLabel(
            self, text="🏦 Conciliador Bancario",
            font=FONT_TITULO
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            self, text="Sistema automatizado de conciliación bancaria",
            font=FONT_SMALL, text_color=COLOR_NEUTRO
        ).pack(pady=(0, 20))

        # — Selección de archivos —
        self._frame_archivos()

        # — Separador —
        ctk.CTkFrame(self, height=2, fg_color="#333333").pack(
            fill="x", padx=24, pady=16
        )

        # — Barra de progreso —
        self._frame_progreso()

        # — Log —
        self._frame_log()

        # — Métricas —
        self._frame_metricas()

        # — Botón ejecutar —
        self.btn_ejecutar = ctk.CTkButton(
            self, text="Ejecutar conciliación",
            font=FONT_LABEL, height=44,
            command=self._ejecutar
        )
        self.btn_ejecutar.pack(pady=(12, 8), padx=24, fill="x")

        # — Botón abrir carpeta (oculto hasta éxito) —
        self.btn_carpeta = ctk.CTkButton(
            self, text="📂 Abrir carpeta de resultados",
            font=FONT_SMALL, height=36,
            fg_color="transparent", border_width=1,
            command=self._abrir_carpeta
        )

    def _frame_archivos(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=24)

        # Cartola
        ctk.CTkLabel(frame, text="Cartola bancaria", font=FONT_SMALL).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        ctk.CTkEntry(
            frame, textvariable=self.path_cartola,
            font=FONT_SMALL, height=36, width=480
        ).grid(row=1, column=0, sticky="ew")
        ctk.CTkButton(
            frame, text="Examinar", width=100, height=36,
            font=FONT_SMALL,
            command=lambda: self._seleccionar_archivo(self.path_cartola)
        ).grid(row=1, column=1, padx=(8, 0))

        # Libro
        ctk.CTkLabel(frame, text="Libro auxiliar", font=FONT_SMALL).grid(
            row=2, column=0, sticky="w", pady=(12, 4)
        )
        ctk.CTkEntry(
            frame, textvariable=self.path_libro,
            font=FONT_SMALL, height=36, width=480
        ).grid(row=3, column=0, sticky="ew")
        ctk.CTkButton(
            frame, text="Examinar", width=100, height=36,
            font=FONT_SMALL,
            command=lambda: self._seleccionar_archivo(self.path_libro)
        ).grid(row=3, column=1, padx=(8, 0))

        frame.columnconfigure(0, weight=1)

    def _frame_progreso(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=24)

        self.lbl_paso = ctk.CTkLabel(
            frame, text="Listo para ejecutar",
            font=FONT_SMALL, text_color=COLOR_NEUTRO
        )
        self.lbl_paso.pack(anchor="w")

        self.barra = ctk.CTkProgressBar(frame, height=10)
        self.barra.pack(fill="x", pady=(4, 0))
        self.barra.set(0)

    def _frame_log(self):
        self.log_box = ctk.CTkTextbox(
            self, font=FONT_LOG, height=140,
            activate_scrollbars=True
        )
        self.log_box.pack(fill="x", padx=24, pady=(12, 0))
        self.log_box.configure(state="disabled")

    def _frame_metricas(self):
        self.frame_metricas = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_metricas.pack(fill="x", padx=24, pady=(8, 0))

        self.lbl_estado = ctk.CTkLabel(
            self.frame_metricas, text="",
            font=FONT_METRICA
        )
        self.lbl_estado.pack(anchor="w")

        self.lbl_detalle = ctk.CTkLabel(
            self.frame_metricas, text="",
            font=FONT_SMALL, text_color=COLOR_NEUTRO,
            justify="left"
        )
        self.lbl_detalle.pack(anchor="w")

    # ─── Acciones ─────────────────────────────────────────────────────────────

    def _seleccionar_archivo(self, variable: ctk.StringVar):
        ruta = filedialog.askopenfilename(
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if ruta:
            variable.set(ruta)

    def _ejecutar(self):
        cartola = self.path_cartola.get().strip()
        libro   = self.path_libro.get().strip()

        if not cartola or not libro:
            self._mostrar_error("Debes seleccionar ambos archivos antes de ejecutar.")
            return

        if not Path(cartola).exists():
            self._mostrar_error(f"Archivo no encontrado:\n{cartola}")
            return

        if not Path(libro).exists():
            self._mostrar_error(f"Archivo no encontrado:\n{libro}")
            return

        self._estado_ejecutando()

        thread = threading.Thread(
            target=self._correr_pipeline,
            args=(cartola, libro),
            daemon=True
        )
        thread.start()
          
    def _correr_pipeline(self, cartola: str, libro: str):
        try:
            metricas = run(
                path_cartola=Path(cartola),
                path_libro=Path(libro),
                paso_callback=self._actualizar_progreso,
            )
            self.after(0, self._estado_exito, metricas)

        except ConciliadorError as e:
            self.after(0, self._mostrar_error, str(e))

        except Exception as e:
            self.after(0, self._mostrar_error, f"Error inesperado:\n{e}")

    def _actualizar_progreso(self, paso: int, interno: float):
            porcentaje = (paso - 1 + interno) / 6
            texto = PASOS[paso - 1]
            self._queue.put(("progreso", porcentaje, texto))
        
    def _procesar_queue(self):
            ultimo = None
            try:
                while True:
                    ultimo = self._queue.get_nowait()
            except queue.Empty:
                pass
            if ultimo is not None and ultimo[0] == "progreso":
                _, porcentaje, texto = ultimo
                self.barra.set(porcentaje)
                # Solo actualizar label si el texto cambió
                if texto != self.lbl_paso.cget("text"):
                    self.lbl_paso.configure(text=texto)
            self.after(50, self._procesar_queue)
        
               
    # ─── Estados de UI ────────────────────────────────────────────────────────

    def _estado_ejecutando(self):
            self.btn_ejecutar.configure(state="disabled", text="Ejecutando...")
            self.btn_carpeta.pack_forget()
            self.barra.configure(mode="determinate")
            self.barra.set(0)
            self._limpiar_log()
            self._limpiar_metricas()
            self.lbl_paso.configure(text="Iniciando...", text_color=COLOR_NEUTRO)

    def _estado_exito(self, metricas: dict):
        self.barra.stop()
        self.barra.configure(mode="determinate")
        self.barra.set(1.0)
        self.lbl_paso.configure(
            text="✅ Proceso completado exitosamente",
            text_color=COLOR_EXITO
        )
        self.btn_ejecutar.configure(state="normal", text="Ejecutar de nuevo")
        self.btn_carpeta.pack(pady=(4, 0), padx=24, fill="x")

        # Métricas
        total = metricas["exactos"] + metricas["sugeridos"] + metricas["manuales"]
        tasa  = ((metricas["exactos"] + metricas["sugeridos"]) / total * 100) if total else 0

        self.lbl_estado.configure(
            text=f"✅ Conciliación completada — {total} transacciones",
            text_color=COLOR_EXITO
        )
        self.lbl_detalle.configure(
                    text=(
                        f"Exacto: {metricas['exactos']}   "
                        f"Sugerido: {metricas['sugeridos']}   "
                        f"Manual: {metricas['manuales']}   "
                        f"│   Tasa automática: {tasa:.1f}%\n"
                        f"Diferencia de saldo: ${metricas['diferencia']:,.0f}"
                    ),
                    text_color=COLOR_NEUTRO
                )

    def _mostrar_error(self, mensaje: str):
        self.barra.stop()
        self.barra.configure(mode="determinate")
        self.barra.set(0)
        self.lbl_paso.configure(
            text="❌ Error en el proceso",
            text_color=COLOR_ERROR
        )
        self.btn_ejecutar.configure(state="normal", text="Reintentar")
        self.lbl_estado.configure(
            text="❌ El proceso terminó con errores",
            text_color=COLOR_ERROR
        )
        self.lbl_detalle.configure(
            text=mensaje, text_color=COLOR_ERROR
        )
        self._escribir_log(f"ERROR: {mensaje}")

    # ─── Log ──────────────────────────────────────────────────────────────────

    def _escribir_log(self, texto: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", texto + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _limpiar_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _limpiar_metricas(self):
        self.lbl_estado.configure(text="")
        self.lbl_detalle.configure(text="")

    # ─── Abrir carpeta ────────────────────────────────────────────────────────

    def _abrir_carpeta(self):
        from config.config import OUTPUT_DIR
        subprocess.Popen(f'explorer "{OUTPUT_DIR}"')


# ─── Punto de entrada ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = ConciliadorApp()
    app.mainloop()