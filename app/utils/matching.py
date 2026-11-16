import re
from app.utils.referensi import PENDIDIKAN_LEVEL, baca_pendidikan

_STOP_WORDS = {
    'dan', 'atau', 'dengan', 'untuk', 'dari', 'pada', 'yang', 'di', 'ke', 'ini',
    'the', 'and', 'for', 'with', 'from', 'to', 'a', 'an', 'of', 'in', 'on',
    'kerja', 'pekerjaan', 'mampu', 'memiliki', 'minimal', 'lebih', 'baik',
    'serta', 'pengalaman', 'tahun', 'posisi', 'sebagai', 'dapat', 'akan'
}


def _normalise_skills(pencari, skills=None):
    values = []
    raw = (pencari.get('keterampilan') or '')
    for value in re.split(r'[,|;\n]+', raw):
        value = value.strip().lower()
        if value and len(value) > 1:
            values.append(value)
    for item in skills or []:
        value = item.get('nama_skill') if isinstance(item, dict) else item
        value = (value or '').strip().lower()
        if value and len(value) > 1:
            values.append(value)
    # Hilangkan duplikat sambil mempertahankan urutan.
    return list(dict.fromkeys(values))


def _contains_phrase(text, phrase):
    phrase = phrase.strip().lower()
    if not phrase:
        return False
    # Batas kata menghindari contoh: skill 'java' ikut cocok dengan 'javascript'.
    return bool(re.search(r'(?<![a-z0-9])' + re.escape(phrase) + r'(?![a-z0-9])', text))


def explain_match(pencari, lowongan, skills=None, pengalaman=None):
    """Rincian skor kecocokan 0-100 berbasis aturan, bukan model machine learning.

    Bobot: pendidikan 30%, skill 45%, lokasi 15%, pengalaman relevan 10%.
    """
    job_text = ' '.join([
        str(lowongan.get('posisi') or ''),
        str(lowongan.get('deskripsi') or '')
    ]).lower()

    # 1. Pendidikan (maksimum 30)
    education_score = 0
    pencari_pend = baca_pendidikan(pencari.get('pendidikan'))
    diterima = baca_pendidikan(lowongan.get('pendidikan'))
    if pencari_pend and diterima:
        level = PENDIDIKAN_LEVEL[pencari_pend[0]]
        level_diterima = [PENDIDIKAN_LEVEL[p] for p in diterima]
        if pencari_pend[0] in diterima:
            education_score = 30
        elif level > max(level_diterima):
            education_score = 26
        elif level == min(level_diterima) - 1:
            education_score = 11
        elif min(level_diterima) < level < max(level_diterima):
            education_score = 15

    # 2. Skill terhadap posisi dan uraian pekerjaan (maksimum 45)
    worker_skills = _normalise_skills(pencari, skills)
    matched_skills = [skill for skill in worker_skills if _contains_phrase(job_text, skill)]
    skill_score = 0
    if worker_skills:
        ratio = len(matched_skills) / len(worker_skills)
        skill_score = int(45 * min(ratio * 1.5, 1.0))

    # 3. Lokasi (maksimum 15)
    worker_location = (pencari.get('kecamatan') or '').lower().strip()
    job_location = (lowongan.get('lokasi') or '').lower().strip()
    location_score = 0
    if worker_location and job_location:
        if worker_location in job_location or job_location in worker_location:
            location_score = 15

    # 4. Relevansi pengalaman kerja (maksimum 10)
    experience_score = 0
    best_experience_ratio = 0.0
    for item in pengalaman or []:
        experience_text = ' '.join([
            str(item.get('posisi') or ''),
            str(item.get('deskripsi') or '')
        ]).lower()
        terms = {
            token for token in re.findall(r'[a-z0-9+#.]{3,}', experience_text)
            if token not in _STOP_WORDS
        }
        if terms:
            matched_terms = sum(1 for token in terms if _contains_phrase(job_text, token))
            best_experience_ratio = max(best_experience_ratio, matched_terms / len(terms))
    if best_experience_ratio:
        experience_score = int(10 * min(best_experience_ratio * 1.5, 1.0))

    total = min(education_score + skill_score + location_score + experience_score, 100)
    reasons = []
    if matched_skills:
        reasons.append('Skill cocok: ' + ', '.join(matched_skills[:8]))
    if education_score:
        reasons.append('Pendidikan memenuhi atau mendekati kriteria')
    if location_score:
        reasons.append('Lokasi sesuai')
    if experience_score:
        reasons.append('Pengalaman relevan ditemukan')
    if not reasons:
        reasons.append('Lengkapi data pendidikan, skill, dan pengalaman untuk hasil yang lebih akurat')

    return {
        'total': total,
        'pendidikan': education_score,
        'skill': skill_score,
        'lokasi': location_score,
        'pengalaman': experience_score,
        'matched_skills': matched_skills,
        'reasons': reasons,
    }


def calculate_match_score(pencari, lowongan, skills=None, pengalaman=None):
    """Kembalikan skor ringkas agar tetap kompatibel dengan pemanggil lama."""
    return explain_match(pencari, lowongan, skills, pengalaman)['total']


def get_matched_lowongan(pencari, lowongan_list, skills=None, pengalaman=None):
    """Tambahkan skor/rincian match ke lowongan dan urutkan berdasarkan skor."""
    for lowongan in lowongan_list:
        breakdown = explain_match(pencari, lowongan, skills, pengalaman)
        lowongan['match_score'] = breakdown['total']
        lowongan['match_breakdown'] = breakdown
    return lowongan_list
