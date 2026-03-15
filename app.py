import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq

st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

def genera_proiezione_ortogonale(lista_dati, premium=False):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect('equal')
    ax.axis('off')
    
    limit = 60
    ax.plot([-limit, limit], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-limit, limit], color='black', linewidth=1)
    ax.text(-limit+2, 2, "P.V.", fontsize=12, fontweight='bold', color='gray')
    ax.text(-limit+2, -4, "P.O.", fontsize=12, fontweight='bold', color='gray')
    ax.text(2, limit-4, "P.L.", fontsize=12, fontweight='bold', color='gray')
    
    for dati in lista_dati:
        tipo = dati.get('tipo', 'solido').lower()
        L, P, H = dati.get('lunghezza', 6), dati.get('profondita', 6), dati.get('altezza', 10)
        dPV, dPL = dati.get('dist_pv', 5), dati.get('dist_pl', 5)
        lati, rot = dati.get('lati', 4), dati.get('rotazione', 0)
        aux = dati.get('piano_ausiliario', False)
        
        angle = np.radians(rot)
        x_c, y_c = -dPL - L/2, -dPV - P/2
        offset = np.pi/4 if lati == 4 and rot == 0 else 0
        theta = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset
        vx, vy = x_c + (L/2) * np.cos(theta), y_c + (P/2) * np.sin(theta)
        
        # 1. PIANO ORIZZONTALE (Sempre)
        ax.plot(np.append(vx, vx[0]), np.append(vy, vy[0]), color='black', linewidth=2)
        if 'pir' in tipo or 'con' in tipo:
            for p_x, p_y in zip(vx, vy): ax.plot([x_c, p_x], [y_c, p_y], color='black', linewidth=0.8)

        if premium:
            x_min, x_max = np.min(vx), np.max(vx)
            y_min, y_max = np.min(vy), np.max(vy)
            
            # 2. PIANO VERTICALE
            if 'pir' in tipo or 'con' in tipo:
                ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color='black', linewidth=2)
            else:
                ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color='black', linewidth=2)
            
            # 3. PIANO LATERALE (Archi)
            t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
            for ry in [y_min, y_max, y_c]:
                r = abs(ry)
                ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='orange', linestyle='--', linewidth=0.6)
            
            # 4. PIANO AUSILIARIO (Solo se necessario)
            if aux:
                ang_aux = np.radians(-35) # Angolo LT ausiliaria
                ax.plot([-limit, 0], [(-limit*np.tan(ang_aux))-25, (-25)], color='blue', linewidth=1.5, linestyle='-.')
                ax.text(-limit+5, (-limit*np.tan(ang_aux))-22, "L.T. Ausiliaria (P.A.)", color='blue', fontsize=10)
                for i in range(len(vx)):
                    dist = 25
                    ax.plot([vx[i], vx[i]-dist*np.sin(ang_aux)], [vy[i], vy[i]+dist*np.cos(ang_aux)], color='blue', linestyle=':', linewidth=0.6, alpha=0.5)

    if not premium:
        ax.text(20, 20, "BLOCCATO\nSblocca Premium", color='red', alpha=0.3, fontsize=18, ha='center', va='center', rotation=45)
    
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    return fig

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
    else: st.success("✅ MODALITÀ AVANZATA ATTIVA")

st.title("📐 TavolaPronta AI Master")
st.info("Esempio: Disegna un parallelepipedo 6x4x10 ruotato di 30 gradi e proietta la sua vera forma su un piano ausiliario.")
traccia = st.text_area("Cosa vuoi disegnare?")

if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        prompt = """Analizza la traccia e restituisci JSON lista 'solidi'. 
        Se chiede 'piano ausiliario' o 'vera forma', imposta 'piano_ausiliario': true.
        Se rotazione non specificata, rotazione=0. Lati: Esagono=6, Quadrato=4.
        JSON: {"solidi": [{"tipo", "lunghezza", "profondita", "altezza", "dist_pv", "dist_pl", "rotazione", "lati", "piano_ausiliario"}]}"""
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": traccia}],
            response_format={"type": "json_object"}
        )
        lista = json.loads(res.choices[0].message.content).get("solidi", [])
        st.pyplot(genera_proiezione_ortogonale(lista, premium=st.session_state.premium))
