import os
import socket
import subprocess
import sys
import time

from django.contrib.staticfiles.management.commands.runserver import (
    Command as DjangoRunserverCommand,
)
from django.core.management.base import CommandError


class _SshDbTunnel:
    local_host = '127.0.0.1'
    local_port = 5433
    remote_host = '127.0.0.1'
    remote_port = 5432
    ssh_alias = 'servidor'
    wait_timeout = 10.0
    retry_interval = 0.2

    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr
        self.process = None

    def port_is_open(self):
        try:
            with socket.create_connection(
                (self.local_host, self.local_port),
                timeout=0.25,
            ):
                return True
        except OSError:
            return False

    def start(self):
        self.stdout.write('[DB Tunnel] Verificando tunel SSH...')
        if self.port_is_open():
            self.stdout.write('[DB Tunnel] Tunel ja existente, reutilizando.')
            return

        self.stdout.write(
            '[DB Tunnel] Abrindo 127.0.0.1:5433 -> servidor:5432'
        )
        command = [
            'ssh',
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
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creationflags,
            )
        except OSError as exc:
            raise CommandError(
                f'[DB Tunnel] Nao foi possivel iniciar o SSH: {exc}'
            ) from exc

        deadline = time.monotonic() + self.wait_timeout
        while time.monotonic() < deadline:
            if self.port_is_open():
                self.stdout.write('[DB Tunnel] Tunel estabelecido.')
                return

            if self.process.poll() is not None:
                error_output = self.process.communicate()[1].strip()
                detail = f': {error_output}' if error_output else ''
                raise CommandError(
                    f'[DB Tunnel] O SSH encerrou antes de abrir a porta{detail}'
                )

            time.sleep(self.retry_interval)

        raise CommandError(
            '[DB Tunnel] A porta 127.0.0.1:5433 nao ficou disponivel a tempo.'
        )

    def stop(self):
        if self.process is None or self.process.poll() is not None:
            return

        self.stdout.write('[DB Tunnel] Encerrando tunel SSH.')
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        finally:
            self.process = None


class Command(DjangoRunserverCommand):
    def run(self, **options):
        if os.environ.get('AUTO_SSH_DB_TUNNEL', '').lower() not in {
            '1',
            'true',
            'yes',
            'on',
        }:
            return super().run(**options)

        tunnel = _SshDbTunnel(self.stdout, self.stderr)
        try:
            tunnel.start()
            return super().run(**options)
        finally:
            tunnel.stop()
