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
    ax.plot([-35, 35], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-35, 35], color='black', linewidth=1)
    
    tipo = dati.get('tipo', 'solido').lower()
    L, P, H = dati.get('lunghezza', 6), dati.get('profondita', 5), dati.get('altezza', 10)
    dPV, dPL = dati.get('dist_pv', 2), dati.get('dist_pl', 3)
    rot, lati = dati.get('rotazione', 0), dati.get('lati', 4)

    x_c, y_c = -dPL - L/2, -dPV - P/2
    angle = np.radians(rot)
    theta = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle
    vx, vy = x_c + (L/2) * np.cos(theta), y_c + (P/2) * np.sin(theta)
    punti_po = np.column_stack([vx, vy])
    punti_chiusi = np.vstack([punti_po, punti_po[0]])

    ax.plot(punti_chiusi[:, 0], punti_chiusi[:, 1], color='black', linewidth=2.5)
    if 'piramide' in tipo or 'cono' in tipo:
        for p in punti_po: ax.plot([x_c, p[0]], [y_c, p[1]], color='black', linewidth=1)

    if premium:
        x_min, x_max = np.min(vx), np.max(vx)
        y_min, y_max = np.min(vy), np.max(vy)
        if 'piramide' in tipo or 'cono' in tipo:
            ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color='black', linewidth=2.5)
        else:
            ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color='black', linewidth=2.5)
        for px in [x_min, x_max, x_c]:
            ax.plot([px, px], [y_max, H if px==x_c and 'pir' in tipo else 0], color='gray', linestyle=':', linewidth=0.7)
        t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
        for ry in [y_min, y_max, y_c]:
            r = abs(ry)
            ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='orange', linestyle='--', linewidth=0.8)
            ax.plot([r, r], [0, H if ry==y_c and 'pir' in tipo else 0], color='gray', linestyle=':', linewidth=0.7)
        z_min, z_max, z_c = abs(y_max), abs(y_min), abs(y_c)
        if 'piramide' in tipo or 'cono' in tipo:
            ax.plot([z_min, z_max, z_c, z_min], [0, 0, H, 0], color='black', linewidth=2.5)
        else:
            ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color='black', linewidth=2.5)

    ax.text(-28, 1, "P.V.", fontsize=14, fontweight='bold')
    ax.text(-28, -2, "P.O.", fontsize=14, fontweight='bold')
    ax.text(2, 28, "P.L.", fontsize=14, fontweight='bold')
    return fig

if 'premium' not in st.session_state: st.session_state.premium = False

st.title("📐 TavolaPronta AI Master")

with st.sidebar:
    st.header("💎 Versione Premium")
    if not st.session_state.premium:
        st.link_button("Mensile (4,99€)", LINK_MENSILE)
        st.link_button("Lifetime (19,99€)", LINK_LIFETIME)
        code = st.text_input("Codice licenza:", type="password")
        if st.button("Attiva Premium"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
    else:
        st.success("✅ Licenza Master Attiva")

traccia = st.text_area("Inserisci la traccia:")
if st.button("🚀 GENERA DISEGNO"):
    if traccia:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Estrai JSON: tipo, lunghezza, profondita, altezza, dist_pv, dist_pl, rotazione, lati."}],
            response_format={"type": "json_object"}
        )
        dati = json.loads(res.choices[0].message.content)
        st.pyplot(genera_proiezione_ortogonale(dati, premium=st.session_state.premium))
        if not st.session_state.premium: st.warning("Sblocca Premium per PV e PL")
