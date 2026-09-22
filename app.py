import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="MGMERL Automation V2", page_icon="📊", layout="wide")
rng = np.random.default_rng(42)

REF = {
    "1.33": ("Water Safe", "Site", "WASH"),
    "2.17": ("ODF / mobilisation communautaire", "Communauté", "WASH"),
    "3.09": ("Sensibilisation communautaire", "Session", "ADO"),
    "3.22": ("Sensibilisation thématique", "Session", "ADO"),
    "4.17": ("Action club de jeunes", "Session", "ADO"),
    "4.05": ("Counselling nutrition", "Personne", "Nutrition"),
    "6.26": ("Animation communautaire", "Session", "ADO"),
}

@st.cache_data
def generate(n=6500):
    codes=list(REF)
    d=pd.DataFrame({
        "response_key":[f"R{i:06d}" for i in range(1,n+1)],
        "TA":rng.choice([f"TA {i:02d}" for i in range(1,25)],n),
        "Commune":rng.choice([f"Commune {x}" for x in "ABCDEFG"],n),
        "Village":[f"Village {x:03d}" for x in rng.integers(1,500,n)],
        "Site_ID":[f"S{x:05d}" for x in rng.integers(1,1300,n)],
        "Code":rng.choice(codes,n),
        "Femmes":rng.integers(0,90,n),
        "Hommes":rng.integers(0,80,n),
        "Statut":rng.choice(["Finalisé","Rejeté","Brouillon"],n,p=[.92,.05,.03])
    })
    d["Total"]=d.Femmes+d.Hommes
    d["Unite_attendue"]=d.Code.map(lambda x:REF[x][1])
    d["Unite"]=d.Unite_attendue
    d["Domaine"]=d.Code.map(lambda x:REF[x][2])
    d["Activite"]=d.Code.map(lambda x:REF[x][0])
    d["Quantite"]=rng.integers(1,8,n)

    ix=rng.choice(d.index,n//45,False); d.loc[ix,"Total"]+=3
    ix=rng.choice(d.index,n//75,False); d.loc[ix,"Unite"]="Unité invalide"
    ix=rng.choice(d.index,n//110,False); d.loc[ix,"Code"]="9.99"
    ix=rng.choice(d.index,n//95,False); d.loc[ix,"Site_ID"]=""
    return pd.concat([d,d.sample(n//90,random_state=42)],ignore_index=True)

def control(d):
    q=d.copy()
    q["Doublon"]=q.duplicated("response_key",keep=False)
    q["Beneficiaires_incoherents"]=q.Total.ne(q.Femmes+q.Hommes)
    q["Activite_non_prevue"]=~q.Code.isin(REF)
    q["Unite_incorrecte"]=(~q.Activite_non_prevue)&q.Unite.ne(q.Unite_attendue)
    q["Site_manquant"]=q.Site_ID.fillna("").str.strip().eq("")
    checks=["Doublon","Beneficiaires_incoherents","Activite_non_prevue","Unite_incorrecte","Site_manquant"]
    q["Nb_erreurs"]=q[checks].sum(axis=1)
    q["Decision"]=np.where(q.Nb_erreurs>0,"À vérifier","Conforme")
    return q,checks

raw=generate()
q,checks=control(raw)
valid=q[(q.Statut=="Finalisé")&(q.Decision=="Conforme")]

ind=pd.DataFrame([
["WSH-DEMO-01","Sites uniques Water Safe","NB_SITES_UNIQUES",valid.loc[valid.Code=="1.33","Site_ID"].nunique()],
["WSH-DEMO-02","Personnes mobilisation ODF","SOMME_PERSONNES",valid.loc[valid.Code=="2.17","Total"].sum()],
["NUT-DEMO-01","Personnes counselling","SOMME_PERSONNES",valid.loc[valid.Code=="4.05","Total"].sum()],
["ADO-DEMO-01","Sessions actions clubs","NB_ACTIVITES",valid.loc[valid.Code.isin(["3.09","3.22","4.17","6.26"]),"response_key"].nunique()],
["ADO-DEMO-02","Bénéficiaires actions clubs","SOMME_PERSONNES",valid.loc[valid.Code.isin(["3.09","3.22","4.17","6.26"]),"Total"].sum()],
["GOV-DEMO-01","Communes couvertes","NB_COMMUNES_UNIQUES",valid.Commune.nunique()]
],columns=["Indicateur","Description","Methode","Resultat"])

st.sidebar.title("⚙️ Simulation MGMERL")
st.sidebar.success("Données 100 % synthétiques")
communes=st.sidebar.multiselect("Communes",sorted(q.Commune.unique()),default=sorted(q.Commune.unique()))
view=q[q.Commune.isin(communes)]

st.title("📊 MGMERL Data Automation & Quality Control")
st.caption("Portfolio V2 — données entièrement synthétiques et anonymisées")
st.markdown("**mWater / Collecte terrain → Validation MGMERL → Grande Base → Indicateurs → PITT / Reporting**")

cols=st.columns(6)
values=[
("Formulaires",view.response_key.nunique()),
("Lignes",len(view)),
("À vérifier",int((view.Decision=="À vérifier").sum())),
("Conformité",f"{100*(view.Decision=='Conforme').mean():.1f}%"),
("Sites",view.Site_ID.replace("",np.nan).nunique()),
("Indicateurs",len(ind))]
for c,(label,value) in zip(cols,values):
    c.metric(label,value)

tabs=st.tabs(["🏠 Pilotage","🛡️ Data Quality","🗃️ Grande Base","🧮 Indicateurs","👥 Performance TA","🔎 Traçabilité","🧭 Architecture"])

with tabs[0]:
    st.subheader("Pilotage MGMERL")
    st.info("Réduire les contrôles manuels et sécuriser le passage des données terrain vers le reporting.")
    summary=view.groupby("Commune").agg(Formulaires=("response_key","nunique"),Anomalies=("Nb_erreurs","sum"))
    st.bar_chart(summary)
    st.dataframe(summary,use_container_width=True)

with tabs[1]:
    st.subheader("Moteur Data Quality")
    labels=["Doublons","Femmes + Hommes ≠ Total","Activités hors référentiel","Unités incorrectes","Sites manquants"]
    issues=pd.DataFrame({"Contrôle":labels,"Occurrences":[int(view[x].sum()) for x in checks]}).set_index("Contrôle")
    st.bar_chart(issues)
    st.dataframe(issues,use_container_width=True)
    st.dataframe(view[view.Decision=="À vérifier"].head(250),use_container_width=True)

with tabs[2]:
    st.subheader("Grande Base consolidée")
    sub=st.tabs(["01_FORMULAIRES","02_ACTIVITES","03_BENEFICIAIRES","04_SITES"])
    dfs=[
        view[["response_key","TA","Commune","Statut","Decision"]].drop_duplicates(),
        view[["response_key","Code","Activite","Domaine","Quantite","Unite"]],
        view[["response_key","Femmes","Hommes","Total"]],
        view[["response_key","Site_ID","Commune","Village"]]
    ]
    for t,df in zip(sub,dfs):
        with t:
            st.dataframe(df.head(300),use_container_width=True)

with tabs[3]:
    st.subheader("Moteur d'indicateurs")
    st.dataframe(ind,use_container_width=True,hide_index=True)
    st.bar_chart(ind.set_index("Indicateur")["Resultat"])
    st.code("NB_SITES_UNIQUES | SOMME_PERSONNES | NB_ACTIVITES | NB_COMMUNES_UNIQUES")

with tabs[4]:
    st.subheader("Performance et qualité par TA")
    p=view.groupby("TA").agg(Formulaires=("response_key","nunique"),A_verifier=("Decision",lambda x:int((x=="À vérifier").sum()))).reset_index()
    p["Taux_qualite_pct"]=((p.Formulaires-p.A_verifier)/p.Formulaires*100).clip(0,100).round(1)
    p=p.sort_values("Taux_qualite_pct",ascending=False)
    st.dataframe(p,use_container_width=True,hide_index=True)
    st.bar_chart(p.set_index("TA")["Taux_qualite_pct"])

with tabs[5]:
    st.subheader("Traçabilité formulaire → activité → indicateur")
    key=st.selectbox("Formulaire",view.response_key.drop_duplicates().head(1200))
    one=view[view.response_key==key]
    st.dataframe(one,use_container_width=True,hide_index=True)
    if not one.empty:
        st.metric("Anomalies détectées",int(one.Nb_erreurs.iloc[0]))
        st.write("**Décision :**",one.Decision.iloc[0])

with tabs[6]:
    st.subheader("Architecture de la solution")
    st.markdown("""
### 1. Collecte terrain
**mWater / Kobo / formulaires numériques**

⬇️

### 2. Validation MGMERL
Référentiel • unités • bénéficiaires • doublons • cohérence

⬇️

### 3. Grande Base
**Formulaires → Activités → Bénéficiaires → Sites**

⬇️

### 4. Moteur d'indicateurs
Règles métier • agrégations • sites uniques • personnes • sessions

⬇️

### 5. Reporting
**PITT • Dashboard • Performance TA • Traçabilité**
""")
    st.warning("Démonstration technique : aucune donnée opérationnelle réelle.")

st.divider()
st.caption("Python • Pandas • Streamlit • Data Quality • ETL • MEAL/MGMERL Automation")
