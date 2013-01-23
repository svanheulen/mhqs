#!/usr/bin/python2

# Copyright 2012 Seth VanHeulen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

### configuration ###
port = 8080
quest_path = 'quests'
#####################

import BaseHTTPServer
import os

class MHP3rdHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        content = '<html><!--<GAME-STYLE></GAME-STYLE>--><body>'
        for quest in os.listdir(quest_path):
            q = os.path.join(quest_path, quest)
            content += '<form action="%s" download csum="%s" fsize="%s" method="post"><input type="submit" value="download: %s"></form>' % (quest, self._calc_csum(q), os.path.getsize(q), quest)
        content += '</body></html>'
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', len(content))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        try:
            f = open(os.path.join(quest_path, os.path.basename(self.path)), 'rb')
        except:
            self.send_error(404, "Not Found")
        self.send_response(200)
        self.send_header('Content-type', 'application/octet-stream')
        f.seek(0, 2)
        self.send_header('Content-Length', f.tell())
        f.seek(0)
        self.end_headers()
        self.wfile.write(f.read())
        f.close()

    def _calc_csum(self, q):
        f = open(q)
        temp = f.read()
        f.close()
        csum = 0
        for i in temp:
            csum += ord(i)
            csum &= 0xffffffff
        return csum & 0xffff

httpd = BaseHTTPServer.HTTPServer(('', port), MHP3rdHTTPRequestHandler)
httpd.serve_forever()
