# -*- coding: utf-8 -*-
import datetime, sys, ssl
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse
else:
    import urlparse

from lib.requests_toolbelt.adapters import host_header_ssl
from lib import doh
from platformcode import config, logger
import requests
from core import scrapertools
from core import db
from urllib3.poolmanager import PoolManager
from urllib3.util.ssl_ import create_urllib3_context
from urllib3.util import connection
from requests.adapters import HTTPAdapter

current_date = datetime.datetime.now()
CIPHERS = "ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384"
dns_providers = {'cloudflare': { 'host': '1.0.0.1', 'path' : '/dns-query'}, 'google': { 'host': '8.8.4.4', 'path' : '/resolve'}}

class CipherSuiteAdapter(HTTPAdapter):

    def __init__(self, domain, ssl_options=ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1, override_dns = True, ssl_ciphers = CIPHERS, **kwargs):
        self.ssl_options = ssl_options
        self.ssl_ciphers = ssl_ciphers
        super(CipherSuiteAdapter, self).__init__(**kwargs) 
        if override_dns:

            # hack[1/3] to patch urllib3 create connection
            if not hasattr(connection, 'original_create_connection'):
                connection.original_create_connection = connection.create_connection

            # hack[2/3] function that use doh for host name resolution
            def override_dns_connection(address, *args, **kwargs):
                """Wrap urllib3's create_connection to resolve the name elsewhere"""
                # resolve hostname to an ip address; use your own
                # resolver here, as otherwise the system resolver will be used.
                host, port = address
                hostname = self.getIp(host)
                if not hostname:
                    hostname = host #fallback
                    logger.debug("Override dns failed, fallback to normal dns resolver")

                return connection.original_create_connection((hostname, port), *args, **kwargs)

            # hack[3/3] patch urllib3 create connection with custom function
            connection.create_connection = override_dns_connection

    def flushDns(self, domain, **kwargs):
        del db['dnscache'][domain]

    def getIp(self, domain):
        cache = db['dnscache'].get(domain, {})
        ip = None
        if type(cache) != dict or (cache.get('datetime') and
                                   current_date - cache.get('datetime') > datetime.timedelta(hours=1)):
            cache = None

        if not cache:  # not cached
            try:
                cfg_provider = config.get_setting('resolver_dns_provider').lower()                
                provider = dns_providers[cfg_provider]
                logger.debug('selected ' + cfg_provider + 'dns provider with address ' + provider['host'] + ' and path ' + provider['path'] )
                
                ip = doh.query(domain, server = provider['host'], path= provider['path'], fallback=False) # fallback is not necessary here
                if ip is None or not len(ip): # resolver is not available or return no results
                    ip = None
                else:
                    ip = ip[0]
                    logger.info('Query DoH: ' + domain + ' = ' + str(ip))
                    # IPv6 address
                    if ':' in ip:
                        ip = '[' + ip + ']'
                    self.writeToCache(domain, ip)
            except Exception:
                import traceback
                logger.error(traceback.format_exc())
        else:
            ip = cache.get('ip')

        if ip:
            logger.info('Cache DNS: ' + domain + ' = ' + str(ip))
        else:
            logger.error('Failed to resolve hostname ' + domain + ', fallback to normal dns')
        return ip

    def writeToCache(self, domain, ip):
        db['dnscache'][domain] = {'ip': ip, 'datetime': current_date}

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = create_urllib3_context(ciphers=self.ssl_ciphers, cert_reqs=ssl.CERT_REQUIRED, options=self.ssl_options)
        self.poolmanager = PoolManager(*pool_args, ssl_context=ctx, **pool_kwargs)

    def send(self, request, flushedDns=False, **kwargs):
        try:
            return super(CipherSuiteAdapter, self).send(request, **kwargs)
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.exceptions.SSLError) as e:
            logger.info(e)
            try:
                parse = urlparse.urlparse(request.url)
            except:
                raise requests.exceptions.InvalidURL
            if parse.netloc:
                domain = parse.netloc
                logger.info('Request for ' + domain + ' failed')
                if not flushedDns:
                    logger.info('Flushing dns cache for ' + domain)
                    self.flushDns(domain, **kwargs)
                    return self.send(request, flushedDns=True, **kwargs)
        except Exception as e:
            logger.error(e)
            raise e
