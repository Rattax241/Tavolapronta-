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
    
    limit = 60
    ax.plot([-limit, limit], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-limit, limit], color='black', linewidth=1)
    ax.text(-limit+2, 2, "P.V.", fontsize=12, fontweight='bold', color='gray')
    ax.text(-limit+2, -5, "P.O.", fontsize=12, fontweight='bold', color='gray')
    ax.text(2, limit-5, "P.L.", fontsize=12, fontweight='bold', color='gray')
    
    # Estrazione sicura
    tipo = str(dati.get('tipo', 'solido')).lower()
    L = float(dati.get('lunghezza') or 6)
    P = float(dati.get('profondita') or 4)
    H = float(dati.get('altezza') or 10)
    dPV = float(dati.get('dist_pv') or 5)
    dPL = float(dati.get('dist_pl') or 7)
    rot = float(dati.get('rotazione') or 0)
    lati = int(dati.get('lati') or 4)
    aux = bool(dati.get('piano_ausiliario', False))

    # 1. PIANO ORIZZONTALE (P.O.)
    x_c, y_c = -dPL - L/2, -dPV - P/2
    angle = np.radians(rot)
    offset = np.pi/4 if lati == 4 and rot == 0 else 0
    t = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset
    vx = x_c + (L/2) * np.cos(t)
    vy = y_c + (P/2) * np.sin(t)
    ax.plot(np.append(vx, vx[0]), np.append(vy, vy[0]), color='black', linewidth=2.5)

    if premium:
        x_min, x_max = np.min(vx), np.max(vx)
        y_min, y_max = np.min(vy), np.max(vy)
        
        # 2. PIANO VERTICALE (P.V.)
        ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color='black', linewidth=2.5)
        
        # 3. PIANO LATERALE (P.L.)
        t_arco_pl = np.linspace(1.5*np.pi, 2*np.pi, 50)
        for ry in [y_min, y_max]:
            r = abs(ry)
            ax.plot(r*np.cos(t_arco_pl), r*np.sin(t_arco_pl), color='orange', linestyle='--', linewidth=1)
            ax.plot([r, r], [0, H], color='black', linewidth=1.5)
        ax.plot([abs(y_min), abs(y_max)], [H, H], color='black', linewidth=1.5)

        # 4. PIANO AUSILIARIO (P.A.) - Stile Ribaltamento a Sinistra
        if aux:
            ang_pa = np.radians(135) # Linea inclinata nel quadrante PV/PO a sinistra
            ax.plot([0, limit*np.cos(ang_pa)], [0, limit*np.sin(ang_pa)], color='blue', linewidth=2, linestyle='-.')
            ax.text(limit*np.cos(ang_pa)+2, limit*np.sin(ang_pa)-2, "P.A.", color='blue', fontweight='bold')
            
            # Archi di ribaltamento per portare la X del PO sul piano inclinato
            t_arco_aux = np.linspace(0.5*np.pi, ang_pa, 50)
            for val_x in [abs(x_min), abs(x_max)]:
                ax.plot(-val_x*np.cos(t_arco_aux - np.pi/2), val_x*np.sin(t_arco_aux - np.pi/2), color='blue', linestyle='--', linewidth=0.8)
                
            # Disegno vera forma semplificata perpendicolare
            ax.plot([x_min-5, x_min-15], [H+5, H+15], color='blue', linewidth=1.5)

    return fig

# --- UI APP ---
if 'premium' not in st.session_state: st.session_state.premium = False
with st.sidebar:
    st.title("💎 Area Master")
    if not st.session_state.premium:
        code = st.text_input("Codice licenza:", type="password")
        if st.button("Attiva Master"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
    else:
        st.success("✅ MODALITÀ MASTER ATTIVA")
        if st.button("Logout"):
            st.session_state.premium = False
            st.rerun()

st.title("📐 TavolaPronta AI Master")
traccia = st.text_area("Cosa vuoi disegnare?")

if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt = """Rispondi SOLO JSON. No testo. 
            Se chiede 'piano ausiliario', 'vera forma' o 'ribaltamento', piano_ausiliario: true.
            JSON: {"tipo": "cubo", "lunghezza": 6, "profondita": 4, "altezza": 10, "dist_pv": 5, "dist_pl": 7, "rotazione": 0, "lati": 4, "piano_ausiliario": false}"""
            
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": traccia}, {"role": "system", "content": prompt}],
                response_format={"type": "json_object"}
            )
            dati = json.loads(res.choices[0].message.content)
            
            # Sanificazione per evitare TypeError
            if isinstance(dati, list): dati = dati[0]
            
            st.pyplot(genera_proiezione_ortogonale(dati, premium=st.session_state.premium))
        except Exception as e:
            st.error("Riprova semplificando la traccia.")
