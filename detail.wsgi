#!/usr/bin/env python3

from wsgiref.simple_server import make_server
from webob import Request
from cgi import escape
import mysql.connector
from mysql.connector import errorcode
import os


def get_connection():
    connection = None
    try:
        username = ''
        password = ''
        for line in open(os.path.dirname(os.path.abspath(__file__)) + '/.database-username', 'r'):
            username = line.strip()
            break
        for line in open(os.path.dirname(os.path.abspath(__file__)) + '/.database-password', 'r'):
            password = line.strip()
            break

        connection = mysql.connector.connect(user=username, password=password, database='opentaal')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("ERROR: Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("ERROR: Database does not exists")
        else:
            print("ERROR: Other error %s" % err)
    else:
        print("ERROR: more serious error")
#FIXME        connection.close()

    return connection

def decode_judgement(judgement, alternative):
    status = ''
    if judgement.islower():
        status = 'kandidaat '

    if judgement.upper() == 'K':
        if alternative == '':
            return '%sgekeurd basiswoord (%s)' % (status, judgement)
        else:
            return '%sgekeurd basiswoord en flexie (%s)' % (status, judgement)
    elif judgement.upper() == 'B':
        return '%sonkeurbaar basiswoord (%s)' % (status, judgement)
    elif judgement.upper() == 'F':
        return '%sonkeurbare flexie (%s)' % (status, judgement)
    elif judgement.upper() == 'H':
        return '%shoofdletterschrijfwijze (%s)' % (status, judgement)
    elif judgement.upper() == 'X':
        if alternative == '-':
            return '%sniet geschikt voor collectie (%s)' % (status, judgement)
        else:
            return '%sfoute spelling (%s)' % (status, judgement)
    elif judgement.upper() == 'D':
        return '%sdeel van een woord (%s)' % (status, judgement)
    else:
        return 'ERROR status=%s judgement%s' % (status, judgement)


def detail_app(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Woorddetails - OpenTaal</title>
    <link rel="stylesheet" href="jquery.mobile-1.4.4.min.css">
    <link rel="icon" href="favicon.ico" />
    <script src="jquery-2.1.1.min.js"></script>
    <script src="jquery.mobile-1.4.4.min.js"></script>
</head>
<body style="font-variant-ligatures: none;"><!--TODO ligaturen uitzetten -->
<div data-role="page">
<div data-role="header" class="jqm-header">
    <h1>OpenTaal</h1>
    <h2>Woorddetails</h2>
</div><!-- /header -->

<div role="main" class="ui-content jqm-content">
<div id="word" class="ui-body-d ui-content">
'''
    word = ''
    info = ''
    if environ['REQUEST_METHOD'] == 'POST':
        req = Request(environ)
#        word = unicode(req.params.get('name', 'default')).encode('utf-8') ## escape(...)
        word = req.params.get('word', '').strip()

        query = "SELECT * FROM details WHERE word = %s"
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (word, ))

        next_version = ''
        version_2_10 = ''
        version_2_00 = ''
        version_1_10 = ''
        version_1_00 = ''
        ntg1996 = ''
        egb = 0
        base_word = ''
        alternatief = ''
        woordtype = ''
        exclude_spell_checker = 0
        temporal_qualifier = 0
        found = False

        for (a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12) in cursor:
            next_version = a1
            version_2_10 = a2
            version_2_00 = a3
            version_1_10 = a4
            version_1_00 = a5
            ntg1996 = a6
            egb = a7
            base_word = a8
            alternative = a9
            word_type = a10
            exclude_spell_checker = a11
            temporal_qualifier = a12
            found = True

        cursor.close()
        connection.close()

        info += '<h3>woord</h3><p><div style="font-family:courier;">%s</div></p>\n' % word
        if found:
            info += '<h3>oordeel</h3><p>%s</p>\n' % decode_judgement(next_version, alternative)
            if next_version.upper() == 'F' or next_version.upper() == 'K' and base_word != '':
                if base_word == '':
                    info += '''<h3>basiswoord</h3>
<font color="red">er is nog geen basiswoord opgegeven</a>\n'''
                else:
                    info += '''<h3>basiswoord</h3>
  <form action="detail.wsgi" method="post">
  <a href="javascript:;" onclick="parentNode.submit();"><div style="font-family:courier;">%s</div></a>
  <input type="hidden" name="word" value="%s"/>
  </form>\n''' % (base_word, base_word)

                if next_version.upper() in ('K', 'B', 'F') and alternative != '':
                    info += '<h3>alternatief</h3><div style="font-family:courier;">%s</div>\n' % alternative
                elif next_version.upper() == 'X' and alternative != '-':
                    info += '<h3>correctie</h3><div style="font-family:courier;">%s</div>\n' % alternative
                elif next_version.upper() == 'D':
                    info += '<h3>voorbeelden</h3><div style="font-family:courier;">%s</div>\n' % alternative.replace(';', '; ')
                elif next_version.upper() == 'H':
                    info += '<h3>normale versie</h3><div style="font-family:courier;">%s</div>\n' % alternative

                if word_type != '':
                    info += '<h3>woordtype</h3>%s\n' % word_type
        else:
            info += '<h3>woord zit niet in collectie</h3>'

    html += '<form action="detail.wsgi" method="post" class="ui-filterable">'
    if word == '':
        html += '<input name="word" id="word" autofocus placeholder="Voer het gezochte woord in" required type=search data-clear-btn="true" />'
    else:
        html += '<input name="word" id="word" autofocus placeholder="Voer het gezochte woord in" required type=search data-clear-btn="true" value="%s" />' % word
    html += '<input data-theme="b" value="Zoek" type="submit" />'
    html += '</form>'
#    html += '<ul id="autocomplete" data-role="listview" data-inset="true" data-filter="true" data-input="#word"></ul>'

    ## FIXME generic-family:monospace
    if info != '':
        html += info

    html += '''
    <div data-role="collapsible-set" data-theme="b">
                    <div data-role="collapsible" data-collapsed="true">
                        <h3>Colofon</h3>
                        <small>De getoonde gegevens zijn eigendom van Stichting OpenTaal en volgende de <a target="_blank" href="http://www.opentaal.org/licentie">licenties</a> BSD (herziene versie) en Creative Commons Naamsvermelding 3.0. Het ontwerp en de ontwikkeling van deze zoekinterface is mogelijk gemaakt door <a target="_blank" href="http://hellebaard.nl">Hellebaard</a>.</small>
                    </div>
                </div>
</div><!-- /word -->
</div><!-- /main -->
</div><!-- /page -->
</body>
</html>'''
    return [html.encode('utf-8')]


def application(environ, start_response):
    return detail_app(environ, start_response)

if __name__ == '__main__':
    httpd = make_server('', 8000, detail_app)
    print("Serving on port 8000...")
    httpd.serve_forever()
