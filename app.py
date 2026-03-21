import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq
from mpl_toolkits.mplot3d import Axes3D

# --- CONFIGURAZIONE INTERFACCIA (FEDELE AL TUO SCREENSHOT) ---
st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

# --- COSTANTI E LICENZA ---
LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

# --- MOTORE GEOMETRICO MASTER UNIVERSALE ---
def genera_vista_3d_master(lista_solidi):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    limit = 35
    ax.set_axis_off()
    xx, yy = np.meshgrid(np.linspace(-limit, 0, 2), np.linspace(-limit, 0, 2))
    ax.plot_surface(xx, yy, np.zeros_like(xx), alpha=0.05, color='gray') 
    ax.plot_surface(xx, np.zeros_like(xx), yy + limit, alpha=0.05, color='blue') 
    ax.plot_surface(np.zeros_like(xx), xx, yy + limit, alpha=0.05, color='red') 
    colori = ['#2c3e50', '#2980b9', '#e74c3c']
    for i, dati in enumerate(lista_solidi[:3]):
        tipo, L, P, H = dati.get('tipo', '').lower(), float(dati.get('lunghezza') or 6), float(dati.get('profondita') or 5), float(dati.get('altezza') or 10)
        dPV, dPL = float(dati.get('dist_pv') or 10), float(dati.get('dist_pl') or 10)
        rot, incl = np.radians(float(dati.get('rotazione') or 0)), np.radians(float(dati.get('inclinazione') or 0))
        x_c, y_c = -dPL - L/2, -dPV - P/2
        if 'pir' in tipo or 'con' in tipo:
            v_x, v_y, v_z = x_c + H * np.sin(incl), y_c, H * np.cos(incl)
            t = np.linspace(0, 2*np.pi, int(dati.get('lati', 6))+1)
            bx, by = x_c + (L/2) * np.cos(t + rot), y_c + (P/2) * np.sin(t + rot)
            for x_b, y_b in zip(bx, by):
                ax.plot([x_b, v_x], [y_b, v_y], [0, v_z], color=colori[i], linewidth=1.5)
                ax.fill_between([x_b, v_x], [y_b, v_y], [0, v_z], color=colori[i], alpha=0.1)
        else:
            t = np.linspace(0, 2*np.pi, 100 if 'cil' in tipo else int(dati.get('lati', 4))+1)
            for z in [0, H]:
                ax.plot(x_c + (L/2)*np.cos(t+rot), y_c + (P/2)*np.sin(t+rot), z, color=colori[i], linewidth=2)
            for a in np.linspace(0, 2*np.pi, 5 if 'cil' in tipo else int(dati.get('lati', 4))):
                ax.plot([x_c+(L/2)*np.cos(a+rot), x_c+(L/2)*np.cos(a+rot)], [y_c+(P/2)*np.sin(a+rot), y_c+(P/2)*np.sin(a+rot)], [0, H], color=colori[i], alpha=0.3, linestyle='--')
    ax.view_init(25, 45)
    return fig

def genera_proiezione_ortogonale(lista_solidi, premium=False):
    fig, ax = plt.subplots(figsize=(14, 14), facecolor='#ffffff')
    ax.set_aspect('equal')
    ax.axis('off')
    limit = 85
    ax.plot([-limit, limit], [0, 0], color='#2c3e50', linewidth=2) 
    ax.plot([0, 0], [-limit, limit], color='#2c3e50', linewidth=1) 
    ax.text(-limit+2, 2, "P.V.", fontsize=12, color='#7f8c8d')
    ax.text(-limit+2, -5, "P.O.", fontsize=12, color='#7f8c8d')
    ax.text(2, limit-5, "P.L.", fontsize=12, color='#7f8c8d')
    colori = ['#2c3e50', '#2980b9', '#e74c3c'] 
    for i, dati in enumerate(lista_solidi[:3]):
        tipo, L, P, H = str(dati.get('tipo', 'solido')).lower(), float(dati.get('lunghezza') or 6), float(dati.get('profondita') or 5), float(dati.get('altezza') or 10)
        dPV, dPL = float(dati.get('dist_pv') or 10), float(dati.get('dist_pl') or 10)
        rot, incl = np.radians(float(dati.get('rotazione') or 0)), np.radians(float(dati.get('inclinazione') or 0))
        x_c, y_c = -dPL - L/2, -dPV - P/2
        t = np.linspace(0, 2*np.pi, 100 if 'cil' in tipo else int(dati.get('lati', 4))+1)
        if dati.get('lati')==4 and float(dati.get('rotazione') or 0)==0: t += np.pi/4 
        vx, vy = x_c + (L/2) * np.cos(t + rot), y_c + (P/2) * np.sin(t + rot)
        ax.plot(np.append(vx, vx[0]), np.append(vy, vy[0]), color=colori[i], linewidth=2.5)
        if premium:
            x_min, x_max = np.min(vx), np.max(vx)
            for px in vx[::20]: ax.plot([px, px], [y_c, 0], color='#dcdde1', linestyle=':', linewidth=0.6)
            h_p, off_x = H * np.cos(incl), H * np.sin(incl)
            if 'pir' in tipo: ax.plot([x_min, x_max, x_c + off_x, x_min], [0, 0, h_p, 0], color=colori[i], linewidth=2.5)
            else: ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color=colori[i], linewidth=2.5)
            for ry in vy[::20]:
                r = abs(ry)
                ax.plot(r*np.cos(np.linspace(1.5*np.pi, 2*np.pi, 30)), r*np.sin(np.linspace(1.5*np.pi, 2*np.pi, 30)), color='#dcdde1', linestyle='--', linewidth=0.5)
            z_min, z_max = abs(np.max(vy)), abs(np.min(vy))
            if 'pir' in tipo: ax.plot([z_min, z_max, abs(y_c), z_min], [0, 0, h_p, 0], color=colori[i], linewidth=2.5)
            else: ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color=colori[i], linewidth=2.5)
    return fig

# --- SIDEBAR ---
if 'premium' not in st.session_state: st.session_state.premium = False
with st.sidebar:
    st.title("💎 Area Premium Master")
    if not st.session_state.premium:
        # Stato simulato attivo per test
        with st.container(border=True):
            st.success("✅ ABBONAMENTO MASTER ATTIVO")
        st.info("💡 L'abbonamento sblocca P.V., P.L. e la nuova **Vista 3D Assonometrica**.")
        with st.container(border=True):
            st.write("🚧 **Work in Progress**: Ottimizzazione algoritmi di tangenza e piani ausiliari.")
        if st.button("Logout Licenza"): st.session_state.premium = False
    else:
        st.success("✅ ABBONAMENTO MASTER ATTIVO")
        if st.button("Logout Licenza"): st.session_state.premium = False

# --- MAIN APP ---
st.title("📐 TavolaPronta AI Master")
st.write("Generazione tecnica multi-solido professionale.")
traccia = st.text_area("Cosa vuoi disegnare oggi? (Supporta fino a 3 solidi):", height=120)
if st.button("🚀 GENERA TAVOLA PROFESSIONALE"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "Sei un esperto di geometria descrittiva. Restituisci JSON 'solidi' con parametri dist_pv, dist_pl, rotazione, inclinazione e lati. Calcola la tangenza matematica tra i solidi basandoti sulla traccia."}],
                response_format={"type": "json_object"}
            )
            dati = json.loads(res.choices[0].message.content).get('solidi', [])
            st.pyplot(genera_proiezione_ortogonale(dati, premium=True))
            st.divider()
            st.subheader("📦 Vista 3D Master sbloccata")
            st.pyplot(genera_vista_3d_master(dati))
        except Exception:
            st.error("Errore nell'analisi geometrica dei solidi. Verifica i parametri inseriti.")
