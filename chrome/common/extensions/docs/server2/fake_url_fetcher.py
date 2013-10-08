# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from functools import partial
import os

from future import Future
from local_file_system import LocalFileSystem


class _Response(object):
  def __init__(self, content=''):
    self.content = content
    self.headers = { 'content-type': 'none' }
    self.status_code = 200


class FakeUrlFetcher(object):
  def __init__(self, base_path):
    self._base_path = base_path

  def _ReadFile(self, filename):
    with open(os.path.join(self._base_path, filename), 'r') as f:
      return f.read()

  def _ListDir(self, directory):
    # In some tests, we need to test listing a directory from the HTML returned
    # from SVN. This reads an HTML file that has the directories HTML.
    if not os.path.isdir(os.path.join(self._base_path, directory)):
      return self._ReadFile(directory[:-1])
    files = os.listdir(os.path.join(self._base_path, directory))
    html = '<html><title>Revision: 00000</title>\n'
    for filename in files:
      if filename.startswith('.'):
        continue
      if os.path.isdir(os.path.join(self._base_path, directory, filename)):
        html += '<a>' + filename + '/</a>\n'
      else:
        html += '<a>' + filename + '</a>\n'
    html += '</html>'
    return html

  def FetchAsync(self, url):
    url = url.rsplit('?', 1)[0]
    return Future(value=self.Fetch(url))

  def Fetch(self, url):
    url = url.rsplit('?', 1)[0]
    result = _Response()
    if url.endswith('/'):
      result.content = self._ListDir(url)
    else:
      result.content = self._ReadFile(url)
    return result


class FakeURLFSFetcher(object):
  '''Use a file_system to resolve fake fetches. Mimics the interface of Google
  Appengine's urlfetch.
  '''
  @staticmethod
  def Create(file_system):
    return partial(FakeURLFSFetcher, file_system)

  @staticmethod
  def CreateLocal():
    return partial(FakeURLFSFetcher, LocalFileSystem(''))

  def __init__(self, file_system, base_path):
    self._base_path = base_path
    self._file_system = file_system

  def FetchAsync(self, url, **kwargs):
    return Future(value=self.Fetch(url))

  def Fetch(self, url, **kwargs):
    return _Response(
        self._file_system.ReadSingle(self._base_path + '/' + url, binary=True))
