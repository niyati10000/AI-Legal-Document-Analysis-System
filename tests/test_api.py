import pytest
import hashlib
from database import ApiKey, LegalDocument, DocumentVersion, BiasReport, Summary

def test_api_status_polling_requires_login(client):
    """Test status polling route requires login redirect"""
    response = client.get('/api/v1/documents/1/status')
    assert response.status_code == 302 # Redirect to login

def test_api_status_polling_success(client, test_user, db):
    """Test status polling when logged in"""
    # Log in test_user
    client.post('/login', data={'email': 'test@example.com', 'password': 'password123'})
    
    doc = LegalDocument(user_id=test_user.id, title='Test doc', doc_type='NDA', current_status='analyzing')
    db.session.add(doc)
    db.session.commit()
    
    response = client.get(f'/api/v1/documents/{doc.id}/status')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'analyzing'
    assert data['title'] == 'Test doc'

def test_api_key_authentication(client, test_user, db):
    """Test Bearer API key verification on developer routes"""
    raw_key = "lex_live_abc123"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    new_key = ApiKey(user_id=test_user.id, key_hash=key_hash, name='Test Token')
    db.session.add(new_key)
    db.session.commit()
    
    # 1. Access without key
    response = client.get('/api/v1/documents')
    assert response.status_code == 401
    
    # 2. Access with invalid key
    response = client.get('/api/v1/documents', headers={'Authorization': 'Bearer wrongkey'})
    assert response.status_code == 401
    
    # 3. Access with valid key
    response = client.get('/api/v1/documents', headers={'Authorization': f'Bearer {raw_key}'})
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

def test_api_compare_versions_diff(client, test_user, db):
    """Test version difference comparison engine"""
    # Log in test_user
    client.post('/login', data={'email': 'test@example.com', 'password': 'password123'})
    
    doc = LegalDocument(user_id=test_user.id, title='Diff Test', doc_type='Agreement', current_status='completed')
    db.session.add(doc)
    db.session.flush()
    
    v1 = DocumentVersion(doc_id=doc.id, version_number=1, content='This is the original text of the agreement.')
    v2 = DocumentVersion(doc_id=doc.id, version_number=2, content='This is the updated text of the agreement with edits.')
    db.session.add_all([v1, v2])
    db.session.commit()
    
    response = client.post('/api/v1/document/diff', json={
        'doc_id': doc.id,
        'version_a': 1,
        'version_b': 2
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'diff_html' in data
    # Verify diff spans are rendered (diff_add should be present for the additions)
    assert 'diff_add' in data['diff_html'] or 'diff_chg' in data['diff_html']

def test_analysis_page_renders_completed(client, test_user, db):
    """Test that the analysis page renders correctly for a completed document (was crashing with 500)"""
    client.post('/login', data={'email': 'test@example.com', 'password': 'password123'})
    
    doc = LegalDocument(user_id=test_user.id, title='Analysis Page Test', doc_type='Contract', current_status='completed')
    db.session.add(doc)
    db.session.flush()
    
    v1 = DocumentVersion(doc_id=doc.id, version_number=1, content='Sample legal clause for testing the analysis page rendering.')
    db.session.add(v1)
    
    summary = Summary(doc_id=doc.id, summary_text='This is a test summary.', length_setting='medium')
    db.session.add(summary)
    
    bias = BiasReport(doc_id=doc.id, bias_score=0.45, bias_type='Gender', explanation='Detected gender bias indicators.')
    bias.categories = {'Gender': 0.45, 'Racial': 0.1, 'Socioeconomic': 0.05, 'Age': 0.0}
    db.session.add(bias)
    db.session.commit()
    
    response = client.get(f'/analysis/{doc.id}')
    assert response.status_code == 200
    assert b'Analysis Page Test' in response.data
    assert b'This is a test summary' in response.data

def test_analysis_page_renders_processing(client, test_user, db):
    """Test that the analysis page shows a polling loader for in-progress documents"""
    client.post('/login', data={'email': 'test@example.com', 'password': 'password123'})
    
    doc = LegalDocument(user_id=test_user.id, title='Queued Doc', doc_type='Agreement', current_status='analyzing')
    db.session.add(doc)
    db.session.commit()
    
    response = client.get(f'/analysis/{doc.id}')
    assert response.status_code == 200
    assert b'ANALYSIS PROGRESS' in response.data


