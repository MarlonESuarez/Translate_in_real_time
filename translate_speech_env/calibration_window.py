"""
Ventana de calibración de voz
Permite al usuario grabar 10 frases para crear su perfil personalizado
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sounddevice as sd
import numpy as np
import threading
import time
import queue
from voice_profile import VoiceProfile, get_default_profile_path


class CalibrationWindow:
    """Ventana modal para calibración de voz"""

    def __init__(self, parent, user_name="Usuario"):
        self.parent = parent
        self.user_name = user_name

        # Crear ventana modal
        self.window = tk.Toplevel(parent)
        self.window.title("Calibración de Voz")
        self.window.geometry("700x600")
        self.window.resizable(False, False)
        self.window.grab_set()  # Modal

        # Perfil de voz
        self.voice_profile = VoiceProfile(user_name=user_name)
        self.current_phrase = 0
        self.is_recording = False
        self.recorded_audio = None
        self.sample_rate = 16000

        # Estado
        self.calibration_complete = False

        # Cola para comunicación thread-safe con UI
        self.ui_queue = queue.Queue()

        # Crear widgets
        self.create_widgets()

        # Iniciar procesamiento de cola UI
        self.process_ui_queue()

        # Centrar ventana
        self.center_window()

    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """Crear todos los widgets de la interfaz"""

        # Header
        header_frame = tk.Frame(self.window, bg='#2196F3', height=100)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        title = tk.Label(header_frame,
                        text="🎤 Calibración de Voz",
                        font=('Segoe UI', 20, 'bold'),
                        bg='#2196F3',
                        fg='white')
        title.pack(pady=15)

        subtitle = tk.Label(header_frame,
                           text=f"Perfil de: {self.user_name}",
                           font=('Segoe UI', 11),
                           bg='#2196F3',
                           fg='white')
        subtitle.pack()

        # Main content
        content_frame = tk.Frame(self.window, bg='white', padx=30, pady=20)
        content_frame.pack(fill='both', expand=True)

        # Instrucciones
        instructions = tk.Label(content_frame,
                               text="Lee cada frase en voz alta para calibrar tu perfil.\n"
                                    "Habla con naturalidad, como lo harías normalmente.",
                               font=('Segoe UI', 10),
                               bg='white',
                               fg='#555',
                               justify='left')
        instructions.pack(pady=(0, 20))

        # Progreso
        progress_frame = tk.Frame(content_frame, bg='white')
        progress_frame.pack(fill='x', pady=(0, 15))

        self.progress_label = tk.Label(progress_frame,
                                       text="Frase 1 de 10",
                                       font=('Segoe UI', 10, 'bold'),
                                       bg='white')
        self.progress_label.pack(anchor='w')

        self.progress_bar = ttk.Progressbar(progress_frame,
                                           length=600,
                                           mode='determinate',
                                           maximum=10)
        self.progress_bar.pack(fill='x', pady=5)

        # Frase actual
        phrase_frame = tk.Frame(content_frame, bg='#f5f5f5', padx=20, pady=15)
        phrase_frame.pack(fill='x', pady=(0, 20))

        self.phrase_label = tk.Label(phrase_frame,
                                     text=self._get_current_phrase(),
                                     font=('Segoe UI', 14),
                                     bg='#f5f5f5',
                                     fg='#333',
                                     wraplength=550,
                                     justify='center')
        self.phrase_label.pack()

        # Botón de grabación
        self.record_button = tk.Button(content_frame,
                                       text="🎤 Mantén ESPACIO para grabar",
                                       command=self.toggle_recording,
                                       font=('Segoe UI', 12, 'bold'),
                                       bg='#4CAF50',
                                       fg='white',
                                       activebackground='#45a049',
                                       relief='flat',
                                       cursor='hand2',
                                       height=3,
                                       width=30)
        self.record_button.pack(pady=20)

        # Estado
        self.status_label = tk.Label(content_frame,
                                     text="Presiona el botón o mantén ESPACIO para grabar",
                                     font=('Segoe UI', 9),
                                     bg='white',
                                     fg='#757575')
        self.status_label.pack()

        # Botones de control
        button_frame = tk.Frame(content_frame, bg='white')
        button_frame.pack(side='bottom', pady=20)

        self.skip_button = tk.Button(button_frame,
                                     text="Omitir Calibración",
                                     command=self.skip_calibration,
                                     font=('Segoe UI', 10),
                                     bg='#f5f5f5',
                                     relief='flat',
                                     cursor='hand2',
                                     padx=20,
                                     pady=10)
        self.skip_button.pack(side='left', padx=10)

        self.next_button = tk.Button(button_frame,
                                     text="Siguiente >",
                                     command=self.next_phrase,
                                     font=('Segoe UI', 10, 'bold'),
                                     bg='#2196F3',
                                     fg='white',
                                     activebackground='#0b7dda',
                                     relief='flat',
                                     cursor='hand2',
                                     state='disabled',
                                     padx=20,
                                     pady=10)
        self.next_button.pack(side='left', padx=10)

        # Bind keyboard events
        self.window.bind('<space>', self.on_space_press)
        self.window.bind('<KeyRelease-space>', self.on_space_release)

    def _get_current_phrase(self):
        """Obtiene la frase actual para mostrar"""
        phrase = VoiceProfile.CALIBRATION_PHRASES[self.current_phrase]
        return phrase.format(user_name=self.user_name)

    def update_phrase_display(self):
        """Actualiza la visualización de la frase actual"""
        self.phrase_label.config(text=self._get_current_phrase())
        self.progress_label.config(text=f"Frase {self.current_phrase + 1} de 10")
        self.progress_bar['value'] = self.current_phrase

    def on_space_press(self, event=None):
        """Inicia grabación al presionar ESPACIO"""
        if not self.is_recording:
            self.start_recording()

    def on_space_release(self, event=None):
        """Detiene grabación al soltar ESPACIO"""
        if self.is_recording:
            self.stop_recording()

    def toggle_recording(self):
        """Toggle grabación (para botón)"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Inicia la grabación de audio"""
        if self.is_recording:
            return

        self.is_recording = True
        self.recorded_audio = []

        # Actualizar UI
        self.record_button.config(
            text="⏺️ Grabando... (suelta ESPACIO)",
            bg='#f44336'
        )
        self.status_label.config(
            text="🎤 Grabando... Habla claramente",
            fg='#f44336'
        )

        # Iniciar grabación en thread separado
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()

    def _record_audio(self):
        """Graba audio en background"""
        try:
            # Grabar hasta que se detenga
            def callback(indata, frames, time_info, status):
                if self.is_recording:
                    self.recorded_audio.append(indata.copy())

            with sd.InputStream(channels=1,
                              samplerate=self.sample_rate,
                              callback=callback,
                              blocksize=int(self.sample_rate * 0.1)):
                while self.is_recording:
                    time.sleep(0.1)

        except Exception as e:
            self.window.after(0, lambda: self.show_error(f"Error al grabar: {e}"))

    def stop_recording(self):
        """Detiene la grabación"""
        if not self.is_recording:
            return

        self.is_recording = False

        # Actualizar UI
        self.record_button.config(
            text="⏳ Procesando...",
            bg='#FF9800',
            state='disabled'
        )
        self.status_label.config(
            text="Procesando audio...",
            fg='#FF9800'
        )

        # Procesar audio en thread
        threading.Thread(target=self._process_recording, daemon=True).start()

    def _process_recording(self):
        """Procesa la grabación y la analiza"""
        try:
            if not self.recorded_audio:
                self.ui_queue.put(('error', "No se grabó audio"))
                return

            # Concatenar chunks de audio
            audio_array = np.concatenate(self.recorded_audio, axis=0).flatten()

            # Verificar duración mínima (1 segundo)
            duration = len(audio_array) / self.sample_rate
            if duration < 1.0:
                self.ui_queue.put(('error', "Audio muy corto. Necesitas al menos 1 segundo."))
                return

            # Analizar audio con VoiceProfile
            characteristics = self.voice_profile.add_calibration_sample(
                audio_array,
                self.sample_rate,
                self.current_phrase
            )

            # Enviar resultado a UI
            quality = characteristics['quality_score']
            if quality >= 0.7:
                self.ui_queue.put(('success', quality))
            elif quality >= 0.5:
                self.ui_queue.put(('ok', quality))
            else:
                self.ui_queue.put(('poor', quality))

        except Exception as e:
            self.ui_queue.put(('error', f"Error al procesar: {e}"))

    def process_ui_queue(self):
        """Procesa mensajes de la cola para actualizar UI de forma thread-safe"""
        try:
            while True:
                msg_type, data = self.ui_queue.get_nowait()

                if msg_type == 'success':
                    self._on_recording_success(data)
                elif msg_type == 'ok':
                    self._on_recording_ok(data)
                elif msg_type == 'poor':
                    self._on_recording_poor(data)
                elif msg_type == 'error':
                    self.show_error(data)
                    self._reset_record_button()

        except queue.Empty:
            pass

        # Volver a verificar en 100ms
        self.window.after(100, self.process_ui_queue)

    def _on_recording_success(self, quality):
        """Grabación de buena calidad"""
        self.status_label.config(
            text=f"✅ Excelente! Calidad: {quality*100:.0f}%",
            fg='#4CAF50'
        )
        self.next_button.config(state='normal')
        self._reset_record_button()

    def _on_recording_ok(self, quality):
        """Grabación de calidad aceptable"""
        self.status_label.config(
            text=f"✓ Bueno. Calidad: {quality*100:.0f}% (puedes repetir si quieres)",
            fg='#FF9800'
        )
        self.next_button.config(state='normal')
        self._reset_record_button()

    def _on_recording_poor(self, quality):
        """Grabación de baja calidad"""
        result = messagebox.askyesno(
            "Calidad Baja",
            f"La calidad de audio es baja ({quality*100:.0f}%).\n\n"
            "¿Quieres grabar de nuevo?\n\n"
            "Tip: Habla más fuerte o acércate al micrófono."
        )

        if result:  # Sí, grabar de nuevo
            self.status_label.config(
                text="Intenta de nuevo, habla más fuerte",
                fg='#f44336'
            )
            # Eliminar última muestra
            if self.voice_profile.calibration_data:
                self.voice_profile.calibration_data.pop()
        else:  # No, continuar
            self.next_button.config(state='normal')

        self._reset_record_button()

    def _reset_record_button(self):
        """Resetea el botón de grabación"""
        self.record_button.config(
            text="🎤 Mantén ESPACIO para grabar",
            bg='#4CAF50',
            state='normal'
        )

    def next_phrase(self):
        """Avanza a la siguiente frase"""
        self.current_phrase += 1

        # Resetear estado
        self.next_button.config(state='disabled')
        self.recorded_audio = None

        if self.current_phrase >= 10:
            # Calibración completa
            self.finish_calibration()
        else:
            # Actualizar UI para siguiente frase
            self.update_phrase_display()
            self.status_label.config(
                text="Presiona el botón o mantén ESPACIO para grabar",
                fg='#757575'
            )

    def finish_calibration(self):
        """Finaliza la calibración y guarda el perfil"""
        # Finalizar análisis
        success = self.voice_profile.finalize_calibration()

        if not success:
            self.show_error("Error al finalizar calibración")
            return

        # Guardar perfil
        try:
            profile_path = get_default_profile_path(self.user_name)
            self.voice_profile.save(str(profile_path))

            # Mostrar resumen
            summary = self.voice_profile.get_summary()

            messagebox.showinfo(
                "Calibración Completa",
                f"✅ Tu perfil de voz ha sido creado exitosamente!\n\n{summary}\n\n"
                f"El sistema ahora está optimizado para tu voz."
            )

            self.calibration_complete = True
            self.window.destroy()

        except Exception as e:
            self.show_error(f"Error al guardar perfil: {e}")

    def skip_calibration(self):
        """Omite la calibración"""
        result = messagebox.askyesno(
            "Omitir Calibración",
            "¿Seguro que quieres omitir la calibración?\n\n"
            "La calibración mejora significativamente la precisión\n"
            "de reconocimiento de voz. Puedes hacerla después desde\n"
            "el menú de configuración."
        )

        if result:
            self.calibration_complete = False
            self.window.destroy()

    def show_error(self, message):
        """Muestra un mensaje de error"""
        messagebox.showerror("Error", message)

    def get_voice_profile(self):
        """
        Retorna el perfil de voz creado.

        Returns:
            VoiceProfile si calibración exitosa, None si se omitió
        """
        if self.calibration_complete:
            return self.voice_profile
        return None


# Test standalone
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal

    cal_window = CalibrationWindow(root, user_name="Marlon")
    root.wait_window(cal_window.window)

    profile = cal_window.get_voice_profile()
    if profile:
        print("\n" + profile.get_summary())
    else:
        print("\nCalibración omitida")

    root.destroy()
