import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq

st.set_page_config(page_title="TavolaPronta AI Master", layout="wide")

# --- MOTORE DI DISEGNO PROFESSIONALE ---
def genera_tavola_master(dati, premium=True):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect('equal')
    ax.axis('off') # Nasconde i bordi del grafico per sembrare un foglio bianco

    # Disegno Squadratura e Assi (come un foglio reale)
    ax.plot([-25, 25], [0, 0], color='black', linewidth=1.5) # Linea di terra
    ax.plot([0, 0], [-25, 25], color='black', linewidth=1)   # Asse verticale
    
    # Recupero Dati
    L, P, H = dati.get('lunghezza', 6), dati.get('profondita', 5), dati.get('altezza', 10)
    dPV, dPL = dati.get('dist_pv', 2), dati.get('dist_pl', 3)
    rot = dati.get('rotazione', 0) # Inclinazione opzionale

    # --- PIANO ORIZZONTALE (P.O.) ---
    x_c, y_c = -dPL - L/2, -dPV - P/2
    # Calcolo vertici ruotati
    def get_rot_rect(xc, yc, l, p, r):
        angle = np.radians(r)
        c, s = np.cos(angle), np.sin(angle)
        pts = np.array([[-l/2, -p/2], [l/2, -p/2], [l/2, p/2], [-l/2, p/2], [-l/2, -p/2]])
        return pts @ np.array([[c, -s], [s, c]]) + [xc, yc]

    poly_po = get_rot_rect(x_c, y_c, L, P, rot)
    ax.plot(poly_po[:, 0], poly_po[:, 1], color='black', linewidth=2)
    ax.text(x_c, y_c - P, "P.O.", fontsize=12, fontweight='bold')

    if premium:
        # --- PIANO VERTICALE (P.V.) ---
        x_start, x_end = np.min(poly_po[:, 0]), np.max(poly_po[:, 0])
        ax.plot([x_start, x_end, x_end, x_start, x_start], [0, 0, H, H, 0], color='blue', linewidth=2)
        
        # Linee di richiamo (proiezioni)
        for vx in [x_start, x_end]:
            ax.plot([vx, vx], [np.min(poly_po[:, 1]), H], color='gray', linestyle=':', linewidth=0.8)

        # --- PIANO LATERALE (P.L.) ---
        y_low, y_high = np.min(poly_po[:, 1]), np.max(poly_po[:, 1])
        # Archi di ribaltamento
        t = np.linspace(1.5*np.pi, 2*np.pi, 50)
        for r in [abs(y_low), abs(y_high)]:
            ax.plot(r*np.cos(t), r*np.sin(t), color='orange', linestyle='--', linewidth=0.8)
            ax.plot([r, r], [0, H], color='gray', linestyle=':', linewidth=0.8) # Proiezione in alto
        
        ax.plot([abs(y_high), abs(y_low), abs(y_low), abs(y_high), abs(y_high)], [0, 0, H, H, 0], color='green', linewidth=2)
        
        # Titoli Piani
        ax.text(-20, 2, "P.V.", fontsize=12)
        ax.text(15, 2, "P.L.", fontsize=12)

    return fig

# --- INTERFACCIA STREAMLIT ---
st.title("📐 TavolaPronta AI Master")
st.write("Generazione tavole tecniche con standard da ufficio progetti")

traccia = st.text_area("Copia qui la traccia del libro (es: Parallelepipedo 6x4x8 a 2cm da PV e 3cm da PL)")

if st.button("🚀 GENERA TAVOLA PROFESSIONALE"):
    if traccia:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Estrai JSON: lunghezza, profondita, altezza, dist_pv, dist_pl, rotazione."}],
            response_format={"type": "json_object"}
        )
        dati = json.loads(res.choices[0].message.content)
        fig = genera_tavola_master(dati, premium=st.session_state.get('premium', True))
        st.pyplot(fig)
