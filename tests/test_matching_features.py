from app.utils.matching import calculate_match_score, explain_match
from app.utils.chatbot import generate_reply
from app.utils.job_scraper import parse_feed


def test_skill_matching_uses_worker_skills_and_description():
    worker = {'pendidikan': 'D4/S1', 'kecamatan': 'Lamongan', 'keterampilan': 'Microsoft Excel'}
    job = {
        'pendidikan': 'SMA/SMK,D3,D4/S1',
        'lokasi': 'Lamongan, Jawa Timur',
        'posisi': 'Staf Administrasi',
        'deskripsi': 'Menguasai Microsoft Excel dan pengolahan data.'
    }
    skills = [{'nama_skill': 'Microsoft Excel'}]
    result = explain_match(worker, job, skills, [])
    assert result['total'] == 90
    assert 'microsoft excel' in result['matched_skills']
    assert calculate_match_score(worker, job, skills, []) == result['total']


def test_matching_does_not_treat_java_as_javascript():
    worker = {'pendidikan': 'SMA/SMK', 'kecamatan': 'Babat', 'keterampilan': ''}
    job = {'pendidikan': 'SMA/SMK', 'lokasi': 'Babat', 'posisi': 'Frontend Developer', 'deskripsi': 'Menguasai JavaScript'}
    result = explain_match(worker, job, [{'nama_skill': 'Java'}], [])
    assert result['matched_skills'] == []


def test_chatbot_uses_faq_without_api_credentials():
    reply, mode = generate_reply('Bagaimana cara menambah portofolio?')
    assert mode == 'faq'
    assert 'portofolio' in reply.lower()


def test_parse_rss_feed_extracts_job_fields():
    xml = b'''<?xml version="1.0"?><rss version="2.0"><channel><title>Contoh Portal</title>
    <item><title>Teknisi Komputer</title><link>https://jobs.example/teknisi</link>
    <guid>job-1</guid><description>Memperbaiki perangkat komputer.</description>
    <pubDate>Sat, 14 Nov 2026 08:00:00 GMT</pubDate></item></channel></rss>'''
    jobs = parse_feed(xml, 'Contoh Portal', 'https://feed.example/jobs.xml')
    assert len(jobs) == 1
    assert jobs[0]['posisi'] == 'Teknisi Komputer'
    assert jobs[0]['source_key'] == 'job-1'
    assert jobs[0]['url_lamaran'] == 'https://jobs.example/teknisi'
