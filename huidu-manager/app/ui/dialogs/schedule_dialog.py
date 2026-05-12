import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QCheckBox, QLineEdit, QGroupBox,
    QMessageBox, QProgressDialog, QScrollArea, QWidget, QGridLayout,
    QFrame, QComboBox
)
from PyQt6.QtCore import Qt
from app.ui.workers import ScheduleFetchWorker, ScheduleSyncWorker

class ScheduleDialog(QDialog):
    def __init__(self, device_id, programs_cache, manager, parent=None):
        super().__init__(parent)
        self.device_id = device_id
        # We work on a deep copy of programs to avoid modifying cache before saving
        self.programs = {k: json.loads(json.dumps(v)) for k, v in programs_cache.items()}
        self.manager = manager
        
        self.setWindowTitle(f"Palinsesto - {device_id}")
        self.resize(700, 500)
        
        self.current_selected_uuid = None
        self.screen_task_data = None
        self._loading = False  # Impedisce salvataggio automatico durante il caricamento UI
        
        self.setup_ui()
        self.load_screen_schedule()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- TOP: Screen Power Schedule ---
        screen_group = QGroupBox("Risparmio Energetico (Spegnimento Schermo)")
        screen_layout = QHBoxLayout(screen_group)
        
        self.chk_screen_off = QCheckBox("Spegni automaticamente lo schermo")
        self.chk_screen_off.toggled.connect(self.on_screen_off_toggled)
        
        self.txt_screen_off_time = QLineEdit()
        self.txt_screen_off_time.setPlaceholderText("Es: 00:00-06:00")
        self.txt_screen_off_time.setEnabled(False)
        self.txt_screen_off_time.setToolTip("Inserire orario di spegnimento (es. 00:00-06:00). Lo schermo sarà spento in questa fascia.")
        
        screen_layout.addWidget(self.chk_screen_off)
        screen_layout.addWidget(QLabel("Fascia oraria spegnimento:"))
        screen_layout.addWidget(self.txt_screen_off_time)
        
        main_layout.addWidget(screen_group)
        
        # --- MIDDLE: Programs Schedule ---
        prog_group = QGroupBox("Palinsesto Playlist")
        prog_layout = QHBoxLayout(prog_group)
        
        # List of programs
        self.lst_programs = QListWidget()
        self.lst_programs.setFixedWidth(250)
        self.lst_programs.currentRowChanged.connect(self.on_program_selected)
        
        for uid, p in self.programs.items():
            name = p.get("name", "Senza Nome")
            status = p.get("status", "live")
            play_ctrl = p.get("playControl")
            if status == "disabled":
                display_name = f"🚫 {name}"
            elif play_ctrl is not None:
                display_name = f"📅 {name}"
            else:
                display_name = f"▶ {name}"
            
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, uid)
            self.lst_programs.addItem(item)
            
        prog_layout.addWidget(self.lst_programs)
        
        # Right panel for Program Schedule Editor
        self.editor_panel = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_panel)
        self.editor_panel.setEnabled(False)
        
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["Riproduci Sempre (H24)", "Personalizzato (Scegli orari/giorni)", "Disattivata (Non riprodurre)"])
        self.cmb_mode.currentIndexChanged.connect(self.on_mode_changed)
        self.editor_layout.addWidget(QLabel("Modalità riproduzione:"))
        self.editor_layout.addWidget(self.cmb_mode)
        
        # Days of week
        self.days_group = QGroupBox("Giorni della settimana")
        days_layout = QGridLayout(self.days_group)
        self.chk_days = {}
        days_map = [
            ("Mon", "Lunedì", 0, 0), ("Tue", "Martedì", 0, 1), ("Wed", "Mercoledì", 0, 2),
            ("Thu", "Giovedì", 1, 0), ("Fri", "Venerdì", 1, 1), ("Sat", "Sabato", 1, 2),
            ("Sun", "Domenica", 2, 0)
        ]
        for day_code, day_name, row, col in days_map:
            chk = QCheckBox(day_name)
            self.chk_days[day_code] = chk
            days_layout.addWidget(chk, row, col)
        
        self.editor_layout.addWidget(self.days_group)
        
        # Time ranges
        self.time_group = QGroupBox("Fasce Orarie")
        time_layout = QVBoxLayout(self.time_group)
        self.txt_times = QLineEdit()
        self.txt_times.setPlaceholderText("Es: 08:00-12:00, 15:00-20:00")
        self.txt_times.setToolTip("Inserisci fasce orarie separate da virgola (formato HH:MM-HH:MM)")
        time_layout.addWidget(QLabel("Orari di riproduzione:"))
        time_layout.addWidget(self.txt_times)
        
        self.editor_layout.addWidget(self.time_group)
        self.editor_layout.addStretch()
        
        prog_layout.addWidget(self.editor_panel)
        main_layout.addWidget(prog_group)
        
        # --- BOTTOM: Actions ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Annulla")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_save = QPushButton("Salva e Sincronizza")
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.clicked.connect(self.on_save)
        btn_layout.addWidget(self.btn_save)
        
        main_layout.addLayout(btn_layout)

    def load_screen_schedule(self):
        """Scarica i task dello schermo dal controller in background."""
        self.chk_screen_off.setEnabled(False)
        self.fetch_worker = ScheduleFetchWorker(self.manager, self.device_id)
        
        def on_tasks(tasks):
            self.chk_screen_off.setEnabled(True)
            self.screen_task_data = tasks
            screen_cfg = tasks.get("screen", [])
            if screen_cfg:
                # Cerca un task di spegnimento ("data": "false")
                for t in screen_cfg:
                    if str(t.get("data", "")).lower() == "false":
                        tr = t.get("timeRange", "")
                        # tr formato "00:00:00~06:00:00"
                        if tr:
                            tr = tr.replace("~", "-")
                            # Rimuoviamo i secondi se sono "00" per semplificare UI
                            parts = tr.split("-")
                            if len(parts) == 2:
                                s, e = parts[0][:5], parts[1][:5]
                                self.txt_screen_off_time.setText(f"{s}-{e}")
                            else:
                                self.txt_screen_off_time.setText(tr)
                        self.chk_screen_off.setChecked(True)
                        break
                        
        def on_error(err):
            self.chk_screen_off.setEnabled(True)
            QMessageBox.warning(self, "Errore Palinsesto Schermo", err)
            
        self.fetch_worker.finished.connect(on_tasks)
        self.fetch_worker.error.connect(on_error)
        self.fetch_worker.start()

    def on_screen_off_toggled(self, checked):
        self.txt_screen_off_time.setEnabled(checked)

    def on_program_selected(self, row):
        if row < 0: return

        # 1. Salva la configurazione del programma PRECEDENTE (se c'era)
        self._save_current_editor_to_memory()

        # 2. Blocca il salvataggio automatico mentre carichiamo il nuovo programma nell'editor
        self._loading = True

        item = self.lst_programs.item(row)
        uid = item.data(Qt.ItemDataRole.UserRole)
        self.current_selected_uuid = uid

        p = self.programs[uid]
        play_ctrl = p.get("playControl")
        status = p.get("status", "live")

        self.editor_panel.setEnabled(True)

        if status == "disabled":
            # Disattivata esplicitamente
            self.cmb_mode.setCurrentIndex(2)
            self._set_editor_defaults()
        elif play_ctrl is None:
            # Live: nessuna finestra oraria → Riproduci Sempre
            self.cmb_mode.setCurrentIndex(0)
            self._set_editor_defaults()
        else:
            # Personalizzato (programmed con playControl valido)
            self.cmb_mode.setCurrentIndex(1)
            # Giorni
            week = play_ctrl.get("week", {}).get("enable", "")
            enabled_days = week.split(",") if week else []
            for day_code, chk in self.chk_days.items():
                chk.setChecked(day_code in enabled_days)
            # Fasce orarie
            times = play_ctrl.get("time", [])
            time_strs = []
            for t in times:
                s = t.get("start", "")[:5]
                e = t.get("end", "")[:5]
                if s and e:
                    time_strs.append(f"{s}-{e}")
            self.txt_times.setText(", ".join(time_strs))

        # Fine caricamento: ora i segnali di modifica possono scattare normalmente
        self._loading = False

    def _set_editor_defaults(self):
        for chk in self.chk_days.values():
            chk.setChecked(True)
        self.txt_times.setText("")

    def on_mode_changed(self, index):
        is_custom = (index == 1)
        self.days_group.setEnabled(is_custom)
        self.time_group.setEnabled(is_custom)

    def _save_current_editor_to_memory(self):
        """Salva la configurazione dell'editor nella copia locale dei programmi.

        Viene chiamata quando si cambia selezione o alla conferma del dialog.
        Garantita di non scattare durante il caricamento iniziale grazie al flag _loading.
        """
        if not self.current_selected_uuid: return
        if getattr(self, "_loading", False): return

        p = self.programs[self.current_selected_uuid]

        idx = self.cmb_mode.currentIndex()
        if idx == 0:
            # "Riproduci Sempre" → live, nessun playControl
            p["playControl"] = None
            p["status"] = "live"
        elif idx == 2:
            # "Disattivata" → disabled, nessun playControl (no date-trappola!)
            p["playControl"] = None
            p["status"] = "disabled"
        else:
            # "Personalizzato" → programmed con playControl valido
            active_days = [day_code for day_code, chk in self.chk_days.items() if chk.isChecked()]
            if not active_days:
                active_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

            time_str = self.txt_times.text().strip()
            time_list = []
            if time_str:
                ranges = [r.strip() for r in time_str.split(",")]
                for r in ranges:
                    parts = r.split("-")
                    if len(parts) == 2:
                        s, e = parts[0].strip(), parts[1].strip()
                        if len(s) == 5: s += ":00"
                        if len(e) == 5: e += ":00"
                        time_list.append({"start": s, "end": e})
            if not time_list:
                time_list = [{"start": "00:00:00", "end": "23:59:59"}]

            p["playControl"] = {
                "week": {"enable": ",".join(active_days)},
                "date": [{"start": "2020-01-01", "end": "2099-12-31"}],
                "time": time_list,
            }
            p["status"] = "programmed"

        # Aggiorna l'icona nella lista
        for i in range(self.lst_programs.count()):
            lst_item = self.lst_programs.item(i)
            if lst_item.data(Qt.ItemDataRole.UserRole) == self.current_selected_uuid:
                name = p.get("name", "")
                status = p.get("status", "live")
                if status == "disabled":
                    display_name = f"🚫 {name}"
                elif p.get("playControl") is not None:
                    display_name = f"📅 {name}"
                else:
                    display_name = f"▶ {name}"
                lst_item.setText(display_name)
                break

    def on_save(self):
        self._save_current_editor_to_memory()

        # 1. Costruisci i task dello schermo
        screen_tasks = []
        if self.chk_screen_off.isChecked():
            tr = self.txt_screen_off_time.text().strip()
            if not tr:
                QMessageBox.warning(self, "Attenzione", "Inserire una fascia oraria per lo spegnimento.")
                return
            parts = tr.split("-")
            if len(parts) != 2:
                QMessageBox.warning(self, "Attenzione", "Formato spegnimento non valido. Usare HH:MM-HH:MM")
                return
            s = parts[0].strip()
            e = parts[1].strip()
            if len(s) == 5: s += ":00"
            if len(e) == 5: e += ":00"

            screen_tasks.append({
                "timeRange": f"{s}~{e}",
                "dateRange": "2024-01-01~2099-12-31",
                "MonthFilter": "Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec",
                "data": "false"
            })
        else:
            screen_tasks = []

        self.progress_dlg = QProgressDialog("Sincronizzazione orari schermo...", None, 0, 0, self)
        self.progress_dlg.setWindowTitle("Attendere")
        self.progress_dlg.setModal(True)
        self.progress_dlg.show()

        self.sync_worker = ScheduleSyncWorker(
            self.manager, self.device_id, screen_tasks, None
        )

        def on_done():
            self.progress_dlg.accept()
            QMessageBox.information(self, "Fatto", "Palinsesto sincronizzato correttamente.")
            self.accept()

        def on_error(err):
            self.progress_dlg.accept()
            QMessageBox.critical(self, "Errore", str(err))

        self.sync_worker.finished.connect(on_done)
        self.sync_worker.error.connect(on_error)
        self.sync_worker.start()
