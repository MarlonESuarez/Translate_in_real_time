"""
Interfaz gráfica para el traductor de voz en tiempo real
Español → Inglés
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
from translate_realtime import RealtimeTranslator
import sys


class TranslatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Traductor de Voz - Español → Inglés")
        self.root.geometry("600x700")
        self.root.resizable(False, False)

        # Variables
        self.translator = None
        self.is_translating = False
        self.output_queue = queue.Queue()

        # Configurar estilo
        self.setup_styles()

        # Crear widgets
        self.create_widgets()

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
            # Crear traductor con callback personalizado
            self.translator = TranslatorGUIAdapter(
                model_size=model_size,
                push_to_talk=push_to_talk,
                gui_callback=self.on_translation
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
            self.translator = None

        # Restaurar controles
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.ptt_button.pack_forget()

        self.update_status("Detenido", '#757575')
        self.append_output("--- Sesión terminada ---", 'status')


class TranslatorGUIAdapter(RealtimeTranslator):
    """Adaptador del traductor para trabajar con GUI"""

    def __init__(self, model_size, push_to_talk, gui_callback):
        self.gui_callback = gui_callback
        super().__init__(model_size=model_size,
                        source_language="es",
                        push_to_talk=push_to_talk)

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
                        audio_energy = np.abs(chunk).mean()

                        if audio_energy > 0.01:
                            try:
                                self.audio_queue.put(chunk, block=False)
                            except queue.Full:
                                try:
                                    self.audio_queue.get_nowait()
                                    self.audio_queue.put(chunk, block=False)
                                except:
                                    pass
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

                    audio_prepared = load_audio_from_array(audio_chunk, self.sample_rate)

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
