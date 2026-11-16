-- Jalankan sekali pada database SI-PENAKERLA yang sudah berisi data.
-- Tidak menghapus tabel maupun data yang sudah ada.

CREATE TABLE IF NOT EXISTS keahlian_pencari (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pencari_kerja_id INT NOT NULL,
    nama_skill VARCHAR(100) NOT NULL,
    kategori VARCHAR(60),
    tingkat ENUM('Pemula', 'Menengah', 'Mahir', 'Ahli') NOT NULL DEFAULT 'Menengah',
    pengalaman_tahun DECIMAL(4,1) NOT NULL DEFAULT 0,
    UNIQUE KEY unique_skill_pencari (pencari_kerja_id, nama_skill),
    FOREIGN KEY (pencari_kerja_id) REFERENCES pencari_kerja(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS portofolio_kerja (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pencari_kerja_id INT NOT NULL,
    judul VARCHAR(150) NOT NULL,
    deskripsi TEXT,
    tautan VARCHAR(500),
    tahun YEAR,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pencari_kerja_id) REFERENCES pencari_kerja(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS lowongan_eksternal (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sumber VARCHAR(200) NOT NULL,
    source_key VARCHAR(255) NOT NULL,
    source_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    posisi VARCHAR(200) NOT NULL,
    perusahaan VARCHAR(200),
    deskripsi TEXT,
    lokasi VARCHAR(200),
    url_lamaran VARCHAR(1000) NOT NULL,
    tanggal_publikasi DATETIME,
    terakhir_diambil DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_external_hash (source_hash),
    INDEX idx_external_date (tanggal_publikasi, terakhir_diambil)
);
