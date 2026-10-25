import streamlit as st
import sqlite3
import re
import json
import zipfile
import io
import urllib.request
from datetime import datetime
import pandas as pd

# =========================================================
# 1. KONFIGURATION & LOGIN (100% LOKAL - KEIN API-KEY NÖTIG!)
# =========================================================
st.set_page_config(
    page_title="Coach Arif OS | Arif 345 Local AI",
    layout="wide",
    page_icon="🦁"
)

PASSWORD = "arif2026"

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Coach Arif OS – Privater Login")
    pwd = st.text_input("Bitte Zugangscode eingeben:", type="password")
    if st.button("Anmelden"):
        if pwd == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Falscher Zugangscode.")
    st.stop()

# =========================================================
# 2. DATENBANKEN INITIALISIEREN (knowledge.db & clients.db)
# =========================================================
conn_k = sqlite3.connect("knowledge.db", check_same_thread=False, timeout=20)
cur_k = conn_k.cursor()

cur_k.execute("""
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rubric TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    title TEXT NOT NULL,
    core_rules TEXT NOT NULL,
    practical_application TEXT NOT NULL
)
""")
conn_k.commit()

conn_c = sqlite3.connect("clients.db", check_same_thread=False, timeout=20)
cur_c = conn_c.cursor()

cur_c.execute("""
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    gender TEXT,
    age INTEGER,
    height_cm REAL,
    weight_kg REAL,
    kfa_pct REAL,
    waist_cm REAL,
    pal REAL,
    goal TEXT,
    phase TEXT,
    complaints TEXT,
    training_days INTEGER,
    bench_kg REAL DEFAULT 0,
    squat_kg REAL DEFAULT 0,
    deadlift_kg REAL DEFAULT 0,
    ohp_kg REAL DEFAULT 0,
    pullup_kg REAL DEFAULT 0,
    notes TEXT,
    updated_at TEXT
)
""")

cur_c.execute("""
CREATE TABLE IF NOT EXISTS client_chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT
)
""")
conn_c.commit()

# Sicherstellen, dass alle Spalten in clients existieren (falls ältere DB vorhanden)
existing_cols = [row[1] for row in cur_c.execute("PRAGMA table_info(clients)").fetchall()]
required_migrations = [
    ("weight_kg", "REAL DEFAULT 85.0"),
    ("kfa_pct", "REAL DEFAULT 22.0"),
    ("waist_cm", "REAL DEFAULT 90.0"),
    ("pal", "REAL DEFAULT 1.55"),
    ("goal", "TEXT DEFAULT 'Fettabbau / Diät'"),
    ("phase", "TEXT DEFAULT 'Phase 1: Detox & Reset'"),
    ("complaints", "TEXT DEFAULT ''"),
    ("training_days", "INTEGER DEFAULT 3"),
    ("bench_kg", "REAL DEFAULT 60.0"),
    ("squat_kg", "REAL DEFAULT 80.0"),
    ("deadlift_kg", "REAL DEFAULT 100.0"),
    ("ohp_kg", "REAL DEFAULT 40.0"),
    ("pullup_kg", "REAL DEFAULT 0.0"),
    ("notes", "TEXT DEFAULT ''"),
    ("updated_at", "TEXT DEFAULT ''")
]
for col_name, col_def in required_migrations:
    if col_name not in existing_cols:
        try:
            cur_c.execute(f"ALTER TABLE clients ADD COLUMN {col_name} {col_def}")
        except Exception:
            pass
conn_c.commit()

# =========================================================
# 3. MASTER-WISSENSDATENBANK (ALLE 4 RUBRIKEN INKL. PEPTIDE)
# =========================================================
MASTER_KNOWLEDGE = [
    # ==================== RUBRIK 1: TRAINING (ARIF 345 SYSTEM) ====================
    (
        "Training",
        "Arif 345 Progression",
        "Das Arif 345 Progressions-System (3x7 -> 4x6 -> 5x5)",
        "Das 'Arif 345'-System ist eine hocheffiziente Hybrid-Progression für schnellen, nachhaltigen Kraft- und Muskelaufbau als Fundament für langfristige Erfolge.\n"
        "DAS 3-STUFEN-SCHEMA FÜR DIE GRUNDÜBUNGEN:\n"
        "- Stufe 1: 3 Sätze mit 7 Wiederholungen (3x7)\n"
        "- Stufe 2: 4 Sätze mit 6 Wiederholungen (4x6)\n"
        "- Stufe 3: 5 Sätze mit 5 Wiederholungen (5x5)\n\n"
        "ABLAUF AM BEISPIEL BANKDRÜCKEN (60 kg):\n"
        "1. Einheit (z.B. Montag Push): Du absolvierst 3 Sätze x 7 Wiederholungen mit 60 kg. Schaffst du alle Sätze sauber, wird im Log ein 'X' eingetragen.\n"
        "2. Einheit (z.B. Donnerstag Push): Du bleibst bei 60 kg und greifst 4 Sätze x 6 Wiederholungen an.\n"
        "3. Einheit: Wenn 4x6 erfolgreich war, greifst du im nächsten Training 5 Sätze x 5 Wiederholungen mit 60 kg an.\n"
        "4. Gewichtssteigerung: Erst wenn der gesamte Arif-345-Zyklus (3x7 -> 4x6 -> 5x5) mit einem Gewicht erfolgreich absolviert wurde, wird das Arbeitsgewicht in der nächsten Einheit erhöht (z.B. auf 62,5 kg) und der Zyklus startet wieder vorn bei 3x7.\n"
        "WICHTIGE REGEL: Es wird immer nur EINE Arif-345-Progression pro Übung/Workout durchgeführt. Die Startgewichte basieren auf den vorab getesteten 5-Rep-Max-Werten.",
        "Fazit: Das Arif-345-System steuert die progressive Überlastung systematisch über drei feste Satz-Wiederholungs-Stufen (3x7, 4x6, 5x5) bei gleichbleibendem Gewicht. Erst nach Abschluss aller drei Stufen wird das Gewicht erhöht, was Überlastungen verhindert und kontinuierliche Kraftsteigerungen garantiert."
    ),
    (
        "Training",
        "Arif 345 Progression",
        "Die 5 Hauptübungen, Gewichtssteigerungen & Logbuch-Regeln (X / F)",
        "DIE HAUPTÜBUNGEN IM ARIF 345 SYSTEM & EXAKTE GEWICHTSSTEIGERUNGEN NACH EINEM ZYKLUS:\n"
        "1. Bankdrücken (Bench Press): +2,5 kg insgesamt (1,25 kg pro Seite) nach abgeschlossenem 345-Zyklus.\n"
        "2. Schulterdrücken (Overhead Press): +2,5 kg insgesamt (1,25 kg pro Seite).\n"
        "3. Kniebeugen (Squats): +5,0 kg insgesamt (2,5 kg pro Seite).\n"
        "4. Kreuzheben (Deadlift): +5,0 kg insgesamt (2,5 kg pro Seite).\n"
        "5. Klimmzüge (Pull-Ups): Start immer mit dem eigenen Körpergewicht. Nach abgeschlossenem Zyklus +1,25 kg Zusatzgewicht.\n\n"
        "LOGBUCH-FÜHRUNG & REGELN BEI NICHT-SCHAFFEN (FAIL):\n"
        "- Erfolg = 'X' im entsprechenden Feld (3x7, 4x6 oder 5x5).\n"
        "- Scheitern = 'F' (beim 1. Mal), 'FF' (beim 2. Mal), 'FFF' (beim 3. Mal).\n"
        "- Wann zählt ein Satz als Failed ('F')? 1. Wenn nicht ALLE Sätze und Wiederholungen vollständig geschafft wurden (selbst wenn im letzten Satz nur 1 Wiederholung fehlt!). 2. Wenn die Ausführung unsauber war (zu viel Schwung, Abfälschen oder Hilfe durch den Spotter).\n"
        "- WAS NIEMALS GETAN WERDEN DARF: Niemals Gewichte oder Arbeitssätze überspringen! Immer strikt von links nach rechts (3x7 -> 4x6 -> 5x5) und von leicht nach schwer abarbeiten.",
        "Fazit: Ehrlichkeit im Training-Logbuch ist Pflicht – schon eine einzige fehlende oder abgefälschte Wiederholung gilt als Fehlversuch ('F') und verbietet das Vorrücken. Durch die exakt definierten Gewichtssprünge (+1,25 kg bis +5 kg) und das Verbot, Stufen zu überspringen, werden Stagnation und Verletzungen im Keim erstickt."
    ),
    (
        "Training",
        "Arif 345 Trainingsstruktur",
        "Dreiteiliger Trainingsaufbau, Satzpausen & Push-Pull-Legs Split",
        "JEDES ARIF 345 WORKOUT IST IN 3 PHASEN UNTERTEILT:\n"
        "1. Mobility Warmup (ca. 10 Minuten): Aufwärmen der Gelenke, dynamisches Dehnen, Schulter-Warmup mit Therabändern.\n"
        "2. Arif 345 Arbeitssätze (ca. 40–60 Minuten): Fokus auf die Hauptübungen im 3x7 / 4x6 / 5x5 Schema. Satzpause zwischen den Arif-345-Sätzen: 60–120 Sekunden (bei sehr schweren Lasten zur vollen ATP/Kreatinphosphat-Erholung bis 3 Min.).\n"
        "3. Accessories / Zubehörübungen (ca. 30–60 Minuten): 8–15 Wiederholungen pro Satz, ans Limit gehen mit sauberer Technik für maximalen Pump. Satzpause bei Accessories: 30–60 Sekunden.\n\n"
        "AUFTEILUNG DER 3 TRAININGSTAGE (PUSH / PULL / LEGS):\n"
        "- PUSH-TAG: Bench Press (Arif 345), Overhead Press (Arif 345), Incline Dumbbell Press (4x 8–15), Chest Fly Machine (3x 8–15), Dumbbell Lateral Raise (4x 8–15), Cable Crossover (4x 8–15), Tricep Pushdown (4x 8–15).\n"
        "- PULL-TAG: Deadlift (Arif 345), Pull-Ups (Arif 345), Dumbbell Row (5x 8–15), Cable Pullover (5x 8–15), Shrugs (4x 8–15), Close Grip Pulldown (4x 8–15), Biceps Curls (4x 8–15).\n"
        "- LEGS-TAG: Squats (Arif 345), Leg Extensions (5x 8–15), Leg Curls (5x 8–15), Hip Thrust (5x 8–15), Lunges with Dumbbells (5x 8–15), Calf Raises (5x 8–15).\n"
        "FLEXIBILITÄTS-REGEL IM GYM: Die Arif-345-Grundübungen werden NIEMALS rotiert. Zubehörübungen (Accessories) dürfen bei besetzten Geräten sofort durch eine gleichwertige Alternative ersetzt werden.",
        "Fazit: Der Push-Pull-Legs-Plan kombiniert schwere mechanische Last in den Grundübungen mit hohem metabolischem Pump in den Zubehörübungen. Während die Arif-345-Hauptübungen unantastbar sind, bleiben die Accessories im Studio flexibel austauschbar."
    ),
    (
        "Training",
        "Arif 345 Core Finisher",
        "Arif 345 Bauch-Workout (10-Minuten Core Finisher Prinzip)",
        "ZEITPUNKT & INTEGRATION:\n"
        "Das Arif 345 Bauch-Workout wird NACH JEDEM TRAINING durchgeführt – immer NACH dem Gewichtetraining und VOR dem Cardio.\n\n"
        "DAS 10-MINUTEN-PRINZIP (MIT TIMER):\n"
        "- Gesamtdauer: 10 Minuten (5 Sätze insgesamt): 1 Minute maximale Wiederholungen -> 1 Minute Pause (5 Durchgänge = 10 Minuten).\n"
        "- Wer in der Belastungsminute nur 40 Sekunden schafft, macht trotzdem exakt 60 Sekunden Pause und zieht den nächsten Satz durch.\n\n"
        "ÜBUNGSAUSWAHL NACH SCHWIERIGKEITSGRAD:\n"
        "- Beginner: Bauchmaschine, Kabel-Crunches, Mountain Climbers, Planks.\n"
        "- Fortgeschritten: Flachbank Sit-Ups, Negativbank Sit-Ups, Roman Chair, Heel Touches, Flutter Kicks, Russian Twists.\n"
        "- Experte: Hanging Leg Raises, Abs Roller, Weighted Sit-Ups, Windshield Wipers, Dragon Flag.",
        "Fazit: Das 10-minütige Bauch-Intervall (5x 1 Min. Arbeit / 1 Min. Pause) am Ende jeder Krafteinheit sorgt für maximale Rumpfstabilität und Bauchmuskel-Hypertrophie."
    ),
    (
        "Training",
        "Diät-Training, Cardio & Gelenkschutz",
        "Trainingssteuerung im Defizit, Cardio-Regeln & Gelenkschonung (Schulter, Knie, LWS)",
        "1. KRAFTTRAINING & CARDIO IN DER DIÄT:\n"
        "- Krafttraining im Defizit dient dem Muskelerhalt ('Muskeln sind das Kapital'). Trainingsqualität und schwere Lasten gehen vor blindem Volumen.\n"
        "- Alltagsbewegung (>10.000 Schritte = aktiv, <5.000 = sitzend) ist die Basis. Cardio ist ein ergänzendes Werkzeug, kein Straftraining. Zu viel Cardio erhöht Kortisol, verschlechtert Regeneration und triggert Heißhunger.\n\n"
        "2. BIOMECHANISCHER GELENKSCHUTZ IM GYM:\n"
        "- Schulterbeschwerden / Impingement: Kein schweres Drücken hinter dem Kopf, kein aufrechtes Rudern mit enger Innenrotation. Stattdessen: Kurzhanteldrücken im Neutralgriff, Schrägbank, Fokus auf Außenrotatoren, Facepulls und Band Pull-Aparts im 10-Minuten Mobility-Warmup.\n"
        "- Kniebeschwerden / Patellasehne: Knievorschub unter Schmerz reduzieren, Fokus auf hintere Kette. Statt tiefen freien High-Bar-Kniebeugen: Box Squats, Spanische Kniebeugen (Isometrie für Kollagensynthese), Hip Thrusts, Rumänisches Kreuzheben und Beinbeuger.\n"
        "- Rückenschmerzen / LWS / Bandscheibe: Rumpfstabilität (Bracing) vor Last. Falls konventionelles Kreuzheben schmerzt: Wechsel auf Trap-Bar Deadlift, Rumänisches Kreuzheben mit sauberer Hüftbeugung und brustgestütztes Rudern (Chest-Supported Row) statt freiem Langhantelrudern.",
        "Fazit: Bei Gelenkbeschwerden wird niemals in den Schmerz hinein trainiert, sondern der Reiz über gelenkschonende Winkel (Neutralgriff, Box Squats, Trap-Bar, Bruststütze) und gezieltes 10-Minuten-Mobility-Warmup aufrechterhalten."
    ),
    (
        "Training",
        "Leistungsphysiologie (OTL Modul 4)",
        "ATP, Kreatinphosphat, Laktat, Beta-Oxidation & Energiebereitstellung im Sport",
        "DIE 4 STOFFWECHSELWEGE DER ENERGIEBEREITSTELLUNG:\n"
        "1. Anaerob-alaktazid (Kreatinphosphat + ADP -> ATP): Sofort verfügbar ohne Sauerstoff und ohne Laktat. Hält bei Maximalbelastung 6–20 Sek. WICHTIG FÜR SATZPAUSEN: Kreatinphosphat füllt sich nach 30 Sek. zu 70 % und nach 3–5 Minuten zu fast 100 % wieder auf!\n"
        "2. Anaerob-laktazid (Anaerobe Glykolyse): Schneller Abbau von Glukose zu Pyruvat und Laktat (Milchsäure) ohne Sauerstoff. Liefert 2 ATP pro Glukosemolekül, dominiert Belastungen von 15–60 Sekunden (Maximum bei 40–50 Sek. – typischer Pump-/Accessory-Satz).\n"
        "3. Aerob-glykolytisch (Aerobe Glykolyse): Vollständiger Glukoseabbau in den Mitochondrien (Zitronensäurezyklus + Atmungskette) unter Sauerstoffverbrauch. Liefert 30–36 ATP pro Glukosemolekül. Übernimmt ab 90–180 Sek. Belastung. Glykogenspeicher halten ca. 90 Min.\n"
        "4. Aerob-lipolytisch (Beta-Oxidation freier Fettsäuren): Fettsäuren werden NUR aerob verbrannt. Liefert 106 ATP (Palmitinsäure), läuft aber sehr langsam ('Fette verbrennen im Feuer der Kohlenhydrate').",
        "Fazit: Schwere Kraftsätze (Arif 345) hängen vom Kreatinphosphat-System ab und benötigen 2–3+ Minuten Pause zur ATP-Regeneration, während Pump-Sätze (8–15 Wdh.) über die anaerobe Glykolyse laufen."
    ),

    # ==================== RUBRIK 2: ERNÄHRUNG ====================
    (
        "Ernährung",
        "Arif 345 Philosophie & Prozess",
        "Dein Fitness Coach Arif: Philosophie, GROW-Modell & 2-Phasen-System",
        "1. POSITIONIERUNG & COACHING-ANSATZ:\n"
        "- Rolle & USP: Begleiter und Kontrollinstanz ('Du musst dich um nichts kümmern, ich gebe dir den Rahmen vor.').\n"
        "- Individuelle Anpassung an Alltag, Schichtdienst und kulturelle Besonderheiten (insbesondere türkische Küche). Keine extremen Verbote ('Die Dosis macht das Gift').\n"
        "- GROW-Modell: Goal (Ziel), Reality (Realitätscheck), Options (Handlungsoptionen), Will / Way forward (Umsetzung, 2x/Woche Check-in).\n\n"
        "2. DAS 2-PHASEN-MODELL & DIE 3 PRAXIS-SÄULEN:\n"
        "- Phase 1 (Detox & Reset – 1 Monat): Struktureller Verzicht auf Entzündungs-Trigger nach der Arif-345-Positivliste zur Magen-Darm-Regulierung.\n"
        "- Phase 2 (Flexible Kontrolle): Nachhaltiger Übergang in ein flexibles Alltags-Essverhalten.\n"
        "- Die 3 Praxis-Säulen: 1. Proteinbetont (20–30 % Thermogenese & Sättigung). 2. Naturbelassene Lebensmittel (Kartoffel-Prinzip: Salzkartoffel ~80 kcal/100g -> Bratkartoffel ~150 kcal -> Pommes ~350 kcal -> Chips ~500 kcal). 3. Kein dauerhaftes Snacken (Insulinruhe für Fettverbrennung/Lipolyse).",
        "Fazit: Über das 2-Phasen-Modell (1 Monat Reset, danach flexible Kontrolle) und die 3 Praxis-Säulen (Proteinbetont, Naturbelassen, Kein Snacken) wird Disziplin im Alltag verankert."
    ),
    (
        "Ernährung",
        "Arif 345 Food List",
        "Nährstoffdichte, Leber-Vergleich & Positiv-/Negativliste",
        "1. MIKRONÄHRSTOFF-VERGLEICH PRO 100g (APFEL vs. KAROTTE vs. ROTES FLEISCH vs. RINDERLEBER):\n"
        "- Eisen: Apfel 0,1 mg | Karotte 0,6 mg | Rotes Fleisch 3,3 mg | Rinderleber 8,8 mg\n"
        "- Zink: Apfel 0,05 mg | Karotte 0,3 mg | Rotes Fleisch 4,4 mg | Rinderleber 4,0 mg\n"
        "- Vitamin A (Retinol): Apfel 0 IU | Karotte 0 IU | Rotes Fleisch 40 IU | Rinderleber 53.400 IU!\n"
        "- Vitamin B12: Apfel 0 mcg | Karotte 0 mcg | Rotes Fleisch 1,84 mcg | Rinderleber 111,3 mcg!\n"
        "- Folsäure (B9): Apfel 8 mcg | Karotte 24 mcg | Rotes Fleisch 4 mcg | Rinderleber 145,0 mcg\n\n"
        "2. ARIF 345 POSITIVLISTE:\n"
        "- Fleisch & Innereien: Rind, Lamm, Kalb, Pute, Huhn, Wild, Rinder-/Hühnerleber, Herz.\n"
        "- Eier & Milchprodukte: Bio-Eier, Rohmilch/Weidemilch, A2-Ziegenmilch, Naturjoghurt, Skyr, Magerquark, Kefir, Ayran, gereifter Hartkäse (Parmesan, Gruyère, Emmentaler, Gouda).\n"
        "- Fisch: Wildfang-Lachs, Makrele, Sardine, Hering, Kabeljau, Zander, Forelle.\n"
        "- Kohlenhydrate, Obst & Gemüse: Kartoffeln, Süßkartoffeln, Basmati-/Jasminreis, Buchweizen, Rohhonig, Beeren, Äpfel, Zitrusfrüchte, Banane, Wassermelone, Tomaten, Gurken, Zucchini, Paprika, Karotten, Rote Bete, Brokkoli (Sulforaphan), Sauerkraut, Kimchi.\n"
        "- Fette & Nüsse: Weidebutter, Ghee, Natives Olivenöl extra, Kokosöl, Avocado, unbehandelte Nüsse/Kerne (Macadamia, Walnüsse, Mandeln).\n\n"
        "3. NEGATIVLISTE (ZU MEIDEN):\n"
        "- Fast Food, Frittiertes, Transfette, Margarine, erhitzte Industrie-Samenöle (Sonnenblumen-, Soja-, Maiskeim-, Distelöl), Weizen/Gluten-Backwaren, Flüssigzucker/Softdrinks, künstliche Zusatzstoffe/Emulgatoren, Soja-Isolate (besonders für Männer).",
        "Fazit: Die Arif-345-Positivliste setzt auf höchste Mikronährstoff- und Aminosäuredichte (Fleisch, Fisch, Eier, Leber, fermentierte Milchprodukte, Kartoffeln, Reis, Obst, Weidebutter/Olivenöl) und streicht industrielle Samenöle, Transfette und Gluten-Trigger."
    ),
    (
        "Ernährung",
        "Kaloriendefizit & Diät-Steuerung",
        "Diät-Blueprint, 10–14 Tage Plateau-Checkliste, Beispielpläne & Cheat-Meal-Protokoll",
        "1. KALORIENSTEUERUNG & PLATEAU-REGELN:\n"
        "- Grundsatz: 'Nicht so wenig wie möglich essen – sondern so viel wie nötig und so wenig wie sinnvoll.'\n"
        "- Wann Kalorien NICHT gesenkt werden: Niemals in Woche 1–2 oder nach 2–4 Tagen Gewichtsstillstand (Wasserbindung durch Salz, Kohlenhydrate, Muskelkater oder Kortisol!).\n"
        "- Wann Kalorien gesenkt werden: Erst wenn über MINDESTENS 10–14 TAGE der Gewichtstrend, die Umfänge und das Spiegelbild stagnieren UND die Checkliste geprüft wurde (Tracking exakt? Schritte konstant? Schlaf/Stress okay?).\n"
        "- Wie viel senken? Immer nur um -100 bis -200 kcal aus Kohlenhydraten oder Fetten – NIEMALS aus dem Protein!\n\n"
        "2. PRAXIS-BEISPIELPLÄNE:\n"
        "- Mann (100 kg, Diät): 2.400–2.600 kcal | 200–230 g Protein | 70–80 g Fett | Rest KH (Frühstück: Hafer/Buchweizen + Whey + Beeren; Mittag: 200g Hähnchen + 120g Reis + Gemüse + 10g Olivenöl; Pre-Workout: 250g Skyr + Banane + Honig; Post-Workout: 200g Rinderhack + 300g Kartoffeln + Gemüse; Abend: 250g Magerquark + 15g Nüsse).\n"
        "- Frau (80 kg, Diät): 1.800–2.000 kcal | 140–170 g Protein | 55–65 g Fett (Zyklusschutz!) | Rest KH ums Training.\n\n"
        "3. CHEAT-MEAL-PROTOKOLL:\n"
        "- Niemals in den ersten 2–3 Wochen ('Erst Kontrolle, dann Flexibilität') und niemals bei Stagnation oder aus Frust.\n"
        "- Wenn die Basis sitzt: Maximal alle 7–14 Tage ein geplantes Cheat Meal (NIEMALS ein ganzer Cheat Day!), proteinreich, ohne Vorab-Hungern und ohne Straf-Cardio am Folgetag.",
        "Fazit: Kalorien werden erst nach 10–14 Tagen echtem Stillstand um -100 bis -200 kcal (aus KH/Fett) reduziert. Geplante Cheat Meals (einzelne Mahlzeit alle 7–14 Tage) werden erst nach 3 Wochen stabiler Umsetzung eingebaut."
    ),
    (
        "Ernährung",
        "Kohlenhydrate, Ballaststoffe & GI/GL (OTL Modul 5 / Screenshots)",
        "Kohlenhydrate, Resistente Stärke & Vollständige GI- und GL-Tabellen",
        "1. KOHLENHYDRATE (4,1 kcal/g) & RESISTENTE STÄRKE:\n"
        "- Gehirn benötigt ca. 130 g Glukose/Tag; Mindestzufuhr in Diäten >= 1 g/kg KG. Muskelglykogen speichert 250–600 g, Leberglykogen 80–120 g (1 g Glykogen bindet bis zu 3 g Wasser!).\n"
        "- Nach dem Krafttraining sind die GLUT4-Transporter der Muskelzellen für ca. 2 Stunden AUCH OHNE INSULIN aktiv und saugen Kohlenhydrate direkt in den Muskel.\n"
        "- Ballaststoffe (Richtwert 30 g/Tag bzw. 15 g pro 1.000 kcal): Lösliche Ballaststoffe (Pektin, Hafer-Beta-Glucane) und retrogradierte resistente Stärke (abgekühlte Kartoffeln / abgekühlter Reis!) nähren das Mikrobiom, senken LDL-Cholesterin um 5 % und flachen Blutzuckerspitzen ab.\n\n"
        "2. TABELLE 5.1: GLYKÄMISCHER INDEX (GI):\n"
        "- HOCH (>70): Traubenzucker (100), Datteln getrocknet (99), Bratkartoffeln (95), Cornflakes (85), Gummibärchen (80).\n"
        "- MITTEL (55–70): Weißbrot (70), Haushaltszucker (70), Gnocchi (70), Banane (65), Grieß (65), Langkornreis (60), Mango (58), Sultaninen (56).\n"
        "- NIEDRIG (<55): Orangensaft (52), Kiwi (50), Basmatireis (50), Porridge (49), Spaghetti al dente (45), Kichererbsen (41), Wildreis (35), Glasnudeln (30), Rote Linsen (25), Mandeln (22), Grüne Linsen (22), Avocado (20), Sojabohnen (15), Buttermilch (15), Tomate (10), Zucchini (10).\n\n"
        "3. TABELLE 5.2: GLYKÄMISCHE LAST (GL = GI x KH pro Portion / 100):\n"
        "- HOCH (>20): Basmatireis gekocht 150g (GL 24), Kartoffeln gekocht 150g (GL 23), Spaghetti weiß gekocht 150g (GL 20).\n"
        "- MITTEL (10–19): Cornflakes 30g (GL 19), Zuckermais 150g (GL 12), Ananas 125g (GL 10).\n"
        "- NIEDRIG (<10): Banane 100g (GL 9), Orangensaft 200g (GL 8), Wassermelone 125g (GL 8), Apfel 115g (GL 7), Haushaltszucker 10g (GL 7), Kartoffelchips 25g (GL 6), Grüne Linsen 150g (GL 6), Orange 145g (GL 5), Aprikosen 125g (GL 4), Cashewnüsse 50g (GL 4), Karotten roh 150g (GL 4), Karotten gekocht 150g (GL 2), Kiwi 45g (GL 2).",
        "Fazit: Die Glykämische Last (GL) bewertet die echte Portionsgröße (z.B. hat 125g Wassermelone nur GL 8). Wer Kohlenhydrate mit Protein, Ballaststoffen und Fetten kombiniert oder rund ums Training isst (aktive GLUT4-Transporter), hält Blutzucker und Insulin optimal unter Kontrolle."
    ),
    (
        "Ernährung",
        "Fette & Blutfettwerte (OTL Modul 6 / Screenshot)",
        "Gesättigte Fettsäuren, Omega-6-zu-Omega-3-Balance & Cholesterin-Referenzwerte",
        "1. FETTSÄUREN & HORMONE (9,3 kcal/g):\n"
        "- Richtwert: 0,8–1,0 g/kg KG pro Tag. ABSOLUTE UNTERGRENZE IN DER DIÄT: 0,5 g/kg KG pro Tag (darunter brechen Testosteron, Östrogen und fettlösliche Vitamine A, D, E, K ein!).\n"
        "- Biologische Hierarchie der Fette: 1. Surfactant in den Lungen-Alveolen (verhindert Lungenkollaps und Hypoxie) -> 2. Zellmembranen (-70 mV Ruhepotenzial) -> 3. Steroidhormone (aus Cholesterin über Pregnenolon) -> 4. Wärmeproduktion.\n"
        "- Gesättigte Fettsäuren (C-C-Einfachbindungen; 45 % der deutschen Fettzufuhr aus Wurst, fettem Käse, Schmalz, Speck, Kokos-/Palmfett): Ein Übermaß hemmt die eigene Fettsäuresynthese, fördert direkte Fetteinlagerung und hebt LDL stark an (auf 7–10 % begrenzen).\n"
        "- Einfach ungesättigte Fettsäuren (Olivenöl, Avocado, Nüsse; 10–13 %): Senken LDL.\n"
        "- Omega-6 zu Omega-3 Verhältnis: Sollte von 15:1 auf mindestens 5:1 (optimal <= 2,5:1) gesenkt werden. 2–3 g kombiniertes EPA/DHA pro Tag (aus Lachs, Makrele, Hering oder Fisch-/Algenöl) senken Triglyzeride um 25–30 %, bauen Leberfett ab und hemmen Entzündungen.\n"
        "- Transfettsäuren (<1 %; Frittiertes, Blätterteig, Pommes, Chips): Machen Zellmembranen starr, erhöhen LDL massiv und senken HDL.\n\n"
        "2. BLUTFETT-REFERENZWERTE & NATÜRLICHE SENKER:\n"
        "- Zielwerte: Gesamtcholesterin <= 200 mg/dl | LDL <= 150 mg/dl | HDL > 50 mg/dl | Risikoindex (LDL/HDL) < 3,0 | Triglyzeride < 200 mg/dl.\n"
        "- Natürliche LDL-Senker: 30–70 g Nüsse/Tag (-6 bis -12 % LDL), grüner/schwarzer Tee (-10 bis -15 % LDL), 5–10 g lösliche Ballaststoffe (-5 % LDL).",
        "Fazit: Fette niemals unter 0,5 g/kg KG kürzen. Durch den Verzicht auf Transfette und Sonnenblumenöl zugunsten von Olivenöl, Weidebutter, Nüssen und 2–3 g Omega-3 (EPA/DHA) werden Surfactant, Zellmembranen und Hormonachsen geschützt sowie Entzündungen und Blutfette gesenkt."
    ),
    (
        "Ernährung",
        "Proteine & Aminosäuren (OTL Modul 7 / Screenshots)",
        "Proteine, Biologische Wertigkeit (136), Reflux-Hilfe & 3-Achsen-Entscheidungshierarchie",
        "1. PROTEIN-HIERARCHIE NACH ZIELGRUPPE (1,2 BIS 2,5 g/kg KG):\n"
        "- Breitensportler & Alltagsaktive (>10.000 Schritte): 1,2–1,4 g/kg KG.\n"
        "- Ambitionierte Kraftsportler & Diätende: 1,4–2,2 g/kg KG (im strengen Defizit 1,8–2,5 g/kg KG).\n"
        "- Biologische Prioritäts-Rangfolge der 6 Proteinfunktionen: 1. Struktur, 2. Transport (Albumin, Transferrin), 3. Immunsystem, 4. Enzyme (Protease, Lipase, Amylase), 5. Vererbung, 6. Muskulatur (erst an 6. Stelle!). Zielwert Gesamteiweiß im Blut: 80–83 g/l.\n"
        "- Achse 1 (Ziel): Muskelaufbau > Muskelerhalt > 'nur' Fettabbau.\n"
        "- Achse 2 (Statur): Trainiert + niedriger KFA > trainiert + hoher KFA > übergewichtig ohne viel Muskelmasse > Normalo. (Bei Adipositas wird Protein auf die fettfreie Masse FFM oder das Normalgewicht bezogen!).\n"
        "- Achse 3 (Bilanz): Kaloriendefizit > ausgeglichene Bilanz > Kalorienüberschuss.\n\n"
        "2. BIOLOGISCHE WERTIGKEIT & THERAPEUTISCHER NUTZEN BEI REFLUX:\n"
        "- Top-Kombinationen: Vollei + Kartoffeln (36:64 %) = 136 | Milch + Weizen = 125 | Vollei + Soja = 124 | Vollei + Milch = 119 | Quark/Milch + Kartoffeln = 114.\n"
        "- REFLUX / SODBRENNEN: Mehrere über den Tag verteilte, kleine eiweißreiche Speisen mildern die Beschwerden von Reflux deutlich (zusätzlich HNO-ärztliche Abklärung empfehlen).\n"
        "- NIEREN: Für Nierengesunde absolut unbedenklich; erst ab >3 g/kg KG bei Wassermangel und hoher Purinzufuhr steigt das Gicht-/Harnsäurerisiko.",
        "Fazit: Im Kaloriendefizit und bei trainierter Statur ist der Proteinbedarf am höchsten (1,8–2,5 g/kg KG; bei starkem Übergewicht bezogen auf FFM/Normalgewicht). Kleine, über den Tag verteilte Proteinmahlzeiten lindern zudem effektiv Reflux-Beschwerden."
    ),

    # ==================== RUBRIK 3: GESUNDHEIT ====================
    (
        "Gesundheit",
        "Physiologische Grundgesetze (Screenshots)",
        "Die 4 Goldenen Gesetze der Ernährung, Fließbandgesetz, Hypoxie & Transportproteine (Albumin/Transferrin)",
        "1. DIE 4 GOLDENEN GESETZE DER ERNÄHRUNG:\n"
        "- 1. Gesetz der Ernährungsgrundlage: 'Ich -> Biologischer Körper => Ressourcen / Material => Genetischer Wachstumsplan (99,99 %)'.\n"
        "- 2. Gesetz der natürlichen Auslese.\n"
        "- 3. Das Fließbandgesetz (3 Stufen): Stufe 1: Zerkleinerung/Aufspaltung (Magen/Darm) -> Stufe 2: Transport (Blutbahn über Transportproteine) -> Stufe 3: Synthese (Zelle baut eigenes Körpergewebe auf: Essen [fremd] -> Organismus -> Transport -> Körper-Ort [unser]).\n"
        "- 4. Gesetz des Feedbacks & Food-Imprintings.\n\n"
        "2. TRANSPORTPROTEINE (ALBUMIN & TRANSFERRIN) & HYPOXIE:\n"
        "- Albumin ist das zentrale Transportprotein im Blutplasma für Fettsäuren, Hormone, Mineralien und Medikamente (Plasmaproteinbindung).\n"
        "- Transferrin transportiert Eisen: Ohne ausreichendes Transferrin (durch zu geringe Proteinzufuhr!) bleiben Eisentabletten trotz hoher Zufuhr völlig wirkungslos!\n"
        "- Hypoxie (Sauerstoffmangel): Bei aerober Verbrennung liefert 1 Glukosemolekül 36 ATP, bei Hypoxie (anaerober Glykolyse) nur 2 ATP (18-facher Leistungsabfall + Übersäuerung durch Milchsäure -> Brain Fog, Lethargie, Heißhunger auf Süßes).",
        "Fazit: Nach dem 3-stufigen Fließbandgesetz sind Supplements (wie Eisen) völlig wirkungslos, wenn durch Proteinmangel die Transportproteine im Blut (Albumin und Transferrin) fehlen. Immer erst Stufe 1 (Verdauung) und Stufe 2 (Proteinbasis) sichern!"
    ),
    (
        "Gesundheit",
        "Knochen, Genetik & Hormone (Screenshot)",
        "Schädel-, Kiefer- & Knochenentwicklung: Fettlösliche Vitamine (A, D, K2), Protein & Hormonmilieu",
        "FAKTOREN FÜR KNOCHEN-, SCHÄDEL- UND KIEFERSTRUKTUR:\n"
        "1. Hochwertiges Protein, Mineralstoffe (Kalzium, Phosphor, Magnesium, Zink) und die fettlöslichen Vitamine A (Retinol), D (Zielblutspiegel 35–60 ng/ml) und K2 (in Leber, Weidebutter, Eigelb, gereiftem Käse). Vitamin K2 transportiert Kalzium aus den Arterien/Gefäßwänden gezielt in Knochen und Zähne.\n"
        "2. Ein funktionierendes hormonelles Milieu (Testosteron, Östrogen, Schilddrüse, Wachstumshormon/IGF-1) ist für Knochenwachstum und Knochendichte zwingend notwendig.\n"
        "3. Mechanisches Kauen allein reicht nicht aus, wenn diese biochemischen Baustoffe fehlen.",
        "Fazit: Stabile Knochen, Gelenke und Kieferstrukturen benötigen zwingend hochwertiges Protein, Mineralstoffe, die fettlöslichen Vitamine A, D und K2 sowie ein intaktes Hormonmilieu."
    ),
    (
        "Gesundheit",
        "Verdauungssystem & Mikrobiom (OTL Modul 1 & 4)",
        "Verdauungskette (Magensäure, Intrinsic Factor, Galle, Bürstensaum, Zöliakie, Mikrobiom & Leber)",
        "1. MAGEN & SALZSÄURE (HCl):\n"
        "- Denaturiert Proteine, aktiviert Pepsin, tötet Keime ab, macht Eisen/Kalzium/Magnesium verfügbar und bildet den Intrinsic Factor (zwingend nötig für die Vitamin-B12-Aufnahme im Dünndarm!). Stress hemmt den Nervus vagus (Parasympathikus) und blockiert Magensäure, Bauchspeicheldrüse und Gallenblase.\n\n"
        "2. DÜNNDARM-BÜRSTENSAUM (30–40 m²), LAKTOSE & ZÖLIAKIE:\n"
        "- Laktoseintoleranz: Laktasemangel im Bürstensaum führt zu bakterieller Gärung im Dickdarm (Blähungen, Krämpfe, Durchfall). Lösung: Fermentierte Milchprodukte (Kefir, Ayran, gereifter Hartkäse) oder laktosefreie Varianten.\n"
        "- Zöliakie: Autoimmunreaktion auf Gluten zerstört den Bürstensaum -> schwere Nährstoffmängel. Bei Verdacht erst zum Arzt schicken (vor Bluttest noch nicht eigenmächtig glutenfrei essen!).\n\n"
        "3. DICKDARM-MIKROBIOM (1,5 KG) & LEBER:\n"
        "- Protektive Darmbakterien bilden aus löslichen Ballaststoffen, resistenter Stärke (abgekühlte Kartoffeln/Reis) und Fermentiertem (Sauerkraut, Kimchi) kurzkettige Fettsäuren für die Darmwand und Botenstoffe für die Darm-Hirn-Achse.\n"
        "- Die Leber baut giftiges Ammoniak zu Harnstoff um, bildet Albumin/Transferrin/IGF-1 und Gallensäuren.",
        "Fazit: Gründliches Kauen in Ruhe aktiviert über den Nervus vagus Magensäure, Gallenfluss und Bauchspeicheldrüse. Bei Blähbauch oder Mängeln werden Gluten und unfermentierte Milch gestrichen und der Darm über resistente Stärke sowie Sauerkraut/Kefir aufgebaut."
    ),
    (
        "Gesundheit",
        "Biometrie, Schlaf, Blutbild & RED-S Schutz",
        "Umsatzberechnung (Mifflin-St. Jeor), WHtR, 20-Punkte-Blutbild, Zyklus & RED-S Grenze (30 kcal/kg FFM)",
        "1. FORMELN & KENNZAHLEN:\n"
        "- Fettfreie Masse (FFM) = Gewicht (kg) - Speicherfett (kg). 1 kg Körperfett = 7.000 kcal.\n"
        "- Mifflin-St. Jeor Grundumsatz (GU): Männer = (10 x kg) + (6,25 x cm) - (5 x Alter) + 5 | Frauen = (10 x kg) + (6,25 x cm) - (5 x Alter) - 161.\n"
        "- Gesamtumsatz (TDEE) = GU x PAL (Büro/Sitzend 1,4–1,5; Aktiv 1,6–1,8). WHtR = Taille (cm) ÷ Größe (cm) (Ziel unter 40 J.: <= 0,50).\n\n"
        "2. ENERGIEVERFÜGBARKEIT (EA) & RED-S SCHUTZGRENZE:\n"
        "- Formel: EA = (Kalorienzufuhr - Sportverbrauch) ÷ kg FFM.\n"
        "- Optimal: >= 45 kcal/kg FFM | Diätbereich: 30–45 kcal/kg FFM | KRITISCHE UNTERGRENZE: < 30 kcal/kg FFM!\n"
        "- Unter 30 kcal/kg FFM droht nach 2–4 Wochen RED-S: Grundumsatz-Drosselung, Abfall von Schilddrüse (T3), Leptin, Testosteron und Östrogen (Zyklusverlust/Amenorrhö), Knochenabbau, Kraftverlust und Infektanfälligkeit.\n\n"
        "3. WEIBLICHER ZYKLUS & GROSSES BLUTBILD:\n"
        "- Zyklusphasen: Follikelphase (Tag 6–14, Östrogen steigt -> beste Phase für Diät & Kraft) | Ovulation (Tag 14, wenigstes Wasser) | Lutealphase (Tag 15–28, Progesteron hoch -> +1 bis 3 kg Wassereinlagerung & mehr Hunger, KEIN Fettzuwachs!).\n"
        "- 20-Punkte-Blutbild: Gesamt-/Freies Testosteron, Östradiol (E2), SHBG, LH/FSH, Progesteron, Prolaktin, GOT/GPT/GGT, Kreatinin/Harnstoff/GFR, HDL/LDL/Triglyzeride/ApoB, Nüchtern-Glukose/Insulin (HOMA-Index), HbA1c, Blutdruck, Homocystein, hsCRP, Großes Blutbild (Hämatokrit), Ferritin/Eisen/Transferrin, Vitamin D3, Zink/Magnesium, PSA.",
        "Fazit: Die Energieverfügbarkeit darf niemals dauerhaft unter 30 kcal pro kg fettfreier Masse sinken, um Hormon- und Stoffwechselschäden (RED-S) zu verhindern. Gleichzeitig sichern 7–8 Stunden Schlaf und regelmäßige Blutbildkontrollen die langfristige Gesundheit."
    ),

    # ==================== RUBRIK 4: PEPTIDE (BEYOND PEPTIDES 2026) ====================
    (
        "Peptide",
        "Heilung, Regeneration & Immunsystem",
        "BPC-157, TB-500, GHK-Cu, KPV & Thymosin Alpha-1 (Wirkung, Dosierung & Protokolle)",
        "1. BPC-157 (Body Protection Compound - 15 Aminosäuren):\n"
        "- Mechanismus: Fördert Angiogenese (Gefäßneubildung über VEGF), erhöht GH-Rezeptor-Expression an Fibroblasten, schützt Epithel-/Endothelbarrieren, beschleunigt Heilung von Sehnen, Bändern, Muskeln und Magen-Darm-Schleimhaut (Ulzera, Gastritis, Leaky Gut).\n"
        "- Dosierung (Research/Off-Label): Oral (GI-Trakt, extrem magensäurestabil): 500 mcg bis 1 mg täglich. Subkutan/i.m. (Verletzungen): 250–500 mcg/Tag (1–2x täglich) nahe der Verletzung. HWZ systemisch <30 Min., aber langanhaltende lokale Signalkaskaden.\n\n"
        "2. TB-500 (Synthetisches Fragment von Thymosin Beta-4, AS 17–23):\n"
        "- Mechanismus: Prodrug (aktiver Metabolit Ac-LKKTE), steuert Aktin-Migration, Wundheilung, Kollagenorganisation und wirkt antiinflammatorisch. Nicht direkt in der unmittelbaren Akutphase (erste Tage) einsetzen, um überschießende Narbenbildung zu vermeiden.\n"
        "- Dosierung: 2–5 mg pro Woche s.c. (aufgeteilt auf 1–2 Injektionen/Woche) über 4–8 Wochen. Systemische Wirkung, oral unwirksam.\n\n"
        "3. GHK-Cu (Kupfertripeptid):\n"
        "- Mechanismus: Endogener Kupfertransporter (unterstützt Superoxiddismutase, Kollagenvernetzung, Mitochondrien) und moduliert tausende Gene (Reparatur-Shift). Stark für Hautdicke, Wundheilung, Bindegewebe und Haarwachstum.\n"
        "- Dosierung: Topisch 0,1–1,0 % Creme (1x/Tag); Subkutan (Healing) 0,5–2 mg/Tag initial; Subkutan (Kosmetisch) 250–300 mcg/Tag für 4–12 Wochen (moderate Zinkzufuhr beachten!).\n\n"
        "4. KPV (Lysin-Prolin-Valin, C-terminales Alpha-MSH-Fragment ohne Bräunung):\n"
        "- Mechanismus: Blockiert NF-kB und proinflammatorische Zytokine, stärkt Tight Junctions im Darm (Colitis, Morbus Crohn, Leaky Gut), verlängert die Anagenphase der Haare.\n"
        "- Dosierung: Oral (Darm) 250–500 mcg nüchtern 1–2x/Tag; Subkutan 250–500 mcg 1x/Tag für 2–16 Wochen.\n\n"
        "5. THYMOSIN ALPHA-1 (Ta1 / Thymalfasin - 28 Aminosäuren):\n"
        "- Mechanismus: Fördert T-Zell-Reifung (CD4+/CD8+), NK-Zellen und Zytokin-Balance bei hoher Trainings-/Diätlast oder Infekten.\n"
        "- Dosierung: Immunsupport 1,0–1,5 mg s.c. 2–3x/Woche (4–8 Wochen); Akutphase 1,0–1,6 mg s.c. täglich für 7–14 Tage.",
        "Fazit: Im Injury-Recovery-Protokoll werden in der Akutphase (2–3 Wochen) BPC-157 (250–500 mcg/Tag) und TB-500 kombiniert und in einer 5–6-wöchigen Konsolidierungsphase ausgeschlichen, während KPV und orales BPC-157 den Goldstandard für die Darmbarriere bilden."
    ),
    (
        "Peptide",
        "Fettverlust & Inkretin-Agonisten (GLP-1 / GIP / Glukagon)",
        "Semaglutid, Tirzepatid, Retatrutid & HGH Fragment 176-191 / AOD-9604",
        "1. SEMAGLUTID (Mono-Agonist: GLP-1 | HWZ ~165 Std.):\n"
        "- Mechanismus: Verzögert Magenentleerung, dämpft dopaminerge Food-Reward-Signale im ZNS, verbessert glukoseabhängige Insulinsekretion.\n"
        "- Athleten-Dosierung: Start 0,25 mg/Woche s.c., Zielbereich 0,25–0,5 mg/Woche (hohes Protein & Krafttraining gegen Muskelverlust zwingend!).\n\n"
        "2. TIRZEPATID (Twincretin: GLP-1 + GIP | HWZ ~5 Tage):\n"
        "- Mechanismus: Übertrifft Semaglutid beim Fettverlust, steigert periphere Insulinsensitivität massiv, baut bis zu 70 % Leberfett ab und eliminiert 'Food Noise'.\n"
        "- Athleten-Dosierung: Mini-Cut 2,5–5 mg/Woche s.c., Wettkampfdiät 5–7,5 mg/Woche (Steigerung frühestens alle 2–4 Wochen).\n\n"
        "3. RETATRUTID (Triple-Agonist: GLP-1 + GIP + Glukagon | HWZ ~6–7 Tage):\n"
        "- Mechanismus: Aktiviert zusätzlich den Glukagon-Rezeptor in der Leber -> steigert aktiv die hepatische Beta-Oxidation und den Ruheenergieverbrauch um +100 bis +250 kcal/Tag (verhindert das Einschlafen des Grundumsatzes in der Diät).\n"
        "- Dosierung: Langsame Titration ab 2–4 mg/Woche s.c. (Studien-Zielbereich 8–12 mg/Woche). Tipp: Wochendosis auf 2 kleinere Injektionen splitten, um GI-Nebenwirkungen zu minimieren.\n\n"
        "4. HGH FRAGMENT 176-191 & AOD-9604:\n"
        "- Mechanismus: Isolierter lipolytischer Abschnitt des Wachstumshormons (AS 176–191). Stimuliert Lipolyse (HSL/ATGL) und hemmt Lipogenese OHNE IGF-1-Anstieg und OHNE Insulinresistenz. Wirkt NUR im nüchternen Zustand und im Kaloriendefizit!\n"
        "- Dosierung: 500 mcg/Tag s.c. (250 mcg morgens nüchtern + 4 Std. fasten & 250 mcg vor dem Schlafen, 3–4 Std. nach letzter Mahlzeit; Zyklus: 3 Wochen ON / 1 Woche OFF).",
        "Fazit: Während Semaglutid und Tirzepatid primär über Hunger- und Insulinregulation wirken, erhöht der Triple-Agonist Retatrutid über den Glukagon-Rezeptor zusätzlich aktiv den Kalorienverbrauch und die Fettoxidation."
    ),
    (
        "Peptide",
        "Mitochondrien, Ausdauer & Zellenergie",
        "SLU-PP-332, MOTS-c, Methylene Blue (5-Stunden-Regel) & NAD+ (NMN / NR)",
        "1. SLU-PP-332 (ERR-alpha/gamma Agonist / 'Trainingsmimetikum'):\n"
        "- Mechanismus: Aktiviert Estrogen-Related-Receptors -> steigert mitochondriale Biogenese, Fettsäureoxidation und Ausdauerleistung ohne ZNS-Stimulation (Puls/Blutdruck bleiben ruhig) und ohne mTOR-Hemmung.\n"
        "- Dosierung (Research): 500 mcg bis 2 mg oral morgens täglich oder 1–1,5 mg/Woche s.c. (auf 2–3 Gaben verteilt).\n\n"
        "2. MOTS-c (Mitochondrial abgeleitetes Peptid - 16 Aminosäuren):\n"
        "- Mechanismus: Aktiviert den zellulären Energiesensor AMPK, fördert Glukoseaufnahme in die Skelettmuskulatur, verbessert Insulinsensitivität und metabolische Flexibilität.\n"
        "- Dosierung (Research): ca. 5 mg s.c., 2x pro Woche über 4–6 Wochen.\n\n"
        "3. METHYLENE BLUE (Methylenblau - Mitochondrialer Redox-Carrier):\n"
        "- Mechanismus: Überbrückt als Elektronendonator/-akzeptor geschädigte Komplexe (I–III) der Atmungskette, steigert ATP-Effizienz in Gehirn und Muskel und fängt überschüssige freie Radikale (ROS) ab.\n"
        "- WICHTIGE SICHERHEITSREGELN: 1. Wirkt als MAO-A-Inhibitor -> NIEMALS mit SSRI/SNRI-Antidepressiva kombinieren (Gefahr eines lebensbedrohlichen Serotonin-Syndroms!). 2. DIE 5-STUNDEN-REGEL: Mindestens 5 Stunden Abstand zum Krafttraining einhalten, um anabole ROS-Entzündungssignale für die Muskelhypertrophie nicht zu blockieren! Dosierung: 5–15 mg/Tag (Fokus Mitochondrien) bis 15–30 mg/Tag (Kognition).\n\n"
        "4. NAD+ & VORSTUFEN (NMN, NR, NADH):\n"
        "- Mechanismus: Essenzieller Cofaktor der Atmungskette sowie Substrat für Sirtuine und DNA-Reparatur (PARP-Enzyme).\n"
        "- Dosierung (oral): NMN 250 mg/Tag, NR 300–500 mg/Tag, NADH 5–20 mg/Tag.",
        "Fazit: Das Mitochondrien-Boost-Protokoll kombiniert SLU-PP-332 (morgens für mitochondriale Biogenese), MOTS-c (an Ruhetagen für AMPK-Aktivierung) und Methylene Blue (mit mind. 5 Std. Abstand zum Krafttraining für direkten Elektronentransport)."
    ),
    (
        "Peptide",
        "Wachstumshormon-Achse (HGH-Secretagogues & IGF-1)",
        "GHRH (Sermorelin, Tesamorelin, CJC-1295), GHRPs, Ipamorelin, MK-677 & IGF-1 (LR3 / DES)",
        "1. GRUNDREGEL FÜR ALLE HGH-SECRETAGOGUES:\n"
        "- Insulin hemmt die GH-Ausschüttung der Hypophyse stark! Alle GHRH/GHRP-Peptide müssen STRIKT NÜCHTERN (mind. 2–3 Std. nach der letzten Mahlzeit, danach 30–60 Min. nichts essen) injiziert werden.\n\n"
        "2. KLASSE I – GHRH-ANALOGA:\n"
        "- Sermorelin (Mod-GRF 1-29): HWZ ~10–20 Min., sanfter Puls für Schlaf & Achsenpflege; 100–300 mcg s.c. 1–2x/Tag.\n"
        "- Tesamorelin: Klinisch validiert zur starken Reduktion von viszeralem Bauchfett; 1–2 mg s.c. 1x/Tag (8–12 Wochen).\n"
        "- CJC-1295 mit DAC: Durch Albuminbindung mehrtägige HWZ, hebt Basis-GH und IGF-1 dauerhaft; 0,5–2 mg s.c. 1x/Woche.\n\n"
        "3. KLASSE II & III – GHRPs & SELEKTIVE GHRELIN-AGONISTEN:\n"
        "- Klassische GHRPs: GHRP-2 (100–300 mcg, moderater Hunger), GHRP-6 (100–300 mcg, massiver Hunger-Spike nach 15–30 Min.), Hexarelin (50–150 mcg, stärkster GH-Peak, aber rasche Rezeptor-Desensibilisierung & Anstieg von Cortisol/Prolaktin).\n"
        "- Ipamorelin (Selektives GHS): 100–300 mcg s.c. 1–3x/Tag; sauberer GH-Puls OHNE Anstieg von Cortisol, Prolaktin oder Heißhunger.\n"
        "- Goldstandard-Kombi (CJC-1295 ohne DAC + Ipamorelin): Je 100–200 mcg CJC-1295 ohne DAC + 100–300 mcg Ipamorelin zeitgleich abends vor dem Schlafen (und optional morgens nüchtern) für 8–12 Wochen für einen synergistischen, physiologischen GH-Peak.\n\n"
        "4. MK-677 (Ibutamoren) & IGF-1 (LR3 / DES):\n"
        "- MK-677: Oraler Ghrelin-Agonist (HWZ 20–24h), 5–25 mg/Tag (meist abends). Steigert GH/IGF-1 (+20–60 %) und Tiefschlaf, verursacht aber starken Hunger, Wassereinlagerung und verschlechtert die Insulinsensitivität (Blutzucker überwachen!).\n"
        "- IGF-1 LR3 & DES: Direkter Zellproliferations- und Satellitenzell-Booster. LR3 wirkt systemisch (~20h), DES lokal (~20–30 Min.). Strikte Kohlenhydratzufuhr wegen Hypoglykämie-Risiko nötig.",
        "Fazit: Die Kombination aus CJC-1295 (ohne DAC) und Ipamorelin vor dem Schlafen gilt als sauberste Methode zur Steigerung der körpereigenen, pulsatilen Wachstumshormonausschüttung ohne Cortisol- oder Prolaktin-Nebenwirkungen."
    ),
    (
        "Peptide",
        "Hormonachse (HPTA), Libido, Bräunung & Nootropika",
        "hCG, hMG, Kisspeptin-10, Melanotan II, PT-141, DSIP, Epitalon, Selank & Semax",
        "1. HPTA-ACHSE & FERTILITÄT (hCG, hMG & Kisspeptin-10):\n"
        "- hCG: LH-Analogon an den Leydig-Zellen, erhält intratestikuläres Testosteron und Hodenvolumen unter TRT/AAS (250–500 I.E. s.c. 2–3x/Woche; vor einer SERM-PCT 500 I.E. alle 2 Tage für 10–14 Tage, aber NIEMALS während der eigentlichen PCT nutzen, da es die Hypophyse weiter supprimiert; erhöht zudem intratestikuläre Aromatase/Östrogen!).\n"
        "- hMG: Liefert zusätzlich FSH für die Sertoli-Zellen -> zwingend nötig für echte Spermienreifung bei Kinderwunsch (25–150 I.E. s.c. 2–3x/Woche kombiniert mit hCG).\n"
        "- Kisspeptin-10: Stimuliert im Hypothalamus die pulsatile GnRH-Freisetzung (100–200 mcg s.c. 2–3x/Woche für 2–4 Wochen).\n\n"
        "2. MELANOTAN II (MT-II) & PT-141 (Bremelanotid):\n"
        "- Melanotan II: Unselektiver Melanocortin-Agonist (MC1R–MC5R) für Eumelanin-Bräunung, UV-Schutz, Libido und Appetithemmung. Langsam einschleichen: Start 125 mcg s.c. täglich (20–30 Min. vor Sonne), steigern bis Wunschbräune, dann Erhaltung alle 5–7 Tage (Warnung: Übelkeit, Flush, neue Muttermale; kontraindiziert bei Melanomrisiko).\n"
        "- PT-141: Selektiver zentraler MC4R-Agonist für Libido/Erregung über das ZNS (bei Männern & Frauen wirksam). 1–2 mg s.c. 45–60 Min. vorab (max. 1 Dosis/24h, max. 8/Monat; NIEMALS gleichzeitig mit PDE-5-Hemmern wie Sildenafil/Tadalafil wegen Blutdruckspitzen und Priapismus-Gefahr!).\n\n"
        "3. SCHLAF, LONGEVITY & NOOTROPIKA (DSIP, Epitalon, Selank, Semax):\n"
        "- DSIP (Delta-Sleep-Inducing Peptide): Fördert Tiefschlaf (N3) und senkt nächtliches Cortisol ohne Sedierung; 100 mcg s.c. vor dem Schlafen (4 Wochen ON / 1 Woche OFF).\n"
        "- Epitalon: Aktiviert Telomerase (Telomerschutz) und stellt die nächtliche Melatoninproduktion der Zirbeldrüse wieder her; 200–300 mcg s.c. abends über 4 Wochen, danach 3 Monate Pause.\n"
        "- Selank: Anxiolytisches Tuftsin-Analogon (GABA-A-Modulation + BDNF) für 'Calm Focus' unter Stress ohne Suchtpotenzial; 200–500 mcg intranasal 1–2x/Tag (4 Wochen ON / 4 Wochen OFF).\n"
        "- Semax: ACTH-Fragment (ohne Cortisol-Effekt), steigert BDNF, synaptische Plastizität, Arbeitsgedächtnis und mentalen Fokus; 200–600 mcg intranasal morgens (10–14 Tage ON / 7 Tage OFF).",
        "Fazit: Für kognitive Spitzenleistung unter Stress liefern Semax (Fokus/BDNF) und Selank (Ruhe/GABA) intranasal gezielte Unterstützung, während DSIP und Epitalon Tiefschlaf und zelluläre Regeneration optimieren."
    ),
    (
        "Peptide",
        "Handwerkliche Praxis & Rekonstitution",
        "Anmischen mit BAC Water, Konzentrationsberechnung, Lagerung & Fertig-Stacks (GLOW / KLOW)",
        "1. REKONSTITUTION (ANMISCHEN) SCHRITT FÜR SCHRITT:\n"
        "- Lösungsmittel: Für Mehrfachentnahmen zwingend bakteriostatisches Wasser (BAC Water mit 0,9 % Benzylalkohol) verwenden (steriles Wasser ohne Konservierungsmittel ist nur für den Einmalgebrauch).\n"
        "- Ablauf: Gummistopfen beider Vials mit Alkoholpad desinfizieren -> BAC Water langsam entlang der Glasinnenwand ins Peptid-Vial laufen lassen (niemals direkt mit Druck auf das Lyophilisat-Pulver spritzen!) -> Vial NIEMALS schütteln, sondern nur sanft schwenken/rollen, bis die Lösung komplett klar ist.\n\n"
        "2. KONZENTRATIONSBERECHNUNG & INJEKTION:\n"
        "- Beispielrechnung: 10 mg Peptid + 2 ml BAC Water = 5 mg pro ml (5.000 mcg/ml). Auf einer Standard-100-IU-Insulinspritze (1 ml = 100 Einheiten) entspricht 1 IU (Einheit/Teilstrich) exakt 0,05 mg = 50 mcg.\n"
        "- Lagerung & Nadeln: Angemischte Peptide stets im Kühlschrank bei 2–8 °C lagern (Haltbarkeit ca. 30 Tage). Subkutane Injektion (45–90° Winkel in Bauchfettfalte) mit 29–31G Insulinspritzen (8–12 mm Länge), Einstichstellen rotieren, danach nicht reiben.\n\n"
        "3. MISCHEN IN EINER SPRITZE & KOMBI-VIALS (GLOW / KLOW):\n"
        "- Kompatible Peptide auf BAC-Water-Basis (z.B. BPC-157 + TB-500) können direkt vor der Injektion zusammen in einer Spritze aufgezogen werden, sollten aber nicht langfristig zusammengemischt gelagert werden.\n"
        "- Fertige Misch-Vials ('GLOW' = BPC-157 + TB-500 + GHK-Cu | 'KLOW' = zusätzlich KPV): Erlauben keine individuelle Dosisanpassung der Einzelkomponenten, und das reaktive Kupferpeptid (GHK-Cu) beschleunigt den Abbau der anderen Peptide – solche Fertigmischungen nach dem Anmischen innerhalb von maximal 2 Wochen aufbrauchen!",
        "Fazit: Saubere Hygiene, sanftes Anmischen mit BAC Water entlang der Glaswand ohne Schütteln sowie kühle Lagerung bei 2–8 °C sichern die biologische Aktivität und Sterilität jedes Peptids."
    )
]

def sync_master_knowledge():
    for rub, sub, title, rules, prac in MASTER_KNOWLEDGE:
        existing = cur_k.execute("SELECT id FROM knowledge_base WHERE title = ?", (title,)).fetchone()
        if existing:
            cur_k.execute(
                "UPDATE knowledge_base SET rubric=?, sub_category=?, core_rules=?, practical_application=? WHERE id=?",
                (rub, sub, rules, prac, existing[0])
            )
        else:
            cur_k.execute(
                "INSERT INTO knowledge_base (rubric, sub_category, title, core_rules, practical_application) VALUES (?, ?, ?, ?, ?)",
                (rub, sub, title, rules, prac)
            )
    conn_k.commit()

sync_master_knowledge()

# =========================================================
# 4. KUNDEN-DATENBANK HELFER & AUTOMATISCHE NAMENSERKENNUNG
# =========================================================
def get_all_clients():
    return cur_c.execute(
        "SELECT id, name, gender, age, height_cm, weight_kg, kfa_pct, waist_cm, pal, goal, phase, complaints, training_days, bench_kg, squat_kg, deadlift_kg, ohp_kg, pullup_kg, notes FROM clients ORDER BY name ASC"
    ).fetchall()

def get_client_by_id(cid):
    row = cur_c.execute(
        "SELECT id, name, gender, age, height_cm, weight_kg, kfa_pct, waist_cm, pal, goal, phase, complaints, training_days, bench_kg, squat_kg, deadlift_kg, ohp_kg, pullup_kg, notes FROM clients WHERE id=?",
        (cid,)
    ).fetchone()
    if not row:
        return None
    keys = ["id", "name", "gender", "age", "height_cm", "weight_kg", "kfa_pct", "waist_cm", "pal", "goal", "phase", "complaints", "training_days", "bench_kg", "squat_kg", "deadlift_kg", "ohp_kg", "pullup_kg", "notes"]
    return dict(zip(keys, row))

def detect_client_in_text(user_text):
    """Prüft, ob Coach Arif im Text den Namen eines gespeicherten Kunden erwähnt."""
    t_low = user_text.lower()
    for row in get_all_clients():
        c_name = row[1].strip()
        if c_name and len(c_name) >= 2:
            first_name = c_name.split()[0].lower()
            if c_name.lower() in t_low or re.search(r"\b" + re.escape(first_name) + r"\b", t_low):
                return get_client_by_id(row[0])
    return None

def load_chat_messages(client_id):
    rows = cur_c.execute(
        "SELECT role, content FROM client_chats WHERE client_id=? ORDER BY id ASC",
        (client_id,)
    ).fetchall()
    if rows:
        return [{"role": r[0], "content": r[1]} for r in rows]
    if client_id == 0:
        welcome = (
            "Hallo Arif! Ich bin dein **lokaler Arif 345 KI-Co-Coach**.\n\n"
            "- Du kannst links in der Seitenleiste **Kunden anlegen & auswählen** (jeder Kunde hat seinen eigenen gespeicherten Chat!).\n"
            "- Deine Datenbank umfasst jetzt alle **4 Säulen: Training, Ernährung, Gesundheit & Peptide**.\n"
            "- Nenne mir hier einfach den **Namen eines gespeicherten Kunden** oder schildere einen Fall per **Sprache oder Text**!"
        )
    else:
        c_info = get_client_by_id(client_id)
        c_name = c_info["name"] if c_info else "Kunde"
        welcome = (
            f"Hallo Arif! Dies ist die persönliche Coaching-Akte und der separate Chat für **{c_name}**.\n\n"
            f"Alle Körperdaten, Kraftwerte und Beschwerden von **{c_name}** sind automatisch geladen. "
            f"Frag mich einfach nach dem kompletten Plan, einer Anpassung oder sprich deine Frage ein!"
        )
    return [{"role": "assistant", "content": welcome}]

def save_chat_message(client_id, role, content):
    cur_c.execute(
        "INSERT INTO client_chats (client_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (client_id, role, content, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn_c.commit()

def clear_chat_messages(client_id):
    cur_c.execute("DELETE FROM client_chats WHERE client_id=?", (client_id,))
    conn_c.commit()

# =========================================================
# 5. LOKALE ARIF 345 KI-ENGINE (MIT KUNDEN-VERKNÜPFUNG)
# =========================================================
if "case_memory" not in st.session_state:
    st.session_state.case_memory = {
        "name": None,
        "gender": None,
        "age": None,
        "weight": None,
        "height": None,
        "kfa": None,
        "waist": None,
        "pal": 1.55,
        "goal": None,
        "phase": None,
        "days": None,
        "bench_kg": 0,
        "squat_kg": 0,
        "deadlift_kg": 0,
        "ohp_kg": 0,
        "pullup_kg": 0,
        "complaints": set()
    }

SYMPTOM_MAP = {
    "schulter": ["schulter", "impingement", "rotatoren", "bankdrücken schmerz", "überkopf"],
    "knie": ["knie", "patella", "meniskus", "kniebeuge schmerz", "beintraining schmerz"],
    "rücken": ["rücken", "lws", "bandscheibe", "ischias", "kreuzheben schmerz", "unterer rücken"],
    "reflux": ["reflux", "sodbrennen", "magensäure", "aufstoßen", "speiseröhre"],
    "darm": ["blähbauch", "blähung", "durchfall", "verstopfung", "darm", "verdauung", "laktose", "zöliakie", "gluten", "bauchschmerz", "kpv"],
    "eisen_müde": ["eisen", "müde", "müdigkeit", "erschöpft", "antriebslos", "transferrin", "blutbild", "haarausfall", "ferritin", "hypoxie"],
    "plateau": ["plateau", "stagniert", "stagnation", "nimmt nicht ab", "gewicht steht", "waage", "stillstand"],
    "heißhunger": ["heißhunger", "snacken", "süßigkeiten", "fressattacke", "cheat", "appetit", "hunger"],
    "schlaf_stress": ["schlaf", "schlecht geschlafen", "stress", "kortisol", "schichtdienst", "nachtschicht", "regeneration", "dsip", "epitalon"],
    "blutfette_leber": ["cholesterin", "ldl", "triglyzerid", "fettleber", "blutfett", "entzündung", "omega"],
    "kultur": ["türkisch", "kultur", "familie", "auswärts", "alltag"],
    "peptide": ["peptid", "bpc", "bpc-157", "tb-500", "tb500", "ghk", "kpv", "retatrutid", "tirzepatid", "semaglutid", "ipamorelin", "cjc", "mk-677", "mk677", "slu-pp", "mots-c", "methylene", "methylenblau", "semax", "selank", "pt-141", "melanotan", "hcg", "hmg", "kisspeptin", "bac water", "rekonstitution"]
}

def load_client_into_memory(c_dict, mem):
    if not c_dict:
        return
    mem["name"] = c_dict.get("name")
    mem["gender"] = c_dict.get("gender")
    mem["age"] = c_dict.get("age")
    mem["weight"] = c_dict.get("weight_kg")
    mem["height"] = c_dict.get("height_cm")
    mem["kfa"] = c_dict.get("kfa_pct")
    mem["waist"] = c_dict.get("waist_cm")
    mem["pal"] = c_dict.get("pal") or 1.55
    mem["goal"] = c_dict.get("goal")
    mem["phase"] = c_dict.get("phase")
    mem["days"] = c_dict.get("training_days") or 3
    mem["bench_kg"] = c_dict.get("bench_kg") or 0
    mem["squat_kg"] = c_dict.get("squat_kg") or 0
    mem["deadlift_kg"] = c_dict.get("deadlift_kg") or 0
    mem["ohp_kg"] = c_dict.get("ohp_kg") or 0
    mem["pullup_kg"] = c_dict.get("pullup_kg") or 0
    comp_text = f"{c_dict.get('complaints', '')} {c_dict.get('notes', '')}".lower()
    for key, keywords in SYMPTOM_MAP.items():
        if any(k in comp_text for k in keywords):
            mem["complaints"].add(key)

def extract_case_parameters(text, mem):
    t = text.lower()
    if any(w in t for w in ["frau", "weiblich", "kundin", "klientin"]):
        mem["gender"] = "Weiblich"
    elif any(w in t for w in ["mann", "männlich", "kunde", "klient"]):
        if not mem["gender"]:
            mem["gender"] = "Männlich"

    m_weight = re.search(r"(\d{2,3}(?:[\.,]\d+)?)\s*(?:kg|kilo)", t)
    if m_weight:
        val = float(m_weight.group(1).replace(",", "."))
        if 35 <= val <= 250:
            mem["weight"] = val

    m_height = re.search(r"(\d{3})\s*cm", t)
    if m_height:
        val = float(m_height.group(1))
        if 140 <= val <= 220:
            mem["height"] = val

    m_age = re.search(r"(\d{2})\s*(?:jahre|j\.|alt)", t)
    if m_age:
        val = int(m_age.group(1))
        if 14 <= val <= 90:
            mem["age"] = val

    m_kfa = re.search(r"(\d{1,2}(?:[\.,]\d+)?)\s*%\s*(?:kfa|körperfett)?", t)
    if m_kfa:
        val = float(m_kfa.group(1).replace(",", "."))
        if 4 <= val <= 60:
            mem["kfa"] = val

    m_days = re.search(r"(\d)\s*(?:x|mal|tage)\s*(?:pro woche|training|gym|woche|trainieren)?", t)
    if m_days:
        d = int(m_days.group(1))
        if 1 <= d <= 7:
            mem["days"] = d

    if any(w in t for w in ["abnehmen", "diät", "fettverlust", "fettabbau", "defizit", "definieren", "übergewicht", "adipositas"]):
        mem["goal"] = "Fettabbau / Diät"
    elif any(w in t for w in ["aufbau", "muskelaufbau", "masse", "zunehm", "kraft"]):
        mem["goal"] = "Muskel- & Kraftaufbau"

    for key, keywords in SYMPTOM_MAP.items():
        if any(k in t for k in keywords):
            mem["complaints"].add(key)

def search_relevant_db_entries(query_text, limit=3):
    rows = cur_k.execute("SELECT rubric, sub_category, title, core_rules, practical_application FROM knowledge_base").fetchall()
    words = [w.lower() for w in re.findall(r"\w+", query_text) if len(w) > 2]
    scored = []
    for r in rows:
        blob = f"{r[0]} {r[1]} {r[2]} {r[3]} {r[4]}".lower()
        score = sum(3 if w in r[2].lower() else (1 if w in blob else 0) for w in words)
        if score > 0:
            scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in scored[:limit]]

def generate_local_arif_coaching_response(user_text, active_client_id=0):
    mem = st.session_state.case_memory

    if active_client_id > 0:
        c_dict = get_client_by_id(active_client_id)
        load_client_into_memory(c_dict, mem)
    else:
        detected_client = detect_client_in_text(user_text)
        if detected_client:
            load_client_into_memory(detected_client, mem)

    extract_case_parameters(user_text, mem)
    kb_matches = search_relevant_db_entries(user_text, limit=3)

    sections = []
    client_header = f"für **{mem['name']}**" if mem.get("name") else "(Arif 345 System)"
    sections.append(f"### 🦁 Coach-zu-Coach Analyse {client_header}")

    # 1. BIOMETRIE & MAKRO-BERECHNUNG
    if mem["weight"]:
        w = mem["weight"]
        h = mem["height"] if mem["height"] else 175.0
        a = mem["age"] if mem["age"] else 30
        g = mem["gender"] if mem["gender"] else "Männlich"
        kfa = mem["kfa"] if mem["kfa"] else (24.0 if g == "Weiblich" else 20.0)
        waist = mem["waist"] if mem["waist"] else 88.0
        pal = mem["pal"] if mem["pal"] else 1.55

        ffm = round(w * (1 - kfa / 100.0), 1)
        gu = round((10 * w) + (6.25 * h) - (5 * a) + (5 if g == "Männlich" else -161))
        tdee = round(gu * pal)
        whtr = round(waist / h, 2) if h > 0 else 0
        reds_limit = round(ffm * 30 + 250)

        goal = mem["goal"] if mem["goal"] else "Fettabbau / Diät"
        phase_str = mem["phase"] if mem.get("phase") else "Phase 1: Detox & Reset"

        if "Fettabbau" in goal or "Diät" in goal:
            target_kcal = max(tdee - 450, reds_limit)
            ref_weight = ffm * 1.15 if kfa >= 28 else w
            prot_g = round(ref_weight * 2.0)
            fat_g = max(round(w * 0.8), round(w * 0.5))
        else:
            target_kcal = tdee + 250
            prot_g = round(w * 1.8)
            fat_g = round(w * 1.0)

        carb_kcal = max(target_kcal - (prot_g * 4.1) - (fat_g * 9.3), 100 * 4.1)
        carb_g = round(carb_kcal / 4.1)

        sections.append(
            f"#### 📊 1. Berechnete Biometrie & Makro-Vorgabe ({g}, {w} kg, {h} cm, {a} J. | {phase_str})\n"
            f"- **Fettfreie Masse (FFM):** `{ffm} kg` (KFA: `{kfa}%`) | **WHtR:** `{whtr}` *(Ziel <= 0,50)*\n"
            f"- **Grundumsatz (Mifflin-St. Jeor):** `{gu} kcal` | **Gesamtumsatz (TDEE bei PAL {pal}):** `{tdee} kcal`\n"
            f"- **RED-S Schutzgrenze (>= 30 kcal/kg FFM):** Niemals dauerhaft unter **`{reds_limit} kcal`** gehen!\n"
            f"- **Empfohlene Ziel-Kalorien ({goal}):** **`{target_kcal} kcal / Tag`**\n"
            f"- **Makro-Verteilung nach Arif 345:**\n"
            f"  * **Protein:** **`{prot_g} g`** *(20–30 % Thermogenese/NIT, Muskelschutz & Transportproteine Albumin/Transferrin)*\n"
            f"  * **Fett:** **`{fat_g} g`** *(mind. 0,5 g/kg KG Hormonschutz; Weidebutter, Olivenöl, Eier, Lachs & 2–3 g EPA/DHA)*\n"
            f"  * **Kohlenhydrate:** **`{carb_g} g`** *(gezielt Pre- und Post-Workout über Kartoffeln, Basmatireis, Buchweizen & Beeren)*"
        )

    # 2. SPEZIFISCHE BESCHWERDEN & SYMPTOME AUSWERTEN
    c_blocks = []
    if "schulter" in mem["complaints"]:
        c_blocks.append(
            "🩺 **Schulterbeschwerden / Impingement (Training & Entzündung):**\n"
            "- **Sofort-Anpassung im Arif 345 Push-Plan:** Wechsle beim Bankdrücken/Schulterdrücken auf **Kurzhanteln im Neutralgriff** (Handflächen zueinander – öffnet das Schulterdach!) oder moderates Schrägbankdrücken.\n"
            "- **Warmup-Pflicht:** 10 Min. Mobility-Warmup mit Therabändern (Außenrotation, Facepulls, Band Pull-Aparts).\n"
            "- **Ernährungs- & Peptid-Hebel:** Streiche entzündungsfördernde Samenöle, gib täglich **2–3 g Omega-3 (EPA/DHA)**; aus der Peptid-Rubrik sind lokal **BPC-157** (250–500 mcg/Tag s.c.) und **TB-500** (2–5 mg/Woche) die spezifischen Regulatoren für Sehnenheilung."
        )
    if "knie" in mem["complaints"]:
        c_blocks.append(
            "🩺 **Kniebeschwerden / Patellasehne (Legs-Tag Anpassung):**\n"
            "- **Sofort-Anpassung am Legs-Tag:** Reduziere schmerzhaften Knievorschub. Ersetze freie tiefe Kniebeugen durch **Box Squats** oder **Spanische Kniebeugen** (isometrischer Reiz regt die Kollagensynthese der Patellasehne an).\n"
            "- **Fokus hintere Kette:** Priorisiere **Hip Thrusts, Rumänisches Kreuzheben (RDL) und Beinbeuger (Leg Curls)** (je 5 Sätze x 8–15 Reps)."
        )
    if "rücken" in mem["complaints"]:
        c_blocks.append(
            "🩺 **Rücken- / LWS-Beschwerden (Pull- & Legs-Tag Anpassung):**\n"
            "- **Sofort-Anpassung im Arif 345 System:** Wechsle von klassischem Kreuzheben auf die **Trap-Bar (Hex-Bar)** oder **Rumänisches Kreuzheben** und nutze **brustgestütztes Rudern (Chest-Supported Row)**.\n"
            "- **Rumpf-Stabilität (Core Finisher):** Baue im 10-Minuten-Bauch-Finisher statische **Planks** für maximales Rumpf-Bracing ein."
        )
    if "reflux" in mem["complaints"]:
        c_blocks.append(
            "🔥 **Reflux / Sodbrennen (OTL Modul 1 & 7 Verknüpfung):**\n"
            "- **Ernährungs-Lösung:** Verteile das Essen auf **4–5 kleinere, eiweißreiche Mahlzeiten** über den Tag (stärkt den unteren Speiseröhrenschließmuskel und lindert Reflux nachweislich).\n"
            "- **Fett- & Timing-Regel:** Keine riesigen, fettreichen Mahlzeiten (bis zu 8 Std. Magenverweildauer) spät abends; letzte Mahlzeit 2–3 Std. vor dem Schlafen."
        )
    if "darm" in mem["complaints"]:
        c_blocks.append(
            "🦠 **Blähbauch, Verdauungsprobleme & Unverträglichkeiten (Phase 1 Reset):**\n"
            "- **Start mit Phase 1 (1 Monat Detox & Reset):** Streiche Weizen/Gluten, industrielle Samenöle, künstliche Emulgatoren und unfermentierte Milch.\n"
            "- **Mikrobiom-Aufbau & Peptide:** Nutze **abgekühlte Kartoffeln oder abgekühlten Reis** (resistente Stärke) sowie **Kefir, Ayran und Sauerkraut/Kimchi**. Aus der Peptid-Datenbank schützen **orales BPC-157** (500 mcg/Tag) und **KPV** (250–500 mcg nüchtern) gezielt die Tight Junctions der Darmwand."
        )
    if "eisen_müde" in mem["complaints"]:
        c_blocks.append(
            "⚡ **Müdigkeit, Erschöpfung & Eisenmangel (Fließbandgesetz & Transferrin):**\n"
            "- **Die Supplement-Falle (Stufe 2 Fließbandgesetz):** Eisen benötigt das Transportprotein **Transferrin** (und andere Stoffe **Albumin**). Fehlt Protein in der Ernährung, sind Eisentabletten völlig wirkungslos!\n"
            "- **Arif 345 Lösung:** 1. Proteinzufuhr auf **1,8–2,2 g/kg KG** sichern. 2. In Ruhe kauen (Nervus vagus -> Magensäure & Intrinsic Factor für Vitamin B12). 3. Rotes Rindfleisch und 1–2x/Woche **Rinderleber** (8,8 mg Eisen, 111 mcg B12, 53.400 IU Vitamin A) einbauen."
        )
    if "plateau" in mem["complaints"]:
        c_blocks.append(
            "📉 **Gewichts-Plateau / Stagnation auf der Waage (Diät-Blueprint):**\n"
            "- **Die 10–14 Tage Checkliste:** Erst wenn über **mindestens 10–14 Tage** weder Wochendurchschnitt noch Bauchumfang/Spiegelbild sinken und Tracking + Schritte (>10.000) zu 100 % saßen, senken wir um **-100 bis -200 kcal** (aus Kohlenhydraten oder Fetten – **niemals aus dem Protein!**)."
        )
    if "heißhunger" in mem["complaints"]:
        c_blocks.append(
            "🍫 **Heißhunger, Snacken & Cheat-Anfragen:**\n"
            "- **Kartoffel-Prinzip & GL:** Gekochte Salzkartoffeln (80 kcal/100g) mit Vollei (Biologische Wertigkeit 136!) + großes Gemüsevolumen halten Insulin flach.\n"
            "- **Cheat-Meal-Regel:** Keine Cheats in den ersten 2–3 Wochen! Danach maximal alle 7–14 Tage **ein einzelnes geplantes Cheat Meal** (niemals ein Cheat Day)."
        )
    if "schlaf_stress" in mem["complaints"]:
        c_blocks.append(
            "😴 **Schlafmangel, hoher Stress & Schichtdienst:**\n"
            "- **Hormon-Schutz:** Schlafmangel senkt das Wachstumshormon Somatotropin (GH) und erhöht Kortisol (zieht Wasser, baut Muskeln ab und steigert Hunger). Cardio reduzieren, abends Magerquark/Skyr + komplexe Kohlenhydrate (Kartoffeln/Reis fördern Serotonin/Melatonin) + Magnesium (350–400 mg)."
        )
    if "blutfette_leber" in mem["complaints"]:
        c_blocks.append(
            "🫀 **Erhöhte Blutfette (LDL / Triglyzeride) & Fettleber:**\n"
            "- **Hebel:** Gesättigte Fette aus Wurst/Schmalz senken, Transfette streichen. Täglich **2–3 g EPA/DHA (Omega-3)** (-25 bis -30 % Triglyzeride & Leberfettabbau), **30–70 g Walnüsse/Mandeln** (-6 bis -12 % LDL) und **lösliche Ballaststoffe** (Äpfel/Pektin, Beeren)."
        )

    if c_blocks:
        sections.append("#### 🛠️ 2. Spezifische Lösungen für die genannten Beschwerden\n" + "\n\n".join(c_blocks))

    # 3. KONKRETER ARIF 345 TRAININGS- & PROGRESSIONSVORSCHLAG
    days = mem["days"] if mem["days"] else 3
    step_num = "3" if (c_blocks or mem["weight"]) else "2"
    strength_info = ""
    if any([mem.get("bench_kg"), mem.get("squat_kg"), mem.get("deadlift_kg"), mem.get("ohp_kg")]):
        strength_info = (
            f"\n- **Aktuelle Arif 345 Arbeitsgewichte von {mem.get('name') or 'Kunde'}:** "
            f"Bankdrücken: `{mem.get('bench_kg', 0)} kg` (+2,5 kg nach Zyklus) | "
            f"Schulterdrücken: `{mem.get('ohp_kg', 0)} kg` (+2,5 kg) | "
            f"Kniebeugen: `{mem.get('squat_kg', 0)} kg` (+5,0 kg) | "
            f"Kreuzheben: `{mem.get('deadlift_kg', 0)} kg` (+5,0 kg) | "
            f"Klimmzüge: `+{mem.get('pullup_kg', 0)} kg` (+1,25 kg)"
        )

    sections.append(
        f"#### 🏋️‍♂️ {step_num}. Konkreter Trainings- & Ernährungs-Fahrplan (Arif 345){strength_info}\n"
        f"- **Trainingsstruktur ({days}x pro Woche im Gym – Push / Pull / Legs):**\n"
        f"  1. **10 Min. Mobility Warmup:** Gelenke mobilisieren, Schulter-Warmup mit Theraband.\n"
        f"  2. **Arif 345 Hauptübung (40–60 Min., 60–120 Sek. bis 3 Min. Pause für volle ATP/Kreatinphosphat-Resynthese):** Stufe 1 (**3x7**) -> Stufe 2 (**4x6**) -> Stufe 3 (**5x5**). Erst wenn alle 3 Stufen sauber mit `X` geschafft sind, Gewicht erhöhen.\n"
        f"  3. **Accessories (30–45 Min., 30–60 Sek. Pause):** 4–5 Sätze à 8–15 Wdh. ans Limit für maximalen Pump.\n"
        f"  4. **Arif 345 Core Finisher (10 Min. direkt nach den Gewichten, VOR dem Cardio):** 5 Sätze à 1 Min. Belastung / 1 Min. Pause.\n"
        f"- **Ernährungs-Struktur:**\n"
        f"  * Fokus auf die **Arif 345 Positivliste** (Rind, Huhn, Wildfang-Fisch, Eier, Leber, Skyr/Quark, Kefir/Ayran, Kartoffeln, Basmatireis, Beeren, Sauerkraut, Olivenöl, Weidebutter) in **3–4 festen Mahlzeiten ohne Snacken**."
    )

    # 4. PASSENDE ORIGINAL-AUSZÜGE AUS DER WISSENSDATENBANK
    if kb_matches:
        ref_lines = []
        for rub, sub, title, rules, prac in kb_matches:
            ref_lines.append(f"**[{rub} | {sub}] {title}**\n{rules}\n\n> 🎯 *{prac}*")
        sections.append("#### 📚 Direkt gefundene Details aus deiner Wissensdatenbank\n\n" + "\n\n---\n\n".join(ref_lines))

    # 5. PROAKTIVE RÜCKFRAGEN
    missing_questions = []
    if not mem["weight"]:
        missing_questions.append("Wie lauten **Alter, Größe, Gewicht und KFA** des Kunden (oder leg ihn kurz im Reiter *'👥 Kunden-Datenbank'* an), damit ich Kalorien, Makros und RED-S-Grenze exakt berechne?")
    if not mem["complaints"]:
        missing_questions.append("Gibt es spezifische **Beschwerden** (Schulter, Knie, LWS, Reflux, Blähbauch, Müdigkeit/Eisenmangel oder Waagen-Stillstand)?")

    if missing_questions:
        sections.append(
            "---\n💬 **Meine Rückfragen an dich für den nächsten Schritt:**\n" +
            "\n".join([f"{i+1}. {q}" for i, q in enumerate(missing_questions)])
        )
    else:
        c_label = mem.get("name") or "diesen Kunden"
        sections.append(
            f"---\n💬 **Nächster Schritt für {c_label}:** Soll ich dir konkrete **Beispiel-Mahlzeiten für den Tag** oder den angepassten **Push/Pull/Legs-Übungsplan** ausgeben?"
        )

    return "\n\n".join(sections)

# =========================================================
# 6. SEITENLEISTE: KUNDEN-AUSWAHL & NAVIGATION
# =========================================================
st.sidebar.title("🦁 Coach Arif OS")
st.sidebar.success("✅ 100 % Lokal & Sprach-Aktiv")

nav = st.sidebar.radio("Hauptmenü", [
    "1. 💬 KI-Co-Coach & Kunden-Chat",
    "2. 👥 Kunden-Datenbank (Anlegen & Bearbeiten)",
    "3. 📚 Wissensdatenbank & ZIP-Import"
])

st.sidebar.markdown("---")
st.sidebar.subheader("👤 Aktiver Gesprächskontext")

all_clients = get_all_clients()
client_options = {0: "🌐 Allgemeiner Coach-Chat (Alle Themen)"}
for row in all_clients:
    client_options[row[0]] = f"👤 {row[1]} ({row[5]} kg | {row[9]})"

if "selected_client_id" not in st.session_state:
    st.session_state.selected_client_id = 0

selected_cid = st.sidebar.selectbox(
    "Wähle den Kunden-Chat:",
    options=list(client_options.keys()),
    format_func=lambda x: client_options.get(x, "Chat"),
    index=list(client_options.keys()).index(st.session_state.selected_client_id) if st.session_state.selected_client_id in client_options else 0
)

if selected_cid != st.session_state.selected_client_id:
    st.session_state.selected_client_id = selected_cid
    st.session_state.case_memory = {
        "name": None, "gender": None, "age": None, "weight": None, "height": None,
        "kfa": None, "waist": None, "pal": 1.55, "goal": None, "phase": None,
        "days": None, "bench_kg": 0, "squat_kg": 0, "deadlift_kg": 0, "ohp_kg": 0, "pullup_kg": 0,
        "complaints": set()
    }
    if selected_cid > 0:
        load_client_into_memory(get_client_by_id(selected_cid), st.session_state.case_memory)
    st.rerun()

if st.session_state.selected_client_id > 0:
    load_client_into_memory(get_client_by_id(st.session_state.selected_client_id), st.session_state.case_memory)

mem = st.session_state.case_memory
n_str = mem.get("name") or "Allgemein / Automatisch"
w_str = f"{mem['weight']} kg" if mem.get("weight") else "–"
h_str = f"{mem['height']} cm" if mem.get("height") else "–"
a_str = f"{mem['age']} J." if mem.get("age") else "–"
k_str = f"{mem['kfa']}%" if mem.get("kfa") else "–"
c_str = ", ".join(mem["complaints"]) if mem.get("complaints") else "Keine spezifischen"

st.sidebar.caption("Aktive Kundendaten im KI-Gedächtnis:")
st.sidebar.write(f"• **Kunde:** {n_str}")
st.sidebar.write(f"• **Gewicht / Größe:** {w_str} / {h_str}")
st.sidebar.write(f"• **Alter / KFA:** {a_str} / {k_str}")
st.sidebar.write(f"• **Ziel:** {mem.get('goal') or 'Noch offen'}")
st.sidebar.write(f"• **Beschwerden:** {c_str}")

# =========================================================
# MODUL 1: KI-CO-COACH & SEPARATER KUNDEN-CHAT (MIT SPRACHE)
# =========================================================
if nav.startswith("1."):
    active_cid = st.session_state.selected_client_id
    active_client_obj = get_client_by_id(active_cid) if active_cid > 0 else None

    if active_client_obj:
        st.title(f"💬 Kunden-Chat & Coaching-Akte: {active_client_obj['name']}")
        st.info(
            f"**Gespeichertes Profil:** {active_client_obj['gender']}, {active_client_obj['age']} J., "
            f"{active_client_obj['height_cm']} cm, **{active_client_obj['weight_kg']} kg** (KFA: {active_client_obj['kfa_pct']}%, Taille: {active_client_obj['waist_cm']} cm) | "
            f"**Ziel:** {active_client_obj['goal']} ({active_client_obj['phase']}) | "
            f"**Beschwerden/Notizen:** {active_client_obj['complaints'] or 'Keine'}"
        )
    else:
        st.title("💬 Dein interaktiver Arif 345 KI-Co-Coach")
        st.write("Sprich oder schreibe mit deinem KI-Agenten. Wenn du den **Namen eines gespeicherten Kunden** nennst, erkennt der Agent ihn sofort!")

    # SPRACHSTEUERUNG (VORLESEN + LIVE-MIKROFON)
    col_v1, col_v2, col_v3 = st.columns([2, 1, 1])
    with col_v1:
        tts_toggle = st.toggle("🔊 KI-Coach spricht Antworten laut mit dir aus (Sprachausgabe)", value=True)
    with col_v2:
        stop_tts = st.button("⏹️ Stimme stoppen")
    with col_v3:
        if st.button("🗑️ Diesen Chat leeren"):
            clear_chat_messages(active_cid)
            st.rerun()

    if stop_tts:
        st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

    with st.expander("🎙️ Live-Spracheingabe (Browser-Mikrofon oder Mac-Diktat nutzen)", expanded=False):
        st.caption(
            "**Option A (Am schnellsten auf dem Mac):** Klicke unten direkt in das Chat-Eingabefeld und drücke **2x die `Fn`-Taste** (oder die Mikrofon-Taste `F5` auf deiner Mac-Tastatur) – dein Mac schreibt alles, was du sagst, live ins Chatfeld!\n\n"
            "**Option B (Browser-Sprachrekorder):** Klicke hier auf **'🎙️ Mikrofon starten'**, sprich deinen Satz ein und kopiere ihn mit 1 Klick:"
        )
        st.components.v1.html(
            """
            <div style="font-family: sans-serif; padding: 8px; background: #1e1e24; color: white; border-radius: 8px;">
                <button id="startBtn" style="background:#e63946; color:white; border:none; padding:8px 14px; border-radius:6px; cursor:pointer; font-weight:bold;">
                    🎙️ Mikrofon starten (Deutsch)
                </button>
                <button id="copyBtn" style="background:#457b9d; color:white; border:none; padding:8px 14px; border-radius:6px; cursor:pointer; margin-left:8px;">
                    📋 Text kopieren
                </button>
                <span id="statusTxt" style="margin-left:12px; font-size:13px; color:#a8dadc;">Bereit zum Sprechen...</span>
                <textarea id="speechOut" rows="2" style="width:100%; margin-top:8px; border-radius:6px; padding:6px; font-size:14px;" placeholder="Dein gesprochener Text erscheint live hier..."></textarea>
            </div>
            <script>
            const startBtn = document.getElementById('startBtn');
            const copyBtn = document.getElementById('copyBtn');
            const statusTxt = document.getElementById('statusTxt');
            const speechOut = document.getElementById('speechOut');
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognition) {
                const recognition = new SpeechRecognition();
                recognition.lang = 'de-DE';
                recognition.continuous = true;
                recognition.interimResults = true;
                let listening = false;
                startBtn.onclick = () => {
                    if (!listening) {
                        recognition.start();
                        listening = true;
                        startBtn.innerText = "⏹️ Aufnahme beenden";
                        startBtn.style.background = "#2a9d8f";
                        statusTxt.innerText = "🔴 Höre zu... Bitte jetzt sprechen!";
                    } else {
                        recognition.stop();
                        listening = false;
                        startBtn.innerText = "🎙️ Mikrofon starten (Deutsch)";
                        startBtn.style.background = "#e63946";
                        statusTxt.innerText = "Aufnahme gestoppt.";
                    }
                };
                recognition.onresult = (event) => {
                    let transcript = '';
                    for (let i = 0; i < event.results.length; i++) {
                        transcript += event.results[i][0].transcript;
                    }
                    speechOut.value = transcript;
                };
            } else {
                statusTxt.innerText = "Bitte nutze Chrome/Safari oder drücke 2x die Fn-Taste auf deinem Mac.";
            }
            copyBtn.onclick = () => {
                speechOut.select();
                document.execCommand('copy');
                statusTxt.innerText = "✅ Kopiert! Jetzt unten ins Chatfeld einfügen (Cmd+V).";
            };
            </script>
            """,
            height=135
        )

    # Schnell-Buttons
    q_col1, q_col2, q_col3 = st.columns(3)
    quick_prompt = None
    if q_col1.button("📋 Kompletten Plan & Makros ausgeben"):
        target_name = active_client_obj["name"] if active_client_obj else "meinen Kunden"
        quick_prompt = f"Erstelle mir bitte die komplette Biometrie-, Makro- und Trainingsübersicht nach dem Arif 345 System für {target_name}."
    if q_col2.button("🩺 Gelenkschutz & Beschwerden prüfen"):
        target_name = active_client_obj["name"] if active_client_obj else "meinen Kunden"
        quick_prompt = f"Worauf muss ich beim Trainings- und Ernährungsplan für {target_name} wegen seiner Beschwerden (Schulter, Knie, Reflux, Verdauung, Müdigkeit) besonders achten?"
    if q_col3.button("🧬 Peptid-Protokolle abfragen"):
        quick_prompt = "Gib mir bitte eine Übersicht über die wichtigsten Peptid-Protokolle (Heilung BPC-157/TB-500, Fettverlust Retatrutid/SLU-PP-332 und Rekonstitution) aus unserer Datenbank."

    messages = load_chat_messages(active_cid)
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Schreibe oder diktiere (2x Fn-Taste auf dem Mac) deine Frage oder nenne einen Kundennamen...")
    active_input = quick_prompt if quick_prompt else user_input

    if active_input:
        save_chat_message(active_cid, "user", active_input)
        with st.chat_message("user"):
            st.markdown(active_input)
        with st.chat_message("assistant"):
            reply = generate_local_arif_coaching_response(active_input, active_client_id=active_cid)
            st.markdown(reply)
        save_chat_message(active_cid, "assistant", reply)
        st.session_state.speak_latest = True
        st.rerun()

    # Automatische Sprachausgabe der neuesten KI-Antwort
    if tts_toggle and st.session_state.get("speak_latest", False) and len(messages) > 1 and messages[-1]["role"] == "assistant":
        st.session_state.speak_latest = False
        raw_speech = messages[-1]["content"]
        clean_speech = re.sub(r"[#*`>_~-]", " ", raw_speech)
        clean_speech = clean_speech.replace('"', "'").replace("\n", " ")
        clean_speech = re.sub(r"\s+", " ", clean_speech)[:1450]
        st.components.v1.html(
            f"""
            <script>
            window.speechSynthesis.cancel();
            var utter = new SpeechSynthesisUtterance("{clean_speech}");
            utter.lang = 'de-DE';
            utter.rate = 1.05;
            window.speechSynthesis.speak(utter);
            </script>
            """,
            height=0
        )

# =========================================================
# MODUL 2: KUNDEN-DATENBANK (ANLEGEN, BEARBEITEN & DIREKT-CHAT)
# =========================================================
elif nav.startswith("2."):
    st.title("👥 Kunden-Datenbank & Arif 345 Kunden-Akten")
    st.write("Lege hier deine Klienten an. Jeder Klient bekommt sofort einen **eigenen, dauerhaft gespeicherten Chat** und wird vom KI-Coach automatisch am Namen erkannt.")

    with st.expander("➕ Neuen Kunden anlegen oder bestehenden Kunden aktualisieren", expanded=True):
        with st.form("client_form"):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                f_name = st.text_input("Name des Kunden (z.B. Mehmet Yilmaz)*")
                f_gender = st.selectbox("Geschlecht", ["Männlich", "Weiblich"])
                f_age = st.number_input("Alter", 14, 90, 32)
                f_height = st.number_input("Größe (cm)", 140.0, 220.0, 178.0, step=1.0)
            with c2:
                f_weight = st.number_input("Aktuelles Gewicht (kg)", 40.0, 250.0, 92.0, step=0.5)
                f_kfa = st.number_input("Geschätzter KFA (%)", 4.0, 60.0, 23.0, step=0.5)
                f_waist = st.number_input("Taillenumfang (cm)", 45.0, 180.0, 94.0, step=0.5)
                f_pal = st.number_input("PAL-Aktivitätsfaktor", 1.2, 2.4, 1.55, step=0.05)
            with c3:
                f_goal = st.selectbox("Hauptziel", ["Fettabbau / Diät", "Muskel- & Kraftaufbau", "Recomposition / Definition"])
                f_phase = st.selectbox("Coaching-Phase", ["Phase 1: Detox & Reset (Monat 1)", "Phase 2: Flexible Kontrolle"])
                f_days = st.number_input("Trainingstage / Woche im Gym", 1, 6, 3)
                f_complaints = st.text_input("Beschwerden (Schulter, Knie, Reflux, Eisen, Darm...)", placeholder="z.B. Schulter-Impingement, Sodbrennen")
            with c4:
                st.caption("🏋️‍♂️ Arif 345 Arbeitsgewichte (optional):")
                f_bench = st.number_input("Bankdrücken (kg)", 0.0, 300.0, 60.0, step=2.5)
                f_ohp = st.number_input("Schulterdrücken (kg)", 0.0, 200.0, 40.0, step=2.5)
                f_squat = st.number_input("Kniebeugen (kg)", 0.0, 350.0, 80.0, step=5.0)
                f_dead = st.number_input("Kreuzheben (kg)", 0.0, 400.0, 100.0, step=5.0)

            f_notes = st.text_area("Zusätzliche Notizen (Alltag, Schichtdienst, türkische Küche, Schlaf, Vorlieben):", height=70)

            if st.form_submit_button("💾 Kundenprofil speichern / aktualisieren"):
                if f_name.strip():
                    existing_c = cur_c.execute("SELECT id FROM clients WHERE lower(name)=?", (f_name.strip().lower(),)).fetchone()
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    if existing_c:
                        cur_c.execute("""
                            UPDATE clients SET gender=?, age=?, height_cm=?, weight_kg=?, kfa_pct=?, waist_cm=?, pal=?,
                            goal=?, phase=?, complaints=?, training_days=?, bench_kg=?, squat_kg=?, deadlift_kg=?, ohp_kg=?, notes=?, updated_at=?
                            WHERE id=?
                        """, (f_gender, f_age, f_height, f_weight, f_kfa, f_waist, f_pal, f_goal, f_phase, f_complaints, f_days, f_bench, f_squat, f_dead, f_ohp, f_notes, now_str, existing_c[0]))
                        conn_c.commit()
                        st.success(f"Kundenprofil von '{f_name}' wurde aktualisiert!")
                    else:
                        cur_c.execute("""
                            INSERT INTO clients (name, gender, age, height_cm, weight_kg, kfa_pct, waist_cm, pal, goal, phase, complaints, training_days, bench_kg, squat_kg, deadlift_kg, ohp_kg, notes, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (f_name.strip(), f_gender, f_age, f_height, f_weight, f_kfa, f_waist, f_pal, f_goal, f_phase, f_complaints, f_days, f_bench, f_squat, f_dead, f_ohp, f_notes, now_str))
                        conn_c.commit()
                        st.success(f"Kunde '{f_name}' wurde neu angelegt!")
                    st.rerun()
                else:
                    st.warning("Bitte gib mindestens den Namen des Kunden ein.")

    st.markdown("---")
    st.subheader(f"📋 Gespeicherte Kunden ({len(all_clients)})")
    if all_clients:
        for row in all_clients:
            cid, cname, cgen, cage, ch, cw, ckfa, cwaist, cpal, cgoal, cphase, ccomp, cdays, cbench, csquat, cdead, cohp, cpull, cnotes = row
            with st.expander(f"👤 {cname} — {cw} kg | {cgoal} | {cphase} | Beschwerden: {ccomp or 'Keine'}"):
                col_a, col_b, col_c = st.columns([2, 2, 1])
                with col_a:
                    st.write(f"**Daten:** {cgen}, {cage} J., {ch} cm, {cw} kg, KFA: {ckfa}%, Taille: {cwaist} cm, PAL: {cpal}")
                    st.write(f"**Beschwerden:** {ccomp or 'Keine'} | **Notizen:** {cnotes or '–'}")
                with col_b:
                    st.write(f"**Arif 345 Gewichte ({cdays}x/Woche):**")
                    st.write(f"Bank: `{cbench} kg` | OHP: `{cohp} kg` | Beuge: `{csquat} kg` | Heben: `{cdead} kg`")
                with col_c:
                    if st.button(f"💬 Zum Chat von {cname}", key=f"chat_btn_{cid}"):
                        st.session_state.selected_client_id = cid
                        st.rerun()
                    if st.button("🗑️ Kunde löschen", key=f"del_c_{cid}"):
                        cur_c.execute("DELETE FROM clients WHERE id=?", (cid,))
                        cur_c.execute("DELETE FROM client_chats WHERE client_id=?", (cid,))
                        conn_c.commit()
                        if st.session_state.selected_client_id == cid:
                            st.session_state.selected_client_id = 0
                        st.rerun()
    else:
        st.info("Noch keine Kunden gespeichert. Lege oben über das Formular deinen ersten Kunden an.")

# =========================================================
# MODUL 3: WISSENSDATENBANK & AUTOMATISCHER ZIP-ENTPACKER
# =========================================================
elif nav.startswith("3."):
    st.title("📚 Deine Master-Wissensdatenbank & ZIP-Importer")

    with st.expander("📦 ZIP-Datei oder Dokumente direkt entpacken & automatisch einordnen"):
        st.write(
            "Lade hier eine **`.zip`-Datei** (oder `.txt`, `.md`, `.csv`, `.rtf`) hoch. "
            "Die App entpackt alle darin enthaltenen Textdokumente automatisch und ordnet sie nach Inhalt in **Training**, **Ernährung**, **Gesundheit** oder **Peptide** ein!"
        )
        uploaded_files = st.file_uploader(
            "ZIP-Archiv oder Textdateien auswählen:",
            type=["zip", "txt", "md", "csv", "rtf"],
            accept_multiple_files=True
        )
        if uploaded_files and st.button("🚀 Dateien jetzt entpacken & in Wissensdatenbank einspeisen"):
            imported_count = 0

            def classify_and_insert(filename, raw_text):
                clean_t = raw_text.strip()
                if len(clean_t) < 20:
                    return 0
                low_t = clean_t.lower()
                if any(w in low_t for w in ["peptid", "bpc-157", "tb-500", "retatrutid", "tirzepatid", "semaglutid", "ipamorelin", "mk-677", "bac water", "rekonstitution"]):
                    rub = "Peptide"
                elif any(w in low_t for w in ["training", "satz", "sätze", "wiederholung", "übung", "bankdrücken", "kniebeuge", "cardio", "muskelaufbau"]):
                    rub = "Training"
                elif any(w in low_t for w in ["darm", "magen", "blut", "hormon", "leber", "krankheit", "schlaf", "albumin", "transferrin", "reflux"]):
                    rub = "Gesundheit"
                else:
                    rub = "Ernährung"

                title_str = f"Import: {filename}"
                first_sentences = re.split(r"(?<=[.!?])\s+", clean_t)
                fazit_str = "Fazit: " + " ".join(first_sentences[:2])[:300]
                cur_k.execute(
                    "INSERT INTO knowledge_base (rubric, sub_category, title, core_rules, practical_application) VALUES (?, ?, ?, ?, ?)",
                    (rub, "ZIP / Datei-Import", title_str, clean_t[:15000], fazit_str)
                )
                return 1

            for uf in uploaded_files:
                if uf.name.lower().endswith(".zip"):
                    try:
                        with zipfile.ZipFile(io.BytesIO(uf.read())) as z:
                            for zname in z.namelist():
                                if zname.endswith("/") or "__MACOSX" in zname:
                                    continue
                                if any(zname.lower().endswith(ext) for ext in [".txt", ".md", ".csv", ".rtf", ".json"]):
                                    data_bytes = z.read(zname)
                                    text_content = data_bytes.decode("utf-8", errors="ignore")
                                    imported_count += classify_and_insert(zname, text_content)
                    except Exception as e:
                        st.error(f"Fehler beim Entpacken von {uf.name}: {e}")
                else:
                    text_content = uf.read().decode("utf-8", errors="ignore")
                    imported_count += classify_and_insert(uf.name, text_content)

            conn_k.commit()
            st.success(f"✅ {imported_count} Dokumente wurden erfolgreich entpackt, kategorisiert und in deiner Wissensdatenbank gespeichert!")
            st.rerun()

    col_s1, col_s2 = st.columns([4, 1])
    with col_s1:
        search_q = st.text_input(
            "🔍 Volltext-Suche in allen 4 Rubriken (Training, Ernährung, Gesundheit & Peptide):",
            placeholder="z.B. BPC-157, Retatrutid, BAC Water, Transferrin, Fließbandgesetz, Reflux, 345, RED-S..."
        )
    with col_s2:
        df_export = pd.read_sql_query("SELECT rubric AS Rubrik, sub_category AS Kategorie, title AS Titel, core_rules AS Volltext, practical_application AS Fazit FROM knowledge_base", conn_k)
        st.download_button(
            "📥 Backup (CSV)",
            data=df_export.to_csv(index=False).encode("utf-8"),
            file_name="arif_345_wissensdatenbank.csv",
            mime="text/csv"
        )

    if search_q:
        t = f"%{search_q}%"
        found = cur_k.execute(
            "SELECT rubric, sub_category, title, core_rules, practical_application FROM knowledge_base WHERE title LIKE ? OR core_rules LIKE ? OR practical_application LIKE ? OR sub_category LIKE ?",
            (t, t, t, t)
        ).fetchall()
        st.success(f"{len(found)} passende Wissens-Module für '{search_q}' gefunden:")
        for rub, sub, title, rules, prac in found:
            with st.expander(f"[{rub} | {sub}] {title}", expanded=True):
                st.markdown(f"**📖 Detaillierter Inhalt & Regeln:**\n\n{rules}")
                st.info(f"**🎯 {prac}**")
        st.markdown("---")

    tab_trn, tab_ern, tab_ges, tab_pep = st.tabs([
        "🏋️‍♂️ 1. Training (Arif 345)",
        "🥗 2. Ernährung",
        "🩺 3. Gesundheit & Stoffwechsel",
        "🧬 4. Peptide"
    ])

    def render_rubric(r_name):
        with st.expander(f"➕ Eigenes Wissen manuell zu '{r_name}' hinzufügen"):
            with st.form(f"form_{r_name}"):
                sub = st.text_input("Unterkategorie (z.B. Übungsausführung, Rezepte, Blutbild, Peptid-Protokoll)")
                title = st.text_input("Titel des Eintrags")
                rules = st.text_area("Vollständiger Text / Regeln / Zahlenwerte", height=180)
                prac = st.text_area("Fazit für die Praxis (2–3 Sätze)", height=80)
                if st.form_submit_button("💾 In Wissensdatenbank speichern") and title and rules:
                    cur_k.execute(
                        "INSERT INTO knowledge_base (rubric, sub_category, title, core_rules, practical_application) VALUES (?, ?, ?, ?, ?)",
                        (r_name, sub if sub else "Allgemein", title, rules, prac if prac else "Fazit: Direkt im Coaching anwenden.")
                    )
                    conn_k.commit()
                    st.success(f"'{title}' wurde in '{r_name}' gespeichert!")
                    st.rerun()

        rows = cur_k.execute("SELECT id, sub_category, title, core_rules, practical_application FROM knowledge_base WHERE rubric=? ORDER BY id ASC", (r_name,)).fetchall()
        st.caption(f"Aktuell **{len(rows)} umfassende Module** in der Rubrik **{r_name}** gespeichert:")
        for eid, sub, title, rules, prac in rows:
            with st.expander(f"[{sub}] {title}"):
                st.markdown(f"**📖 Detaillierter Inhalt & Regeln:**\n\n{rules}")
                st.info(f"**🎯 {prac}**")
                if st.button("🗑️ Eintrag löschen", key=f"del_{eid}"):
                    cur_k.execute("DELETE FROM knowledge_base WHERE id=?", (eid,))
                    conn_k.commit()
                    st.rerun()

    with tab_trn:
        render_rubric("Training")
    with tab_ern:
        render_rubric("Ernährung")
    with tab_ges:
        render_rubric("Gesundheit")
    with tab_pep:
        render_rubric("Peptide")