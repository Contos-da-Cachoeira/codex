import hashlib

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError


def digest(file):
    checksum = hashlib.sha256()
    for chunk in iter(lambda: file.read(64 * 1024), b''):
        checksum.update(chunk)
    return checksum.hexdigest()


class Command(BaseCommand):
    help = 'Copy existing local media to SFTP without overwriting remote files.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Actually copy files.')

    def handle(self, *args, **options):
        if not getattr(settings, 'STORAGES', {}).get('default', {}).get('BACKEND', '').endswith('SFTPStorage'):
            raise CommandError('Configure SFTP storage before running this command.')
        pending = []
        for path in sorted(settings.MEDIA_ROOT.rglob('*')):
            if not path.is_file() or path.is_symlink():
                continue
            name = path.relative_to(settings.MEDIA_ROOT).as_posix()
            if default_storage.exists(name):
                with path.open('rb') as local, default_storage.open(name, 'rb') as remote:
                    if digest(local) != digest(remote):
                        raise CommandError(f'Different remote file: {name}. Nothing overwritten.')
                self.stdout.write(f'Already synchronized: {name}')
            else:
                pending.append((path, name))
        for path, name in pending:
            if options['apply']:
                with path.open('rb') as source:
                    saved = default_storage.save(name, File(source))
                if saved != name:
                    raise CommandError(f'Concurrent upload: saved as {saved}; expected {name}.')
                with path.open('rb') as local, default_storage.open(name, 'rb') as remote:
                    if digest(local) != digest(remote):
                        raise CommandError(f'Upload verification failed: {name}')
            self.stdout.write(f'{"Copied" if options["apply"] else "Would copy"}: {name}')
        self.stdout.write(self.style.SUCCESS(f'{len(pending)} file(s); apply={options["apply"]}'))
