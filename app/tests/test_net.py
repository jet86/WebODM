from django.test import TestCase
from app import net
import urllib3.util.connection as ul3conn
from unittest.mock import patch, MagicMock
import requests


class TestNet(TestCase):
    def setUp(self):
        pass

    def test_net_functions(self):
        from webodm import settings
        
        self.assertFalse(net.is_dns_resolution_problem(Exception("[Errno 11002] Lookup timed out")))
        settings.DNS_RESOLUTION_FALLBACK = True
        self.assertTrue(net.is_dns_resolution_problem(Exception("[Errno 11002] Lookup timed out")))
        self.assertFalse(net.is_dns_resolution_problem(Exception("Some other error")))
        
        self.assertFalse(net.patched)
        self.assertEqual(ul3conn.create_connection, net.create_connection_orig)

        # Success patch
        self.assertTrue(net.patch_dns_resolution())

        self.assertTrue(net.patched)
        self.assertEqual(ul3conn.create_connection, net.create_connection_custom_dns)

        # Already patched
        self.assertFalse(net.patch_dns_resolution())

        # Should affect all requests library calls
        r = requests.get("https://webodm.org")
        self.assertEqual(r.status_code, 200)
        self.assertTrue('webodm.org' in net.dns_cache)