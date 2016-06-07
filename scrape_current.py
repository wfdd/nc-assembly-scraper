
import csv
import datetime as dt
import itertools as it
import re
import sqlite3
import subprocess
import urllib.request
import sys

import dryscrape
import icu

with open('gender.csv') as file:
    ids_to_gender = {i['id']: i['gender'] for i in csv.DictReader(file)}

with open('photos.csv') as file:
    ids_to_photo = {i['id']: i['photo'] for i in csv.DictReader(file)}

birth_date_match = re.compile(r'^\s*(?:'
                              r'(?P<d>\d{1,2}\s+\w+\s+\d{4})|'
                              r'(?P<y>\d{4})\s+(?:senesinde|yılında)'
                              r')[^\.]+doğdu',
                              re.MULTILINE)
nonword_match = re.compile(r'[^\w\s-]')
title_match = re.compile(r'(?:D[RrTt]|Prof)\.\s*')
whitespace_match = re.compile(r'[\s-]+')

decap_name = icu.Transliterator.createInstance('tr-title').transliterate
tr2lcascii = icu.Transliterator.createInstance('tr-ASCII; lower').transliterate

parse_date = icu.DateFormat.createDateInstance(icu.DateFormat.LONG,
                                               icu.Locale('tr')).parse

def create_id(s):
    return whitespace_match.sub('-', nonword_match.sub('', tr2lcascii(s)))


def parse_bio_doc(url):
    with urllib.request.urlopen(url) as file:
        doc = file.read()
    text = subprocess.run(('antiword', '-w 0', '-'),
                          input=doc, stdout=subprocess.PIPE).stdout.decode()

    birth_date = birth_date_match.search(text)
    if birth_date:
        birth_date = birth_date.groupdict()
        if birth_date['y']:
            birth_date = birth_date['y']
        else:
            try:
                birth_date = dt.date.fromtimestamp(parse_date(birth_date['d']))\
                    .isoformat()
            except icu.ICUError:
                print('Unable to parse ' + repr(birth_date), file=sys.stderr)
                birth_date = None
    name = text.replace('[pic]', '').strip().partition('\n')[0]
    name = decap_name(title_match.sub('', ' '.join(name.split())))
    return birth_date, name


def parse_table(doc, url):
    return (prepare_row(v.xpath('./td'), url)
            for v in doc.xpath('//table[@id="ctl00_ContentPlaceHolder1_ASPxPageControl1_ASPxGridView3_DXMainTable"]'
                               '//tr[@class="dxgvDataRow"]'))


def parse_pages(session):
    while True:
        yield parse_table(session.document(), session.url())
        page = session.at_xpath('//table[@id="ctl00_ContentPlaceHolder1_ASPxPageControl1_ASPxGridView3_DXPagerBottom"]'
                                '//td[@class="dxpPageNumber dxpCurrentPageNumber"]'
                                '/following-sibling::td[@class="dxpPageNumber"]')
        if not page:
            break
        page.click()
        while session.at_css('#ctl00_ContentPlaceHolder1_ASPxPageControl1_'
                             'ASPxGridView3_LPV'):
            # Wait for the table to be updated
            ...


def prepare_row(row, url):
    area, _, _, party, _ = (i.text_content().strip() for i in row)
    birth_date, name = parse_bio_doc(row[-1].xpath('.//a/@href')[0])
    id_ = create_id(name)
    return (id_,
            name,
            birth_date,
            ids_to_gender[id_],
            party,
            '8',
            area,
            ids_to_photo.get(id_, None),
            url)


def start_session(page):
    session = dryscrape.Session(base_url='http://www.cm.gov.nc.tr/')
    session.set_attribute('auto_load_images', False)
    session.visit(page)
    return session


def main():
    session = start_session('Milletvekillerimiz1.aspx')
    with sqlite3.connect('data.sqlite') as c:
        c.execute('''\
CREATE TABLE IF NOT EXISTS data
(id, name, birth_date, gender, 'group', term, area, image, source,
 UNIQUE (id, name, birth_date, gender, 'group', term, area, image, source))''')
        c.executemany('INSERT OR REPLACE INTO data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      it.chain.from_iterable(parse_pages(session)))

if __name__ == '__main__':
    main()
