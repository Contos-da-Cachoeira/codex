import os
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.core.management.base import CommandError
from django.test import SimpleTestCase

from core.management.commands.runserver import Command, _SshDbTunnel


class SshDbTunnelTests(SimpleTestCase):
	@patch('core.management.commands.runserver.socket.create_connection')
	def test_reuses_an_existing_tunnel(self, create_connection):
		create_connection.return_value.__enter__.return_value = object()
		stdout = StringIO()
		tunnel = _SshDbTunnel(stdout, StringIO())
		with patch.object(
			tunnel,
			'postgres_health_check',
			return_value=(True, ''),
		) as health_check:
			tunnel.start()

		self.assertIsNone(tunnel.process)
		self.assertFalse(tunnel.tunnel_created_by_us)
		health_check.assert_called_once_with()
		self.assertIn(
			'Tunel ja existente e validado, reutilizando.',
			stdout.getvalue(),
		)

	@patch('core.management.commands.runserver.time.sleep')
	@patch('core.management.commands.runserver.socket.create_connection')
	@patch('core.management.commands.runserver.subprocess.Popen')
	def test_starts_and_stops_only_the_created_process(
		self,
		popen,
		create_connection,
		sleep,
	):
		create_connection.side_effect = [OSError(), MagicMock()]
		process = popen.return_value
		process.poll.return_value = None
		stdout = StringIO()
		tunnel = _SshDbTunnel(stdout, StringIO())
		tunnel.postgres_health_check = MagicMock(return_value=(True, ''))

		tunnel.start()
		tunnel.stop()

		command = popen.call_args.args[0]
		self.assertEqual(command[:3], ['ssh', '-o', 'BatchMode=yes'])
		self.assertIn('127.0.0.1:5433:127.0.0.1:5432', command)
		self.assertEqual(command[-1], 'servidor')
		self.assertIn('BatchMode=yes', command)
		self.assertIn('ConnectTimeout=10', command)
		process.terminate.assert_called_once_with()
		process.wait.assert_called()
		self.assertIsNone(tunnel.process)
		self.assertFalse(tunnel.tunnel_created_by_us)

	@patch('core.management.commands.runserver.socket.create_connection')
	@patch('core.management.commands.runserver.subprocess.Popen')
	def test_reports_ssh_stderr_when_it_exits_before_port_is_open(
		self,
		popen,
		create_connection,
	):
		create_connection.side_effect = OSError()
		process = popen.return_value
		process.poll.return_value = 1

		def write_ssh_error(*args, **kwargs):
			kwargs['stderr'].write('Permission denied\n')
			kwargs['stderr'].flush()
			return process

		popen.side_effect = write_ssh_error
		tunnel = _SshDbTunnel(StringIO(), StringIO())
		with tempfile.TemporaryDirectory() as directory:
			tunnel.ssh_log_path = Path(directory) / 'ssh.log'

			with self.assertRaisesRegex(CommandError, 'Permission denied'):
				tunnel.start()

		self.assertTrue(tunnel.tunnel_created_by_us)

	@patch('core.management.commands.runserver.socket.create_connection')
	def test_rejects_an_invalid_process_on_the_existing_port(
		self,
		create_connection,
	):
		create_connection.return_value.__enter__.return_value = object()
		stdout = StringIO()
		tunnel = _SshDbTunnel(stdout, StringIO())
		tunnel.postgres_health_check = MagicMock(
			return_value=(False, 'connection refused')
		)

		with self.assertRaisesRegex(CommandError, 'nao e um tunel PostgreSQL valido'):
			tunnel.start()

		self.assertIsNone(tunnel.process)
		self.assertFalse(tunnel.tunnel_created_by_us)

	@patch('psycopg.connect')
	def test_postgres_health_check_executes_only_select_one(self, connect):
		connection = connect.return_value
		cursor = connection.cursor.return_value.__enter__.return_value
		cursor.fetchone.return_value = (1,)
		tunnel = _SshDbTunnel(StringIO(), StringIO())

		healthy, detail = tunnel.postgres_health_check()

		self.assertTrue(healthy)
		self.assertEqual(detail, '')
		cursor.execute.assert_called_once_with('SELECT 1')
		connection.close.assert_called_once_with()

	@patch('core.management.commands.runserver._SshDbTunnel')
	@patch('core.management.commands.runserver.DjangoRunserverCommand.run')
	def test_disabled_tunnel_keeps_django_default_flow(
		self,
		django_run,
		tunnel_class,
	):
		command = Command(stdout=StringIO(), stderr=StringIO())
		django_run.return_value = 'started'

		with patch.dict(
			os.environ,
			{'AUTO_SSH_DB_TUNNEL': 'False', 'RUN_MAIN': 'false'},
			clear=False,
		):
			result = command.run(use_reloader=True)

		self.assertEqual(result, 'started')
		tunnel_class.assert_not_called()
		django_run.assert_called_once_with(use_reloader=True)

	@patch('core.management.commands.runserver._SshDbTunnel')
	@patch('core.management.commands.runserver.DjangoRunserverCommand.run')
	def test_autoreloader_parent_does_not_manage_tunnel(
		self,
		django_run,
		tunnel_class,
	):
		command = Command(stdout=StringIO(), stderr=StringIO())
		django_run.return_value = 'started'

		with patch.dict(
			os.environ,
			{'AUTO_SSH_DB_TUNNEL': 'True', 'RUN_MAIN': 'false'},
			clear=False,
		):
			result = command.run(use_reloader=True)

		self.assertEqual(result, 'started')
		tunnel_class.assert_not_called()
		django_run.assert_called_once_with(use_reloader=True)

	@patch('core.management.commands.runserver._SshDbTunnel')
	@patch('core.management.commands.runserver.DjangoRunserverCommand.run')
	def test_autoreloader_child_manages_tunnel(
		self,
		django_run,
		tunnel_class,
	):
		command = Command(stdout=StringIO(), stderr=StringIO())
		tunnel = tunnel_class.return_value
		django_run.return_value = 'started'

		with patch.dict(
			os.environ,
			{'AUTO_SSH_DB_TUNNEL': 'True', 'RUN_MAIN': 'true'},
			clear=False,
		):
			result = command.run(use_reloader=True)

		self.assertEqual(result, 'started')
		tunnel.start.assert_called_once_with()
		tunnel.stop.assert_called_once_with()
		django_run.assert_called_once_with(use_reloader=True)

	@patch('core.management.commands.runserver._SshDbTunnel')
	@patch('core.management.commands.runserver.DjangoRunserverCommand.run')
	def test_noreload_process_manages_tunnel(
		self,
		django_run,
		tunnel_class,
	):
		command = Command(stdout=StringIO(), stderr=StringIO())
		tunnel = tunnel_class.return_value
		django_run.return_value = 'started'

		with patch.dict(
			os.environ,
			{'AUTO_SSH_DB_TUNNEL': 'True'},
			clear=False,
		):
			result = command.run(use_reloader=False)

		self.assertEqual(result, 'started')
		tunnel.start.assert_called_once_with()
		tunnel.stop.assert_called_once_with()
		django_run.assert_called_once_with(use_reloader=False)
