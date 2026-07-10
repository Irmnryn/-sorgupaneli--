import streamlit as st
import pandas as pd
import re
from pathlib import Path

# ------------------------------------------------------------
# SAYFA AYARLARI
# ------------------------------------------------------------
st.set_page_config(
    page_title=" MTSO Sorgu Portalı",
    page_icon="",
    layout="wide",
)

VERI_YOLU = Path(__file__).parent / "veri" / "uyeler.xlsx"


# ------------------------------------------------------------
# VERİYİ OKUMA (cache'lenir, her aramada Excel'i yeniden okumaz)
# ------------------------------------------------------------
@st.cache_data
def veri_yukle():
    df = pd.read_excel(VERI_YOLU)

    # Telefon sütunlarını okunabilir metne çevir (3242374000 -> 0324 237 40 00)
    def telefon_formatla(deger):
        if pd.isna(deger):
            return ""
        rakamlar = re.sub(r"\D", "", str(int(deger)))
        if len(rakamlar) == 10:
            rakamlar = "0" + rakamlar
        if len(rakamlar) == 11:
            return f"{rakamlar[0:4]} {rakamlar[4:7]} {rakamlar[7:9]} {rakamlar[9:11]}"
        return str(deger)

    if "isTel" in df.columns:
        df["isTel"] = df["isTel"].apply(telefon_formatla)
    if "burotel" in df.columns:
        df["burotel"] = df["burotel"].apply(telefon_formatla)

    # Boş hücreleri düzgün göster
    df = df.fillna("")
    return df


df = veri_yukle()

# Ekranda gösterilecek sütun adları (kullanıcı dostu Türkçe başlıklar)
SUTUN_ADLARI = {
    "Sıra": "Sıra",
    "ticaretSicilNo": "Ticaret Sicil No",
    "uyeOdaSicilNo": "Oda Sicil No",
    "unvan": "Ünvan",
    "adres": "Adres",
    "isTel": "İş Telefonu",
    "burotel": "Büro Telefonu",
    "YETKİLİ": "Yetkili",
}

# ------------------------------------------------------------
# BAŞLIK
# ------------------------------------------------------------
st.title(" MTSO Sorgu Portalı")
st.caption(f"Toplam {len(df):,} üye kaydı arasında arama yapabilirsiniz.")

st.divider()

# ------------------------------------------------------------
# ARAMA ALANLARI
# ------------------------------------------------------------
sekme_genel, sekme_detay = st.tabs([" Genel Arama", " Detaylı Arama"])

# ---- 1) GENEL ARAMA (örnek koddaki mantığın gelişmiş hali) ----
with sekme_genel:
    arama_terimi = st.text_input(
        "Ünvan, sicil no, adres veya yetkili adı girin:",
        placeholder="Örn: VURUŞKAN, 8494, AKDENİZ ...",
    )

    if arama_terimi:
        sonuclar = df[
            df.astype(str)
            .apply(lambda satir: satir.str.contains(arama_terimi, case=False, na=False))
            .any(axis=1)
        ]
    else:
        sonuclar = df

# ---- 2) DETAYLI ARAMA (alan alan filtreleme) ----
with sekme_detay:
    col1, col2 = st.columns(2)
    with col1:
        f_unvan = st.text_input("Ünvan içinde ara")
        f_sicil = st.text_input("Ticaret Sicil No")
        f_oda_sicil = st.text_input("Oda Sicil No")
    with col2:
        f_adres = st.text_input("Adres içinde ara (ör: ilçe adı)")
        f_yetkili = st.text_input("Yetkili adı içinde ara")

    detay_sonuc = df.copy()
    if f_unvan:
        detay_sonuc = detay_sonuc[detay_sonuc["unvan"].str.contains(f_unvan, case=False, na=False)]
    if f_sicil:
        detay_sonuc = detay_sonuc[detay_sonuc["ticaretSicilNo"].astype(str).str.contains(f_sicil)]
    if f_oda_sicil:
        detay_sonuc = detay_sonuc[detay_sonuc["uyeOdaSicilNo"].astype(str).str.contains(f_oda_sicil)]
    if f_adres:
        detay_sonuc = detay_sonuc[detay_sonuc["adres"].str.contains(f_adres, case=False, na=False)]
    if f_yetkili:
        detay_sonuc = detay_sonuc[detay_sonuc["YETKİLİ"].str.contains(f_yetkili, case=False, na=False)]

    detay_aktif = any([f_unvan, f_sicil, f_oda_sicil, f_adres, f_yetkili])

# Hangi sekme kullanıldıysa onun sonucunu göster
gosterilecek = detay_sonuc if detay_aktif else sonuclar

st.divider()

# ------------------------------------------------------------
# SONUÇLAR
# ------------------------------------------------------------
st.subheader(f"Sonuçlar ({len(gosterilecek):,} kayıt)")

gosterim_df = gosterilecek.rename(columns=SUTUN_ADLARI)

secim = st.dataframe(
    gosterim_df,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
)

# ------------------------------------------------------------
# DETAY PANELİ (bir satıra tıklanınca açılır)
# ------------------------------------------------------------
secili_satirlar = secim.selection.rows if secim and secim.selection else []
if secili_satirlar:
    secili_index = secili_satirlar[0]
    secili_kayit = gosterilecek.iloc[secili_index]

    st.divider()
    st.subheader(f" Detay: {secili_kayit['unvan']}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Ticaret Sicil No:** {secili_kayit['ticaretSicilNo']}")
        st.markdown(f"**Oda Sicil No:** {secili_kayit['uyeOdaSicilNo']}")
        st.markdown(f"**Yetkili:** {secili_kayit['YETKİLİ'] or '—'}")
    with c2:
        st.markdown(f"**İş Telefonu:** {secili_kayit['isTel'] or '—'}")
        st.markdown(f"**Büro Telefonu:** {secili_kayit['burotel'] or '—'}")
    st.markdown(f"**Adres:** {secili_kayit['adres']}")

# ------------------------------------------------------------
# İNDİRME BUTONU
# ------------------------------------------------------------
csv_veri = gosterim_df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="📥 Sonuçları CSV olarak indir",
    data=csv_veri,
    file_name="sorgu_sonuclari.csv",
    mime="text/csv",
)
