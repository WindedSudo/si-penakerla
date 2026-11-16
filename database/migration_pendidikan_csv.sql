-- Migrasi format kolom lowongan.pendidikan ke CSV kanonik (mis. 'SMA/SMK,D3,D4/S1').
-- Format lama memakai garis miring bercampur dengan nama jenjang ('SMA/SMK/D3/S1') sehingga tidak bisa
-- difilter dengan benar. Jalankan SEKALI pada database lama. Nilai yang tidak dikenal dibiarkan.
UPDATE lowongan SET pendidikan = 'SMA/SMK,D3,D4/S1' WHERE pendidikan = 'SMA/SMK/D3/S1';
UPDATE lowongan SET pendidikan = 'D3,D4/S1'         WHERE pendidikan = 'D3/S1';
-- Nilai tunggal ('SMA/SMK', 'D4/S1', 'D3', ...) sudah sesuai format baru.
-- Periksa sisa nilai yang belum sesuai:
-- SELECT id, pendidikan FROM lowongan WHERE pendidikan NOT REGEXP '^(SD|SMP|SMA/SMK|D1|D2|D3|D4/S1|S2|S3)(,(SD|SMP|SMA/SMK|D1|D2|D3|D4/S1|S2|S3))*$';
