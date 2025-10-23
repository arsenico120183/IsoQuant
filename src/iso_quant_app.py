# -*- coding: utf-8 -*-
# IsoQuant – Raw Means, Calibration & Quantification
# Version: 1.1.0 - Ottobre 2024
# Author: Francesco Norelli
# Requirements: pandas, numpy, matplotlib, openpyxl

import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

APP_TITLE = "IsoQuant v1.1.0 – Raw Means, Calibration & Quantification"

# ----------------- Caricamento standard da Excel -----------------
def load_standards_from_excel(excel_path="standards.xlsx"):
    """
    Carica gli standard di riferimento dal file Excel.

    Il file Excel deve avere:
    - Colonna A: Standard Name
    - Colonna B: d18O (‰)
    - Colonna C: d2H (‰)

    Se il file non esiste o c'è un errore, usa valori di default.
    """
    import os
    import sys

    # Valori di default (se il file Excel non esiste o ha errori)
    default_standards = {
        "NIVOLET": {"18O": -22.47, "2H": -171.6},
        "ORMEA":   {"18O": -11.52, "2H":  -77.9},
        "H2OPI":   {"18O":  -6.68, "2H":  -39.4},
        "SSW":     {"18O":  -0.54, "2H":   -2.2},
    }

    # Determina la directory dell'eseguibile o dello script
    if getattr(sys, 'frozen', False):
        # Se è un eseguibile PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Se è uno script Python normale
        script_dir = os.path.dirname(os.path.abspath(__file__))
        application_path = os.path.dirname(script_dir)

    # Costruisci il percorso completo del file Excel
    excel_full_path = os.path.join(application_path, excel_path)

    print(f"Cerco il file Excel in: {excel_full_path}")

    # Se il file non esiste, usa i valori di default
    if not os.path.exists(excel_full_path):
        print(f"File {excel_full_path} non trovato. Uso valori di default.")
        return default_standards

    excel_path = excel_full_path

    try:
        # Leggi il file Excel
        df = pd.read_excel(excel_path, sheet_name="Standards")

        # Rimuovi la riga di intestazione e righe vuote
        df = df.iloc[0:]  # Salta l'intestazione se necessario
        df = df.dropna(subset=[df.columns[0]])  # Rimuovi righe senza nome

        standards = {}
        for _, row in df.iterrows():
            name = str(row.iloc[0]).strip().upper()
            if name and name != "STANDARD NAME":  # Salta l'intestazione
                try:
                    d18O = float(row.iloc[1])
                    d2H = float(row.iloc[2])
                    standards[name] = {"18O": d18O, "2H": d2H}
                except (ValueError, IndexError):
                    continue  # Salta righe con dati invalidi

        if standards:
            print(f"Caricati {len(standards)} standard da {excel_path}")
            return standards
        else:
            print(f"Nessuno standard valido trovato in {excel_path}. Uso valori di default.")
            return default_standards

    except Exception as e:
        print(f"Errore nel leggere {excel_path}: {e}. Uso valori di default.")
        return default_standards

# Carica gli standard all'avvio
STD_DEFAULTS = load_standards_from_excel()
STD_NAMES = set(STD_DEFAULTS.keys())

# ----------------- Utility -----------------
def norm_std_name(s: str) -> str:
    if not isinstance(s, str): return ""
    s = s.strip().upper().replace(" ", "")
    if s.endswith("."): s = s[:-1]
    return s

def analysis_number(s: str) -> int:
    if not isinstance(s, str): return 0
    m = re.findall(r"\d+", s)
    return int(m[-1]) if m else 0

def fit_linear_with_r2(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    A = np.vstack([x, np.ones_like(x)]).T
    a, b = np.linalg.lstsq(A, y, rcond=None)[0]
    yhat = a*x + b
    ss_res = float(np.sum((y - yhat)**2))
    ss_tot = float(np.sum((y - np.mean(y))**2))
    r2 = 1.0 if ss_tot == 0 else max(0.0, 1.0 - ss_res/ss_tot)
    return float(a), float(b), float(r2)

def compute_stats(block: pd.DataFrame):
    if block is None or block.empty:
        return None
    d18Om  = block["d(18_16)Mean"].mean()
    d2Hm   = block["d(D_H)Mean"].mean()
    H2Om   = block["H2O_Mean"].mean()
    d18Osd = block["d(18_16)Mean"].std(ddof=1)
    d2Hsd  = block["d(D_H)Mean"].std(ddof=1)
    H2Osd  = block["H2O_Mean"].std(ddof=1)
    cond_d18O = "NO" if (pd.notna(d18Osd) and d18Osd >= 0.08) else "OK"
    cond_d2H  = "NO" if (pd.notna(d2Hsd)  and d2Hsd  >= 0.8 ) else "OK"
    return {
        "d18Om": d18Om, "d2Hm": d2Hm, "H2Om": H2Om,
        "d18Osd": d18Osd, "d2Hsd": d2Hsd, "H2Osd": H2Osd,
        "COND. d18O": cond_d18O, "COND. d2H": cond_d2H, "n": len(block)
    }

def parse_num(s: str) -> float:
    if s is None: return np.nan
    try:
        return float(str(s).replace(",", "."))
    except Exception:
        return np.nan

def row_std(values):
    # DEV.ST campionaria tra curve (ddof=1); se <2 valori validi => 0
    arr = np.asarray([v for v in values if pd.notna(v)], dtype=float)
    if arr.size < 2:
        return 0.0
    return float(np.std(arr, ddof=1))

# ----------------- Robust CSV loader -----------------
def read_csv_robust(path: str) -> pd.DataFrame:
    """Legge un CSV con separatore virgola mantenendo gli header originali."""
    encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'latin1', 'iso-8859-1']
    separators = [',', ';', '\t']
    
    for encoding in encodings:
        for sep in separators:
            try:
                df = pd.read_csv(path, sep=sep, engine='python', encoding=encoding, on_bad_lines='skip')
                if len(df.columns) > 5:  # Verifica che abbia abbastanza colonne
                    return df
            except Exception:
                continue
    
    # Ultimo tentativo con pandas standard
    try:
        df = pd.read_csv(path, engine='python', on_bad_lines='skip')
        return df
    except Exception as e:
        raise ValueError(f"Impossibile leggere il CSV: {os.path.basename(path)}. Errore: {e}")


# ----------------- App -----------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1500x980")
        self.minsize(1280, 860)
        
        # NUOVO: Tema professionale
        self._setup_professional_theme()

        # Dati per grafici (dal CSV originale)
        self.df = None
        self.analysis_vars = []
        self.only_stable = tk.BooleanVar(value=True)

        # indice campioni (Identifier 1 ↔ Analysis)
        self.sample_items = []    # [{"display","analysis","identifier"}]
        self.current_analysis = None
        self.current_identifier = None
        
        # NUOVO: Storage automatico delle selezioni per ogni campione
        self.sample_selections = {}  # {analysis: [list_of_selected_injections]}

        # Dati per calibrazione (da Excel raw_means)
        self.rm_df = None
        self.curves = []
        self.curves_summary = None

        # Quant
        self.quant_df = None

        # NUOVO: Quantificazione personalizzata
        self.custom_quant_df = None  # Risultati quantificazione personalizzata

        # Target degli standard (editabili da UI)
        self.std_targets = {k: v.copy() for k, v in STD_DEFAULTS.items()}

        # ---------- Top bar ----------
        top = ttk.Frame(self, style='Professional.TFrame'); top.pack(fill="x", padx=8, pady=6)
        ttk.Button(top, text="Load CSV…", command=self.load_csv, style='Professional.TButton').pack(side="left")
        ttk.Button(top, text="Load Excel (raw_means)…", command=self.load_excel_raw_means, style='Professional.TButton').pack(side="left", padx=6)
        ttk.Button(top, text="Standards (target)…", command=self.open_targets_dialog, style='Professional.TButton').pack(side="left", padx=6)
        self.path_lbl = ttk.Label(top, text="No file loaded", style='Muted.TLabel')
        self.path_lbl.pack(side="left", padx=8)

        ttk.Button(top, text="Export Excel (cal)", command=self.export_cal_excel, style='Professional.TButton').pack(side="right")
        ttk.Button(top, text="Export Excel (raw_means)", command=self.export_rm_excel, style='Professional.TButton').pack(side="right", padx=6)

        # ---------- Layout ----------
        left = ttk.Frame(self, style='Professional.TFrame'); left.pack(side="left", fill="y", padx=8, pady=6)
        right = ttk.Frame(self, style='Professional.TFrame'); right.pack(side="left", fill="both", expand=True, padx=8, pady=6)

        # ---------- Left: selezione per IDENTIFIER 1 ----------
        ttk.Label(left, text="Sample (Identifier 1):", style='Title.TLabel').pack(anchor="w")
        self.cmb_sample = ttk.Combobox(left, state="readonly", values=[], style='Professional.TCombobox')
        self.cmb_sample.bind("<<ComboboxSelected>>", lambda e: (self._on_sample_change(), self.refresh_injection_list(), self.recompute_plots()))
        self.cmb_sample.pack(fill="x", pady=(0,6))

        ttk.Checkbutton(left, text="Show only Good==1 & Ignore==0",
                        variable=self.only_stable, command=lambda: (self.refresh_injection_list(), self.recompute_plots())
                        ).pack(anchor="w")

        btns = ttk.Frame(left, style='Professional.TFrame'); btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Select All", command=self.select_all, style='Professional.TButton').pack(side="left", expand=True, fill="x", padx=(0,3))
        ttk.Button(btns, text="None", command=self.select_none, style='Professional.TButton').pack(side="left", expand=True, fill="x", padx=3)
        ttk.Button(left, text="Last 3 Stable", command=self.select_last3, style='Professional.TButton').pack(fill="x")

        ttk.Button(left, text="Write to raw_means", command=self.apply_all_to_raw_means, style='Professional.TButton').pack(fill="x", pady=4)
        
        # NUOVO: Indicatore selezioni salvate
        self.saved_indicator = ttk.Label(left, text="📊 Saved selections: 0", style='Muted.TLabel')
        self.saved_indicator.pack(fill="x", pady=2)

        inj_box = ttk.LabelFrame(left, text="Injections"); inj_box.pack(fill="both", expand=True, pady=(8,0))
        self.scroll = tk.Canvas(inj_box, height=300)
        self.scroll.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(inj_box, orient="vertical", command=self.scroll.yview); sb.pack(side="right", fill="y")
        self.scroll.configure(yscrollcommand=sb.set)
        self.inj_inner = ttk.Frame(self.scroll)
        self.scroll.create_window((0,0), window=self.inj_inner, anchor="nw")
        self.inj_inner.bind("<Configure>", lambda e: self.scroll.configure(scrollregion=self.scroll.bbox("all")))

        # ---------- Right tabs ----------
        self.tabs = ttk.Notebook(right, style='Professional.TNotebook'); self.tabs.pack(fill="both", expand=True)

        # Plot tabs
        self.tab1 = ttk.Frame(self.tabs); self.tabs.add(self.tab1, text="d(18_16)Mean")
        self.tab2 = ttk.Frame(self.tabs); self.tabs.add(self.tab2, text="d(D_H)Mean")
        self.tab3 = ttk.Frame(self.tabs); self.tabs.add(self.tab3, text="H2O_Mean")

        self.fig1 = Figure(figsize=(5,3), dpi=100); self.ax1 = self.fig1.add_subplot(111)
        self.fig2 = Figure(figsize=(5,3), dpi=100); self.ax2 = self.fig2.add_subplot(111)
        self.fig3 = Figure(figsize=(5,3), dpi=100); self.ax3 = self.fig3.add_subplot(111)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.tab1); self.canvas1.get_tk_widget().pack(fill="both", expand=True)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.tab2); self.canvas2.get_tk_widget().pack(fill="both", expand=True)
        self.canvas3 = FigureCanvasTkAgg(self.fig3, master=self.tab3); self.canvas3.get_tk_widget().pack(fill="both", expand=True)

        # Stats
        self.stats = ttk.LabelFrame(right, text="Statistics"); self.stats.pack(fill="x", pady=8)
        self.lbl_stats = ttk.Label(self.stats, text="--", justify="left", font=("Consolas", 10), style='Professional.TLabel')
        self.lbl_stats.pack(anchor="w", padx=6, pady=6)

        # ---- Cal tab ----
        self.tab_cal = ttk.Frame(self.tabs); self.tabs.add(self.tab_cal, text="Cal")

        self.curves_tree = ttk.Treeview(self.tab_cal,
            columns=("Use","Curve","Standards","a18","b18","R2_18","a2","b2","R2_2"),
            show="headings", height=6, style='Professional.Treeview')
        for c,w in [("Use",60),("Curve",80),("Standards",220),("a18",90),("b18",90),("R2_18",90),("a2",90),("b2",90),("R2_2",90)]:
            self.curves_tree.heading(c, text=c); self.curves_tree.column(c, width=w, anchor="center")
        self.curves_tree.pack(fill="x", padx=6, pady=(6,4))
        
        # NUOVO: Pulsanti per gestire selezione curve
        curves_btn_frame = ttk.Frame(self.tab_cal, style='Professional.TFrame')
        curves_btn_frame.pack(fill="x", padx=6, pady=4)
        ttk.Button(curves_btn_frame, text="Enable All Curves", command=self.enable_all_curves, style='Professional.TButton').pack(side="left", padx=3)
        ttk.Button(curves_btn_frame, text="Disable All", command=self.disable_all_curves, style='Professional.TButton').pack(side="left", padx=3)
        ttk.Button(curves_btn_frame, text="Apply Selection", command=self.apply_curve_selection, style='Professional.TButton').pack(side="left", padx=3)
        
        # Bind per toggle al doppio click
        self.curves_tree.bind("<Double-1>", self.toggle_curve_selection)

        grid_box = ttk.LabelFrame(self.tab_cal, text="Calibration Curves (target vs raw_means)")
        grid_box.pack(fill="both", expand=True, padx=6, pady=6)
        self.grid_canvas = tk.Canvas(grid_box)
        self.grid_canvas.pack(side="left", fill="both", expand=True)
        self.grid_scroll = ttk.Scrollbar(grid_box, orient="vertical", command=self.grid_canvas.yview)
        self.grid_scroll.pack(side="right", fill="y")
        self.grid_canvas.configure(yscrollcommand=self.grid_scroll.set)
        self.grid_inner = ttk.Frame(self.grid_canvas)
        self.grid_canvas.create_window((0,0), window=self.grid_inner, anchor="nw")
        self.grid_inner.bind("<Configure>", lambda e: self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox("all")))

        # ---- Quant tab ----
        self.tab_quant = ttk.Frame(self.tabs); self.tabs.add(self.tab_quant, text="Quantification")

        # NUOVO: Pulsante per quantificazione personalizzata
        custom_btn_frame = ttk.Frame(self.tab_quant, style='Professional.TFrame')
        custom_btn_frame.pack(fill="x", padx=6, pady=6)
        ttk.Button(custom_btn_frame, text="🎯 Quantificazione Personalizzata (scegli campioni e curve)",
                   command=self.open_custom_quant_window, style='Professional.TButton').pack(side="left", padx=3)

        # wrapper con scrollbar orizzontale e verticale
        quant_box = ttk.LabelFrame(self.tab_quant, text="Quantification (all enabled curves)")
        quant_box.pack(fill="both", expand=True, padx=6, pady=6)

        self.quant_canvas = tk.Canvas(quant_box)
        self.quant_canvas.pack(side="left", fill="both", expand=True)
        self.quant_vsb = ttk.Scrollbar(quant_box, orient="vertical", command=self.quant_canvas.yview)
        self.quant_hsb = ttk.Scrollbar(quant_box, orient="horizontal", command=self.quant_canvas.xview)
        self.quant_vsb.pack(side="right", fill="y")
        self.quant_hsb.pack(side="bottom", fill="x")
        self.quant_canvas.configure(yscrollcommand=self.quant_vsb.set, xscrollcommand=self.quant_hsb.set)

        self.quant_inner = ttk.Frame(self.quant_canvas)
        self.quant_canvas.create_window((0,0), window=self.quant_inner, anchor="nw")
        self.quant_inner.bind("<Configure>", lambda e: self.quant_canvas.configure(scrollregion=self.quant_canvas.bbox("all")))

        self.quant_tree = None  # creato dinamicamente

        # Status bar
        self.status = ttk.Label(self, anchor="w", text="", style='Muted.TLabel')
        self.status.pack(side="bottom", fill="x")

    def _setup_professional_theme(self):
        """Configura il tema professionale dell'applicazione."""
        # Colori professionali
        self.colors = {
            'primary': '#2C3E50',      # Blu scuro professionale
            'secondary': '#3498DB',    # Blu accento
            'success': '#27AE60',      # Verde successo
            'warning': '#F39C12',      # Arancione avviso
            'danger': '#E74C3C',       # Rosso errore
            'light': '#ECF0F1',        # Grigio chiaro
            'dark': '#34495E',         # Grigio scuro
            'white': '#FFFFFF',        # Bianco
            'text': '#2C3E50',         # Testo principale
            'text_muted': '#7F8C8D'    # Testo secondario
        }
        
        # COMPATIBILITÀ: Verifica se TTK è disponibile prima di configurare
        try:
            self._configure_ttk_styles()
        except Exception as e:
            print(f"Warning: TTK styling not available: {e}")
            # Fallback ai colori base
        
    def _configure_ttk_styles(self):
        """Configura gli stili TTK in modo sicuro."""
        # NUOVO: Palette scientifica per grafici
        self.chart_colors = {
            'o18': '#1f77b4',         # Blu professionale per δ18O
            'o18_dark': '#0d5a8a',    # Blu scuro per linea δ18O
            'd2h': '#d62728',         # Rosso professionale per δ2H  
            'd2h_dark': '#a31f1f',    # Rosso scuro per linea δ2H
            'grid': '#e0e0e0',       # Grigio chiaro per grid
            'background': '#fafafa',  # Sfondo molto chiaro
            'text': '#2c2c2c'        # Testo scuro
        }
        
        # Configura finestra principale
        self.configure(bg=self.colors['light'])
        
        # Configura stile TTK con fallback
        try:
            style = ttk.Style()
        except Exception:
            return  # TTK non disponibile, usa stili default
        style.theme_use('clam')  # Tema base moderno
        
        # Stile per i bottoni
        style.configure('Professional.TButton',
                       font=('Segoe UI', 9),
                       padding=(12, 8),
                       relief='flat')
        style.map('Professional.TButton',
                 background=[('active', self.colors['secondary']),
                           ('!active', self.colors['primary'])],
                 foreground=[('active', self.colors['white']),
                           ('!active', self.colors['white'])])
        
        # Stile per le label
        style.configure('Professional.TLabel',
                       font=('Segoe UI', 9),
                       background=self.colors['light'],
                       foreground=self.colors['text'])
        
        style.configure('Title.TLabel',
                       font=('Segoe UI', 11, 'bold'),
                       background=self.colors['light'],
                       foreground=self.colors['primary'])
        
        style.configure('Muted.TLabel',
                       font=('Segoe UI', 8),
                       background=self.colors['light'],
                       foreground=self.colors['text_muted'])
        
        # Stile per i frame
        style.configure('Professional.TFrame',
                       background=self.colors['light'],
                       relief='flat',
                       borderwidth=1)
        
        # Stile per le combobox
        style.configure('Professional.TCombobox',
                       font=('Segoe UI', 9),
                       fieldbackground=self.colors['white'])
        
        # Stile per i notebook (tabs)
        style.configure('Professional.TNotebook',
                       background=self.colors['light'],
                       borderwidth=0)
        style.configure('Professional.TNotebook.Tab',
                       font=('Segoe UI', 9),
                       padding=(12, 8),
                       background=self.colors['white'],
                       foreground=self.colors['text'])
        style.map('Professional.TNotebook.Tab',
                 background=[('selected', self.colors['secondary']),
                           ('!selected', self.colors['white'])],
                 foreground=[('selected', self.colors['white']),
                           ('!selected', self.colors['text'])])
        
        # Stile per treeview
        style.configure('Professional.Treeview',
                       font=('Segoe UI', 9),
                       background=self.colors['white'],
                       foreground=self.colors['text'],
                       fieldbackground=self.colors['white'])
        style.configure('Professional.Treeview.Heading',
                       font=('Segoe UI', 9, 'bold'),
                       background=self.colors['primary'],
                       foreground=self.colors['white'])
        
        # Font principale gestito tramite TTK styles
    
    def _apply_scientific_chart_style(self, ax, title_prefix, isotope_type):
        """Applica stile scientifico professionale ai grafici di calibrazione."""
        # Colori basati sul tipo di isotopo
        if isotope_type == 'o18':
            point_color = self.chart_colors['o18']
            line_color = self.chart_colors['o18_dark']
            isotope_symbol = 'δ¹⁸O'
        else:  # d2h
            point_color = self.chart_colors['d2h']
            line_color = self.chart_colors['d2h_dark']
            isotope_symbol = 'δ²H'
        
        # Configura sfondo e colori
        ax.set_facecolor(self.chart_colors['background'])
        
        # Grid professionale
        ax.grid(True, alpha=0.3, color=self.chart_colors['grid'], linewidth=0.5)
        ax.set_axisbelow(True)
        
        # Font e titoli scientifici
        ax.set_title(f"{title_prefix} - {isotope_symbol}", 
                    fontsize=11, fontweight='bold', 
                    color=self.chart_colors['text'], pad=15)
        
        # Etichette assi con simboli corretti
        ax.set_xlabel(f"Target {isotope_symbol} (‰)", 
                     fontsize=10, color=self.chart_colors['text'])
        ax.set_ylabel(f"Raw {isotope_symbol} (‰)", 
                     fontsize=10, color=self.chart_colors['text'])
        
        # Stile ticks
        ax.tick_params(axis='both', which='major', labelsize=9, 
                      colors=self.chart_colors['text'])
        
        # Bordi più sottili
        for spine in ax.spines.values():
            spine.set_color(self.chart_colors['grid'])
            spine.set_linewidth(0.8)
        
        return point_color, line_color

    # ----------- Helpers: indice campioni -----------
    def _build_sample_index(self):
        self.sample_items = []
        if self.df is None or self.df.empty: 
            self.cmb_sample["values"] = []; self.cmb_sample.set(""); return
        tmp = self.df.copy()
        
        # Usa "Identifier 1" se esiste, altrimenti usa "Analysis" come identificatore
        if "Identifier 1" in tmp.columns:
            tmp["Identifier 1"] = tmp["Identifier 1"].astype(str).str.strip()
            gid = (tmp.groupby("Analysis")["Identifier 1"]
                      .apply(lambda s: s.dropna().iloc[0] if not s.dropna().empty else "")
                      .reset_index())
            gid = gid.sort_values("Analysis", key=lambda s: s.map(analysis_number))
            values = []
            for _, r in gid.iterrows():
                ident = r["Identifier 1"] or "(sconosciuto)"
                analysis = r["Analysis"]
                display = f"{ident}  [{analysis}]"
                self.sample_items.append({"display": display, "analysis": analysis, "identifier": ident})
                values.append(display)
        else:
            # Fallback: usa Analysis come identificatore quando Identifier 1 non esiste
            gid = tmp.groupby("Analysis").size().reset_index()
            gid = gid.sort_values("Analysis", key=lambda s: s.map(analysis_number))
            values = []
            for _, r in gid.iterrows():
                analysis = r["Analysis"]
                display = f"{analysis}"
                self.sample_items.append({"display": display, "analysis": analysis, "identifier": analysis})
                values.append(display)
        
        self.cmb_sample["values"] = values
        if values:
            self.cmb_sample.current(0)
            self._on_sample_change()

    def _on_sample_change(self):
        # NUOVO: Salva automaticamente le selezioni del campione precedente
        if hasattr(self, 'current_analysis') and self.current_analysis:
            self._auto_save_current_selection()
        
        disp = self.cmb_sample.get()
        found = next((x for x in self.sample_items if x["display"] == disp), None)
        if found:
            self.current_analysis = found["analysis"]
            self.current_identifier = found["identifier"]
        else:
            self.current_analysis = None
            self.current_identifier = None
        
        # NUOVO: Aggiorna colore per il nuovo campione selezionato
        self._update_sample_colors()

    def _auto_save_current_selection(self):
        """Salva automaticamente le selezioni del campione corrente."""
        if self.current_analysis and hasattr(self, 'analysis_vars'):
            selected = self.selected_injections()
            if selected:  # Salva solo se ci sono selezioni
                self.sample_selections[self.current_analysis] = selected
                # Aggiorna status per feedback utente
                self.status.config(text=f"✓ Auto-salvato: {self.current_identifier} [{self.current_analysis}] - {len(selected)} iniezioni")
            else:
                # Rimuovi il campione se non ha selezioni
                self.sample_selections.pop(self.current_analysis, None)
            # Aggiorna indicatore
            self._update_saved_indicator()
    
    def _restore_saved_selection(self):
        """Ripristina le selezioni salvate per il campione corrente."""
        if self.current_analysis in self.sample_selections:
            saved_injections = set(self.sample_selections[self.current_analysis])
            for inj, var in self.analysis_vars:
                var.set(inj in saved_injections)
            return True
        return False

    def _update_saved_indicator(self):
        """Aggiorna l'indicatore del numero di selezioni salvate."""
        if hasattr(self, 'saved_indicator'):
            count = len(self.sample_selections)
            total_injections = sum(len(inj) for inj in self.sample_selections.values())
            self.saved_indicator.config(text=f"📊 Selezioni salvate: {count} campioni ({total_injections} iniezioni)")
        
        # NUOVO: Aggiorna anche i colori della combobox
        self._update_sample_colors()
    
    def _is_sample_completed(self, analysis):
        """Verifica se un campione ha raw_means completati (colonne non-NaN)."""
        if self.df is None or analysis is None:
            return False
        
        # Verifica se esistono colonne raw_means
        raw_means_cols = ["d18Om", "d2Hm", "H2Om", "d18Osd", "d2Hsd", "H2Osd", "COND. d18O", "COND. d2H"]
        available_cols = [col for col in raw_means_cols if col in self.df.columns]
        
        if not available_cols:
            return False
        
        # Trova la riga con l'ultima iniezione per questo Analysis
        sample_rows = self.df[self.df["Analysis"] == analysis]
        if sample_rows.empty:
            return False
        
        last_row = sample_rows.loc[sample_rows["Inj Nr"].idxmax()]
        
        # Verifica se almeno le colonne principali hanno dati
        main_cols = ["d18Om", "d2Hm", "H2Om"]
        main_available = [col for col in main_cols if col in self.df.columns]
        
        if not main_available:
            return False
        
        # Considera completato se almeno d18Om e d2Hm sono non-NaN
        has_d18O = "d18Om" in self.df.columns and pd.notna(last_row.get("d18Om"))
        has_d2H = "d2Hm" in self.df.columns and pd.notna(last_row.get("d2Hm"))
        
        return has_d18O and has_d2H
    
    def _update_sample_colors(self):
        """Aggiorna i colori di sfondo della combobox in base allo stato dei campioni."""
        if not hasattr(self, 'cmb_sample') or not self.sample_items:
            return
        
        # Configura stili per campioni completati e da fare
        style = ttk.Style()
        
        # Verde chiaro per completati
        style.configure('Completed.TCombobox',
                       fieldbackground='#E8F5E8',  # Verde molto chiaro
                       background='#E8F5E8')
        
        # Normale per da fare
        style.configure('Pending.TCombobox', 
                       fieldbackground=self.colors['white'],
                       background=self.colors['white'])
        
        # Determina lo stato del campione corrente
        current_analysis = self.current_analysis
        if current_analysis and self._is_sample_completed(current_analysis):
            self.cmb_sample.configure(style='Completed.TCombobox')
        else:
            self.cmb_sample.configure(style='Pending.TCombobox')

    def _on_injection_change(self):
        """Chiamato quando l'utente cambia selezioni iniezioni."""
        self.recompute_plots()
        # Auto-save immediato delle selezioni correnti
        self._auto_save_current_selection()

    def _get_selected_analysis(self):
        return self.current_analysis

    # ----------------- CSV: grafici -----------------
    def load_csv(self):
        path = filedialog.askopenfilename(title="Select CSV IsoQuant", filetypes=[("CSV", "*.csv"), ("All files", "*.*")])
        if not path: return
        try:
            df = read_csv_robust(path)
            # Gestisci "Identifier 1" (con spazi negli header)
            id_col = None
            for csv_col in df.columns:
                if csv_col.strip() == "Identifier 1":
                    id_col = csv_col
                    break
            if id_col:
                df["Identifier 1"] = df[id_col].astype(str).str.strip()
            
            # Gestisci "Analysis" (con spazi negli header)
            analysis_col = None
            for csv_col in df.columns:
                if csv_col.strip() == "Analysis":
                    analysis_col = csv_col
                    break
            if analysis_col:
                df["Analysis"] = df[analysis_col].astype(str).str.strip()
            
            for col in ["Inj Nr","Good","Ignore"]:
                csv_col = None
                for c in df.columns:
                    if c.strip() == col:
                        csv_col = c
                        break
                if csv_col:
                    # Gestione più robusta della conversione numerica
                    try:
                        if col in ["Good", "Ignore"]:
                            # Per Good/Ignore, gestisci valori speciali
                            temp = pd.to_numeric(df[csv_col], errors="coerce").fillna(0)
                            if col == "Good":
                                # Good: 1 rimane 1, tutto il resto diventa 0
                                df[col] = (temp == 1).astype(int)
                            else:  # Ignore
                                # Ignore: 0 = non ignorare, qualsiasi altro valore = ignorare
                                df[col] = (temp != 0).astype(int)
                        else:
                            df[col] = pd.to_numeric(df[csv_col], errors="coerce")
                    except Exception as e:
                        # Se fallisce, prova a pulire i dati prima
                        cleaned = df[csv_col].astype(str).str.replace(r'[^\d\.\-\+]', '', regex=True)
                        if col in ["Good", "Ignore"]:
                            temp = pd.to_numeric(cleaned, errors="coerce").fillna(0)
                            if col == "Good":
                                df[col] = (temp == 1).astype(int)
                            else:  # Ignore
                                df[col] = (temp != 0).astype(int)
                        else:
                            df[col] = pd.to_numeric(cleaned, errors="coerce")
            df = df.sort_values(["Analysis","Inj Nr"]).reset_index(drop=True)

            needed = ["Analysis","Inj Nr","Good","Ignore","d(18_16)Mean","d(D_H)Mean","H2O_Mean"]
            missing = []
            
            # Controlla ogni colonna necessaria
            for col in needed:
                if col in df.columns:
                    # Colonna già presente - verifica che sia numerica se necessario
                    if col in ["Good", "Ignore"]:
                        # Normalizza Good/Ignore per valori già presenti
                        temp = pd.to_numeric(df[col], errors="coerce").fillna(0)
                        if col == "Good":
                            df[col] = (temp == 1).astype(int)
                        else:  # Ignore
                            df[col] = (temp != 0).astype(int)
                    elif col in ["d(18_16)Mean","d(D_H)Mean","H2O_Mean"]:
                        try:
                            df[col] = pd.to_numeric(df[col], errors="coerce")
                        except Exception:
                            # Pulisci e riprova
                            df[col] = df[col].astype(str).str.replace(r'[^\d\.\-\+eE]', '', regex=True)
                            df[col] = pd.to_numeric(df[col], errors="coerce")
                    continue
                else:
                    # Cerca la colonna con spazi negli header
                    found = False
                    for csv_col in df.columns:
                        if csv_col.strip() == col:
                            if col in ["Good", "Ignore"]:
                                # Gestione robusta per flag Good/Ignore
                                temp = pd.to_numeric(df[csv_col], errors="coerce").fillna(0)
                                if col == "Good":
                                    df[col] = (temp == 1).astype(int)
                                else:  # Ignore
                                    df[col] = (temp != 0).astype(int)
                            elif col in ["d(18_16)Mean","d(D_H)Mean","H2O_Mean"]:
                                # Gestione robusta per colonne numeriche
                                try:
                                    df[col] = pd.to_numeric(df[csv_col], errors="coerce")
                                except Exception:
                                    # Pulisci e riprova
                                    df[col] = df[csv_col].astype(str).str.replace(r'[^\d\.\-\+eE]', '', regex=True)
                                    df[col] = pd.to_numeric(df[col], errors="coerce")
                            else:
                                df[col] = df[csv_col]
                            found = True
                            break
                    if not found:
                        missing.append(col)
            
            if missing:
                raise ValueError(f"Mancano colonne nel CSV: {missing}")

            self.df = df
            self.path_lbl.config(text=os.path.basename(path))
            self._build_sample_index()
            self.refresh_injection_list()
            self.recompute_plots()
            self.status.config(text="CSV caricato. Seleziona il campione (Identifier 1) dalla tendina.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_injection_list(self):
        for w in list(self.inj_inner.children.values()):
            w.destroy()
        self.analysis_vars.clear()
        if self.df is None: return
        a = self._get_selected_analysis()
        if not a: return
        g = self.df[self.df["Analysis"]==a].sort_values("Inj Nr")
        if self.only_stable.get():
            g = g[(g["Good"]==1) & (g["Ignore"]==0)]
        for _, r in g.iterrows():
            var = tk.BooleanVar(value=False)
            try:
                inj = int(r["Inj Nr"]) if pd.notna(r["Inj Nr"]) else 0
                good = int(r['Good']) if pd.notna(r['Good']) else 0
                ignore = int(r['Ignore']) if pd.notna(r['Ignore']) else 0
                
                # Gestisci valori NaN nei dati isotopici
                d18o = r['d(18_16)Mean'] if pd.notna(r['d(18_16)Mean']) else 0.0
                d2h = r['d(D_H)Mean'] if pd.notna(r['d(D_H)Mean']) else 0.0
                h2o = r['H2O_Mean'] if pd.notna(r['H2O_Mean']) else 0.0
                
                label = (f"Inj {inj:02d} | Good={good} Ign={ignore} | "
                         f"δ18O={d18o:.3f}  δ2H={d2h:.3f}  H2O={h2o:.0f}")
                cb = ttk.Checkbutton(self.inj_inner, text=label, variable=var, command=self._on_injection_change)
                cb.pack(anchor="w")
                self.analysis_vars.append((inj, var))
            except Exception as e:
                # Se c'è un errore con questa riga, la saltiamo
                continue
        # NUOVO: Ripristina selezioni salvate o usa default
        if not self._restore_saved_selection():
            self.select_last3(auto_only=True)
        self.recompute_plots()

    def selected_injections(self):
        return sorted([inj for inj, var in self.analysis_vars if var.get()])

    def select_all(self):
        for _, var in self.analysis_vars: var.set(True)
        self.recompute_plots()
        self._auto_save_current_selection()

    def select_none(self):
        for _, var in self.analysis_vars: var.set(False)
        self.recompute_plots()
        self._auto_save_current_selection()

    def select_last3(self, auto_only=False):
        if self.df is None: return
        a = self._get_selected_analysis()
        if not a: return
        
        try:
            # Filtra per Good==1 e Ignore==0, gestendo NaN
            good_mask = (self.df["Good"] == 1) | pd.isna(self.df["Good"])
            ignore_mask = (self.df["Ignore"] == 0) | pd.isna(self.df["Ignore"])
            g = self.df[(self.df["Analysis"]==a) & good_mask & ignore_mask].sort_values("Inj Nr")
            
            if len(g) >= 3:
                last3 = set(g["Inj Nr"].tail(3).astype(int).tolist())
            elif len(g) > 0:
                last3 = set(g["Inj Nr"].astype(int).tolist())
            else:
                last3 = set()
                
            for inj, var in self.analysis_vars:
                if inj in last3:
                    var.set(True)
                elif not auto_only:
                    var.set(False)
        except Exception as e:
            # Se c'è un errore, seleziona le ultime 3 disponibili
            if len(self.analysis_vars) >= 3:
                for i, (inj, var) in enumerate(self.analysis_vars):
                    var.set(i >= len(self.analysis_vars) - 3)
        if not auto_only: 
            self.recompute_plots()
            self._auto_save_current_selection()

    def recompute_plots(self):
        if self.df is None: return
        a = self._get_selected_analysis()
        if not a: return
        all_inj = self.df[self.df["Analysis"]==a].sort_values("Inj Nr")
        inj_sel = self.selected_injections()
        inj_sel_set = set(map(int, inj_sel))
        sel_block = all_inj[all_inj["Inj Nr"].isin(inj_sel_set)].sort_values("Inj Nr")

        sample_name = ""
        if not all_inj.empty and "Identifier 1" in all_inj.columns:
            vals = all_inj["Identifier 1"].dropna().astype(str).unique().tolist()
            sample_name = vals[0] if vals else ""
        if sel_block.empty:
            self.lbl_stats.config(text=f"{sample_name} [{a}] – seleziona almeno una iniezione.")
        else:
            s = compute_stats(sel_block)
            self.lbl_stats.config(text=(
                f"{sample_name}  [{a}]  | iniezioni selezionate: {inj_sel}  (n={s['n']})\n\n"
                f"d18Om = {s['d18Om']:.6f}     d18Osd = {s['d18Osd']:.6f}     COND. d18O = {s['COND. d18O']}\n"
                f"d2Hm  = {s['d2Hm']:.6f}      d2Hsd  = {s['d2Hsd']:.6f}      COND. d2H  = {s['COND. d2H']}\n"
                f"H2Om  = {s['H2Om']:.6f}      H2Osd  = {s['H2Osd']:.6f}\n"
            ))

        def draw(ax, series, title, ylabel):
            ax.clear()
            if all_inj.empty:
                ax.text(0.5, 0.5, "Nessuna iniezione disponibile", ha="center", va="center", transform=ax.transAxes)
            else:
                ax.plot(all_inj["Inj Nr"], all_inj[series], marker="o", linestyle="-", label="Tutte le iniezioni")
                if inj_sel_set:
                    hl = all_inj[all_inj["Inj Nr"].isin(inj_sel_set)]
                    ax.scatter(hl["Inj Nr"], hl[series], s=90, marker="o", edgecolors="k", linewidths=1.0, label="Selezionate")
                ax.legend(loc="best")
            ax.set_title(title); ax.set_xlabel("Inj Nr"); ax.set_ylabel(ylabel); ax.grid(True)

        draw(self.ax1, "d(18_16)Mean", f"{sample_name} – d(18_16)Mean", "d(18_16)Mean")
        draw(self.ax2, "d(D_H)Mean",   f"{sample_name} – d(D_H)Mean",   "d(D_H)Mean")
        draw(self.ax3, "H2O_Mean",     f"{sample_name} – H2O_Mean",     "H2O_Mean")
        for fig, canvas in [(self.fig1, self.canvas1),(self.fig2, self.canvas2),(self.fig3, self.canvas3)]:
            try: fig.tight_layout()
            except Exception: pass
            canvas.draw()

    # ----------------- Excel raw_means: curve & quant -----------------
    def load_excel_raw_means(self):
        path = filedialog.askopenfilename(title="Select Excel with 'raw_means' sheet",
                                          filetypes=[("Excel", "*.xlsx")])
        if not path: return
        try:
            rm = pd.read_excel(path, sheet_name="raw_means", engine="openpyxl")
            rm.columns = [str(c).strip() for c in rm.columns]

            needed = ["Analysis","Inj Nr","d18Om","d2Hm","Identifier 1"]
            missing = [c for c in needed if c not in rm.columns]
            if missing:
                raise ValueError(f"Nel foglio 'raw_means' mancano: {missing}")

            # Pulisci e normalizza i dati prima di qualsiasi operazione
            rm = rm.sort_values(["Analysis","Inj Nr"]).reset_index(drop=True)
            valid = rm.dropna(subset=["d18Om","d2Hm"], how="all")
            
            # MANTIENI TUTTE LE RIPETIZIONI - sono dati legittimi per la calibrazione!
            # Per la calibrazione servono TUTTI i punti standard, non uno solo
            self.rm_df = valid.copy()

            # arricchimenti
            self.rm_df["Identifier 1"] = self.rm_df["Identifier 1"].astype(str).str.strip()
            if "Identifier" in self.rm_df.columns:
                self.rm_df["Identifier"] = self.rm_df["Identifier"].astype(str).str.strip()
            self.rm_df["STD_NAME"] = self.rm_df["Identifier 1"].apply(norm_std_name)
            self.rm_df["Analysis_num"] = self.rm_df["Analysis"].apply(analysis_number)
            self.rm_df = self.rm_df.sort_values("Analysis_num").reset_index(drop=True)

            # Rileva curve, disegna, quantifica
            self.detect_curves_from_blocks()
            self.render_cal_tab()
            self.compute_quant_table()
            self.render_quant_tab()

            self.path_lbl.config(text=os.path.basename(path))
            self.status.config(text=f"Caricato '{os.path.basename(path)}' – curve: {len(self.curves)}; campioni: {len(self.quant_df) if self.quant_df is not None else 0}.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def detect_curves_from_blocks(self):
        """Rileva automaticamente gruppi di standard basandosi sui PATTERN RIPETUTI."""
        self.curves = []
        rows = self.rm_df.copy()
        
        # Trova tutte le righe di standard
        std_rows = rows[rows["STD_NAME"].isin(STD_NAMES)].copy()
        if std_rows.empty:
            return
        
        # NUOVA LOGICA: Riconosci pattern ripetuti di sequenze di standard
        std_sequence = std_rows["STD_NAME"].tolist()
        # Identifica il pattern base (prime 3-4 occorrenze uniche)
        seen_standards = []
        pattern_length = 0
        for std in std_sequence:
            if std not in seen_standards:
                seen_standards.append(std)
                pattern_length += 1
            else:
                # Abbiamo trovato una ripetizione, il pattern base è completo
                break
        
        # Raggruppa in base al pattern rilevato
        if pattern_length > 0:
            blocks = []
            current_block = []
            pattern_count = 0
            
            for i, std in enumerate(std_sequence):
                current_block.append(std_rows.iloc[i])
                pattern_count += 1
                
                # Se abbiamo completato un pattern, inizia nuovo blocco
                if pattern_count == pattern_length:
                    blocks.append(pd.DataFrame(current_block))
                    current_block = []
                    pattern_count = 0
            
            # Aggiungi eventuale blocco incompleto
            if current_block:
                blocks.append(pd.DataFrame(current_block))
        else:
            # Fallback: un solo blocco
            blocks = [std_rows]
        
        block_dfs = blocks
        
        if not block_dfs:
            return

        # Costruisci curve dai blocchi (media per standard, fit e R2)
        # MODIFICA: Usa TUTTE le curve anche con pochi punti
        for i, dfb in enumerate(block_dfs, start=1):
            if dfb.empty: continue
            gb = dfb.groupby("STD_NAME", as_index=False).agg({"d18Om":"mean","d2Hm":"mean"})
            x18, y18, x2, y2, used = [], [], [], [], []
            for _, rr in gb.iterrows():
                sname = rr["STD_NAME"]
                if sname in self.std_targets:
                    if pd.notna(rr["d18Om"]):
                        x18.append(float(rr["d18Om"])); y18.append(float(self.std_targets[sname]["18O"]))
                    if pd.notna(rr["d2Hm"]):
                        x2.append(float(rr["d2Hm"]));   y2.append(float(self.std_targets[sname]["2H"]))
                    used.append(sname)
            
            # MODIFICA CRITICA: NON SCARTARE mai i blocchi, crea sempre una curva
            # Anche se ha pochi punti per la regressione
            if len(used) > 0:  # Basta che ci sia almeno uno standard valido
                # Per 18O
                if len(x18) >= 2:
                    a18,b18,R2_18 = fit_linear_with_r2(x18, y18)
                elif len(x18) == 1:
                    # Un solo punto: usa slope=1 e calcola intercetta
                    a18, b18, R2_18 = 1.0, float(y18[0] - x18[0]), 0.0
                else:
                    a18, b18, R2_18 = 1.0, 0.0, 0.0  # Nessun dato valido per 18O
                
                # Per 2H
                if len(x2) >= 2:
                    a2, b2, R2_2 = fit_linear_with_r2(x2, y2)
                elif len(x2) == 1:
                    # Un solo punto: usa slope=1 e calcola intercetta
                    a2, b2, R2_2 = 1.0, float(y2[0] - x2[0]), 0.0
                else:
                    a2, b2, R2_2 = 1.0, 0.0, 0.0  # Nessun dato valido per 2H
                
                self.curves.append({
                    "id": f"cal{i}",
                    "std_used": sorted(set(used)),
                    "pts18_x": x18, "pts18_y": y18, "a18": a18, "b18": b18, "R2_18": R2_18,
                    "pts2_x":  x2,  "pts2_y":  y2,  "a2":  a2,  "b2":  b2,  "R2_2":  R2_2,
                    "enabled": True,  # NUOVO: Flag per abilitare/disabilitare curve
                })
            # else: blocco scartato se non ha standard riconosciuti

        self.curves_summary = pd.DataFrame([{
            "Curve": c["id"], "Standards": ", ".join(c["std_used"]),
            "a18": c["a18"], "b18": c["b18"], "R2_18": c["R2_18"],
            "a2": c["a2"], "b2": c["b2"], "R2_2": c["R2_2"]
        } for c in self.curves])

    # NUOVO: Metodi per gestire selezione curve
    def enable_all_curves(self):
        """Abilita tutte le curve per la quantificazione."""
        for curve in self.curves:
            curve["enabled"] = True
        self.render_cal_tab()
        
    def disable_all_curves(self):
        """Disabilita tutte le curve per la quantificazione."""
        for curve in self.curves:
            curve["enabled"] = False
        self.render_cal_tab()
    
    def toggle_curve_selection(self, event):
        """Toggle dello stato di una curva al doppio click."""
        selection = self.curves_tree.selection()
        if selection:
            item = selection[0]
            # Trova l'indice della curva dalla riga selezionata
            row_index = self.curves_tree.index(item)
            if 0 <= row_index < len(self.curves):
                self.curves[row_index]["enabled"] = not self.curves[row_index].get("enabled", True)
                self.render_cal_tab()
    
    def apply_curve_selection(self):
        """Ricalcola la quantificazione usando solo le curve selezionate."""
        if not self.curves:
            messagebox.showwarning("Warning", "No curves available.")
            return
        enabled_count = sum(1 for c in self.curves if c.get("enabled", True))
        if enabled_count == 0:
            messagebox.showwarning("Warning", "Select at least one curve for quantification.")
            return
        self.compute_quant_table()
        self.render_quant_tab()
        self.status.config(text=f"Quantification recalculated using {enabled_count} selected curves.")

    def render_cal_tab(self):
        for i in self.curves_tree.get_children():
            self.curves_tree.delete(i)
        for c in self.curves:
            enabled_text = "✓" if c.get("enabled", True) else "✗"
            self.curves_tree.insert("", "end", values=(
                enabled_text, c["id"], ", ".join(c["std_used"]),
                f"{c['a18']:.6f}", f"{c['b18']:.6f}", f"{c['R2_18']:.6f}",
                f"{c['a2']:.6f}",  f"{c['b2']:.6f}",  f"{c['R2_2']:.6f}",
            ))

        for w in list(self.grid_inner.children.values()):
            w.destroy()

        if not self.curves:
            info = ttk.Label(self.grid_inner, text="Nessuna curva trovata nel foglio 'raw_means'.")
            info.grid(row=0, column=0, sticky="w", padx=6, pady=6)
            return

        for r, c in enumerate(self.curves):
            # δ18O - STYLING SCIENTIFICO PROFESSIONALE
            f18 = ttk.Frame(self.grid_inner); f18.grid(row=r, column=0, padx=8, pady=8, sticky="nsew")
            fig18 = Figure(figsize=(4.5,3.5), dpi=100, facecolor='white')
            ax18 = fig18.add_subplot(111)
            
            # Applica stile scientifico
            point_color18, line_color18 = self._apply_scientific_chart_style(ax18, c['id'], 'o18')
            
            # SCATTER POINTS con stile professionale
            ax18.scatter(c["pts18_y"], c["pts18_x"], 
                        s=80, c=point_color18, alpha=0.8, edgecolors='white', 
                        linewidths=2, zorder=5)
            
            # LINEA DI REGRESSIONE con stile elegante
            if len(c["pts18_y"]) > 0:
                xs = np.array([min(c["pts18_y"]), max(c["pts18_y"])])
                ys = (xs - c["b18"]) / c["a18"] if c["a18"] != 0 else xs
                ax18.plot(xs, ys, color=line_color18, linewidth=2.5, alpha=0.9, zorder=4)
            
            # EQUAZIONE con box elegante
            a_inv = 1.0 / c["a18"] if c["a18"] != 0 else 1.0
            b_inv = -c["b18"] / c["a18"] if c["a18"] != 0 else 0.0
            equation_text = f"y = {a_inv:.4f}x + {b_inv:.4f}\nR² = {c['R2_18']:.4f}"
            ax18.text(0.05, 0.95, equation_text, transform=ax18.transAxes, 
                     fontsize=9, ha="left", va="top",
                     bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8, edgecolor=point_color18))
            
            fig18.tight_layout(pad=2.0)
            FigureCanvasTkAgg(fig18, master=f18).get_tk_widget().pack(fill="both", expand=True)

            # δ2H - STYLING SCIENTIFICO PROFESSIONALE  
            f2 = ttk.Frame(self.grid_inner); f2.grid(row=r, column=1, padx=8, pady=8, sticky="nsew")
            fig2 = Figure(figsize=(4.5,3.5), dpi=100, facecolor='white')
            ax2 = fig2.add_subplot(111)
            
            # Applica stile scientifico
            point_color2h, line_color2h = self._apply_scientific_chart_style(ax2, c['id'], 'd2h')
            
            # SCATTER POINTS con stile professionale
            ax2.scatter(c["pts2_y"], c["pts2_x"], 
                       s=80, c=point_color2h, alpha=0.8, edgecolors='white', 
                       linewidths=2, zorder=5)
            
            # LINEA DI REGRESSIONE con stile elegante
            if len(c["pts2_y"]) > 0:
                xs2 = np.array([min(c["pts2_y"]), max(c["pts2_y"])])
                ys2 = (xs2 - c["b2"]) / c["a2"] if c["a2"] != 0 else xs2
                ax2.plot(xs2, ys2, color=line_color2h, linewidth=2.5, alpha=0.9, zorder=4)
            
            # EQUAZIONE con box elegante
            a_inv2 = 1.0 / c["a2"] if c["a2"] != 0 else 1.0
            b_inv2 = -c["b2"] / c["a2"] if c["a2"] != 0 else 0.0
            equation_text2 = f"y = {a_inv2:.4f}x + {b_inv2:.4f}\nR² = {c['R2_2']:.4f}"
            ax2.text(0.05, 0.95, equation_text2, transform=ax2.transAxes, 
                    fontsize=9, ha="left", va="top",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8, edgecolor=point_color2h))
            
            fig2.tight_layout(pad=2.0)
            FigureCanvasTkAgg(fig2, master=f2).get_tk_widget().pack(fill="both", expand=True)

    # ----------------- QUANT: calcolo & UI -----------------
    def compute_quant_table(self):
        """Per ogni campione non-standard, ricalcola su tutte le curve e calcola mean/SD tra curve e ERR."""
        self.quant_df = None
        if self.rm_df is None or self.rm_df.empty or not self.curves:
            return

        # campioni = righe NON standard
        samples = self.rm_df[self.rm_df["STD_NAME"].isin(STD_NAMES) == False].copy()
        if samples.empty:
            self.quant_df = pd.DataFrame()
            return

        # MODIFICA: Conta solo le curve abilitate
        enabled_curves = [c for c in self.curves if c.get("enabled", True)]
        ncurves = len(enabled_curves)
        ric18_cols = [f"d18O_ric{i+1}" for i in range(ncurves)]
        ric2_cols  = [f"d2H_ric{i+1}"  for i in range(ncurves)]

        # metadata da portare avanti se esistono
        meta_cols = [c for c in ["Identifier 1","Identifier","Siringa","H2Osd","COND. d18O","COND. d2H","d18Osd","d2Hsd","Analysis"]
                     if c in samples.columns]

        out_rows = []
        for _, r in samples.iterrows():
            row = {mc: r.get(mc, np.nan) for mc in meta_cols}
            # ric calcolate su tutte le curve
            d18Om = r.get("d18Om", np.nan)
            d2Hm  = r.get("d2Hm",  np.nan)

            ric18_vals = []
            ric2_vals  = []
            # MODIFICA: Usa solo le curve abilitate per la quantificazione
            enabled_curves = [c for c in self.curves if c.get("enabled", True)]
            for c in enabled_curves:
                ric18 = np.nan if pd.isna(d18Om) else (c["a18"]*float(d18Om) + c["b18"])
                ric2  = np.nan if pd.isna(d2Hm)  else (c["a2"] *float(d2Hm)  + c["b2"])
                ric18_vals.append(ric18)
                ric2_vals.append(ric2)

            for name, val in zip(ric18_cols, ric18_vals): row[name] = val
            for name, val in zip(ric2_cols,  ric2_vals):  row[name] = val

            # media e DEV.ST tra curve (tutte le curve presenti)
            # se <2 valori validi, DEV.ST tra curve = 0
            d18Omean = float(np.nanmean(ric18_vals)) if np.isfinite(np.nanmean(ric18_vals)) else np.nan
            d2Hmean  = float(np.nanmean(ric2_vals))  if np.isfinite(np.nanmean(ric2_vals))  else np.nan
            Y  = row_std(ric18_vals)  # DEV.ST tra curve per 18O
            AA = row_std(ric2_vals)   # DEV.ST tra curve per 2H

            row["d18Omean"] = d18Omean
            row["d2Hmean"]  = d2Hmean
            row["Y (DEV.ST 18O tra curve)"]  = Y
            row["AA (DEV.ST 2H tra curve)"] = AA

            # SD intra-campione (dal raw_means)
            J = r.get("d18Osd", np.nan)
            K = r.get("d2Hsd",  np.nan)
            J = 0.0 if pd.isna(J) else float(J)
            K = 0.0 if pd.isna(K) else float(K)

            row["ERR d18O"] = float(np.sqrt(J*J + Y*Y)) if (np.isfinite(J) and np.isfinite(Y)) else np.nan
            row["ERR d2H"]  = float(np.sqrt(K*K + AA*AA)) if (np.isfinite(K) and np.isfinite(AA)) else np.nan

            out_rows.append(row)

        qdf = pd.DataFrame(out_rows)

        # ordina colonne: meta | ric18* | ric2* | mean/sd/err
        cols_meta = [c for c in ["Identifier 1","Identifier","Siringa","H2Osd","COND. d18O","COND. d2H","d18Osd","d2Hsd","Analysis"] if c in qdf.columns]
        cols_ric18 = [c for c in ric18_cols if c in qdf.columns]
        cols_ric2  = [c for c in ric2_cols if c in qdf.columns]
        cols_stats = ["d18Omean","d2Hmean","Y (DEV.ST 18O tra curve)","AA (DEV.ST 2H tra curve)","ERR d18O","ERR d2H"]
        cols_stats = [c for c in cols_stats if c in qdf.columns]

        self.quant_df = qdf[cols_meta + cols_ric18 + cols_ric2 + cols_stats]

    def render_quant_tab(self):
        # reset
        for w in list(self.quant_inner.children.values()):
            w.destroy()
        self.quant_tree = None

        if self.quant_df is None or self.quant_df.empty:
            ttk.Label(self.quant_inner, text="Nessun campione da quantificare o nessuna curva disponibile.").pack(anchor="w", padx=8, pady=8)
            return

        cols = list(self.quant_df.columns)
        self.quant_tree = ttk.Treeview(self.quant_inner, columns=cols, show="headings", height=18)
        for c in cols:
            self.quant_tree.heading(c, text=c)
            # larghezze base
            w = 130
            if c in ["Identifier 1","Identifier"]: w = 180
            if "ric" in c: w = 100
            if c.startswith("ERR"): w = 110
            self.quant_tree.column(c, width=w, anchor="center")
        self.quant_tree.pack(fill="both", expand=True)

        # scrollbar della tree (ri-usa quelle del canvas)
        def _on_tree_configure(event=None):
            self.quant_canvas.configure(scrollregion=self.quant_canvas.bbox("all"))
        self.quant_tree.bind("<Configure>", _on_tree_configure)

        # inserisci righe (limita cifre)
        def fmt(x, n=3):
            try:
                if pd.isna(x): return ""
                return f"{float(x):.{n}f}"
            except Exception:
                return str(x)

        for _, r in self.quant_df.iterrows():
            vals = []
            for c in cols:
                if c.startswith("d18O_ric") or c.startswith("d2H_ric"):
                    vals.append(fmt(r[c], 3))
                elif c in ["d18Omean","d2Hmean"]:
                    vals.append(fmt(r[c], 3))
                elif c.startswith("ERR"):
                    vals.append(fmt(r[c], 3))
                elif "DEV.ST" in c:
                    vals.append(fmt(r[c], 3))
                elif c in ["d18Osd","d2Hsd","H2Osd"]:
                    vals.append(fmt(r[c], 3))
                else:
                    vals.append("" if pd.isna(r[c]) else str(r[c]))
            self.quant_tree.insert("", "end", values=vals)

    # ----------------- NUOVO: Quantificazione Personalizzata -----------------
    def open_custom_quant_window(self):
        """Apre finestra per quantificazione personalizzata con selezione campioni e curve."""
        if self.rm_df is None or self.rm_df.empty:
            messagebox.showwarning("Warning", "Carica prima un file Excel con 'raw_means'.")
            return
        if not self.curves:
            messagebox.showwarning("Warning", "Nessuna curva di calibrazione disponibile.")
            return

        # Ottieni lista campioni (non-standard)
        samples = self.rm_df[self.rm_df["STD_NAME"].isin(STD_NAMES) == False].copy()
        if samples.empty:
            messagebox.showwarning("Warning", "Nessun campione da quantificare trovato.")
            return

        # Crea finestra popup
        win = tk.Toplevel(self)
        win.title("🎯 Quantificazione Personalizzata")
        win.geometry("950x750")
        win.transient(self)
        win.grab_set()

        # --- SEZIONE CURVE ---
        curve_frame = ttk.LabelFrame(win, text="📊 Seleziona Curve di Calibrazione")
        curve_frame.pack(fill="x", padx=10, pady=10)

        # Checkbox per ogni curva
        curve_vars = {}
        curve_checkbox_frame = ttk.Frame(curve_frame)
        curve_checkbox_frame.pack(fill="x", padx=10, pady=10)

        for i, curve in enumerate(self.curves):
            var = tk.BooleanVar(value=curve.get("enabled", True))
            curve_vars[curve["id"]] = var
            cb = ttk.Checkbutton(curve_checkbox_frame,
                                text=f"{curve['id']} ({', '.join(curve['std_used'])})",
                                variable=var)
            cb.pack(side="left", padx=5)

        # Pulsanti rapidi per curve
        curve_btn_frame = ttk.Frame(curve_frame)
        curve_btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(curve_btn_frame, text="Seleziona Tutte",
                  command=lambda: [var.set(True) for var in curve_vars.values()]).pack(side="left", padx=3)
        ttk.Button(curve_btn_frame, text="Deseleziona Tutte",
                  command=lambda: [var.set(False) for var in curve_vars.values()]).pack(side="left", padx=3)

        # --- SEZIONE CAMPIONI ---
        sample_frame = ttk.LabelFrame(win, text="📋 Seleziona Campioni (Ctrl+Click per selezione multipla)")
        sample_frame.pack(fill="both", expand=False, padx=10, pady=10)
        sample_frame.config(height=150)  # Altezza controllata

        # Listbox con scrollbar per campioni
        listbox_frame = ttk.Frame(sample_frame)
        listbox_frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        sample_listbox = tk.Listbox(listbox_frame, selectmode=tk.EXTENDED,
                                    yscrollcommand=scrollbar.set, height=10,
                                    font=("Segoe UI", 10))
        sample_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=sample_listbox.yview)

        # Popola listbox con campioni unici
        sample_identifiers = samples["Identifier 1"].unique().tolist()
        for identifier in sample_identifiers:
            sample_listbox.insert(tk.END, identifier)

        # Pulsanti rapidi per campioni
        sample_btn_frame = ttk.Frame(sample_frame)
        sample_btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(sample_btn_frame, text="Seleziona Tutti",
                  command=lambda: sample_listbox.select_set(0, tk.END)).pack(side="left", padx=3)
        ttk.Button(sample_btn_frame, text="Deseleziona Tutti",
                  command=lambda: sample_listbox.selection_clear(0, tk.END)).pack(side="left", padx=3)

        # --- PULSANTI AZIONE (SPOSTATI SOPRA I RISULTATI) ---
        action_frame_top = ttk.Frame(win, style='Professional.TFrame')
        action_frame_top.pack(fill="x", padx=10, pady=15)

        # Placeholder per i pulsanti (verranno definiti dopo le funzioni)

        # --- SEZIONE RISULTATI ---
        result_frame = ttk.LabelFrame(win, text="📈 Risultati Quantificazione")
        result_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Canvas con scrollbar per tabella risultati
        result_canvas = tk.Canvas(result_frame)
        result_vsb = ttk.Scrollbar(result_frame, orient="vertical", command=result_canvas.yview)
        result_hsb = ttk.Scrollbar(result_frame, orient="horizontal", command=result_canvas.xview)
        result_vsb.pack(side="right", fill="y")
        result_hsb.pack(side="bottom", fill="x")
        result_canvas.pack(side="left", fill="both", expand=True)
        result_canvas.configure(yscrollcommand=result_vsb.set, xscrollcommand=result_hsb.set)

        result_inner = ttk.Frame(result_canvas)
        result_canvas.create_window((0,0), window=result_inner, anchor="nw")
        result_inner.bind("<Configure>", lambda e: result_canvas.configure(scrollregion=result_canvas.bbox("all")))

        result_tree = None  # Verrà creato dinamicamente

        # --- FUNZIONE CALCOLO ---
        def calculate_custom_quant():
            nonlocal result_tree

            # Ottieni curve selezionate
            selected_curves = [cid for cid, var in curve_vars.items() if var.get()]
            if not selected_curves:
                messagebox.showwarning("Warning", "Seleziona almeno una curva.")
                return

            # Ottieni campioni selezionati
            selected_indices = sample_listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("Warning", "Seleziona almeno un campione.")
                return

            selected_samples = [sample_identifiers[i] for i in selected_indices]

            # Filtra campioni
            samples_to_quant = samples[samples["Identifier 1"].isin(selected_samples)].copy()

            # Filtra curve
            curves_to_use = [c for c in self.curves if c["id"] in selected_curves]

            # Calcola quantificazione
            quant_result = self._compute_custom_quant(samples_to_quant, curves_to_use)
            self.custom_quant_df = quant_result

            # Mostra risultati
            if result_tree:
                result_tree.destroy()

            if quant_result is None or quant_result.empty:
                ttk.Label(result_inner, text="Nessun risultato disponibile.").pack(padx=10, pady=10)
                return

            cols = list(quant_result.columns)
            result_tree = ttk.Treeview(result_inner, columns=cols, show="headings", height=10)

            for c in cols:
                result_tree.heading(c, text=c)
                w = 130
                if c in ["Identifier 1", "Identifier"]: w = 180
                if "ric" in c: w = 100
                if c.startswith("ERR"): w = 110
                result_tree.column(c, width=w, anchor="center")

            result_tree.pack(fill="both", expand=True)

            # Inserisci righe
            def fmt(x, n=3):
                try:
                    if pd.isna(x): return ""
                    return f"{float(x):.{n}f}"
                except Exception:
                    return str(x)

            for _, r in quant_result.iterrows():
                vals = []
                for c in cols:
                    if c.startswith("d18O_ric") or c.startswith("d2H_ric"):
                        vals.append(fmt(r[c], 3))
                    elif c in ["d18Omean", "d2Hmean"]:
                        vals.append(fmt(r[c], 3))
                    elif c.startswith("ERR"):
                        vals.append(fmt(r[c], 3))
                    elif "DEV.ST" in c:
                        vals.append(fmt(r[c], 3))
                    elif c in ["d18Osd", "d2Hsd", "H2Osd"]:
                        vals.append(fmt(r[c], 3))
                    else:
                        vals.append("" if pd.isna(r[c]) else str(r[c]))
                result_tree.insert("", "end", values=vals)

            self.status.config(text=f"Quantificazione personalizzata: {len(selected_samples)} campioni, {len(selected_curves)} curve.")

        # --- FUNZIONE EXPORT ---
        def export_custom_quant():
            if self.custom_quant_df is None or self.custom_quant_df.empty:
                messagebox.showwarning("Warning", "Calcola prima la quantificazione personalizzata.")
                return

            path = filedialog.asksaveasfilename(title="Salva Excel (quantificazione personalizzata)",
                                               defaultextension=".xlsx",
                                               filetypes=[("Excel", "*.xlsx")])
            if not path: return

            try:
                with pd.ExcelWriter(path, engine="openpyxl") as xw:
                    self.custom_quant_df.to_excel(xw, sheet_name="custom_quant", index=False)
                messagebox.showinfo("Success", f"Excel salvato: {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        # --- PULSANTI AZIONE (ORA SOPRA I RISULTATI) ---
        ttk.Button(action_frame_top, text="🔄 Calcola e Mostra Quantificazione",
                  command=calculate_custom_quant, style='Professional.TButton').pack(side="left", padx=5)
        ttk.Button(action_frame_top, text="💾 Esporta Excel",
                  command=export_custom_quant, style='Professional.TButton').pack(side="left", padx=5)
        ttk.Button(action_frame_top, text="❌ Chiudi",
                  command=win.destroy, style='Professional.TButton').pack(side="right", padx=5)

    def _compute_custom_quant(self, samples_df, curves_list):
        """Calcola quantificazione personalizzata per campioni e curve selezionate."""
        if samples_df.empty or not curves_list:
            return pd.DataFrame()

        ncurves = len(curves_list)
        ric18_cols = [f"d18O_ric{i+1}" for i in range(ncurves)]
        ric2_cols = [f"d2H_ric{i+1}" for i in range(ncurves)]

        meta_cols = [c for c in ["Identifier 1", "Identifier", "Siringa", "H2Osd", "COND. d18O", "COND. d2H", "d18Osd", "d2Hsd", "Analysis"]
                     if c in samples_df.columns]

        out_rows = []
        for _, r in samples_df.iterrows():
            row = {mc: r.get(mc, np.nan) for mc in meta_cols}
            d18Om = r.get("d18Om", np.nan)
            d2Hm = r.get("d2Hm", np.nan)

            ric18_vals = []
            ric2_vals = []
            for c in curves_list:
                ric18 = np.nan if pd.isna(d18Om) else (c["a18"] * float(d18Om) + c["b18"])
                ric2 = np.nan if pd.isna(d2Hm) else (c["a2"] * float(d2Hm) + c["b2"])
                ric18_vals.append(ric18)
                ric2_vals.append(ric2)

            for name, val in zip(ric18_cols, ric18_vals): row[name] = val
            for name, val in zip(ric2_cols, ric2_vals): row[name] = val

            d18Omean = float(np.nanmean(ric18_vals)) if np.isfinite(np.nanmean(ric18_vals)) else np.nan
            d2Hmean = float(np.nanmean(ric2_vals)) if np.isfinite(np.nanmean(ric2_vals)) else np.nan
            Y = row_std(ric18_vals)
            AA = row_std(ric2_vals)

            row["d18Omean"] = d18Omean
            row["d2Hmean"] = d2Hmean
            row["Y (DEV.ST 18O tra curve)"] = Y
            row["AA (DEV.ST 2H tra curve)"] = AA

            J = r.get("d18Osd", np.nan)
            K = r.get("d2Hsd", np.nan)
            J = 0.0 if pd.isna(J) else float(J)
            K = 0.0 if pd.isna(K) else float(K)

            row["ERR d18O"] = float(np.sqrt(J*J + Y*Y)) if (np.isfinite(J) and np.isfinite(Y)) else np.nan
            row["ERR d2H"] = float(np.sqrt(K*K + AA*AA)) if (np.isfinite(K) and np.isfinite(AA)) else np.nan

            out_rows.append(row)

        qdf = pd.DataFrame(out_rows)

        cols_meta = [c for c in ["Identifier 1", "Identifier", "Siringa", "H2Osd", "COND. d18O", "COND. d2H", "d18Osd", "d2Hsd", "Analysis"] if c in qdf.columns]
        cols_ric18 = [c for c in ric18_cols if c in qdf.columns]
        cols_ric2 = [c for c in ric2_cols if c in qdf.columns]
        cols_stats = ["d18Omean", "d2Hmean", "Y (DEV.ST 18O tra curve)", "AA (DEV.ST 2H tra curve)", "ERR d18O", "ERR d2H"]
        cols_stats = [c for c in cols_stats if c in qdf.columns]

        return qdf[cols_meta + cols_ric18 + cols_ric2 + cols_stats]

    # ----------------- Dialogo: modifica targets -----------------
    def open_targets_dialog(self):
        win = tk.Toplevel(self)
        win.title("Target standard (18O, 2H)")
        win.transient(self)
        win.grab_set()

        hdr = ttk.Frame(win); hdr.pack(fill="x", padx=10, pady=(10,4))
        ttk.Label(hdr, text="Modifica i target degli standard (accetta la virgola).", foreground="#333").pack(side="left")

        frm = ttk.Frame(win); frm.pack(fill="both", expand=True, padx=10, pady=6)

        entries = {}
        row = 0
        # Usa tutti gli standard caricati da Excel (dinamico)
        for name in sorted(self.std_targets.keys()):
            ttk.Label(frm, text=name, width=10).grid(row=row, column=0, sticky="w", padx=4, pady=3)
            ttk.Label(frm, text="18O").grid(row=row, column=1, sticky="e", padx=4)
            e18 = ttk.Entry(frm, width=10)
            e18.insert(0, f"{self.std_targets[name]['18O']}")
            e18.grid(row=row, column=2, sticky="w", padx=4)

            ttk.Label(frm, text="2H").grid(row=row, column=3, sticky="e", padx=4)
            e2 = ttk.Entry(frm, width=10)
            e2.insert(0, f"{self.std_targets[name]['2H']}")
            e2.grid(row=row, column=4, sticky="w", padx=4)

            entries[name] = (e18, e2)
            row += 1

        btns = ttk.Frame(win); btns.pack(fill="x", padx=10, pady=(6,10))

        def on_apply():
            for nm, (e18, e2) in entries.items():
                v18 = parse_num(e18.get()); v2  = parse_num(e2.get())
                if np.isnan(v18) or np.isnan(v2):
                    messagebox.showerror("Errore", f"Valori non validi per {nm}.")
                    return
                self.std_targets[nm]["18O"] = float(v18)
                self.std_targets[nm]["2H"]  = float(v2)
            if self.rm_df is not None and not self.rm_df.empty:
                self.detect_curves_from_blocks()
                self.render_cal_tab()
                self.compute_quant_table()
                self.render_quant_tab()
                self.status.config(text="Target aggiornati. Curve e Quant ricalcolate.")
            win.destroy()

        def on_reset():
            self.std_targets = {k: v.copy() for k, v in STD_DEFAULTS.items()}
            for nm, (e18, e2) in entries.items():
                e18.delete(0, tk.END); e18.insert(0, f"{self.std_targets[nm]['18O']}")
                e2.delete(0, tk.END);  e2.insert(0, f"{self.std_targets[nm]['2H']}")

        ttk.Button(btns, text="Ripristina default", command=on_reset).pack(side="left")
        ttk.Button(btns, text="Annulla", command=win.destroy).pack(side="right")
        ttk.Button(btns, text="Applica", command=on_apply).pack(side="right", padx=6)

    # ----------------- Export -----------------
    def export_rm_excel(self):
        if self.df is None:
            messagebox.showwarning("Warning", "Load a CSV file first to export raw_means.")
            return
        try:
            path = filedialog.asksaveasfilename(title="Save Excel (raw_means)", defaultextension=".xlsx",
                                                filetypes=[("Excel", "*.xlsx")])
            if not path: return
            
            # Esporta solo le righe che hanno raw_means validi (non NaN)
            # Per evitare duplicati, prendi solo l'ultima iniezione per ogni Analysis
            export_df = self.df.copy()
            
            # Filtra solo righe che hanno almeno uno dei raw_means non-NaN
            raw_means_cols = ["d18Om","d2Hm","H2Om","d18Osd","d2Hsd","H2Osd","COND. d18O","COND. d2H"]
            has_raw_means = export_df[raw_means_cols].notna().any(axis=1)
            export_df = export_df[has_raw_means]
            
            if export_df.empty:
                messagebox.showwarning("Warning", "Nessun raw_means da esportare. Usa 'Scrivi su raw_means' prima di esportare.")
                return
            
            # Per ogni Analysis, prendi solo l'ultima riga (quella con Inj Nr massimo)
            export_df = export_df.sort_values(["Analysis","Inj Nr"])
            final_df = export_df.groupby("Analysis").last().reset_index()
            
            # ESPORTA SOLO LE COLONNE NECESSARIE per evitare conflitti con colonne duplicate
            export_cols = ["Analysis","Inj Nr","d18Om","d2Hm","H2Om","d18Osd","d2Hsd","H2Osd","COND. d18O","COND. d2H"]
            # Aggiungi Identifier 1 se esiste
            if "Identifier 1" in final_df.columns:
                export_cols.append("Identifier 1")
            if "Identifier" in final_df.columns:
                export_cols.append("Identifier")
                
            # Filtra solo le colonne che esistono
            available_cols = [col for col in export_cols if col in final_df.columns]
            export_final = final_df[available_cols].copy()
            
            with pd.ExcelWriter(path, engine="openpyxl") as xw:
                export_final.to_excel(xw, sheet_name="raw_means", index=False)
            self.status.config(text=f"Excel 'raw_means' salvato: {os.path.basename(path)} ({len(final_df)} campioni)")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_cal_excel(self):
        if self.curves_summary is None or self.curves_summary.empty:
            messagebox.showwarning("Warning", "Nessuna curva da esportare: carica l'Excel raw_means e rileva le curve.")
            return
        try:
            path = filedialog.asksaveasfilename(title="Salva Excel (cal + quant)", defaultextension=".xlsx",
                                                filetypes=[("Excel", "*.xlsx")])
            if not path: return
            with pd.ExcelWriter(path, engine="openpyxl") as xw:
                self.curves_summary.to_excel(xw, sheet_name="curves", index=False)
                # punti usati per ogni curva
                rows = []
                for c in self.curves:
                    for x,y in zip(c["pts18_x"], c["pts18_y"]):
                        rows.append({"Curve": c["id"], "Iso": "18O", "x_raw": x, "y_target": y})
                    for x,y in zip(c["pts2_x"], c["pts2_y"]):
                        rows.append({"Curve": c["id"], "Iso": "2H",  "x_raw": x, "y_target": y})
                pd.DataFrame(rows).to_excel(xw, sheet_name="points", index=False)
                # quant
                if self.quant_df is not None and not self.quant_df.empty:
                    self.quant_df.to_excel(xw, sheet_name="quant", index=False)
            self.status.config(text=f"Excel salvato: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ----------------- Raw means da selezione (per generare l'xlsx) -----------------
    def apply_all_to_raw_means(self):
        """NUOVO: Applica tutte le selezioni salvate ai raw_means in una sola volta."""
        if self.df is None:
            messagebox.showwarning("Warning", "Carica prima un CSV.")
            return
        
        # Salva prima le selezioni correnti
        self._auto_save_current_selection()
        
        if not self.sample_selections:
            messagebox.showwarning("Warning", "Nessuna selezione di iniezioni salvata. Seleziona almeno un campione con iniezioni.")
            return
        
        # Aggiungi colonne se non esistono
        for c in ["d18Om","d2Hm","H2Om","d18Osd","d2Hsd","H2Osd","COND. d18O","COND. d2H"]:
            if c not in self.df.columns: 
                self.df[c] = np.nan
        
        processed_count = 0
        failed_samples = []
        
        # Processa tutti i campioni salvati
        for analysis, injections in self.sample_selections.items():
            try:
                if not injections:  # Salta se non ci sono iniezioni selezionate
                    continue
                    
                g = self.df[(self.df["Analysis"]==analysis) & (self.df["Inj Nr"].isin(injections))].sort_values("Inj Nr")
                if g.empty:
                    failed_samples.append(f"{analysis} (nessuna iniezione trovata)")
                    continue
                
                s = compute_stats(g)
                if s is None:
                    failed_samples.append(f"{analysis} (errore calcolo stats)")
                    continue
                
                # Trova l'ultima riga per questo Analysis
                last_idx = self.df[self.df["Analysis"]==analysis]["Inj Nr"].idxmax()
                
                # Scrivi i raw_means
                self.df.loc[last_idx, ["d18Om","d2Hm","H2Om","d18Osd","d2Hsd","H2Osd","COND. d18O","COND. d2H"]] = [
                    s["d18Om"], s["d2Hm"], s["H2Om"], s["d18Osd"], s["d2Hsd"], s["H2Osd"], s["COND. d18O"], s["COND. d2H"]
                ]
                processed_count += 1
                
            except Exception as e:
                failed_samples.append(f"{analysis} (errore: {str(e)})")
        
        # Messaggio finale
        if processed_count > 0:
            message = f"✅ Raw means scritti per {processed_count} campioni!"
            if failed_samples:
                message += f"\n⚠️ Falliti: {', '.join(failed_samples)}"
            self.status.config(text=message)
            # NUOVO: Aggiorna colori dopo aver scritto raw_means
            self._update_sample_colors()
            messagebox.showinfo("Completed", message + "\n\nPuoi ora esportare il file Excel con 'Esporta Excel (raw_means)'.")
        else:
            messagebox.showerror("Errore", "Nessun campione processato. Verifica le selezioni.")

    def apply_to_raw_means(self):
        """DEPRECATO: Mantiene compatibilità ma non è più usato nell'UI."""
        if self.df is None:
            return
        a = self._get_selected_analysis()
        if not a:
            messagebox.showwarning("Warning", "Scegli prima un campione (Identifier 1).")
            return
        inj = self.selected_injections()
        g = self.df[(self.df["Analysis"]==a) & (self.df["Inj Nr"].isin(inj))].sort_values("Inj Nr")
        if g.empty:
            messagebox.showwarning("Warning", "Seleziona almeno una iniezione.")
            return
        s = compute_stats(g)
        last_idx = self.df[self.df["Analysis"]==a]["Inj Nr"].idxmax()
        for c in ["d18Om","d2Hm","H2Om","d18Osd","d2Hsd","H2Osd","COND. d18O","COND. d2H"]:
            if c not in self.df.columns: self.df[c] = np.nan
        self.df.loc[last_idx, ["d18Om","d2Hm","H2Om","d18Osd","d2Hsd","H2Osd","COND. d18O","COND. d2H"]] = [
            s["d18Om"], s["d2Hm"], s["H2Om"], s["d18Osd"], s["d2Hsd"], s["H2Osd"], s["COND. d18O"], s["COND. d2H"]
        ]
        # NUOVO: Aggiorna colori dopo aver scritto raw_means
        self._update_sample_colors()
        self.status.config(text=f"Raw means scritti per '{self.current_identifier}' [{a}]. Esporta 'raw_means' e ricaricalo per vedere le curve/quant.")


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()





