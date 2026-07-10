import re
import streamlit as st
import pandas as pd

# ------------------------------------------------------------
# SAYFA AYARLARI
# ------------------------------------------------------------
st.set_page_config(
    page_title="Sorgu Paneli",
    page_icon="",
    layout="wide",
)

# ------------------------------------------------------------
# ÖZEL GÖRÜNÜM (CSS) — daha büyük yazılar, geniş dosya yükleme alanı
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    .baslik {
        text-align: center;
        font-size: 2.6rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .altbaslik {
        text-align: center;
        color: #6b7280;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    /* Dosya yükleme kutusu: büyük, mor, kesikli çerçeve */
    div[data-testid="stFileUploaderDropzone"] {
        border: 3px dashed #4f46e5;
        border-radius: 18px;
        padding: 2.5rem;
        background-color: #f5f6ff;
    }
    div[data-testid="stFileUploaderDropzone"] * {
        font-size: 1.15rem !important;
    }
    /* Arama kutusu: büyük yazı, büyük kutu */
    div[data-testid="stTextInput"] input {
        font-size: 1.4rem !important;
        padding: 0.9rem 1rem !important;
        border-radius: 12px !important;
        border: 2px solid #4f46e5 !important;
    }
    /* Sonuç tablosu başlığı (expander) büyük yazı */
    div[data-testid="stExpander"] summary {
        font-size: 1.3rem !important;
        font-weight: 700 !important;
    }
    /* Tablo hücrelerindeki yazı biraz büyüsün */
    div[data-testid="stDataFrame"] * {
        font-size: 1.02rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# TÜRKÇE BÜYÜK/KÜÇÜK HARF + BOŞLUK DUYARSIZ NORMALLEŞTİRME
# ------------------------------------------------------------
TR_DEGISIM = {"İ": "i", "I": "ı", "Ş": "ş", "Ğ": "ğ", "Ü": "ü", "Ö": "ö", "Ç": "ç"}


def normallestir(metin: str) -> str:
    """Türkçe karaktere duyarlı biçimde küçük harfe çevirir ve TÜM boşlukları siler.
    Böylece 'Model Teknoloji', 'MODEL  TEKNOLOJİ', 'modelteknoloji' hepsi eşleşir."""
    metin = str(metin)
    for buyuk, kucuk in TR_DEGISIM.items():
        metin = metin.replace(buyuk, kucuk)
    metin = metin.lower()
    metin = re.sub(r"\s+", "", metin)
    return metin


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
)

# ------------------------------------------------------------
# 2) SABİT ARAMA ÇUBUĞU
# ------------------------------------------------------------
st.write("")
arama_terimi = st.text_input(
    "🔍 Arama",
    placeholder="Aramak istediğiniz firma / kişi / sicil no yazın... ",
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
# 4) ARAMA MANTIĞI (boşluk / büyük-küçük harf duyarsız)
# ------------------------------------------------------------
if arama_terimi:
    aranan = normallestir(arama_terimi)

    # Her satırın TÜM sütunlarını tek bir normalleştirilmiş metinde birleştiriyoruz,
    # sonra aranan kelime bu metnin içinde geçiyor mu diye bakıyoruz.
    satir_metinleri = df.astype(str).apply(
        lambda satir: normallestir(" ".join(satir.values)), axis=1
    )
    sonuclar = df[satir_metinleri.str.contains(re.escape(aranan), na=False)]
    baslik_metni = f"🔎 '{arama_terimi}' için {len(sonuclar):,} sonuç bulundu"
else:
    sonuclar = df
    baslik_metni = f"📋 Tüm kayıtlar ({len(sonuclar):,} satır)"

# ------------------------------------------------------------
# 5) SONUÇLAR — GENİŞ, KAYDIRMASIZ, TÜM SATIRLARIN SIĞDIĞI TABLO
# ------------------------------------------------------------
with st.expander(baslik_metni, expanded=True):
    # Tüm satırların kaydırma olmadan görünmesi için tablo yüksekliğini
    # satır sayısına göre otomatik hesaplıyoruz.
    satir_yuksekligi = 35
    tablo_yuksekligi = (len(sonuclar) + 1) * satir_yuksekligi + 3
    tablo_yuksekligi = min(tablo_yuksekligi, 2000)  # aşırı uzamasın diye üst sınır

    st.dataframe(
        sonuclar,
        use_container_width=True,
        hide_index=True,
        height=tablo_yuksekligi,
    )

    csv_veri = sonuclar.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Sonuçları CSV olarak indir",
        data=csv_veri,
        file_name="sorgu_sonuclari.csv",
        mime="text/csv",
    )

    # ----------------------------------------------------------
    # 6) DETAY GÖRÜNÜMÜ
    # ----------------------------------------------------------
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
            secenekler[etiket] = orijinal_index

        secilen_etiket = st.selectbox("Kayıt", list(secenekler.keys()), label_visibility="collapsed")
        secilen_index = secenekler[secilen_etiket]

        if secilen_index is not None:
            secili_satir = sonuclar.loc[secilen_index]
            st.markdown("#### 📋 Kayıt Detayı")
            for sutun_adi in sonuclar.columns:
                deger = secili_satir[sutun_adi]
                st.markdown(f"**{sutun_adi}:** {deger if str(deger).strip() else '—'}")
