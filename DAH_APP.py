import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="Dashboard DAH Bounkani", layout="wide")

# --- PARAMÈTRES KOBO ---
# Assurez-vous que ces secrets sont bien configurés dans Streamlit Cloud
KOBO_TOKEN = st.secrets["kobo_token"]
FORM_ID = st.secrets["form_id"]
KOBO_URL = f"https://kf.kobotoolbox.org/api/v2/assets/{FORM_ID}/data/?format=json"

st.title("📊 Rapport de Vulnérabilité (Inondations) - Bounkani")
st.markdown("---")

@st.cache_data(ttl=300)
def load_kobo_data():
    headers = {"Authorization": f"Token {KOBO_TOKEN}"}
    try:
        response = requests.get(KOBO_URL, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data['results'])
        else:
            st.error(f"Erreur Kobo : {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return None

df = load_kobo_data()

if df is not None and not df.empty:
    # 1. INDICATEURS CLÉS (LES CHIFFRES)
    total = len(df)
    col1, col2, col3 = st.columns(3)
    col1.metric("Ménages Évalués", total)
    
    # Calcul des personnes sans eau potable (basé sur votre colonne)
    col_eau = 'bes_eau/potab_inond'
    if col_eau in df.columns:
        sans_eau = (df[col_eau] == 'non').sum()
        col2.metric("Urgence Eau Potable", f"{sans_eau} ménages", delta="Besoin d'aide", delta_color="inverse")

    st.write("## 📉 Analyses Graphiques")
    
    # 2. GRAPHIQUE DES DÉPARTEMENTS
    col_dept = 'ident/departement'
    if col_dept in df.columns:
        st.write("### Répartition par Département")
        # On compte les occurrences et on crée le graphique
        df_dept = df[col_dept].value_counts().reset_index()
        df_dept.columns = ['Département', 'Nombre']
        fig1 = px.bar(df_dept, x='Département', y='Nombre', 
                     color='Département', text_auto=True,
                     color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig1, use_container_width=True)

    # 3. DEUX GRAPHES CÔTE À CÔTE (SEXE ET STATUT)
    g1, g2 = st.columns(2)
    
    with g1:
        col_sexe = 'ident/sexe_chef'
        if col_sexe in df.columns:
            st.write("### Sexe du Chef de Ménage")
            fig2 = px.pie(df, names=col_sexe, hole=0.5, 
                         color_discrete_sequence=['#636EFA', '#EF553B'])
            st.plotly_chart(fig2, use_container_width=True)

    with g2:
        col_statut = 'ident/statut_enq'
        if col_statut in df.columns:
            st.write("### Statut des Ménages")
            fig3 = px.pie(df, names=col_statut, hole=0.5,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig3, use_container_width=True)

    # 4. BESOINS ALIMENTAIRES
    col_repas = 'bes_alim/repas_jour'
    if col_repas in df.columns:
        st.write("### Nombre de repas par jour")
        fig4 = px.histogram(df, x=col_repas, 
                           labels={col_repas: 'Nombre de repas'},
                           color_discrete_sequence=['#FFA15A'])
        st.plotly_chart(fig4, use_container_width=True)

    # TABLEAU DE DÉTAIL
    with st.expander("🔍 Voir les données brutes"):
        st.dataframe(df)

else:
    st.info("Aucune donnée disponible. Vérifiez que vos enquêteurs ont envoyé leurs formulaires.")

# Bouton de téléchargement
if df is not None:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Télécharger les données", csv, "donnees_dah.csv", "text/csv")
