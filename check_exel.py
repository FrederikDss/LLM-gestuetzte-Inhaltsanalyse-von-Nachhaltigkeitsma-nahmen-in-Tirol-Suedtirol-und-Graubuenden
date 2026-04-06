import pandas as pd
import os

# ==========================================
# KONFIGURATION
# ==========================================
# 1. Dateiname
KATEGORIEN_DATEI = "2026-01-21_Kategoriensystem_Beispiele.xlsx"

# 2.  exakten Spaltennamen 
COL_CAT   = "Kategorie (Spalten-Überschrift)"
COL_DEF   = "Definition"
COL_LABEL = "Mögliche Labels"
COL_CRIT  = "Einschlusskriterien // Ausschlusskriterien"
COL_EX1   = "Few-Shot-Beispiel 1"
COL_EX2   = "Few-Shot-Beispiel 2"

# Ausgabedatei
OUTPUT_TXT = "debug_neue_struktur_check.txt"

# ==========================================
# DIAGNOSE-LAUF
# ==========================================
print(f"--- START NEUER DEBUG-CHECK ---")

# A) Existenz-Check
if not os.path.exists(KATEGORIEN_DATEI):
    print(f"❌ FEHLER: Datei nicht gefunden: {KATEGORIEN_DATEI}")
    exit()

try:
    print(f"Lese Excel ein: {KATEGORIEN_DATEI} ...")
    df_rules = pd.read_excel(KATEGORIEN_DATEI)

    # B) Spalten-Check
    missing_cols = []
    for c in [COL_CAT, COL_DEF, COL_LABEL, COL_CRIT]:
        if c not in df_rules.columns:
            missing_cols.append(c)
    
    if missing_cols:
        print(f"❌ KRITISCHER FEHLER: Folgende Spalten fehlen in der Excel:")
        for m in missing_cols:
            print(f"   - {m}")
        print("Bitte Excel-Spaltennamen prüfen!")
        exit()

    # C) Datenaufbereitung (Exakt wie im Hauptskript)
    # Kategorie auffüllen
    df_rules[COL_CAT] = df_rules[COL_CAT].ffill()

    knowledge_text = ""
    grouped = df_rules.groupby(COL_CAT)
    
    count_cats = 0
    
    for name, group in grouped:
        count_cats += 1
        knowledge_text += f"\n{'='*60}\n"
        knowledge_text += f"### KATEGORIE: {name}\n"
        knowledge_text += f"{'='*60}\n"
        
        # 1. Allgemeine Definition
        defs = group[COL_DEF].dropna()
        if not defs.empty:
            knowledge_text += f"ALLGEMEINE DEFINITION:\n{defs.iloc[0]}\n\n"
        else:
            knowledge_text += "(! WARNUNG: Keine Definition gefunden !)\n\n"
        
        knowledge_text += "--- ZUORDNUNG LABEL -> KRITERIEN & BEISPIELE ---\n"
        
        # 2. Zeilenweise Iteration
        found_labels = 0
        for idx, row in group.iterrows():
            # Label holen
            current_label = str(row[COL_LABEL]) if pd.notna(row[COL_LABEL]) else "N/A"
            
            # Zeilen ohne Label überspringen
            if current_label == "N/A" or current_label == "nan":
                continue
            
            found_labels += 1
            knowledge_text += f"\n👉 LABEL: '{current_label}'\n"
            
            # Kriterien auslesen
            if COL_CRIT in row and pd.notna(row[COL_CRIT]):
                crit_text = str(row[COL_CRIT]).replace("\n", " ")
                knowledge_text += f"   ⚡ KRITERIEN: {crit_text}\n"
            else:
                knowledge_text += f"   (Keine spezifischen Kriterien in dieser Zeile)\n"
            
            # Beispiele auslesen
            examples = []
            if COL_EX1 in row and pd.notna(row[COL_EX1]): examples.append(str(row[COL_EX1]))
            if COL_EX2 in row and pd.notna(row[COL_EX2]): examples.append(str(row[COL_EX2]))
                
            if examples:
                for ex in examples:
                    knowledge_text += f"   📝 BEISPIEL: \"{ex}\"\n"
            else:
                knowledge_text += f"   (Keine Beispiele in dieser Zeile)\n"
        
        if found_labels == 0:
            knowledge_text += "(WARNUNG: In dieser Kategorie wurden keine Labels gefunden. Checke die Spalte 'Mögliche Labels'!)\n"

    # D) Speichern
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write(knowledge_text)
        
    print(f"✅ ERFOLG! {count_cats} Kategorien verarbeitet.")
    print(f"👉 Öffne jetzt die Datei: {OUTPUT_TXT}")
    print("   Prüfe dort, ob unter '⚡ KRITERIEN' deine Texte stehen.")

except Exception as e:
    print(f"❌ SYSTEM-FEHLER: {e}")
    if "Permission denied" in str(e):
        print("💡 TIPP: Die Excel-Datei ist noch offen")