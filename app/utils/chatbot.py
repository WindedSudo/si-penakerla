"""Asisten karier dengan penyedia OpenAI-compatible opsional dan fallback FAQ lokal."""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _faq_reply(message):
    text = (message or '').lower()
    if any(word in text for word in ('lowongan', 'pekerjaan', 'kerja', 'loker', 'cari kerja')):
        return ('Untuk mencari pekerjaan, buka menu **Lowongan** lalu pilih urutan **Paling Cocok**. '
                'Periksa posisi, lokasi, pendidikan, dan tenggat sebelum melamar. '
                'Lowongan eksternal tersedia pada menu **Lowongan Eksternal** dan proses lamar dilakukan di situs sumber.')
    if any(word in text for word in ('portofolio', 'portfolio', 'proyek', 'project')):
        return ('Tambahkan karya yang relevan pada menu **Keahlian & Portofolio**. Sertakan judul, ringkasan hasil, '
                'tahun, dan tautan publik seperti GitHub atau Behance. Jangan memasukkan dokumen rahasia perusahaan.')
    if any(word in text for word in ('skill', 'keahlian', 'keterampilan', 'kemampuan')):
        return ('Kelola keahlian pada menu **Keahlian & Portofolio**. Tambahkan nama skill, kategori, tingkat penguasaan, '
                'dan lama pengalaman secara jujur. Skill ini dipakai sebagai salah satu dasar pencocokan lowongan.')
    if any(word in text for word in ('cv', 'resume', 'lamaran', 'profil')):
        return ('Lengkapi profil, keahlian, dan pengalaman kerja terlebih dahulu. Setelah itu buka **CV Builder** '
                'untuk melihat serta mencetak CV. Perkembangan status lamaran dapat dilihat pada menu **Lamaran Saya**.')
    if any(word in text for word in ('wawancara', 'interview')):
        return ('Persiapan wawancara: pelajari perusahaan dan posisi, siapkan contoh pengalaman dengan metode STAR '
                '(Situasi, Tugas, Aksi, Hasil), datang tepat waktu, dan siapkan pertanyaan tentang pekerjaan. '
                'Jangan mengarang pengalaman atau sertifikasi.')
    if any(word in text for word in ('cocok', 'matching', 'skor')):
        return ('Skor kecocokan pada SI-PENAKERLA merupakan estimasi berbasis data pendidikan, skill, lokasi, '
                'dan pengalaman yang tercantum di profil. Skor tinggi bukan jaminan diterima; baca persyaratan '
                'lowongan dan pastikan profil tetap akurat.')
    return ('Saya Asisten Karier SI-PENAKERLA. Saya dapat membantu menjelaskan pencarian lowongan, kecocokan pekerjaan, '
            'profil, CV, portofolio, skill, dan persiapan wawancara. Apa yang ingin kamu tanyakan?')


def generate_reply(message, profile=None, api_key=None, api_url=None, model=None):
    """Kirim konteks non-sensitif ke model AI bila dikonfigurasi; selain itu gunakan FAQ."""
    profile = profile or {}
    if not (api_key and api_url and model):
        return _faq_reply(message), 'faq'

    # Jangan kirim NIK, tanggal lahir, alamat lengkap, email, atau dokumen CV ke penyedia AI.
    safe_context = {
        'pendidikan': profile.get('pendidikan'),
        'kecamatan': profile.get('kecamatan'),
        'keahlian': [
            {
                'nama_skill': item.get('nama_skill'),
                'kategori': item.get('kategori'),
                'tingkat': item.get('tingkat'),
                'pengalaman_tahun': float(item.get('pengalaman_tahun') or 0),
            }
            for item in profile.get('keahlian', [])[:30]
        ],
        'pengalaman': [
            {'posisi': item.get('posisi'), 'tahun_mulai': item.get('tahun_mulai'),
             'tahun_selesai': item.get('tahun_selesai')}
            for item in profile.get('pengalaman', [])[:10]
        ],
    }
    payload = {
        'model': model,
        'temperature': 0.4,
        'max_tokens': 500,
        'messages': [
            {
                'role': 'system',
                'content': (
                    'Kamu adalah Asisten Karier SI-PENAKERLA untuk pencari kerja di Kabupaten Lamongan. '
                    'Jawab dalam Bahasa Indonesia dengan ringkas, ramah, dan praktis. Bantu pencarian kerja, '
                    'penyesuaian CV, portofolio, skill, kecocokan lowongan, dan wawancara. Jangan menjamin '
                    'penerimaan kerja, jangan mengarang informasi lowongan, dan sarankan verifikasi ke perusahaan. '
                    'Jangan meminta NIK, kata sandi, OTP, atau data pribadi sensitif. Konteks profil yang boleh '
                    'digunakan (tanpa identitas pribadi): ' + json.dumps(safe_context, ensure_ascii=False)
                )
            },
            {'role': 'user', 'content': message}
        ]
    }
    request = Request(
        api_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        method='POST'
    )
    try:
        with urlopen(request, timeout=20) as response:
            result = json.loads(response.read(1024 * 1024).decode('utf-8'))
        answer = result['choices'][0]['message']['content'].strip()
        if answer:
            return answer[:6000], 'ai'
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, IndexError, TypeError):
        pass
    return ('Layanan AI sedang tidak dapat dihubungi. ' + _faq_reply(message), 'faq')
