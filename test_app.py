import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_homepage_loads(client):
    """Test that the landing page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200

def test_chat_page_loads(client):
    """Test that the chat page loads."""
    response = client.get('/chat')
    assert response.status_code == 200

def test_caregiver_page_loads(client):
    """Test that the caregiver page loads."""
    response = client.get('/caregiver')
    assert response.status_code == 200
