import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(page_title="TavolaPronta AI", layout="wide", page_icon="📐")

# --- COSTANTI ---
LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

# --- MOTORE GRAFICO ---
def genera_proiezione_ortogonale(dati, premium=False):
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Parametri dal JSON con paracadute per evitare errori NoneType
    tipo = str(dati.get('tipo', 'solido')).lower()
    L = float(dati.get('lunghezza', 6) or 6)
    P = float(dati.get('profondita', L) or L)
    H = float(dati.get('altezza', 10) or 10)
    dPV = float(dati.get('dist_pv', 2) or 2)
    dPL = float(dati.get('dist_pl', 3) or 3)
    rot = float(dati.get('rotazione', 0) or 0)
    lati = int(dati.get('lati', 4) or 4)
    aux = dati.get('piano_ausiliario', False)

    # Assi e scritte
    limit = 40
    ax.plot([-limit, limit], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-limit, limit], color='black', linewidth=1)
    ax.text(-limit+2, 1, "P.V.", fontsize=12, fontweight='bold')
    ax.text(-limit+2, -3, "P.O.", fontsize=12, fontweight='bold')
    ax.text(1, limit-2, "P.L.", fontsize=12, fontweight='bold')

    # 1. DISEGNO PIANO ORIZZONTALE (P.O.)
    x_c, y_c = -dPL - L/2, -dPV - P/2
    angle = np.radians(rot)
    offset = np.pi/4 if lati == 4 and rot == 0 else 0
    theta = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset
    vx, vy = x_c + (L/2) * np.cos(theta), y_c + (P/2) * np.sin(theta)
    punti_po = np.column_stack([vx, vy])
    punti_chiusi = np.vstack([punti_po, punti_po[0]])
    ax.plot(punti_chiusi[:, 0], punti_chiusi[:, 1], color='black', linewidth=2)
    
    if 'piramide' in tipo or 'cono' in tipo:
        for p in punti_po: ax.plot([x_c, p[0]], [y_c, p[1]], color='black', linewidth=0.8)

    # 2. LOGICA PREMIUM (P.V. e P.L.)
    if premium:
        x_min, x_max = np.min(vx), np.max(vx)
        y_min, y_max = np.min(vy), np.max(vy)
        # P.V.
        if 'piramide' in tipo or 'cono' in tipo:
            ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color='black', linewidth=2)
        else:
            ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color='black', linewidth=2)
        
        # P.L. con Archi
        t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
        for ry in [y_min, y_max, y_c]:
            r = abs(ry)
            ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='orange', linestyle='--', linewidth=0.6)
            
        # 3. PIANO AUSILIARIO (Solo se richiesto dalla traccia)
        if aux:
            ang_aux = np.radians(-30)
            y_base_aux = -20
            ax.plot([-limit, 0], [y_base_aux + -limit*np.tan(ang_aux), y_base_aux], color='blue', linewidth=1.5, linestyle='-.')
            ax.text(-limit+5, y_base_aux + -limit*np.tan(ang_aux) + 2, "L.T. Ausiliaria", color='blue', fontsize=10)
            for i in range(len(vx)):
                ax.plot([vx[i], vx[i]-15], [vy[i], vy[i]+25], color='blue', linestyle=':', linewidth=0.5, alpha=0.5)

    else:
        ax.text(15, 15, "VERSIONE PRO RICHIESTA", color='red', alpha=0.3, fontsize=15, ha='center', va='center', rotation=45)

    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    return fig

# --- LOGICA APP ---
if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.title("💎 Area Master")
    if not st.session_state.premium:
        st.link_button("Abbonamento Mensile (4,99€)", LINK_MENSILE)
        st.link_button("Accesso Illimitato (19,99€)", LINK_LIFETIME)
        codice = st.text_input("Inserisci codice attivazione:", type="password")
        if st.button("Attiva Funzioni Master"):
            if codice == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
    else:
        st.success("✅ MODALITÀ MASTER ATTIVA")

st.title("📐 TavolaPronta AI")
traccia = st.text_area("Incolla qui la traccia dell'esercizio:", placeholder="Esempio: Una piramide esagonale raggio 5 cm...")

if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        with st.spinner("L'IA sta analizzando la geometria..."):
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt_sistema = """Sei un ingegnere. Estrai dati e restituisci JSON. 
            Regole: Esagono=6 lati, Quadrato=4. Se rotazione non detta, rotazione=0. 
            Se chiede 'piano ausiliario' o 'vera forma', imposta 'piano_ausiliario': true.
            JSON: {tipo, lunghezza, profondita, altezza, dist_pv, dist_pl, rotazione, lati, piano_ausiliario}"""
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": traccia}],
                response_format={"type": "json_object"}
            )
            dati = json.loads(res.choices[0].message.content)
            st.pyplot(genera_proiezione_ortogonale(dati, premium=st.session_state.premium))
