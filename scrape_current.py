
import itertools as it
import sqlite3

from scrape_elected import decap_name, start_session, title_match


def tidy_up_row(row):
    area, first, last, party, *_ = (i.strip() for i in row)
    return (decap_name(title_match.sub('', first)), decap_name(last),
            party, '2013', area)


def parse_table(doc):
    return (tidy_up_row(i.text_content() for i in v.xpath('./td'))
            for v in doc.xpath('//table[@id="ctl00_ContentPlaceHolder1_ASPxPageControl1_ASPxGridView3_DXMainTable"]'
                               '//tr[@class="dxgvDataRow"]'))


def parse_pages(session):
    while True:
        yield parse_table(session.document())
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
    (first_name, last_name, party, term, area,
     UNIQUE (first_name, last_name, party, term, area))''')
        c.executemany('INSERT OR REPLACE INTO data VALUES (?, ?, ?, ?, ?)',
                      it.chain.from_iterable(parse_pages(session)))

if __name__ == '__main__':
    main()
