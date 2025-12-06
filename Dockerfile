# 1. Python'un resmi, hafif (slim) sürümünü temel al
FROM python:3.13.3-slim

# 2. Çalışma klasörünü ayarla
WORKDIR /app

# 3. Sistem bağımlılıklarını kur (GÜNCELLENDİ!)
# libgl1-mesa-glx yerine 'libgl1' ve 'libglib2.0-0' kullanıyoruz.
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 4. Kütüphane listesini kopyala ve kur
COPY requirements.txt .
# ÖNCE PyTorch'un CPU versiyonunu kur
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
# tüm kütüphaneleri kur
RUN pip install --no-cache-dir -r requirements.txt

# 5. Projenin geri kalan tüm kodlarını kopyala
COPY . .

# 6. Başlangıç komutu (Docker-compose bunu ezecek ama dursun)
CMD ["python", "main.py"]