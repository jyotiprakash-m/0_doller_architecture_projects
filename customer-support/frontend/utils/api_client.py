"""
API Client — Reusable HTTP client for communicating with the FastAPI backend.
"""
import requests
import logging
import streamlit as st

logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


class APIClient:
    def __init__(self):
        self._token = None

    def set_token(self, token):
        self._token = token

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    def _get(self, path, params=None):
        try:
            r = requests.get(f"{BASE_URL}{path}", headers=self._headers(), params=params, timeout=30)
            if r.status_code == 401:
                st.session_state.token = None
                st.session_state.user = None
                return None
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Cannot connect to backend. Is the server running?")
            return None
        except Exception as e:
            logger.error(f"GET {path} failed: {e}")
            return None

    def _post(self, path, data=None, files=None):
        try:
            if files:
                headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
                r = requests.post(f"{BASE_URL}{path}", headers=headers, files=files, timeout=120)
            else:
                r = requests.post(f"{BASE_URL}{path}", headers=self._headers(), json=data, timeout=120)
            if r.status_code == 401:
                st.session_state.token = None
                st.session_state.user = None
                return None
            if r.status_code == 402:
                st.warning("💎 Insufficient credits. Please purchase more.")
                return None
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Cannot connect to backend. Is the server running?")
            return None
        except Exception as e:
            logger.error(f"POST {path} failed: {e}")
            return None

    def _delete(self, path):
        try:
            r = requests.delete(f"{BASE_URL}{path}", headers=self._headers(), timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"DELETE {path} failed: {e}")
            return None

    # --- Auth ---
    def login(self, email, password):
        return self._post("/api/auth/login", {"email": email, "password": password})

    def register(self, email, password, full_name=""):
        return self._post("/api/auth/register", {"email": email, "password": password, "full_name": full_name})

    def get_me(self):
        return self._get("/api/auth/me")

    # --- Knowledge Base ---
    def create_kb(self, name, description=""):
        return self._post("/api/kb", {"name": name, "description": description})

    def list_kbs(self):
        return self._get("/api/kb")

    def get_kb(self, kb_id):
        return self._get(f"/api/kb/{kb_id}")

    def upload_kb_document(self, kb_id, file):
        return self._post(f"/api/kb/{kb_id}/upload", files={"file": (file.name, file.getvalue(), file.type)})

    def list_kb_documents(self, kb_id):
        return self._get(f"/api/kb/{kb_id}/documents")

    def delete_kb_document(self, kb_id, doc_id):
        return self._delete(f"/api/kb/{kb_id}/documents/{doc_id}")

    def delete_kb(self, kb_id):
        return self._delete(f"/api/kb/{kb_id}")

    # --- Scenarios ---
    def generate_scenarios(self, kb_id, count=3):
        return self._post("/api/simulation/scenarios/generate", {"kb_id": kb_id, "count": count})

    def list_scenarios(self, kb_id=None):
        params = {"kb_id": kb_id} if kb_id else None
        return self._get("/api/simulation/scenarios", params=params)

    def create_scenario(self, data):
        return self._post("/api/simulation/scenarios", data)

    def delete_scenario(self, scenario_id):
        return self._delete(f"/api/simulation/scenarios/{scenario_id}")

    # --- Simulation ---
    def start_session(self, scenario_id):
        return self._post("/api/simulation/start", {"scenario_id": scenario_id})

    def send_response(self, session_id, message):
        return self._post(f"/api/simulation/{session_id}/respond", {"message": message})

    def end_session(self, session_id):
        return self._post(f"/api/simulation/{session_id}/end")

    def list_sessions(self, status=None):
        params = {"status": status} if status else None
        return self._get("/api/simulation/sessions", params=params)

    def get_session(self, session_id):
        return self._get(f"/api/simulation/sessions/{session_id}")

    # --- Evaluation ---
    def run_evaluation(self, session_id):
        return self._post(f"/api/evaluation/{session_id}")

    def get_evaluation(self, session_id):
        return self._get(f"/api/evaluation/{session_id}")

    def get_feedback(self, session_id):
        return self._get(f"/api/evaluation/{session_id}/feedback")

    def get_all_evaluations(self):
        return self._get("/api/evaluation/history/all")

    # --- Analytics ---
    def get_dashboard(self):
        return self._get("/api/analytics/dashboard")

    def get_progress(self):
        return self._get("/api/analytics/progress")

    def get_leaderboard(self):
        return self._get("/api/analytics/leaderboard")
