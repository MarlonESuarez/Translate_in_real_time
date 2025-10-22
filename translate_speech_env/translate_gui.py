"""
Interfaz gráfica para el traductor de voz en tiempo real
Español → Inglés
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading
import queue
from translate_realtime import RealtimeTranslator
from voice_profile import VoiceProfile, get_default_profile_path
from calibration_window import CalibrationWindow
import sys
import os


class TranslatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Traductor de Voz - Español → Inglés")
        self.root.geometry("600x750")
        self.root.resizable(False, False)

        # Variables
        self.translator = None
        self.is_translating = False
        self.output_queue = queue.Queue()
        self.voice_profile = None  # Perfil de voz del usuario

        # Configurar estilo
        self.setup_styles()

        # Crear widgets
        self.create_widgets()

        # Cargar o crear perfil al iniciar
        self.load_or_create_profile()

        # Iniciar verificación de mensajes
        self.check_output_queue()

    def setup_styles(self):
        """Configurar estilos visuales"""
        style = ttk.Style()
        style.theme_use('clam')

        # Botones
        style.configure('Start.TButton',
                       padding=10,
                       font=('Segoe UI', 11, 'bold'),
                       background='#4CAF50',
                       foreground='white')

        style.configure('Stop.TButton',
                       padding=10,
                       font=('Segoe UI', 11, 'bold'),
                       background='#f44336',
                       foreground='white')

        style.configure('PTT.TButton',
                       padding=15,
                       font=('Segoe UI', 12, 'bold'),
                       background='#2196F3',
                       foreground='white')

    def create_widgets(self):
        """Crear todos los widgets de la interfaz"""

        # Header
        header_frame = tk.Frame(self.root, bg='#1976D2', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame,
                              text="🎤 Traductor de Voz en Tiempo Real",
                              font=('Segoe UI', 18, 'bold'),
                              bg='#1976D2',
                              fg='white')
        title_label.pack(pady=20)

        subtitle_label = tk.Label(header_frame,
                                 text="Español → Inglés",
                                 font=('Segoe UI', 10),
                                 bg='#1976D2',
                                 fg='white')
        subtitle_label.pack()

        # Configuración
        config_frame = tk.Frame(self.root, bg='white', padx=20, pady=15)
        config_frame.pack(fill='x')

        # Modo de grabación
        tk.Label(config_frame,
                text="Modo de Grabación:",
                font=('Segoe UI', 10, 'bold'),
                bg='white').grid(row=0, column=0, sticky='w', pady=5)

        self.mode_var = tk.StringVar(value="continuo")
        mode_frame = tk.Frame(config_frame, bg='white')
        mode_frame.grid(row=0, column=1, sticky='w', padx=10)

        tk.Radiobutton(mode_frame,
                      text="Continuo",
                      variable=self.mode_var,
                      value="continuo",
                      bg='white',
                      font=('Segoe UI', 9)).pack(side='left', padx=5)

        tk.Radiobutton(mode_frame,
                      text="Push-to-Talk (ESPACIO)",
                      variable=self.mode_var,
                      value="ptt",
                      bg='white',
                      font=('Segoe UI', 9)).pack(side='left', padx=5)

        # Calidad
        tk.Label(config_frame,
                text="Calidad:",
                font=('Segoe UI', 10, 'bold'),
                bg='white').grid(row=1, column=0, sticky='w', pady=5)

        self.quality_var = tk.StringVar(value="base")
        quality_frame = tk.Frame(config_frame, bg='white')
        quality_frame.grid(row=1, column=1, sticky='w', padx=10)

        tk.Radiobutton(quality_frame,
                      text="Rápido",
                      variable=self.quality_var,
                      value="tiny",
                      bg='white',
                      font=('Segoe UI', 9)).pack(side='left', padx=5)

        tk.Radiobutton(quality_frame,
                      text="Balanced",
                      variable=self.quality_var,
                      value="base",
                      bg='white',
                      font=('Segoe UI', 9)).pack(side='left', padx=5)

        tk.Radiobutton(quality_frame,
                      text="Preciso",
                      variable=self.quality_var,
                      value="small",
                      bg='white',
                      font=('Segoe UI', 9)).pack(side='left', padx=5)

        # Separador
        ttk.Separator(self.root, orient='horizontal').pack(fill='x', pady=10)

        # Perfil de voz
        profile_frame = tk.Frame(self.root, bg='white', padx=20, pady=10)
        profile_frame.pack(fill='x')

        self.profile_label = tk.Label(profile_frame,
                                      text="Perfil de voz: No calibrado",
                                      font=('Segoe UI', 9),
                                      bg='white',
                                      fg='#757575')
        self.profile_label.pack(side='left')

        self.calibrate_button = tk.Button(profile_frame,
                                          text="🎤 Calibrar Voz",
                                          command=self.open_calibration,
                                          font=('Segoe UI', 9),
                                          bg='#FF9800',
                                          fg='white',
                                          activebackground='#F57C00',
                                          relief='flat',
                                          cursor='hand2',
                                          padx=15,
                                          pady=5)
        self.calibrate_button.pack(side='right')

        # Separador
        ttk.Separator(self.root, orient='horizontal').pack(fill='x', pady=10)

        # Área de estado
        status_frame = tk.Frame(self.root, bg='#f5f5f5', padx=20, pady=10)
        status_frame.pack(fill='x')

        self.status_label = tk.Label(status_frame,
                                     text="● Detenido",
                                     font=('Segoe UI', 11, 'bold'),
                                     bg='#f5f5f5',
                                     fg='#757575')
        self.status_label.pack()

        # Botones de control
        button_frame = tk.Frame(self.root, bg='white', pady=15)
        button_frame.pack(fill='x')

        self.start_button = tk.Button(button_frame,
                                      text="▶ Iniciar",
                                      command=self.start_translation,
                                      font=('Segoe UI', 11, 'bold'),
                                      bg='#4CAF50',
                                      fg='white',
                                      activebackground='#45a049',
                                      relief='flat',
                                      cursor='hand2',
                                      width=15,
                                      height=2)
        self.start_button.pack(side='left', padx=20)

        self.stop_button = tk.Button(button_frame,
                                     text="■ Detener",
                                     command=self.stop_translation,
                                     font=('Segoe UI', 11, 'bold'),
                                     bg='#f44336',
                                     fg='white',
                                     activebackground='#da190b',
                                     relief='flat',
                                     cursor='hand2',
                                     width=15,
                                     height=2,
                                     state='disabled')
        self.stop_button.pack(side='left', padx=20)

        # PTT Button (solo visible en modo PTT)
        self.ptt_button = tk.Button(self.root,
                                    text="Mantén ESPACIO para hablar",
                                    font=('Segoe UI', 12, 'bold'),
                                    bg='#2196F3',
                                    fg='white',
                                    activebackground='#0b7dda',
                                    relief='flat',
                                    height=2)
        # No se muestra por defecto

        # Área de traducción
        translation_frame = tk.Frame(self.root, bg='white', padx=20, pady=10)
        translation_frame.pack(fill='both', expand=True)

        tk.Label(translation_frame,
                text="Traducciones:",
                font=('Segoe UI', 10, 'bold'),
                bg='white').pack(anchor='w', pady=(0, 5))

        self.output_text = scrolledtext.ScrolledText(translation_frame,
                                                     font=('Consolas', 10),
                                                     bg='#fafafa',
                                                     fg='#212121',
                                                     relief='solid',
                                                     borderwidth=1,
                                                     wrap='word',
                                                     state='disabled')
        self.output_text.pack(fill='both', expand=True)

        # Configurar tags para colores
        self.output_text.tag_config('spanish', foreground='#1976D2', font=('Consolas', 10, 'bold'))
        self.output_text.tag_config('english', foreground='#388E3C', font=('Consolas', 10, 'bold'))
        self.output_text.tag_config('status', foreground='#757575', font=('Consolas', 9, 'italic'))

        # Footer
        footer_frame = tk.Frame(self.root, bg='#f5f5f5', height=40)
        footer_frame.pack(fill='x', side='bottom')
        footer_frame.pack_propagate(False)

        self.stats_label = tk.Label(footer_frame,
                                    text="Traducciones: 0",
                                    font=('Segoe UI', 9),
                                    bg='#f5f5f5',
                                    fg='#757575')
        self.stats_label.pack(pady=10)

    def append_output(self, text, tag=None):
        """Agregar texto al área de salida"""
        self.output_text.config(state='normal')
        if tag:
            self.output_text.insert('end', text + '\n', tag)
        else:
            self.output_text.insert('end', text + '\n')
        self.output_text.see('end')
        self.output_text.config(state='disabled')

    def update_status(self, status, color):
        """Actualizar etiqueta de estado"""
        self.status_label.config(text=f"● {status}", fg=color)

    def update_stats(self, count):
        """Actualizar estadísticas"""
        self.stats_label.config(text=f"Traducciones: {count}")

    def start_translation(self):
        """Iniciar traducción"""
        if self.is_translating:
            return

        # Obtener configuración
        push_to_talk = (self.mode_var.get() == "ptt")
        model_size = self.quality_var.get()

        # Deshabilitar controles
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')

        # Limpiar output
        self.output_text.config(state='normal')
        self.output_text.delete('1.0', 'end')
        self.output_text.config(state='disabled')

        # Mostrar/ocultar botón PTT
        if push_to_talk:
            self.ptt_button.pack(pady=10)
            self.update_status("Esperando ESPACIO...", '#FF9800')
        else:
            self.ptt_button.pack_forget()
            self.update_status("Grabando...", '#4CAF50')

        self.is_translating = True

        # Iniciar traductor en thread separado
        thread = threading.Thread(target=self.run_translator,
                                 args=(model_size, push_to_talk),
                                 daemon=True)
        thread.start()

    def run_translator(self, model_size, push_to_talk):
        """Ejecutar traductor en background"""
        try:
            # Crear traductor con callback personalizado y perfil de voz
            self.translator = TranslatorGUIAdapter(
                model_size=model_size,
                push_to_talk=push_to_talk,
                gui_callback=self.on_translation,
                voice_profile=self.voice_profile  # Pasar perfil de voz
            )

            self.translator.start()

        except Exception as e:
            self.output_queue.put(('error', f"Error: {str(e)}"))
        finally:
            self.output_queue.put(('finished', None))

    def on_translation(self, event_type, data):
        """Callback para eventos del traductor"""
        self.output_queue.put((event_type, data))

    def check_output_queue(self):
        """Verificar cola de mensajes periódicamente"""
        try:
            while True:
                event_type, data = self.output_queue.get_nowait()

                if event_type == 'translation':
                    self.append_output(f"→ {data}", 'english')
                    if self.translator:
                        self.update_stats(self.translator.translations_spoken)
                    # Restaurar estado
                    if self.mode_var.get() == "ptt":
                        self.update_status("Esperando ESPACIO...", '#FF9800')
                    else:
                        self.update_status("Grabando...", '#4CAF50')

                elif event_type == 'status':
                    # Actualizar estado visual
                    if '🎤 Grabando' in data:
                        self.update_status("Grabando...", '#4CAF50')
                    elif '⏸️ Procesando' in data:
                        self.update_status("Procesando...", '#2196F3')
                    elif '⚠️' in data:
                        self.append_output(data, 'status')
                    elif 'Procesando' in data:
                        self.update_status("Procesando...", '#2196F3')

                elif event_type == 'error':
                    self.append_output(f"❌ Error: {data}", 'status')

                elif event_type == 'finished':
                    self.stop_translation()

        except queue.Empty:
            pass

        # Volver a verificar en 100ms
        self.root.after(100, self.check_output_queue)

    def stop_translation(self):
        """Detener traducción"""
        if not self.is_translating:
            return

        self.is_translating = False

        if self.translator:
            self.translator.stop()
            # Actualizar estadísticas del perfil si existe
            if self.voice_profile:
                self.voice_profile.total_translations = self.translator.translations_spoken
                profile_path = get_default_profile_path(self.voice_profile.user_name)
                self.voice_profile.save(str(profile_path))
            self.translator = None

        # Restaurar controles
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.ptt_button.pack_forget()

        self.update_status("Detenido", '#757575')
        self.append_output("--- Sesión terminada ---", 'status')

    def load_or_create_profile(self):
        """Carga perfil existente o pregunta si crear uno nuevo"""
        # Pedir nombre de usuario
        user_name = simpledialog.askstring(
            "Perfil de Usuario",
            "¿Cuál es tu nombre?",
            initialvalue="Usuario"
        )

        if not user_name:
            user_name = "Usuario"

        # Buscar perfil existente
        profile_path = get_default_profile_path(user_name)

        if os.path.exists(profile_path):
            # Cargar perfil existente
            self.voice_profile = VoiceProfile(user_name=user_name, profile_path=str(profile_path))
            self.update_profile_display()
        else:
            # Preguntar si quiere calibrar ahora
            result = messagebox.askyesno(
                "Calibración de Voz",
                f"Hola {user_name}!\n\n"
                "No tienes un perfil de voz calibrado.\n\n"
                "¿Quieres calibrar tu voz ahora? (2-3 minutos)\n\n"
                "Esto mejorará significativamente la precisión\n"
                "de reconocimiento de voz."
            )

            if result:
                self.open_calibration(user_name)
            else:
                # Crear perfil vacío
                self.voice_profile = VoiceProfile(user_name=user_name)
                self.update_profile_display()

    def open_calibration(self, user_name=None):
        """Abre ventana de calibración"""
        if self.is_translating:
            messagebox.showwarning(
                "Traductor Activo",
                "Detén la traducción antes de calibrar tu voz"
            )
            return

        # Usar nombre actual si no se proporciona
        if not user_name:
            user_name = self.voice_profile.user_name if self.voice_profile else "Usuario"

        # Abrir ventana de calibración
        cal_window = CalibrationWindow(self.root, user_name=user_name)
        self.root.wait_window(cal_window.window)

        # Obtener perfil creado
        new_profile = cal_window.get_voice_profile()

        if new_profile:
            self.voice_profile = new_profile
            self.update_profile_display()
            messagebox.showinfo(
                "Calibración Exitosa",
                "Tu perfil de voz ha sido creado!\n\n"
                "El sistema ahora está optimizado para tu voz."
            )

    def update_profile_display(self):
        """Actualiza la visualización del perfil"""
        if self.voice_profile and self.voice_profile.is_calibrated:
            self.profile_label.config(
                text=f"Perfil: {self.voice_profile.user_name} (Calibrado ✓)",
                fg='#4CAF50'
            )
            self.calibrate_button.config(text="🔄 Recalibrar")
        else:
            name = self.voice_profile.user_name if self.voice_profile else "Usuario"
            self.profile_label.config(
                text=f"Perfil: {name} (No calibrado)",
                fg='#FF9800'
            )


class TranslatorGUIAdapter(RealtimeTranslator):
    """Adaptador del traductor para trabajar con GUI"""

    def __init__(self, model_size, push_to_talk, gui_callback, vad_enabled=True, voice_profile=None):
        self.gui_callback = gui_callback
        super().__init__(model_size=model_size,
                        source_language="es",
                        push_to_talk=push_to_talk,
                        vad_enabled=vad_enabled,
                        vad_threshold=0.5,
                        voice_profile=voice_profile)

    def start(self):
        """Override para eliminar input() de terminal"""
        self.is_recording = True

        # Iniciar thread de TTS
        tts_thread = threading.Thread(target=self.tts_worker)
        tts_thread.daemon = True
        tts_thread.start()

        # Iniciar thread de procesamiento
        processing_thread = threading.Thread(target=self.process_audio_worker)
        processing_thread.daemon = True
        processing_thread.start()

        # Iniciar keyboard listener si está en modo Push-to-Talk
        keyboard_thread = None
        if self.push_to_talk:
            keyboard_thread = threading.Thread(target=self.keyboard_listener_gui)
            keyboard_thread.daemon = True
            keyboard_thread.start()

        try:
            # Iniciar captura de audio
            import sounddevice as sd

            with sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                callback=self.audio_callback,
                blocksize=int(self.sample_rate * 0.1)
            ):
                # Mantener el programa corriendo mientras is_recording sea True
                while self.is_recording:
                    import time
                    time.sleep(0.1)

        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.gui_callback('error', str(e))
        finally:
            self.is_recording = False

            # Limpiar hooks del teclado si está en modo Push-to-Talk
            if self.push_to_talk:
                try:
                    import keyboard
                    keyboard.unhook_all()
                except:
                    pass

            # Esperar a que los threads terminen
            processing_thread.join(timeout=5)
            tts_thread.join(timeout=5)
            if keyboard_thread:
                keyboard_thread.join(timeout=2)

    def keyboard_listener_gui(self):
        """Listener de teclado para GUI (sin prints)"""
        if not self.push_to_talk:
            return

        import keyboard
        import numpy as np

        def on_press():
            if not self.space_pressed:
                self.space_pressed = True
                # Limpiar buffer al empezar a grabar
                self.buffer.clear()
                self.gui_callback('status', '🎤 Grabando...')

        def on_release():
            if self.space_pressed:
                self.space_pressed = False
                self.gui_callback('status', '⏸️ Procesando...')

                # Procesar audio acumulado inmediatamente
                if len(self.buffer) > 0:
                    chunk = np.array(list(self.buffer))

                    # Verificar que tenga al menos 1 segundo de audio
                    if len(chunk) >= self.sample_rate:
                        # Usar VAD mejorado para validar que contiene voz
                        if self.has_speech(chunk):
                            try:
                                self.audio_queue.put(chunk, block=False)
                            except queue.Full:
                                try:
                                    self.audio_queue.get_nowait()
                                    self.audio_queue.put(chunk, block=False)
                                except:
                                    pass
                        else:
                            self.gui_callback('status', '⚠️ No se detectó voz clara')
                    else:
                        self.gui_callback('status', '⚠️ Audio muy corto (min 1s)')

                    # Limpiar buffer
                    self.buffer.clear()

        # Configurar hooks para la barra espaciadora
        keyboard.on_press_key('space', lambda _: on_press())
        keyboard.on_release_key('space', lambda _: on_release())

        # Mantener el listener activo
        while self.is_recording:
            import time
            time.sleep(0.1)

    def process_audio_worker(self):
        """Override para enviar resultados a GUI"""
        while self.is_recording:
            try:
                audio_chunk = self.audio_queue.get(timeout=1.0)

                if not self.is_recording:
                    break

                self.chunks_processed += 1

                self.gui_callback('status', 'Procesando...')

                try:
                    from translate_realtime import load_audio_from_array
                    import time

                    # Si hay perfil de voz, aplicar ajustes personalizados primero
                    if self.voice_profile and self.voice_profile.is_calibrated:
                        audio_chunk = self.voice_profile.apply_to_audio(audio_chunk, self.sample_rate)

                    # Preparar audio con mejoras (silence trimming + normalization)
                    audio_prepared = load_audio_from_array(
                        audio_chunk,
                        self.sample_rate,
                        apply_silence_trim=True,
                        apply_normalization=not (self.voice_profile and self.voice_profile.is_calibrated),  # Skip si profile ya normalizó
                        silence_threshold_db=self.silence_threshold_db,
                        target_rms_db=self.target_rms_db
                    )

                    result = self.model.transcribe(
                        audio_prepared,
                        task="translate",
                        language=self.source_language,
                        fp16=False,
                        verbose=False,
                        beam_size=1,
                        best_of=1,
                        temperature=0
                    )

                    translated_text = result["text"].strip()

                    if translated_text:
                        self.gui_callback('translation', translated_text)
                        self.tts_queue.put(translated_text)

                except Exception as e:
                    self.gui_callback('error', str(e))

            except queue.Empty:
                continue
            except Exception as e:
                self.gui_callback('error', str(e))

    def stop(self):
        """Detener traductor"""
        self.is_recording = False


def main():
    root = tk.Tk()
    app = TranslatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
