"""Prévia local da Wiki em SQLite temporário, independente do servidor de produção."""
import argparse
import os
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'codex'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'wiki.test_settings'
os.environ['AUTO_SSH_DB_TUNNEL'] = '0'
import django
django.setup()
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.runner import DiscoverRunner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8012)
    parser.add_argument('--duration',type=int,default=3600)
    args = parser.parse_args()
    runner = DiscoverRunner(verbosity=0,interactive=False)
    runner.setup_test_environment()
    database = runner.setup_databases()

    class Preview(StaticLiveServerTestCase):
        host = '127.0.0.1'
        port = args.port

    try:
        Preview.setUpClass()
        print(f'PREVIEW: {Preview.live_server_url}/wiki/documentos/ (SQLite temporário; sem contas ou saldos de produção)',flush=True)
        threading.Event().wait(args.duration)
    finally:
        Preview.tearDownClass()
        runner.teardown_databases(database)
        runner.teardown_test_environment()


if __name__ == '__main__':
    main()
