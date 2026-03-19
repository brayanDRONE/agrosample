"""
SERVICIO DE IMPRESIÓN ZEBRA - Sistema SAG-USDA
Versión con interfaz gráfica para usuarios finales
Se ejecuta en la bandeja del sistema (system tray)
"""

import sys
import json
import win32print
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import tkinter as tk
from tkinter import messagebox
import pystray
from PIL import Image, ImageDraw
from datetime import datetime

# ============================================
# CONFIGURACIÓN
# ============================================
SERVICE_PORT = 5000
VERSION = "2.0"  # Actualizado a etiquetas dobles

# Conversión y medidas (asumiendo 203 dpi)
DPI = 203
def mm_to_dots(mm):
    return int(mm * DPI / 25.4)

LABEL_MM = 50              # 5 cm
LABEL_W = mm_to_dots(LABEL_MM)
LABEL_H = mm_to_dots(LABEL_MM)
MARGIN = mm_to_dots(2)     # margen pequeño

# ============================================
# FUNCIONES DE IMPRESIÓN
# ============================================

def get_zebra_printers():
    """Obtiene lista de impresoras Zebra disponibles."""
    printers = [printer[2] for printer in win32print.EnumPrinters(2)]
    zebra_printers = [p for p in printers if 'zebra' in p.lower() or 'zdesigner' in p.lower()]
    return zebra_printers, printers

def split_sample_text(sample_text):
    """Divide texto personalizado en dos líneas para la etiqueta."""
    raw = str(sample_text or 'MUESTRA USDA').strip()
    if not raw:
        raw = 'MUESTRA USDA'

    if '\n' in raw:
        parts = [p.strip() for p in raw.split('\n') if p.strip()]
    elif '|' in raw:
        parts = [p.strip() for p in raw.split('|') if p.strip()]
    else:
        split_once = raw.split(' ', 1)
        parts = [split_once[0], split_once[1] if len(split_once) > 1 else '']

    line1 = parts[0] if parts else 'MUESTRA'
    line2 = parts[1] if len(parts) > 1 else ''
    return line1, line2


def build_zpl_double_label(lote, left_num, right_num=None, sample_text='MUESTRA USDA'):
    """
    Construye ZPL para una tira con dos etiquetas 5x5cm lado a lado.
    Ajusta el tamaño del número para que quepa: si el número es muy largo
    (ej. 4 dígitos) reduce la altura hasta que entre en el ancho disponible.
    Mantiene el diseño: MUESTRA/USDA arriba, número grande centrado,
    debajo "LOTE: <número>" y "MUESTRA"/"USDA" con tamaño aumentado.
    """
    left_x = 0
    right_x = LABEL_W

    SCALE = 1.2  # agrandar 20% por defecto para subtexto
    max_big_by_height = max(1, int(LABEL_H * 0.6 * SCALE))   # altura máxima del número
    sub_font_h = max(10, int(LABEL_H * 0.08 * SCALE))       # tamaño de subtexto aumentado 20%

    # Estimación: ancho de caracter ≈ 0.6 * altura_de_fuente (aprox.)
    def fit_number_font_height(text, max_height, max_width):
        if not text:
            return max_height
        chars = max(1, len(str(text)))
        usable_width = int(max_width * 0.85)  # dejar 15% de margen lateral
        # altura estimada permitida por ancho: usable_width / (chars * char_width_ratio)
        approx_h = int(usable_width / (chars * 0.6))
        return max(10, min(max_height, approx_h))

    # Desplazamiento extra para "USDA": 5% del alto de etiqueta
    extra_usda_down = int(LABEL_H * 0.05)

    # Posiciones:
    top_text_y = int(MARGIN)
    muestra_y = top_text_y
    usda_y = muestra_y + int(sub_font_h * 1.05) + extra_usda_down

    # Reservar espacio superior (2 líneas de subtexto) y espacio inferior para LOTE
    reserved_top = usda_y + sub_font_h
    reserved_bottom = sub_font_h + int(sub_font_h * 0.5)
    available_for_number = LABEL_H - reserved_top - reserved_bottom

    # Base para centrar usando la altura máxima; números más pequeños se centran dentro del mismo bloque
    number_block_h = min(max_big_by_height, available_for_number)
    number_y_base = reserved_top + int((available_for_number - number_block_h) / 2)
    lote_y = number_y_base + number_block_h + int(sub_font_h * 0.2)

    # Calcular altura final para cada número (ajustar si es muy largo)
    left_big_h = fit_number_font_height(left_num, number_block_h, LABEL_W)
    right_big_h = fit_number_font_height(right_num if right_num is not None else "", number_block_h, LABEL_W)

    # Ajustar y para centrar cada número dentro del bloque reservado
    left_number_y = number_y_base + int((number_block_h - left_big_h) / 2)
    right_number_y = number_y_base + int((number_block_h - right_big_h) / 2)

    zpl = []
    zpl.append("^XA")
    zpl.append("^LH0,0")

    line1, line2 = split_sample_text(sample_text)

    # --- IZQUIERDA ---
    # MUESTRA (arriba)
    zpl.append(f"^CF0,{sub_font_h}")
    zpl.append(f"^FO{left_x},{muestra_y}^FB{LABEL_W},1,0,C,0")
    zpl.append(f"^FD{line1}^FS")
    # Línea 2 (debajo)
    zpl.append(f"^CF0,{sub_font_h}")
    zpl.append(f"^FO{left_x},{usda_y}^FB{LABEL_W},1,0,C,0")
    zpl.append(f"^FD{line2}^FS")

    # Número grande (centrado) - IZQUIERDA
    zpl.append(f"^CF0,{left_big_h}")
    zpl.append(f"^FO{left_x},{left_number_y}")
    zpl.append(f"^FB{LABEL_W},1,0,C,0")
    zpl.append(f"^FD{left_num}^FS")

    # LOTE debajo del número - IZQUIERDA
    zpl.append(f"^CF0,{sub_font_h}")
    zpl.append(f"^FO{left_x},{lote_y}^FB{LABEL_W},1,0,C,0")
    zpl.append(f"^FDLOTE: {lote}^FS")

    # --- DERECHA ---
    # Línea 1 (arriba)
    zpl.append(f"^CF0,{sub_font_h}")
    zpl.append(f"^FO{right_x},{muestra_y}^FB{LABEL_W},1,0,C,0")
    zpl.append(f"^FD{line1}^FS")
    # Línea 2 (debajo)
    zpl.append(f"^CF0,{sub_font_h}")
    zpl.append(f"^FO{right_x},{usda_y}^FB{LABEL_W},1,0,C,0")
    zpl.append(f"^FD{line2}^FS")

    # Número grande (centrado) - DERECHA
    zpl.append(f"^CF0,{right_big_h}")
    zpl.append(f"^FO{right_x},{right_number_y}")
    zpl.append(f"^FB{LABEL_W},1,0,C,0")
    zpl.append(f"^FD{right_num if right_num is not None else ''}^FS")

    # LOTE debajo del número derecho (siempre mostrar lote)
    zpl.append(f"^CF0,{sub_font_h}")
    zpl.append(f"^FO{right_x},{lote_y}^FB{LABEL_W},1,0,C,0")
    zpl.append(f"^FDLOTE: {lote}^FS")

    zpl.append("^XZ")
    return "\n".join(zpl)

def imprimir_etiquetas(lote, numeros, printer_name, sample_text='MUESTRA USDA'):
    """Imprime etiquetas en pares (tiras de 10x5cm con dos etiquetas de 5x5cm)."""
    try:
        # Verificar que la impresora existe
        try:
            hPrinter = win32print.OpenPrinter(printer_name)
            win32print.ClosePrinter(hPrinter)
        except Exception as e:
            return {
                "success": False,
                "error": f"Impresora '{printer_name}' no encontrada. Verifique el nombre."
            }
        
        # Imprimir en pares: (0,1), (2,3), ...
        i = 0
        strips_printed = 0
        while i < len(numeros):
            left = str(numeros[i])
            right = str(numeros[i+1]) if i+1 < len(numeros) else None
            etiqueta_zpl = build_zpl_double_label(lote, left, right, sample_text)
            
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Etiqueta AGROSAMPLE", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, etiqueta_zpl.encode('utf-8'))
                    win32print.EndPagePrinter(hPrinter)
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
            
            strips_printed += 1
            i += 2
        
        return {
            "success": True,
            "message": f"✅ Se imprimieron {strips_printed} tiras ({len(numeros)} etiquetas) en '{printer_name}'",
            "printed_count": strips_printed,
            "labels_count": len(numeros)
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Error al imprimir: {str(e)}"
        }

# ============================================
# SERVIDOR HTTP
# ============================================

class ZebraServiceHandler(BaseHTTPRequestHandler):
    """Manejador HTTP para el servicio de impresión."""
    
    log_callback = None  # Callback para logging en GUI
    
    def log_message(self, format, *args):
        """Override para logging personalizado."""
        message = f"{self.address_string()} - {format % args}"
        if self.log_callback:
            self.log_callback(message)
    
    def do_OPTIONS(self):
        """Maneja solicitudes OPTIONS (CORS preflight)."""
        origin = self.headers.get('Origin')
        self.send_response(200)
        
        if origin and ('vercel.app' in origin or 'localhost' in origin or '127.0.0.1' in origin):
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            self.send_header('Access-Control-Allow-Origin', '*')
        
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()
    
    def _set_cors_headers(self):
        """Establece headers CORS."""
        origin = self.headers.get('Origin')
        if origin and ('vercel.app' in origin or 'localhost' in origin or '127.0.0.1' in origin):
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Credentials', 'true')
    
    def do_GET(self):
        """Maneja solicitudes GET (health check)."""
        if self.path == '/health':
            zebra_printers, all_printers = get_zebra_printers()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            
            response = {
                "status": "online",
                "version": VERSION,
                "printers_available": all_printers,
                "zebra_printers": zebra_printers,
                "zebra_available": len(zebra_printers) > 0,
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Maneja solicitudes POST (imprimir)."""
        if self.path == '/print':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                lote = data.get('lote', '')
                numeros = data.get('numeros', [])
                printer = data.get('printer', '')
                sample_text = data.get('sample_text', 'MUESTRA USDA')
                
                # Validaciones
                if not lote:
                    raise ValueError("Número de lote requerido")
                if not numeros:
                    raise ValueError("Lista de números de caja requerida")
                
                # Si no se especificó impresora, usar la primera Zebra
                if not printer:
                    zebra_printers, _ = get_zebra_printers()
                    if zebra_printers:
                        printer = zebra_printers[0]
                    else:
                        raise ValueError("No se encontró impresora Zebra")
                
                # Imprimir
                result = imprimir_etiquetas(lote, numeros, printer, sample_text)
                
                self.send_response(200 if result['success'] else 400)
                self.send_header('Content-Type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
                
                # Log
                if self.log_callback:
                    status = "✅" if result['success'] else "❌"
                    self.log_callback(f"{status} Lote {lote}: {len(numeros)} etiquetas")
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                error_response = {"success": False, "error": str(e)}
                self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
                
                if self.log_callback:
                    self.log_callback(f"❌ Error: {str(e)}")
        else:
            self.send_response(404)
            self.end_headers()

# ============================================
# INTERFAZ GRÁFICA (SYSTEM TRAY)
# ============================================

class PrinterServiceApp:
    """Aplicación con interfaz en bandeja del sistema."""
    
    def __init__(self):
        self.server = None
        self.server_thread = None
        self.icon = None
        self.running = False
        self.log_window = None
        
    def create_image(self):
        """Crea icono para la bandeja del sistema."""
        # Icono simple: círculo verde
        image = Image.new('RGB', (64, 64), color='white')
        dc = ImageDraw.Draw(image)
        dc.ellipse([8, 8, 56, 56], fill='green', outline='darkgreen')
        dc.text((20, 22), "Z", fill='white')
        return image
    
    def start_server(self):
        """Inicia el servidor HTTP."""
        try:
            self.server = HTTPServer(('0.0.0.0', SERVICE_PORT), ZebraServiceHandler)
            ZebraServiceHandler.log_callback = self.add_log
            
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            self.running = True
            
            self.add_log(f"🟢 Servicio iniciado en puerto {SERVICE_PORT}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el servicio:\n{str(e)}")
            return False
    
    def stop_server(self):
        """Detiene el servidor HTTP."""
        if self.server:
            self.server.shutdown()
            self.running = False
            self.add_log("🔴 Servicio detenido")
    
    def add_log(self, message):
        """Agrega mensaje al log (si la ventana está abierta)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)  # También en consola
        
        if self.log_window and hasattr(self.log_window, 'text_widget'):
            try:
                self.log_window.text_widget.insert('end', log_message + '\n')
                self.log_window.text_widget.see('end')
            except:
                pass
    
    def show_status(self, icon, item):
        """Muestra ventana de estado."""
        zebra_printers, all_printers = get_zebra_printers()
        
        status = f"""🖨️  SERVICIO DE IMPRESIÓN ZEBRA - SAG-USDA
        
Estado: {'🟢 Activo' if self.running else '🔴 Detenido'}
Puerto: {SERVICE_PORT}
Versión: {VERSION}

Impresoras Zebra detectadas: {len(zebra_printers)}
{chr(10).join('  • ' + p for p in zebra_printers) if zebra_printers else '  (Ninguna)'}

Todas las impresoras: {len(all_printers)}
        """
        
        messagebox.showinfo("Estado del Servicio", status)
    
    def show_logs(self, icon, item):
        """Muestra ventana de logs."""
        if self.log_window and tk.Toplevel.winfo_exists(self.log_window):
            self.log_window.lift()
            return
        
        self.log_window = tk.Toplevel()
        self.log_window.title("Registro de Actividad - Servicio Zebra")
        self.log_window.geometry("600x400")
        
        # Text widget con scrollbar
        frame = tk.Frame(self.log_window)
        frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side='right', fill='y')
        
        text_widget = tk.Text(frame, yscrollcommand=scrollbar.set, wrap='word')
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=text_widget.yview)
        
        self.log_window.text_widget = text_widget
        
        # Botón cerrar
        btn_close = tk.Button(self.log_window, text="Cerrar", command=self.log_window.destroy)
        btn_close.pack(pady=5)
        
        self.add_log("📋 Ventana de logs abierta")
    
    def test_print(self, icon, item):
        """Imprime etiqueta de prueba."""
        try:
            zebra_printers, _ = get_zebra_printers()
            if not zebra_printers:
                messagebox.showwarning("Sin impresora", "No se detectó ninguna impresora Zebra")
                return
            
            result = imprimir_etiquetas("TEST-001", [1, 2, 3], zebra_printers[0])
            
            if result['success']:
                messagebox.showinfo("Prueba exitosa", 
                    f"✅ 3 etiquetas enviadas a:\n{zebra_printers[0]}")
                self.add_log("🧪 Impresión de prueba exitosa")
            else:
                messagebox.showerror("Error de prueba", result['error'])
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def quit_app(self, icon, item):
        """Cierra la aplicación."""
        self.stop_server()
        icon.stop()
    
    def run(self):
        """Ejecuta la aplicación."""
        # Iniciar servidor
        if not self.start_server():
            return
        
        # Crear icono en bandeja del sistema
        image = self.create_image()
        menu = pystray.Menu(
            pystray.MenuItem("📊 Ver Estado", self.show_status),
            pystray.MenuItem("📋 Ver Registro", self.show_logs),
            pystray.MenuItem("🧪 Prueba de Impresión", self.test_print),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Salir", self.quit_app)
        )
        
        self.icon = pystray.Icon(
            "zebra_service",
            image,
            "Servicio Impresión Zebra",
            menu
        )
        
        # Mostrar notificación de inicio
        self.icon.notify(
            "Servicio de impresión iniciado",
            f"Puerto {SERVICE_PORT} - Haga clic derecho en el icono para opciones"
        )
        
        # Ejecutar
        self.icon.run()

# ============================================
# PUNTO DE ENTRADA
# ============================================

if __name__ == '__main__':
    # Ocultar consola en Windows (cuando se compile a .exe)
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
    
    app = PrinterServiceApp()
    app.run()
