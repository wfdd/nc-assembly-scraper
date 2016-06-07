
import itertools as it
import re
import sqlite3
import subprocess
import urllib.request

import dryscrape
import icu

nonword_match = re.compile(r'[^\w\s-]')
title_match = re.compile(r'(?:D[RrTt]|Prof)\.\s*')
whitespace_match = re.compile(r'[\s-]+')

decap_name = icu.Transliterator.createInstance('tr-title').transliterate
tr2lcascii = icu.Transliterator.createInstance('tr-ASCII; lower').transliterate


def create_id(s):
    return whitespace_match.sub('-', nonword_match.sub('', tr2lcascii(s)))


def extract_name(url):
    with urllib.request.urlopen(url) as file:
        doc = file.read()
    text = subprocess.run(('antiword', '-w 0', '-'),
                          input=doc, stdout=subprocess.PIPE).stdout.decode()
    name = text.replace('[pic]', '').strip().partition('\n')[0]
    name = decap_name(title_match.sub('', ' '.join(name.split())))
    return name


def tidy_up_row(row, url):
    area, _, _, party, _ = (i.text_content().strip() for i in row)
    name = extract_name(row[-1].xpath('.//a/@href')[0])
    return (create_id(name),
            name,
            party,
            '8',
            area,
            None,
            url)


def parse_table(doc, url):
    return (tidy_up_row(v.xpath('./td'), url)
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
(id, name, 'group', term, area, image, source,
 UNIQUE (id, name, 'group', term, area, image, source))''')
        c.executemany('INSERT OR REPLACE INTO data VALUES (?, ?, ?, ?, ?, ?, ?)',
                      it.chain.from_iterable(parse_pages(session)))

if __name__ == '__main__':
    main()
