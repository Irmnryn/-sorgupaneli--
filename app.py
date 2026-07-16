import random
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
    /* Giriş ekranı kutusu (st.container(border=True) için) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 2px solid #4f46e5 !important;
        border-radius: 16px !important;
        background-color: #f5f6ff !important;
        padding: 0.5rem 0.5rem 1.5rem 0.5rem !important;
    }
    .giris-baslik {
        text-align: center;
        font-size: 1.3rem;
        font-weight: 700;
        margin: 0.8rem 0 1.2rem 0;
    }
    .giris-soru {
        text-align: center;
        font-size: 1.6rem;
        font-weight: 700;
        color: #4f46e5;
        margin-bottom: 0.6rem;
    }
    /* Giriş ekranındaki sayı kutusunu da ortala ve büyüt */
    div[data-testid="stNumberInput"] input {
        font-size: 1.4rem !important;
        text-align: center !important;
        border-radius: 12px !important;
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


# ==============================================================
# 0) GİRİŞ EKRANI — Google ile Giriş + Captcha Doğrulama
#    (Sorgu panelinde önceden 8 aramada bir çıkan captcha,
#     artık burada, girişten önce tek seferlik yapılıyor.)
# ==============================================================
if "giris_captcha_dogrulandi" not in st.session_state:
    st.session_state.giris_captcha_dogrulandi = False
if "giris_captcha_a" not in st.session_state:
    st.session_state.giris_captcha_a = random.randint(1, 20)
    st.session_state.giris_captcha_b = random.randint(1, 20)

if not st.user.is_logged_in:
    st.markdown('<div class="baslik">📁 Sorgu Paneli</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="altbaslik">Devam etmek için önce doğrulamayı tamamlayın, ardından Google ile giriş yapın</div>',
        unsafe_allow_html=True,
    )

    sol, orta, sag = st.columns([1, 1.3, 1])
    with orta:
        with st.container(border=True):
            dogrulandi = st.session_state.giris_captcha_dogrulandi

            # ---- ÜSTTE: Google ile Devam Et (doğrulanana kadar pasif) ----
            st.markdown('<div class="giris-baslik">🔑 Giriş Yap</div>', unsafe_allow_html=True)
            if st.button(
                "Google ile Devam Et",
                use_container_width=True,
                type="primary",
                disabled=not dogrulandi,
            ):
                st.login()
            if not dogrulandi:
                st.caption("Bu buton, aşağıdaki doğrulamayı tamamlayınca aktif olacak.")
            else:
                st.success("Doğrulama tamamlandı ✅ — artık giriş yapabilirsiniz.")

            st.divider()

            # ---- ALTTA: Güvenlik Doğrulaması ----
            if not dogrulandi:
                st.markdown('<div class="giris-baslik">🔒 Güvenlik Doğrulaması</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="giris-soru">{st.session_state.giris_captcha_a} '
                    f'+ {st.session_state.giris_captcha_b} = ?</div>',
                    unsafe_allow_html=True,
                )
                with st.form("giris_captcha_formu"):
                    cevap_metni = st.text_input(
                        "Cevabınız",
                        key="giris_captcha_cevap",
                        placeholder="Cevabı buraya yazın",
                        label_visibility="collapsed",
                    )
                    dogrula_butonu = st.form_submit_button(
                        "Doğrula", use_container_width=True
                    )

                if dogrula_butonu:
                    dogru_cevap = st.session_state.giris_captcha_a + st.session_state.giris_captcha_b
                    girilen_temiz = (cevap_metni or "").strip()
                    try:
                        girilen_sayi = int(girilen_temiz)
                    except ValueError:
                        girilen_sayi = None

                    if girilen_sayi is not None and girilen_sayi == dogru_cevap:
                        st.session_state.giris_captcha_dogrulandi = True
                        st.rerun()
                    else:
                        st.error("Cevap yanlış, lütfen tekrar deneyin.")
                        # Yeni soru üret
                        st.session_state.giris_captcha_a = random.randint(1, 20)
                        st.session_state.giris_captcha_b = random.randint(1, 20)

    st.stop()

# ------------------------------------------------------------
# GİRİŞ YAPILDI — kullanıcı bilgisi ve çıkış butonu (kenar çubuğu)
# ------------------------------------------------------------
with st.sidebar:
    kullanici_adi = getattr(st.user, "name", None) or getattr(st.user, "email", "Kullanıcı")
    st.write(f"👋 Hoş geldiniz, **{kullanici_adi}**")
    if st.button("Çıkış yap", use_container_width=True):
        st.logout()

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
# 2) SABİT ARAMA ÇUBUĞU (form: sadece 'Ara'ya basınca ya da Enter'a
#    basınca çalışır, her tuş vuruşunda değil — bu sayede arama sayısını
#    doğru sayabiliyoruz)
# ------------------------------------------------------------
st.write("")

if "arama_sayaci" not in st.session_state:
    st.session_state.arama_sayaci = 0
if "son_arama" not in st.session_state:
    st.session_state.son_arama = ""

with st.form("arama_formu", clear_on_submit=False):
    girilen_terim = st.text_input(
        "🔍 Arama",
        key="arama_kutusu",
        placeholder="Aramak istediğiniz firma / kişi / sicil no yazın... (büyük-küçük harf, boşluk önemli değil)",
        disabled=(yuklenen_dosya is None),
        label_visibility="collapsed",
    )
    ara_butonu = st.form_submit_button("Ara", disabled=(yuklenen_dosya is None))

if ara_butonu:
    st.session_state.son_arama = girilen_terim
    if girilen_terim:
        st.session_state.arama_sayaci += 1

arama_terimi = st.session_state.son_arama

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


def hucreyi_metne_cevir(deger):
    """Sayıları (özellikle telefon/sicil no gibi tam sayı olması gerekenleri)
    '3244540600.0' yerine '3244540600' şeklinde, boş hücreleri de '' olarak
    düzgün metne çevirir. Bu sayede tablo hem hatasız görüntülenir hem de
    sayılar çirkin görünmez."""
    if deger == "" or pd.isna(deger):
        return ""
    if isinstance(deger, float) and deger.is_integer():
        return str(int(deger))
    return str(deger)


# Streamlit'in tabloyu ekranda gösterebilmesi için (Arrow formatı), tüm
# hücreleri metne çeviriyoruz. Aksi halde bir sütunda hem sayı hem boş
# hücre (örn. telefon numarası sütunu) karışık olduğunda uygulama çöküyor.
df = df.map(hucreyi_metne_cevir)

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
