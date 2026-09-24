from io import StringIO
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from core.management.commands.runserver import _SshDbTunnel


class SshDbTunnelTests(SimpleTestCase):
	@patch('core.management.commands.runserver.socket.create_connection')
	def test_reuses_an_existing_tunnel(self, create_connection):
		create_connection.return_value.__enter__.return_value = object()
		stdout = StringIO()
		tunnel = _SshDbTunnel(stdout, StringIO())

		tunnel.start()

		self.assertIsNone(tunnel.process)
		self.assertIn('Tunel ja existente, reutilizando.', stdout.getvalue())

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

		tunnel.start()
		tunnel.stop()

		command = popen.call_args.args[0]
		self.assertEqual(command[:3], ['ssh', '-o', 'ExitOnForwardFailure=yes'])
		self.assertIn('127.0.0.1:5433:127.0.0.1:5432', command)
		self.assertEqual(command[-1], 'servidor')
		process.terminate.assert_called_once_with()
		process.wait.assert_called()
		self.assertIsNone(tunnel.process)
