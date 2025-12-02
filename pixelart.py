import sys, json, os
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QColorDialog, QFontDialog
from PyQt6.QtGui import QImage, QPixmap, QColor, QPainter, QFont
from PyQt6.QtCore import Qt, QPoint

# Archivo donde guardaremos la configuración del tema
CONFIG_FILE = "config.json"

class PixelArtCanvas(QLabel):
    """
    Clase que representa el lienzo de pixel art.
    Hereda de QLabel y muestra un QImage escalado con cuadrícula.
    """
    def __init__(self, width=60, height=60, display_size=600):
        super().__init__()
        # Tamaño del lienzo en cuadros (ej. 60x60)
        self.width_px = width
        self.height_px = height
        # Tamaño en pantalla (ej. 600x600 para que se vean grandes los cuadros)
        self.display_size = display_size

        # Imagen interna donde se guardan los colores reales
        self.image = QImage(width, height, QImage.Format.Format_RGB32)
        self.image.fill(Qt.GlobalColor.white)  # inicializa todo en blanco

        # Estado de dibujo y color actual del pincel
        self.drawing = False
        self.brush_color = QColor("#ff69b4")  # color inicial rosa girly 💖

        # Actualiza la vista inicial
        self.update_display()

    # --- Eventos del mouse ---
    def mousePressEvent(self, event):
        # Clic izquierdo → pintar
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.paint_pixel(event.pos())
        # Clic derecho → borrar (resetear a blanco)
        elif event.button() == Qt.MouseButton.RightButton:
            self.reset_pixel(event.pos())

    def mouseDoubleClickEvent(self, event):
        # Doble clic → resetear a blanco
        self.reset_pixel(event.pos())

    def mouseMoveEvent(self, event):
        # Arrastrar con clic izquierdo → pintar varios píxeles
        if self.drawing and event.buttons() & Qt.MouseButton.LeftButton:
            self.paint_pixel(event.pos())

    def mouseReleaseEvent(self, event):
        # Al soltar el botón → detener dibujo
        self.drawing = False

    # --- Métodos de dibujo ---
    def paint_pixel(self, pos: QPoint):
        """
        Pinta un píxel en la posición indicada con el color actual del pincel.
        """
        # Convertir coordenadas del ratón a coordenadas del lienzo
        x = int(pos.x() * self.width_px / self.width())
        y = int(pos.y() * self.height_px / self.height())
        if 0 <= x < self.width_px and 0 <= y < self.height_px:
            self.image.setPixelColor(x, y, self.brush_color)
            self.update_display()

    def reset_pixel(self, pos: QPoint):
        """
        Restaura un píxel a blanco (borrador).
        """
        x = int(pos.x() * self.width_px / self.width())
        y = int(pos.y() * self.height_px / self.height())
        if 0 <= x < self.width_px and 0 <= y < self.height_px:
            self.image.setPixelColor(x, y, QColor("white"))
            self.update_display()

    def update_display(self):
        """
        Escala la imagen interna para mostrarla en pantalla
        y dibuja una cuadrícula pastel encima.
        """
        scaled = self.image.scaled(self.display_size, self.display_size,
                                   Qt.AspectRatioMode.IgnoreAspectRatio,
                                   Qt.TransformationMode.FastTransformation)

        pixmap = QPixmap.fromImage(scaled)
        painter = QPainter(pixmap)
        painter.setPen(QColor("#d8b0ff"))  # bordes morados pastel
        step = self.display_size / self.width_px
        # Dibujar líneas verticales y horizontales
        for i in range(self.width_px + 1):
            painter.drawLine(int(i * step), 0, int(i * step), self.display_size)
        for j in range(self.height_px + 1):
            painter.drawLine(0, int(j * step), self.display_size, int(j * step))
        painter.end()
        self.setPixmap(pixmap)

    def save_image(self):
        """
        Guarda la imagen como PNG de 1080x1080 sin cuadrícula.
        """
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar imagen", "", "PNG Files (*.png)")
        if filename:
            scaled = self.image.scaled(1080, 1080,
                                       Qt.AspectRatioMode.IgnoreAspectRatio,
                                       Qt.TransformationMode.FastTransformation)
            scaled.save(filename)

    def change_color(self):
        """
        Abre un diálogo para cambiar el color del pincel.
        """
        color = QColorDialog.getColor(initial=self.brush_color, title="Selecciona un color 🎨")
        if color.isValid():
            self.brush_color = color


class PixelArtApp(QWidget):
    """
    Ventana principal de la aplicación.
    Contiene el lienzo y los botones de control.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎀 Pixelita 🎀")
        self.layout = QVBoxLayout()

        # Lienzo principal
        self.canvas = PixelArtCanvas(60, 60, display_size=600)
        self.layout.addWidget(self.canvas)

        # Botones principales
        self.save_btn = QPushButton("💾 Guardar como PNG (1080x1080)")
        self.color_btn = QPushButton("🎨 Cambiar color del pincel")
        self.theme_btn = QPushButton("🌈 Cambiar tema")
        self.reset_btn = QPushButton("🔄 Restablecer tema")

        # Estilo predeterminado (morados femeninos)
        self.default_style = {
            "window_color": "#f3e6ff",   # color de fondo de ventana
            "button_color": "#b57edc",   # color de botones morados
            "font": "Comic Sans MS"      # fuente divertida
        }
        # Cargar estilo actual desde config.json
        self.current_style = self.load_config()

        # Conectar botones a sus funciones
        self.save_btn.clicked.connect(self.canvas.save_image)
        self.color_btn.clicked.connect(self.canvas.change_color)
        self.theme_btn.clicked.connect(self.change_theme)
        self.reset_btn.clicked.connect(self.reset_theme)

        # Añadir botones al layout
        for btn in [self.save_btn, self.color_btn, self.theme_btn, self.reset_btn]:
            self.layout.addWidget(btn)

        self.setLayout(self.layout)
        # Aplicar estilo inicial
        self.apply_style()

    # --- Métodos de estilo/tema ---
    def apply_style(self):
        """
        Aplica el estilo actual a la ventana y botones.
        """
        style = self.current_style
        self.setStyleSheet(f"background-color: {style['window_color']}; font-family: {style['font']}; color: #4b0082;")
        for btn in [self.save_btn, self.color_btn, self.theme_btn, self.reset_btn]:
            btn.setStyleSheet(f"background-color: {style['button_color']}; border-radius: 8px; padding: 6px; font-family: {style['font']}; color: white;")

    def change_theme(self):
        """
        Permite cambiar el tema de la aplicación:
        - Color de ventana
        - Color de botones
        - Fuente
        """
        window_color = QColorDialog.getColor(QColor(self.current_style["window_color"]), title="Color de ventana")
        button_color = QColorDialog.getColor(QColor(self.current_style["button_color"]), title="Color de botones")
        font, ok = QFontDialog.getFont(QFont(self.current_style["font"]))
        if window_color.isValid():
            self.current_style["window_color"] = window_color.name()
        if button_color.isValid():
            self.current_style["button_color"] = button_color.name()
        if ok:
            self.current_style["font"] = font.family()
        self.apply_style()
        self.save_config()

    def reset_theme(self):
        """
        Restablece el tema al estilo predeterminado.
        """
        self.current_style = self.default_style.copy()
        self.apply_style()
        self.save_config()

    def save_config(self):
        """
        Guarda la configuración actual en config.json.
        """
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.current_style, f)

    def load_config(self):
        """
        Carga la configuración desde config.json si existe.
        """
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return self.default_style.copy()


# --- Punto de entrada ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PixelArtApp()
    window.show()
    sys.exit(app.exec())
