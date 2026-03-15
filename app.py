import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq

st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

# --- LINK E CODICI ---
LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

def genera_proiezione_ortogonale(dati, premium=False):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Assi principali
    ax.plot([-35, 35], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-35, 35], color='black', linewidth=1)
    
    # Parametri IA
    tipo = dati.get('tipo', 'solido').lower()
    L, P, H = dati.get('lunghezza', 6), dati.get('profondita', 5), dati.get('altezza', 10)
    dPV, dPL = dati.get('dist_pv', 2), dati.get('dist_pl', 3)
    rot, lati = dati.get('rotazione', 0), dati.get('lati', 4)

    # --- DISEGNO P.O. (Sempre Visibile) ---
    x_c, y_c = -dPL - L/2, -dPV - P/2
    angle = np.radians(rot)
    theta = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle
    vx, vy = x_c + (L/2) * np.cos(theta), y_c + (P/2) * np.sin(theta)
    punti_po = np.column_stack([vx, vy])
    punti_chiusi = np.vstack([punti_po, punti_po[0]])

    ax.plot(punti_chiusi[:, 0], punti_chiusi[:, 1], color='black', linewidth=2.5)
    if 'piramide' in tipo or 'cono' in tipo:
        for p in punti_po: ax.plot([x_c, p[0]], [y_c, p[1]], color='black', linewidth=1)

    # --- LOGICA PREMIUM ---
    if premium:
        x_min, x_max = np.min(vx), np.max(vx)
        y_min, y_max = np.min(vy), np.max(vy)
        # P.V.
        if 'piramide' in tipo or 'cono' in tipo:
            ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color='black', linewidth=2.5)
        else:
            ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color='black', linewidth=2.5)
        # Proiezioni e Archi
        for px in [x_min, x_max, x_c]:
            ax.plot([px, px], [y_max, H if px==x_c and 'pir' in tipo else 0], color='gray', linestyle=':', linewidth=0.7)
        t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
        for ry in [y_min, y_max, y_c]:
            r = abs(ry)
            ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='orange', linestyle='--', linewidth=0.8)
            ax.plot([r, r], [0, H if ry==y_c and 'pir' in tipo else 0], color='gray', linestyle=':', linewidth=0.7)
        # P.L.
        z_min, z_max, z_c = abs(y_max), abs(y_min), abs(y_c)
        if 'piramide' in tipo or 'cono' in tipo:
            ax.plot([z_min, z_max, z_c, z_min], [0, 0, H, 0], color='black', linewidth=2.5)
        else:
            ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color='black', linewidth=2.5)
    else:
        # Messaggio visivo sui quadranti vuoti
        ax.text(15, 15, "BLOCCATO\nSblocca P.L.", color='red', alpha=0.3, fontsize=20, ha='center', va='center', rotation=45)
        ax.text(-15, 15, "BLOCCATO\nSblocca P.V.", color='red', alpha=0.3, fontsize=20, ha='center', va='center', rotation=45)

    ax.text(-30, 1.5, "PIANO VERTICALE", fontsize=10, color='gray')
    ax.text(-30, -2.5, "PIANO ORIZZONTALE", fontsize=10, color='gray')
    ax.text(2, 30, "PIANO LATERALE", fontsize=10, color='gray')
    return fig

# --- UI ---
if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.title("💎 Area Premium")
    if not st.session_state.premium:
        st.info("Attualmente hai accesso solo al P.O. (Piano Orizzontale).")
        st.link_button("Sblocca P.V. e P.L. (4,99€)", LINK_MENSILE)
        st.link_button("Sblocca Tutto per sempre (19,99€)", LINK_LIFETIME)
        st.divider()
        code = st.text_input("Inserisci il codice ricevuto via mail:", type="password")
        if st.button("Attiva Licenza Master"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
            else: st.error("Codice non valido.")
    else:
        st.success("✅ FUNZIONI MASTER ATTIVE")

st.title("📐 TavolaPronta AI")
traccia = st.text_area("Cosa devi disegnare?")

if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Estrai JSON: tipo, lunghezza, profondita, altezza, dist_pv, dist_pl, rotazione, lati."}],
            response_format={"type": "json_object"}
        )
        dati = json.loads(res.choices[0].message.content)
        st.pyplot(genera_proiezione_ortogonale(dati, premium=st.session_state.premium))
        if not st.session_state.premium:
            st.error("🔒 Attenzione: stai visualizzando solo la base (P.O.). Per proiezioni complete, archi e ribaltamenti, attiva la versione Premium.")
