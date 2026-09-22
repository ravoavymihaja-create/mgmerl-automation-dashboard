import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="MGMERL Automation Dashboard", page_icon="📊", layout="wide")
rng=np.random.default_rng(42)
REF={"1.33":"Site","2.17":"Communauté","3.09":"Session","3.22":"Session","4.17":"Session","6.26":"Session"}
COMMUNES=[f"Commune {x}" for x in "ABCDEF"]
AGENTS=[f"TA {i:02d}" for i in range(1,21)]

@st.cache_data
def generate(n=5000):
    df=pd.DataFrame({
        "response_key":[f"R{i:06d}" for i in range(1,n+1)],
        "agent":rng.choice(AGENTS,n),
        "commune":rng.choice(COMMUNES,n),
        "site_id":[f"S{x:04d}" for x in rng.integers(1,1000,n)],
        "activity_code":rng.choice(list(REF),n),
        "women":rng.integers(0,80,n),
        "men":rng.integers(0,70,n),
        "status":rng.choice(["Finalisé","Rejeté"],n,p=[.94,.06])})
    df["total_people"]=df.women+df.men
    df["expected_unit"]=df.activity_code.map(REF); df["unit"]=df.expected_unit
    idx=rng.choice(df.index,n//50,replace=False); df.loc[idx,"total_people"]+=3
    idx=rng.choice(df.index,n//80,replace=False); df.loc[idx,"unit"]="Unité incorrecte"
    idx=rng.choice(df.index,n//100,replace=False); df.loc[idx,"activity_code"]="9.99"
    return pd.concat([df,df.sample(n//100,random_state=42)],ignore_index=True)

def control(df):
    q=df.copy()
    q["Doublon"]=q.duplicated("response_key",keep=False)
    q["Bénéficiaires incohérents"]=q.total_people.ne(q.women+q.men)
    q["Activité non prévue"]=~q.activity_code.isin(REF)
    q["Unité incorrecte"]=(~q["Activité non prévue"])&q.unit.ne(q.expected_unit)
    cols=["Doublon","Bénéficiaires incohérents","Activité non prévue","Unité incorrecte"]
    q["Erreur"]=q[cols].any(axis=1)
    return q,cols

raw=generate(); qc,errcols=control(raw)
valid=qc[(qc.status=="Finalisé")&(~qc.Erreur)]
ind=pd.DataFrame([
["MGM-01","Sites uniques certifiés/vérifiés",valid.loc[valid.activity_code=="1.33","site_id"].nunique()],
["MGM-02","Personnes touchées - activité 2.17",valid.loc[valid.activity_code=="2.17","total_people"].sum()],
["MGM-03","Sessions - activité 3.09",valid.loc[valid.activity_code=="3.09","response_key"].nunique()],
["MGM-04","Femmes touchées - activité 3.22",valid.loc[valid.activity_code=="3.22","women"].sum()],
["MGM-05","Communes couvertes",valid.commune.nunique()]],columns=["Indicateur","Description","Résultat"])

st.title("📊 MGMERL Automation Dashboard")
st.caption("Portfolio de démonstration — données 100 % synthétiques et anonymisées")
st.markdown("**Collecte terrain → Contrôle qualité MGMERL → Consolidation → Indicateurs → Reporting**")
a,b,c,d,e=st.columns(5)
a.metric("Formulaires",f"{raw.response_key.nunique():,}")
b.metric("Lignes analysées",f"{len(raw):,}")
c.metric("Anomalies",f"{qc.Erreur.sum():,}")
d.metric("Conformité",f"{100*(1-qc.Erreur.mean()):.1f}%")
e.metric("Indicateurs",len(ind))

tabs=st.tabs(["Vue d'ensemble","Contrôle qualité","Indicateurs MGMERL","Performance TA","Traçabilité"])
with tabs[0]:
    st.subheader("Pipeline automatisé")
    st.info("Exports terrain → Référentiel MGMERL → Contrôles → Base consolidée → Indicateurs → Reporting")
    x=qc.groupby("commune").agg(Formulaires=("response_key","nunique"),Anomalies=("Erreur","sum"))
    st.bar_chart(x); st.dataframe(x,use_container_width=True)
with tabs[1]:
    st.subheader("Contrôles qualité")
    issues=pd.DataFrame({"Contrôle":errcols,"Nombre":[int(qc[x].sum()) for x in errcols]}).set_index("Contrôle")
    st.bar_chart(issues); st.dataframe(issues,use_container_width=True)
    st.dataframe(qc[qc.Erreur].head(100),use_container_width=True)
with tabs[2]:
    st.subheader("Indicateurs MGMERL simulés")
    st.dataframe(ind,use_container_width=True,hide_index=True)
    st.bar_chart(ind.set_index("Indicateur")["Résultat"])
with tabs[3]:
    st.subheader("Qualité des données par TA")
    p=qc.groupby("agent").agg(Formulaires=("response_key","nunique"),Anomalies=("Erreur","sum")).reset_index()
    p["Taux qualité (%)"]=((p.Formulaires-p.Anomalies)/p.Formulaires*100).clip(lower=0).round(1)
    st.dataframe(p.sort_values("Taux qualité (%)",ascending=False),use_container_width=True,hide_index=True)
with tabs[4]:
    st.subheader("Traçabilité")
    code=st.selectbox("Code activité",sorted(qc.activity_code.unique()))
    st.dataframe(qc[qc.activity_code==code].head(300),use_container_width=True)

st.divider()
st.caption("Python • Pandas • Streamlit • Data Quality • MEAL/MGMERL Automation")
