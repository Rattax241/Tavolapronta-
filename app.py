import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq

st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

def genera_proiezione_ortogonale(dati, premium=False):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect('equal')
    ax.axis('off')
    
    limit = 50
    # Assi Cartesiani Principali
    ax.plot([-limit, limit], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-limit, limit], color='black', linewidth=1)
    
    tipo = str(dati.get('tipo', 'solido')).lower()
    L = float(dati.get('lunghezza', 6) or 6)
    P = float(dati.get('profondita', 5) or 5)
    H = float(dati.get('altezza', 10) or 10)
    dPV = float(dati.get('dist_pv', 2) or 2)
    dPL = float(dati.get('dist_pl', 3) or 3)
    rot = float(dati.get('rotazione', 0) or 0)
    lati = int(dati.get('lati', 4) or 4)
    aux = dati.get('piano_ausiliario', False)

    # 1. PIANO ORIZZONTALE (P.O.)
    x_c, y_c = -dPL - L/2, -dPV - P/2
    angle = np.radians(rot)
    offset = np.pi/4 if lati == 4 and rot == 0 else 0
    theta = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset
    vx, vy = x_c + (L/2) * np.cos(theta), y_c + (P/2) * np.sin(theta)
    ax.plot(np.append(vx, vx[0]), np.append(vy, vy[0]), color='black', linewidth=2)

    if premium:
        # 2. P.V. e P.L. (Standard)
        x_min, x_max = np.min(vx), np.max(vx)
        y_min, y_max = np.min(vy), np.max(vy)
        ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color='black', linewidth=1.5) # PV semplificato

        # 3. PIANO AUSILIARIO (Stile Immagine: Ribaltamento a Sinistra)
        if aux:
            # Asse Inclinato (P.A.alfa)
            ang_pa = np.radians(60) 
            ax.plot([0, -limit*np.cos(ang_pa)], [0, -limit*np.sin(ang_pa)], color='black', linewidth=1.2)
            ax.text(-limit*np.cos(ang_pa), -limit*np.sin(ang_pa), "P.A. α", fontsize=10, fontweight='bold')

            # Archi di ribaltamento verso il piano ausiliario (Quadrante in alto a SX)
            t_arco_sx = np.linspace(0.5*np.pi, np.pi - ang_pa, 50)
            for dist_x in [abs(x_min), abs(x_max)]:
                r = dist_x
                # Disegno l'arco che porta la proiezione dal PV all'asse inclinato
                ax.plot(-r*np.cos(t_arco_sx - np.pi/2), r*np.sin(t_arco_sx - np.pi/2), color='gray', linestyle='--', linewidth=0.7, alpha=0.6)
            
            # Linee di proiezione perpendicolari all'asse inclinato (Vera Forma)
            for i in range(len(vx)):
                # Calcolo proiezione dal PO perpendicolare all'asse inclinato
                ax.plot([vx[i], vx[i]-10], [vy[i], vy[i]-15], color='blue', linestyle=':', linewidth=0.5, alpha=0.4)

    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    return fig

# --- RESTO DEL CODICE INVARIATO ---
if 'premium' not in st.session_state: st.session_state.premium = False
with st.sidebar:
    st.title("💎 Area Master")
    if not st.session_state.premium:
        st.link_button("Sblocca Tutto", LINK_LIFETIME)
        code = st.text_input("Codice:", type="password")
        if st.button("Attiva"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
    else: st.success("✅ MODALITÀ MASTER")

st.title("📐 TavolaPronta AI Master")
traccia = st.text_area("Cosa vuoi disegnare?")
if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        prompt = "Estrai JSON. Se chiede 'piano ausiliario' o 'vera forma', piano_ausiliario: true. JSON: {tipo, lunghezza, profondita, altezza, dist_pv, dist_pl, rotazione, lati, piano_ausiliario}"
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": traccia}], response_format={"type": "json_object"})
        st.pyplot(genera_proiezione_ortogonale(json.loads(res.choices[0].message.content), premium=st.session_state.premium))
