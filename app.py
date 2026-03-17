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
    ax.plot([-limit, limit], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-limit, limit], color='black', linewidth=1)
    ax.text(-limit+2, 2, "P.V.", fontsize=12, fontweight='bold', color='gray')
    ax.text(-limit+2, -4, "P.O.", fontsize=12, fontweight='bold', color='gray')
    ax.text(2, limit-4, "P.L.", fontsize=12, fontweight='bold', color='gray')
    
    # Estrazione sicura dei dati (Anti-Crash)
    tipo = str(dati.get('tipo', 'solido')).lower()
    L = float(dati.get('lunghezza') or 6)
    P = float(dati.get('profondita') or 4)
    H = float(dati.get('altezza') or 10)
    dPV = float(dati.get('dist_pv') or 5)
    dPL = float(dati.get('dist_pl') or 7)
    rot = float(dati.get('rotazione') or 0)
    lati = int(dati.get('lati') or 4)
    aux = dati.get('piano_ausiliario', False)

    # 1. PIANO ORIZZONTALE (Sempre)
    x_c, y_c = -dPL - L/2, -dPV - P/2
    angle = np.radians(rot)
    offset = np.pi/4 if lati == 4 and rot == 0 else 0
    theta = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset
    vx, vy = x_c + (L/2) * np.cos(theta), y_c + (P/2) * np.sin(theta)
    ax.plot(np.append(vx, vx[0]), np.append(vy, vy[0]), color='black', linewidth=2.5)

    if premium:
        x_min, x_max = np.min(vx), np.max(vx)
        y_min, y_max = np.min(vy), np.max(vy)
        
        # 2. PIANO VERTICALE
        ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color='black', linewidth=2)
        
        # 3. PIANO LATERALE (Archi classici a destra)
        t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
        for ry in [y_min, y_max]:
            r = abs(ry)
            ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='orange', linestyle='--', linewidth=0.8)
            ax.plot([r, r], [0, H], color='gray', linestyle=':', linewidth=0.7)

        # 4. PIANO AUSILIARIO (Solo se necessario)
        if aux:
            # Linea di terra inclinata nel quadrante SX (stile immagine caricata)
            ang_pa = np.radians(135) 
            ax.plot([0, limit*np.cos(ang_pa)], [0, limit*np.sin(ang_pa)], color='blue', linewidth=1.5, linestyle='-.')
            
            # Archi di ribaltamento verso SX
            t_arco_aux = np.linspace(0.5*np.pi, ang_pa, 50)
            for r in [abs(x_min), abs(x_max)]:
                ax.plot(-r*np.cos(t_arco_aux - np.pi/2), r*np.sin(t_arco_aux - np.pi/2), color='blue', linestyle='--', linewidth=0.6)

    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    return fig

# --- LOGICA APP ---
if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.title("💎 Area Master")
    if not st.session_state.premium:
        st.link_button("Sblocca P.V. e P.L. (4,99€)", LINK_MENSILE)
        st.link_button("Sblocca Tutto per sempre (19,99€)", LINK_LIFETIME)
        code = st.text_input("Codice licenza:", type="password")
        if st.button("Attiva Master"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
    else: st.success("✅ MODALITÀ MASTER ATTIVA")

st.title("📐 TavolaPronta AI Master")
traccia = st.text_area("Cosa vuoi disegnare?")

if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt = "Rispondi SOLO JSON. Se chiede 'piano ausiliario' o 'vera forma', piano_ausiliario: true. JSON: {tipo, lunghezza, profondita, altezza, dist_pv, dist_pl, rotazione, lati, piano_ausiliario}"
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": traccia}], response_format={"type": "json_object"})
            dati = json.loads(res.choices[0].message.content)
            st.pyplot(genera_proiezione_ortogonale(dati, premium=st.session_state.premium))
        except: st.error("Errore nell'elaborazione della traccia.")
