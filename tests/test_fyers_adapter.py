import os
import json
import time

from src.api import fyers_adapter as fa


def test_refresh_parsing(monkeypatch):
    # backup existing token file
    token_file = fa.TOKEN_FILE
    backup = None
    if os.path.exists(token_file):
        with open(token_file, 'rb') as f:
            backup = f.read()
    try:
        # write an expired token (expires_in negative -> in the past)
        fa.save_token_full('old_access', 'refresh_tok', -10)

        class MockResp:
            def json(self):
                return {'data': {'access_token': 'new_access', 'refresh_token': 'new_refresh', 'expires_in': 3600}}

        def mock_post(url, json=None, headers=None, timeout=None):
            return MockResp()

        monkeypatch.setattr('requests.post', mock_post)

        token = fa._get_valid_access_token()
        assert token == 'new_access'

        # ensure token was persisted
        with open(token_file, 'r', encoding='utf-8') as f:
            dd = json.load(f)
        assert dd.get('access_token') == 'new_access'
        assert dd.get('refresh_token') == 'new_refresh'
    finally:
        # restore backup
        if backup is not None:
            with open(token_file, 'wb') as f:
                f.write(backup)
        else:
            try:
                os.remove(token_file)
            except Exception:
                pass


def test_exchange_auth_code_parses_nested(monkeypatch):
    # ensure exchange_auth_code handles nested 'data' key and persists tokens
    token_file = fa.TOKEN_FILE
    backup = None
    if os.path.exists(token_file):
        with open(token_file, 'rb') as f:
            backup = f.read()
    try:
        class MockResp:
            def json(self):
                return {'data': {'access_token': 'ex_access', 'refresh_token': 'ex_refresh', 'expires_in': 120}}

        monkeypatch.setattr('requests.post', lambda url,
                            json=None, headers=None, timeout=None: MockResp())
        res = fa.exchange_auth_code('dummycode')
        assert res.get('access_token') == 'ex_access'
        # ensure persisted
        with open(token_file, 'r', encoding='utf-8') as f:
            dd = json.load(f)
        assert dd.get('access_token') == 'ex_access'
    finally:
        if backup is not None:
            with open(token_file, 'wb') as f:
                f.write(backup)
        else:
            try:
                os.remove(token_file)
            except Exception:
                pass
