import torch                        # PyTorch Deep Learning kütüphanesidir
import cv2                          # OpenCV Görüntü işleme kütühanesidir
import numpy as np                  # Sayısal Python (Numerical Python): Sayısal işlemler yaparken kullanılır
from PIL import Image               # Pillow (Python Imaging Library): Görüntüleri açma, döndürme, kırpma ve boyutlandırma
from torchvision import transforms  # TorchVision kütüpünün transforms modülü: Data Augmentation, ToTensor, Normalizasyon
import os
import streamlit as st 


# modeli kur
@st.cache_resource
def load_model():
    auth_header = os.environ.get("Authorization")
    if auth_header:
        del os.environ["Authorization"]
    
    model = torch.hub.load("pytorch/vision:main", "deeplabv3_mobilenet_v3_large", pretrained=True, trust_repo=True) # pytorch/vision reposundan Hem encoder hem decoder işlemleri yapan DeepLabV3 için olan Resnet101 modelini kur

    if auth_header:
        os.environ["Authorization"] = auth_header
    
    model.eval() # modeli değerlendirme modu olan evaluation moduna al

    return model

# Remove Background : Data Preprocessing | Model Prediction | Masking 
def remove_background(model, input_source):
    """
    Ana işlem akışını yönetir: Resmi açar, ön işler, modelden geçirir,
    maskeyi oluşturur ve son şeffaf resmi üretir.
    """

    # Streamlitten gelen img dosyası gelirse bazen okuma imleci sonda olabilir, başa alıyoruz.
    if hasattr(input_source, 'seek'):
        input_source.seek(0)

    # görüntüyü açar ve görüntüyü 3 kanallı RGB formatına getirir
    input_image = Image.open(input_source).convert("RGB")

    # --- RESMİ KÜÇÜLTME ---
    max_size = (1024, 1024)
    if input_image.size[0] > max_size[0] or input_image.size[1] > max_size[1]:
        input_image.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Image Preprocessing (Resim Önişleme)
    preprocess = transforms.Compose([
        transforms.ToTensor(), # resmi Tensor formatına çevirir ve min max normalization yapar (x/255)
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]) # İstatistiksel normalizasyon.
    ])

    # preprocess işlemlerini resme uygula
    input_tensor = preprocess(input_image) 

    # PyTorch'a kaç adet resim vereceğimizi kanala gömerek söylüyoruz. Görsel bir tensör genelde şu boyutlardadır: (C, H, W).
    # C → Kanal sayısı (örneğin RGB için 3), H → Yükseklik (Height), W → Genişlik (Width).
    # Ama PyTorch modelleri tek bir resmi bile batch (grup) olarak ister. -> (B, C, H, W)
    # B = batch size (örneğin 32 resimlik grup). Eğer sadece 1 resim varsa bile B = 1 olmalı.
    input_batch = input_tensor.unsqueeze(0)

    # eğer GPU kullanılabilirse ise modeli orada, değilse CPU'da çalıştır
    device = "cuda" if torch.cuda.is_available() else "cpu" 
    model.to(device)
    input_batch = input_batch.to(device) # modele verilecek resmi, modelin bulunduğu yerle aynı yere taşı

    # Model Prediction / Model Inference (hesaplama verimliliğini Gradianları kapatma tekniği ile)
    with torch.no_grad(): # Gradyanları Kapatarak işlemleri yap
        """
        Derin öğrenme modelleri, eğitim sırasında ağırlıklarını güncellemek için gerekli olan gradyanları (türevleri)(Gradient Descent) 
        hesaplamak zorundadır. Bu hesaplama, büyük miktarda bellek (RAM/VRAM) ve işlem gücü (CPU/GPU) tüketir.

        torch.no_grad() bağlam yöneticisi, PyTorch'a bu blok içindeki tüm tensör işlemleri için gradyan hesaplamasını durdurmasını söyler.

        Amaç: Model eğitimi bittiğinde ve siz sadece modelin tahminini (çıkarımını) kullanmak istediğinizde, 
        gradyanlara ihtiyacınız yoktur. Bu bloğu kullanarak:

        - Bellek tüketimini azaltırsınız.
        - İşlem hızını artırırsınız. (Gradyan hesaplaması için harcanan zamanı ortadan kaldırırsınız.)

        Yani model training'de görevli Gradient Descentlerin Model Prediction'da açık kalmasının bir mantığı yok. Kapat!
        """

        output = model(input_batch)["out"][0] # model tahmini yapılıyor
    
    # yukarıdaki "output" değişkeni, tüm pikseller için hangi sınıfa ait olabileceğine dair olasılıkları tutan bir dizi gibi
    # buradaki işlemle, her bir pikselin içerisindeki en yüksek olasılığı alıyoruz. 
    # yani bu piksel %10 kedi, %3 araba, %87 koltuk ise, bunun belirtildiği listede argmax ile max olanı alıyoruz
    # bize tüm olasılıklar değil, en yüksek olanı lazım  
    output_predictions = output.argmax(0)

    # Tahminleri CPU'ya taşıyıp NumPy dizisine çevir
    mask = output_predictions.byte().cpu().numpy()

    # Arka plan genellikle COCO ve Pascal VOC veri setlerinde 0 ID'sine sahiptir.
    # 0 dışındaki tüm sınıflar bir nesne anlamına gelir (insan, araba, kedi, sandalye, vs.)
    # Bu yüzden mask != 0 olan pikselleri ön plan olarak alıyoruz.
    # Etiketi 0 olan yeri 0, yani siyah yap. Etiketi sıfırdan farklı olan yerleri(arkaplan olmayan heryeri) 255, yani beyaz yap
    foreground_mask = np.where(mask != 0, 255, 0).astype(np.uint8) # mask idsi sıfır olmayan herşeyi al. sıfır olanlar kalsın

    # Orijinal resmin boyutlarına uyacak şekilde maskeyi yeniden boyutlandır
    resized_mask = cv2.resize(foreground_mask, input_image.size)
    
    # Şeffaf ön planı oluştur
    foreground = make_transparent_foreground(input_image, resized_mask)

    return Image.fromarray(foreground)

# Fotoğraftaki Arka planı şeffaf yapar, ön planı görünür bırakır.
def make_transparent_foreground(pic, mask): # parametreler;   pic: input resmi       mask: maskeleme
    """
    Bir fotoğrafın arkaplanını şeffaf, ön planını görünür yapar.
    Bu işlem, maske adı verilen siyah-beyaz bir görüntü kullanılarak gerçekleştirilir.
    Maske, fotoğrafın ön planını beyaz yaparak görünür kılarken, arkaplanını planını siyah yaparak şeffaf hale getirir
    """

    # resmi numpy arrayine çevir
    img_np = np.array(pic)

    # RGB'yi RGBA'ya çevir. RGB = 3 kanal → (Kırmızı, Yeşil, Mavi)   RGBA = 4 kanal → (Kırmızı, Yeşil, Mavi, Alfa). Alfa kanalı saydamlık bilgisidir
    rgba_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2RGBA)

    # Alfa kanalını tamamen şeffaf yap. Yani resimdeki her pikselin saydamlık değeri sıfır (tamamen görünmez) hale geliyor. 
    # Mantık şu: "Her yer, aksi ispat edilene kadar arka plandır (şeffaftır)." Bu, bir sonraki adımda işimizi çok kolaylaştırır. 
    # Artık sadece ön planın nerede olduğunu bulup orayı opak hale getirmemiz yeterli olacak.
    rgba_img[:,:,3] = 0

    # Maskede beyaz olan yerlere opaklık veriyoruz
    rgba_img[:,:,3][mask==255]=255
    # mask == 255 demek, birazdan yazacağımız modelin önemli diye belirttiği yerler demek. 
    # oraları 255 yap, saydam değil opak yap dedik. yani burada aslında background kaldırılacak. nasıl?
    # modelin önemli dediği yerlerin opaklığını 0'dan 255'e çıkaracağız. 0 = şeffaf, 255 = opak

    return rgba_img