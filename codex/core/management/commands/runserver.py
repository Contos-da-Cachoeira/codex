import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from django.contrib.staticfiles.management.commands.runserver import (
    Command as DjangoRunserverCommand,
)
from django.conf import settings
from django.core.management.base import CommandError


class _SshDbTunnel:
    local_host = '127.0.0.1'
    local_port = 5433
    remote_host = '127.0.0.1'
    remote_port = 5432
    wait_timeout = 15.0
    retry_interval = 0.2

    def __init__(self, stdout, stderr):
        self.ssh_alias = os.environ.get('SSH_DB_HOST', 'kiwiki')
        self.stdout = stdout
        self.stderr = stderr
        self.process = None
        self.tunnel_created_by_us = False
        self.ssh_log_path = Path.cwd() / '.ssh-db-tunnel.log'

    def port_is_open(self):
        try:
            with socket.create_connection(
                (self.local_host, self.local_port),
                timeout=0.25,
            ):
                return True
        except OSError:
            return False

    def postgres_health_check(self):
        """Validate PostgreSQL through the local SSH forwarding."""
        connection = None
        database = settings.DATABASES['default']
        password = database.get('PASSWORD')

        try:
            import psycopg

            connection = psycopg.connect(
                host=self.local_host,
                port=self.local_port,
                dbname=database['NAME'],
                user=database['USER'],
                password=password,
                connect_timeout=2,
            )
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
        except Exception as exc:
            detail = str(exc).strip() or exc.__class__.__name__
            return False, self._redact_secret(detail, password)
        finally:
            if connection is not None:
                connection.close()

        if result != (1,):
            return False, f'SELECT 1 retornou {result!r}, esperado (1,).'
        return True, ''

    @staticmethod
    def _redact_secret(value, secret):
        if secret:
            return value.replace(str(secret), '<redacted>')
        return value

    def _ssh_log(self):
        try:
            log = self.ssh_log_path.read_text(
                encoding='utf-8',
                errors='replace',
            ).strip()
        except OSError as exc:
            return f'nao foi possivel ler {self.ssh_log_path}: {exc}'

        if not log:
            return f'{self.ssh_log_path} esta vazio.'

        password = settings.DATABASES['default'].get('PASSWORD')
        log = self._redact_secret(log, password)
        if len(log) > 4000:
            log = f'...{log[-4000:]}'
        return log

    def _ssh_command_error(self, message):
        return CommandError(
            f'{message} Log SSH ({self.ssh_log_path}): {self._ssh_log()}'
        )

    def start(self):
        self.stdout.write('[DB Tunnel] Verificando tunel SSH...')
        if self.port_is_open():
            healthy, detail = self.postgres_health_check()
            if healthy:
                self.stdout.write(
                    '[DB Tunnel] Tunel ja existente e validado, reutilizando.'
                )
                return

            raise CommandError(
                '[DB Tunnel] 127.0.0.1:5433 esta ocupada, mas nao e um '
                f'tunel PostgreSQL valido. Falha no health check: {detail}'
            )

        self.stdout.write(
            f'[DB Tunnel] Abrindo 127.0.0.1:5433 -> {self.ssh_alias}:5432'
        )
        command = [
            'ssh',
            '-o',
            'BatchMode=yes',
            '-o',
            'ConnectTimeout=10',
            '-o',
            'ExitOnForwardFailure=yes',
            '-o',
            'ServerAliveInterval=30',
            '-o',
            'ServerAliveCountMax=3',
            '-N',
            '-L',
            '127.0.0.1:5433:127.0.0.1:5432',
            self.ssh_alias,
        ]
        creationflags = 0
        if sys.platform == 'win32':
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        try:
            with self.ssh_log_path.open(
                'w',
                encoding='utf-8',
                errors='replace',
            ) as ssh_log:
                self.process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=ssh_log,
                    creationflags=creationflags,
                )
        except OSError as exc:
            raise CommandError(
                f'[DB Tunnel] Nao foi possivel iniciar o SSH ou abrir o '
                f'log {self.ssh_log_path}: {exc}'
            ) from exc

        self.tunnel_created_by_us = True

        last_db_error = ''
        deadline = time.monotonic() + self.wait_timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise self._ssh_command_error(
                    '[DB Tunnel] O SSH encerrou antes do health check '
                    'PostgreSQL.'
                )

            if self.port_is_open():
                healthy, detail = self.postgres_health_check()
                if healthy:
                    self.stdout.write('[DB Tunnel] Tunel estabelecido.')
                    return
                last_db_error = detail

            time.sleep(self.retry_interval)

        timeout_message = (
            '[DB Tunnel] O health check PostgreSQL nao passou dentro de '
            f'{self.wait_timeout:.0f} segundos.'
        )
        if last_db_error:
            timeout_message += f' Ultimo erro PostgreSQL: {last_db_error}'
        raise self._ssh_command_error(timeout_message)

    def stop(self):
        if not self.tunnel_created_by_us or self.process is None:
            return

        self.stdout.write('[DB Tunnel] Encerrando tunel SSH.')
        process = self.process
        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        finally:
            self.process = None
            self.tunnel_created_by_us = False


class Command(DjangoRunserverCommand):
    def run(self, **options):
        if os.environ.get('AUTO_SSH_DB_TUNNEL', '').lower() not in {
            '1',
            'true',
            'yes',
            'on',
        }:
            return super().run(**options)

        use_reloader = options.get('use_reloader', True)
        is_reloader_child = os.environ.get('RUN_MAIN') == 'true'
        should_manage_tunnel = (
            not use_reloader
            or is_reloader_child
        )

        if not should_manage_tunnel:
            return super().run(**options)

        tunnel = _SshDbTunnel(self.stdout, self.stderr)
        try:
            tunnel.start()
            return super().run(**options)
        finally:
            tunnel.stop()
