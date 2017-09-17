import os.path
import logging
import requests

from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor
from . import center, progress, util


class InvalidLoginException(Exception):
    pass


class RequestFailedException(Exception):
    pass


class AccessDeniedException(RequestFailedException):
    pass


class NebulaClient(object):
    _token = None
    _sess = None

    def __init__(self):
        self._sess = requests.Session()

    def _call(self, path, method='POST', skip_login=False, check_code=False, **kwargs):
        url = center.settings['nebula_link'] + path

        if not skip_login and not self._token:
            if not self.login():
                raise InvalidLoginException()

        if self._token:
            headers = kwargs.setdefault('headers', {})
            headers['X-KN-TOKEN'] = self._token

        try:
            result = self._sess.request(method, url, **kwargs)
        except requests.RequestException:
            logging.exception('Failed to send %s request to %s!' % (method, path))
            return None

        if check_code and result.status_code != 200:
            raise RequestFailedException()

        return result

    def login(self, user=None, password=None):
        if not user:
            user = center.settings['neb_user']
            password = center.settings['neb_password']

        result = self._call('login', skip_login=True, data={
            'user': user,
            'password': password
        })

        if result.status_code != 200:
            return False

        data = result.json()
        if data['result']:
            self._token = data['token']
            return True
        else:
            return False

    def register(self, user, password, email):
        self._call('register', skip_login=True, check_code=True, data={
            'name': user,
            'password': password,
            'email': email
        })

        return True

    def reset_password(self, user):
        self._call('reset_password', skip_login=True, check_code=True, data={'user': user})
        return True

    def get_editable_mods(self):
        result = self._call('mod/editable', 'GET', check_code=True)
        return result.json()['mods']

    def _upload_mod_logos(self, mod):
        logo_chk = None
        if mod.logo_path and os.path.isfile(mod.logo_path):
            _, logo_chk = util.gen_hash(mod.logo_path)
            self.upload_file('logo', mod.logo_path)

        tile_chk = None
        if mod.tile_path and os.path.isfile(mod.tile_path):
            _, tile_chk = util.gen_hash(mod.tile_path)
            self.upload_file('tile', mod.tile_path)

        return logo_chk, tile_chk

    def create_mod(self, mod):
        logo_chk, tile_chk = self._upload_mod_logos(mod)

        self._call('mod/create', check_code=True, json={
            'id': mod.mid,
            'title': mod.title,
            'type': mod.mtype,
            'folder': os.path.basename(mod.folder),
            'logo': logo_chk,
            'tile': tile_chk,
            'members': []
        })
        return True

    def update_mod(self, mod):
        # TODO: Check if these actually changed
        logo_chk, tile_chk = self._upload_mod_logos(mod)

        self._call('mod/update', check_code=True, json={
            'id': mod.mid,
            'title': mod.title,
            'logo': logo_chk,
            'tile': tile_chk,
            'members': [center.settings['neb_user']]
        })
        return True

    def create_release(self, mod):
        result = self._call('mod/release', check_code=True, json=mod.get())
        data = result.json()
        if not data:
            raise RequestFailedException()

        if data['result']:
            return True

        if data.get('reason') == 'unauthorized':
            raise AccessDeniedException()

        raise RequestFailedException(data.get('reason'))

    def upload_file(self, name, path, fn=None):
        _, checksum = util.gen_hash(path)

        result = self._call('upload/check', check_code=True, data={'checksum': checksum})
        data = result.json()
        if data.get('result'):
            # Already uploaded
            return True

        hdl = open(path, 'rb')
        enc = MultipartEncoder({
            'checksum': checksum,
            'file': ('upload', hdl, 'application/octet-stream')
        })

        enc_len = enc.len

        def cb(monitor):
            progress.update(monitor.bytes_read / enc_len, 'Uploading %s...' % name)

        monitor = MultipartEncoderMonitor(enc, cb)
        self._call('upload/file', data=monitor, headers={
            'Content-Type': monitor.content_type
        }, check_code=True)

        return True
