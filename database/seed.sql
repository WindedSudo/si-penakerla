-- Data dasar (akun demo, 2 perusahaan, 3 lowongan). Password: admin123 (admin) / password123 (lainnya).
-- Deadline dibuat relatif terhadap tanggal saat seed dijalankan supaya tidak basi.

INSERT INTO users (id, nama, email, password, role) VALUES 
(1, 'Administrator', 'admin@penakerla.local', '$2b$12$RZMrbzA3Auy1G0xFzT7F2ewuCGE885uHg788olxsWX3iehHAsLXhm', 'admin'),
(2, 'Budi Santoso', 'budi@example.com', '$2b$12$/FHJCcahYJou/oI6WaYauOvDkojbSKhvzNqXCrSValt9vOKo5m/my', 'pencari_kerja'),
(3, 'Siti Aminah', 'siti@example.com', '$2b$12$/FHJCcahYJou/oI6WaYauOvDkojbSKhvzNqXCrSValt9vOKo5m/my', 'pencari_kerja'),
(4, 'Ahmad Fauzi', 'ahmad@example.com', '$2b$12$/FHJCcahYJou/oI6WaYauOvDkojbSKhvzNqXCrSValt9vOKo5m/my', 'pencari_kerja'),
(5, 'PT Lamongan Jaya', 'hr@lamongan-jaya.com', '$2b$12$/FHJCcahYJou/oI6WaYauOvDkojbSKhvzNqXCrSValt9vOKo5m/my', 'perusahaan'),
(6, 'CV Maju Bersama', 'hr@majubersama.com', '$2b$12$/FHJCcahYJou/oI6WaYauOvDkojbSKhvzNqXCrSValt9vOKo5m/my', 'perusahaan');
INSERT INTO pencari_kerja (user_id, nik, tanggal_lahir, jenis_kelamin, alamat, kecamatan, pendidikan, keterampilan) VALUES
(2, '3524000000000001', '1995-05-10', 'Laki-laki', 'Jl. Merdeka No 1', 'Lamongan', 'D4/S1', 'Python, MySQL, PHP'),
(3, '3524000000000002', '1998-08-15', 'Perempuan', 'Jl. Sudirman No 2', 'Babat', 'D3', 'Ms Office, Accurate'),
(4, '3524000000000003', '2000-01-20', 'Laki-laki', 'Jl. Pahlawan No 3', 'Paciran', 'SMA/SMK', 'Mekanik, Otomotif');
INSERT INTO perusahaan (user_id, nama_perusahaan, alamat, kecamatan, email, telepon, status_verifikasi) VALUES
(5, 'PT Lamongan Jaya', 'Kawasan Industri Lamongan', 'Deket', 'hr@lamongan-jaya.com', '0322123456', 'terverifikasi'),
(6, 'CV Maju Bersama', 'Jl. Sunan Drajat', 'Lamongan', 'hr@majubersama.com', '0322654321', 'belum_diverifikasi');
INSERT INTO lowongan (perusahaan_id, posisi, deskripsi, pendidikan, lokasi, gaji, jumlah_kebutuhan, status, deadline) VALUES
(1, 'Operator Produksi', 'Mengoperasikan mesin produksi', 'SMA/SMK', 'Lamongan', 3000000.00, 5, 'aktif', DATE_ADD(CURDATE(), INTERVAL 60 DAY)),
(1, 'Staff Administrasi', 'Menangani administrasi kantor, Ms Office, pembukuan', 'D3,D4/S1', 'Lamongan', 3500000.00, 2, 'aktif', DATE_ADD(CURDATE(), INTERVAL 60 DAY)),
(1, 'Marketing Executive', 'Mencari klien baru, presentasi produk', 'SMA/SMK,D3,D4/S1', 'Lamongan', 4000000.00, 3, 'aktif', DATE_ADD(CURDATE(), INTERVAL 60 DAY));
INSERT INTO pengalaman_kerja (pencari_kerja_id, nama_perusahaan, posisi, tahun_mulai, tahun_selesai, deskripsi) VALUES
(1, 'PT Teknologi Nusantara', 'Junior Web Developer', 2020, 2022, 'Mengembangkan aplikasi web menggunakan PHP dan MySQL. Maintenance sistem internal.'),
(1, 'CV Digital Kreasi', 'Freelance Programmer', 2022, NULL, 'Membuat website company profile dan sistem informasi untuk UMKM.'),
(2, 'Toko Serba Ada', 'Staff Administrasi', 2021, 2023, 'Menangani pembukuan, surat-menyurat, dan pengelolaan data karyawan.');

INSERT INTO notifikasi (user_id, judul, pesan, link, kategori, dibaca, created_at) VALUES
(1, 'Selamat Datang', 'Selamat datang di SI-PENAKERLA sebagai Administrator.', '/admin/dashboard', 'sistem', FALSE, NOW()),
(2, 'Profil Belum Lengkap', 'Silakan lengkapi profil Anda untuk mulai melamar pekerjaan.', '/pencari/profile', 'sistem', FALSE, NOW()),
(2, 'Lowongan Baru 🆕', 'PT Lamongan Jaya membuka lowongan Operator Produksi di Lamongan.', '/pencari/lowongan', 'lowongan', FALSE, NOW()),
(5, 'Akun Terverifikasi ✅', 'Selamat! Akun perusahaan Anda telah diverifikasi.', '/perusahaan/lowongan', 'verifikasi', FALSE, NOW());
