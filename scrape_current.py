
import itertools as it
import re
import sqlite3

import icu

from scrape_elected import decap_name, start_session, title_match

nonword_match = re.compile(r'[^\w\s-]')
whitespace_match = re.compile(r'[\s-]+')

tr2ascii = icu.Transliterator.createInstance('tr-ASCII; lower')\
    .transliterate


def create_id(s):
    return whitespace_match.sub('-', nonword_match.sub('', tr2ascii(s)))


def tidy_up_row(row, url):
    area, first, last, party, *_ = (i.strip() for i in row)
    first, last = decap_name(title_match.sub('', first)), decap_name(last)
    return (create_id(' '.join((first, last))),
            first,
            last,
            party,
            '2013–',
            area,
            None,
            url)


def parse_table(doc, url):
    return (tidy_up_row((i.text_content() for i in v.xpath('./td')), url)
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
        while session.at_css('#ctl00_ContentPlaceHolder1_ASPxGridView1_LPV'):
            # Wait for the table to be updated
            ...


def main():
    session = start_session('Milletvekillerimiz1.aspx')
    with sqlite3.connect('data.sqlite') as c:
        c.execute('''\
CREATE TABLE IF NOT EXISTS data
    (id, first_name, last_name, party, term, area, image, source,
     UNIQUE (id, first_name, last_name, party, term, area, image, source))''')
        c.executemany('INSERT OR REPLACE INTO data VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                      it.chain.from_iterable(parse_pages(session)))

if __name__ == '__main__':
    main()
