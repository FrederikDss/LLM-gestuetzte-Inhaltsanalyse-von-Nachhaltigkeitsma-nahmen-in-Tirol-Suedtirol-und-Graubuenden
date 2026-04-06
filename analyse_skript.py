import os
import glob
import pandas as pd
import json
import time
from datetime import datetime
from openai import OpenAI
from tqdm import tqdm
import pypdf

# ==========================================
# KONFIGURATION
# ==========================================
OPENAI_API_KEY = # <--- HIER KEY EINFÜGEN

INPUT_ORDNER = "./Test_Daten_LLM-Analyse_2026-01-28/"  
KATEGORIEN_DATEI = "2026-01-21_Kategoriensystem_GPT2_Few-Shot-Beispiele.xlsx"
OUTPUT_DATEI = "Ergebnis_Final_Mit_Log.xlsx"
LOG_DATEI = "prozess_log.txt"  # <--- Neue Log-Datei
MODEL = "gpt-4o" 

client = OpenAI(api_key=OPENAI_API_KEY)

# ==========================================
# DEFINITION DER OUTPUT-SPALTEN
# ==========================================
KI_OUTPUT_SPALTEN = [
    "Maßnahme ist einem übergeordneten Ziel zugeordnet",
    "Maßnahme ist zeitlich direkt terminiert",
    "Maßnahme ist spezifisch formuliert",
    "qualitative Zielbeschreibung der Maßnahme ist vorhanden",
    "Indikatoren / Monitoring der Maßnahme sind vohanden",
    "zentrale Nachhaltigkeitsdimension der Maßnahme",
    "regionaler Wirkungsbereich der Maßnahme",
    "Art der Maßnahme",
    "Steuerungslogik / Steuerungsmodus (Governance Mode)",
    "Verbindlichkeitsgrad der Durchsetzung",
    "Transformationslogik",
    "Bewertung der Maßnahme nach ihrer Effizienz",
    "federführender Akteur",
    "Konflikte & Herausforderungen",
    "Reasoning_Begruendung"
]

# ==========================================
# HELFER-FUNKTIONEN (LOGGING & PDF)
# ==========================================

def write_log(message):
    """Schreibt eine Nachricht mit Zeitstempel in die Log-Datei"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    
    # Auf Konsole ausgeben 
    # print(log_entry.strip()) 
    
    with open(LOG_DATEI, "a", encoding="utf-8") as f:
        f.write(log_entry)

def get_pdf_context(pdf_path, page_num):
    try:
        reader = pypdf.PdfReader(pdf_path)
        try:
            p_idx = int(float(page_num)) - 1 
        except:
            return "" 

        text = ""
        start_page = max(0, p_idx - 1)
        end_page = min(len(reader.pages), p_idx + 2)
        
        for i in range(start_page, end_page):
            text += f"\n--- SEITE {i+1} ---\n"
            text += reader.pages[i].extract_text()
            
        return text[:5000]
    except Exception as e:
        write_log(f"FEHLER beim PDF lesen ({pdf_path}): {e}")
        return ""

def classify_measure(measure, quote, context, knowledge):
    """Analyse mit Reasoning"""
    if pd.isna(measure) or len(str(measure)) < 3:
        return json.dumps({"Info": "Leer"})

    # Prompt mit Reasoning-Aufforderung
    system_prompt = f"""
    Du bist ein Experte für Governance-Analyse.
    
    REGELWERK:
    {knowledge}
    
    ANWEISUNG:
    1. Analysiere Maßnahme, Zitat und Kontext.
    2. Erstelle für jede Kategorie eine Entscheidung.
    3. WICHTIG: Erstelle am Ende eine kurze Begründung ("Reasoning"), warum du die Hauptkategorien (wie Steuerungslogik) so gewählt hast.
    
    FORMAT:
    Gib JSON zurück mit exakt diesen Keys:
    {{
      "Maßnahme ist einem übergeordneten Ziel zugeordnet": "...",
      "Maßnahme ist zeitlich direkt terminiert": "...",
      "Maßnahme ist spezifisch formuliert": "...",
      "qualitative Zielbeschreibung der Maßnahme ist vorhanden": "...",
      "Indikatoren / Monitoring der Maßnahme sind vohanden": "...",
      "zentrale Nachhaltigkeitsdimension der Maßnahme": "...",
      "regionaler Wirkungsbereich der Maßnahme": "...",
      "Art der Maßnahme": "...",
      "Steuerungslogik / Steuerungsmodus (Governance Mode)": "...",
      "Verbindlichkeitsgrad der Durchsetzung": "...",
      "Transformationslogik": "...",
      "Bewertung der Maßnahme nach ihrer Effizienz": "...",
      "federführender Akteur": "...",
      "Konflikte & Herausforderungen": "...",
      "Reasoning_Begruendung": "Zusammenfassende Begründung deiner Entscheidung..."
    }}
    """
    
    user_prompt = f"""
    MAßNAHME: {measure}
    ZITAT: {quote}
    KONTEXT PDF: {context}
    """
    
    try:
        start_time = time.time()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        duration = time.time() - start_time
        
        # Log der Dauer und Tokens
        usage = response.usage
        write_log(f"   -> API Success ({duration:.2f}s). Tokens: {usage.total_tokens}")
        
        return response.choices[0].message.content
    except Exception as e:
        write_log(f"   -> API ERROR: {str(e)}")
        return json.dumps({"Error": str(e)})

# ==========================================
# HAUPTPROGRAMM
# ==========================================

# Log-Datei neu starten
with open(LOG_DATEI, "w", encoding="utf-8") as f:
    f.write(f"START ANALYSE-LAUF: {datetime.now()}\n")
    f.write("=========================================\n")

print(f"--- START (Logging aktiv: {LOG_DATEI}) ---")
write_log(f"Skript gestartet. Modell: {MODEL}")
write_log(f"Input-Ordner: {INPUT_ORDNER}")

# ==========================================
# 1. REGELWERK LADEN 
# ==========================================
try:
    print(f"Lese Regelwerk: {KATEGORIEN_DATEI}")
    df_rules = pd.read_excel(KATEGORIEN_DATEI)
    
    # Leere Zellen in der Kategorie-Spalte auffüllen
    col_cat = 'Kategorie (Spalten-Überschrift)'
    df_rules[col_cat] = df_rules[col_cat].ffill()
    
    # ---------------------------------------------------------
    # EXAKTEN SPALTENNAMEN IN EXCEL:
    # ---------------------------------------------------------
    COL_DEF = "Definition"
    COL_CRIT = "Einschlusskriterien // Ausschlusskriterien"  
    COL_EX1 = "Few-Shot-Beispiel 1"
    COL_EX2 = "Few-Shot-Beispiel 2"
    COL_LABEL = "Mögliche Labels"
    # ---------------------------------------------------------

    knowledge_text = ""
    grouped = df_rules.groupby(col_cat)
    
    for name, group in grouped:
        knowledge_text += f"\n{'='*50}\n"
        knowledge_text += f"### KATEGORIE: {name}\n"
        knowledge_text += f"{'='*50}\n"
        
        # A) Allgemeine Definition
        defs = group[COL_DEF].dropna()
        if not defs.empty:
            knowledge_text += f"ALLGEMEINE DEFINITION:\n{defs.iloc[0]}\n\n"
        
        knowledge_text += "--- REGELN UND BEISPIELE PRO LABEL ---\n"
        
        # B) Zeilenweise Iteration (verbindet Label mit Kriterium & Beispiel)
        for idx, row in group.iterrows():
            # Label holen
            current_label = str(row[COL_LABEL]) if pd.notna(row[COL_LABEL]) else "N/A"
            
            # Zeilen ohne Label überspringen
            if current_label == "N/A" or current_label == "nan":
                continue
             # 1.   
            knowledge_text += f"\n👉 WENN LABEL '{current_label}':\n"
            
            
            if COL_CRIT in row and pd.notna(row[COL_CRIT]):
                crit_text = str(row[COL_CRIT]).replace("\n", " ")
              
                knowledge_text += f"   KRITERIEN (Einschluss/Ausschluss): {crit_text}\n"
            
            # 2. Beispiele holen
            examples = []
            if COL_EX1 in row and pd.notna(row[COL_EX1]): examples.append(str(row[COL_EX1]))
            if COL_EX2 in row and pd.notna(row[COL_EX2]): examples.append(str(row[COL_EX2]))
                
            if examples:
                knowledge_text += f"   BEISPIELE (Typisch für '{current_label}'):\n"
                for ex in examples:
                    knowledge_text += f"     - \"{ex}\"\n"
        
        knowledge_text += "\n"

    print("✅ Regelwerk erfolgreich geladen.")
    
    # Debug-Datei speichern
    with open("debug_finales_prompting.txt", "w", encoding="utf-8") as f:
        f.write(knowledge_text)

except Exception as e:
    print(f"❌ FEHLER beim Regelwerk: {e}")
    print(f"Bitte prüfen Sie, ob die Spalte '{COL_CRIT}' exakt so in Excel heißt.")
    print(f"Gefundene Spalten: {df_rules.columns.tolist()}")
    exit()

# 2. VERARBEITUNG
all_results = []
files = glob.glob(INPUT_ORDNER + "*.csv")
write_log(f"Gefundene CSV-Dateien: {len(files)}")

for file_path in files:
    filename = os.path.basename(file_path)
    pdf_path = file_path.replace(".csv", ".pdf")
    
    write_log(f"\n--- Starte Datei: {filename} ---")
    
    try:
        df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8-sig')
        if len(df.columns) <= 1: df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig')

        col_text = next((c for c in df.columns if 'Massnahme' in c or 'Beschreibung' in c or 'Text' in c), None)
        col_zit = next((c for c in df.columns if 'Zitat' in c), None)
        col_page = next((c for c in df.columns if 'Seite' in c), None)
        
        if not col_text:
            write_log(f"SKIP: Keine Textspalte in {filename}")
            continue
            
        
        df_subset = df 
        
        write_log(f"Anzahl Maßnahmen in Datei: {len(df_subset)}")
        
        for index, row in tqdm(df_subset.iterrows(), total=len(df_subset)):
            measure_text = str(row[col_text])
            quote_text = str(row[col_zit]) if col_zit else ""
            page_num = row[col_page] if col_page else 1
            
            # Log
            write_log(f"Bearbeite Maßnahme ID {index}: {measure_text[:50]}...")
            
            pdf_ctx = ""
            if os.path.exists(pdf_path):
                pdf_ctx = get_pdf_context(pdf_path, page_num)
            else:
                write_log(f"WARNUNG: PDF nicht gefunden: {pdf_path}")
            
            
            json_result = classify_measure(measure_text, quote_text, pdf_ctx, knowledge_text)
            
            result_row = row.to_dict()
            result_row['Source_File'] = filename
            
            try:
                parsed_json = json.loads(json_result)
                result_row.update(parsed_json)
                
                # REASONING in die Log-Datei
                 
                reasoning = parsed_json.get("Reasoning_Begruendung", "Keine Begründung")
                write_log(f"   => REASONING: {reasoning}")
                
            except:
                write_log(f"   => ERROR parsing JSON: {json_result}")
                result_row['Error_Log'] = json_result
            
            all_results.append(result_row)
            time.sleep(0.4)
            
    except Exception as e:
        write_log(f"ERROR File Loop {filename}: {e}")

# 3. SPEICHERN
if len(all_results) > 0:
    write_log("\nVerarbeitung abgeschlossen. Speichere Excel...")
    df_final = pd.DataFrame(all_results)
    
    # Sortierung
    ki_cols_present = [c for c in KI_OUTPUT_SPALTEN if c in df_final.columns]
    original_cols = [c for c in df_final.columns if c not in KI_OUTPUT_SPALTEN]
    final_order = original_cols + ki_cols_present
    
    df_final = df_final[final_order]
    
    df_final.to_excel(OUTPUT_DATEI, index=False)
    write_log(f"Datei erfolgreich gespeichert: {OUTPUT_DATEI}")
    print(f"Fertig! Log-Datei liegt hier: {LOG_DATEI}")
else:
    write_log("Keine Daten verarbeitet.")
    