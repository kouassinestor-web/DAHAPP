import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="Dashboard Bounkani", layout="wide")

# --- PARAMÈTRES KOBO (À remplir) ---
KOBO_TOKEN = "7f409a0bdd3da09fe59e8ae57e5c099f011d2405" # Exemple: "a1b2c3d4e5f6..."
FORM_ID = "abrJjNyA6FX9LLzg6CUW7f" # Exemple: "aN7Hpxyz..."
KOBO_URL = f"https://kobo.humanitarianresponse.info/api/v2/assets/{FORM_ID}/data/?format=json"

st.title("📊 Rapport de Vulnérabilité : Région du Bounkani")
st.markdown("---")

@st.cache_data(ttl=600) # Rafraîchit les données toutes les 10 minutes
def load_kobo_data():
    headers = {"Authorization": f"Token {KOBO_TOKEN}"}
    # On teste l'URL directe sans le /data/ à la fin pour voir si le formulaire est reconnu
    test_url = f"https://kf.kobotoolbox.org/api/v2/assets/{FORM_ID}/?format=json"
    
    response = requests.get(test_url, headers=headers)
    
    if response.status_code == 200:
        # Si on arrive ici, l'ID est BON. On tente alors de récupérer les données.
        data_url = f"https://kf.kobotoolbox.org/api/v2/assets/{FORM_ID}/data/?format=json"
        data_response = requests.get(data_url, headers=headers)
        if data_response.status_code == 200:
            return pd.DataFrame(data_response.json()['results'])
        else:
            st.error(f"Formulaire trouvé, mais erreur d'accès aux données : {data_response.status_code}")
    elif response.status_code == 404:
        st.error(f"L'ID du formulaire '{FORM_ID}' est introuvable sur kf.kobotoolbox.org. Vérifiez l'ID dans l'URL de votre navigateur.")
    elif response.status_code == 401:
        st.error("Le Token est incorrect ou vous n'avez pas les permissions.")
    else:
        st.error(f"Erreur inconnue : {response.status_code}")
    return None

# Chargement des données
df = load_kobo_data()

if df is not None:
    # 1. INDICATEURS CLÉS (KPI)
    total_menages = len(df)
    col1, col2, col3 = st.columns(3)
    col1.metric("Ménages Évalués", total_menages)

    # Calcul Urgence WASH (basé sur votre colonne 'bes_eau/potab_inond')
    if 'bes_eau/potab_inond' in df.columns:
        besoin_wash = (df['bes_eau/potab_inond'] == 'non').sum()
        col2.metric("Sans Eau Potable", f"{besoin_wash}", delta="Urgent", delta_color="inverse")

    st.divider()

    # 2. ANALYSE GÉOGRAPHIQUE
    if 'ident/departement' in df.columns:
        st.write("### 📍 Analyse par Département")
        fig_dept = px.bar(df['ident/departement'].value_counts(), 
                         labels={'value': 'Nombre de fiches', 'index': 'Département'},
                         color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig_dept, use_container_width=True)

    # 3. PROFIL DES RÉPONDANTS
    st.write("### 👥 Profil des Chefs de Ménage")
    c1, c2 = st.columns(2)
    with c1:
        if 'ident/sexe_chef' in df.columns:
            fig_sexe = px.pie(df, names='ident/sexe_chef', title="Répartition par Sexe", hole=0.4)
            st.plotly_chart(fig_sexe)
    with c2:
        if 'ident/statut_enq' in df.columns:
            fig_statut = px.pie(df, names='ident/statut_enq', title="Statut (Réfugié/Hôte/PDI)", hole=0.4)
            st.plotly_chart(fig_statut)

    # 4. TABLEAU DE DONNÉES BRUTES
    with st.expander("🔍 Voir le détail des fiches collectées"):
        st.dataframe(df)

    # 5. BOUTON DE TÉLÉCHARGEMENT
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Télécharger le rapport complet (CSV)", csv, "rapport_dah_bounkani.csv", "text/csv")

else:
    st.warning("⚠️ En attente de synchronisation des données depuis les téléphones des enquêteurs...")
