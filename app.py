import streamlit as st
import pandas as pd

# ------------------------------------------------------------
# SAYFA AYARLARI
# ------------------------------------------------------------
st.set_page_config(
    page_title="Sorgu Paneli",
    page_icon="",
    layout="centered",
)

# ------------------------------------------------------------
# ÖZEL GÖRÜNÜM (CSS)
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    .baslik {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .altbaslik {
        text-align: center;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    div[data-testid="stFileUploaderDropzone"] {
        border: 2px dashed #4f46e5;
        border-radius: 16px;
        padding: 2rem;
        background-color: #f5f6ff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# BAŞLIK
# ------------------------------------------------------------
st.markdown('<div class="baslik">📁 Sorgu Paneli</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="altbaslik">Bir Excel dosyası yükleyin, ardından aramak istediğiniz kaydı yazın</div>',
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# 1) BÜYÜK, ORTALANMIŞ DOSYA YÜKLEME ŞABLONU
# ------------------------------------------------------------
yuklenen_dosya = st.file_uploader(
    "Excel dosyanızı buraya sürükleyin ya da seçmek için tıklayın",
    type=["xlsx", "xls"],
    label_visibility="visible",
)

# ------------------------------------------------------------
# 2) SABİT ARAMA ÇUBUĞU (dosya yüklenmese de görünür durur)
# ------------------------------------------------------------
st.write("")
arama_terimi = st.text_input(
    "🔍 Arama",
    placeholder="Aramak istediğiniz firma / kelimeyi yazın...",
    disabled=(yuklenen_dosya is None),
    label_visibility="collapsed",
)

# ------------------------------------------------------------
# 3) DOSYA YOKSA BİLGİLENDİRME, VARSA OKU
# ------------------------------------------------------------
if yuklenen_dosya is None:
    st.info("Arama yapabilmek için önce yukarıdan bir Excel dosyası yükleyin.")
    st.stop()

try:
    df = pd.read_excel(yuklenen_dosya)
except Exception as hata:
    st.error(f"Dosya okunamadı, lütfen geçerli bir Excel dosyası yükleyin. Hata: {hata}")
    st.stop()

df = df.fillna("")

st.success(f"'{yuklenen_dosya.name}' yüklendi — {len(df):,} satır, {len(df.columns)} sütun bulundu.")

# ------------------------------------------------------------
# 4) ARAMA MANTIĞI
# ------------------------------------------------------------
if arama_terimi:
    sonuclar = df[
        df.astype(str)
        .apply(lambda satir: satir.str.contains(arama_terimi, case=False, na=False))
        .any(axis=1)
    ]
    baslik_metni = f"🔎 '{arama_terimi}' için {len(sonuclar):,} sonuç bulundu"
else:
    sonuclar = df
    baslik_metni = f"📋 Tüm kayıtlar ({len(sonuclar):,} satır)"

# ------------------------------------------------------------
# 5) SONUÇLAR — AÇILIR PANELDE (dosya/arama değiştikçe otomatik açık)
# ------------------------------------------------------------
with st.expander(baslik_metni, expanded=True):
    st.dataframe(sonuclar, use_container_width=True, hide_index=True)

    csv_veri = sonuclar.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Sonuçları CSV olarak indir",
        data=csv_veri,
        file_name="sorgu_sonuclari.csv",
        mime="text/csv",
    )

    # --------------------------------------------------------
    # 6) DETAY GÖRÜNÜMÜ (hangi sütunlar geleceği bilinmediği için
    #    her satırı ilk birkaç sütunundan oluşan bir etiketle listeliyoruz)
    # --------------------------------------------------------
    if len(sonuclar) > 0:
        st.divider()
        st.markdown("**Bir kaydın tüm ayrıntılarını görmek için seçin:**")

        onizleme_sutun_sayisi = min(3, len(sonuclar.columns))

        def satir_etiketi(satir):
            parcalar = [str(satir[sutun]) for sutun in sonuclar.columns[:onizleme_sutun_sayisi]]
            return " — ".join(p for p in parcalar if p)

        secenekler = {"— Kayıt seçin —": None}
        for orijinal_index, satir in sonuclar.iterrows():
            etiket = satir_etiketi(satir) or f"Kayıt #{orijinal_index}"
            secenekler[f"{etiket}"] = orijinal_index

        secilen_etiket = st.selectbox("Kayıt", list(secenekler.keys()), label_visibility="collapsed")
        secilen_index = secenekler[secilen_etiket]

        if secilen_index is not None:
            secili_satir = sonuclar.loc[secilen_index]
            st.markdown("#### 📋 Kayıt Detayı")
            for sutun_adi in sonuclar.columns:
                deger = secili_satir[sutun_adi]
                st.markdown(f"**{sutun_adi}:** {deger if str(deger).strip() else '—'}")
