
import itertools as it
import sqlite3

import dryscrape


def parse_table(doc):
    return (tuple(i.text_content().strip() for i in v.xpath('./td'))
            for v in doc.xpath('//table[@id="ctl00_ContentPlaceHolder1_ASPxGridView1_DXMainTable"]'
                               '//tr[@class="dxgvDataRow"]'))


def parse_pages(session):
    while True:
        yield parse_table(session.document())
        page = session.at_xpath('//td[@class="dxpPageNumber dxpCurrentPageNumber"]'
                                '/following-sibling::td[@class="dxpPageNumber"]')
        if not page:
            break
        page.click()
        while session.at_css('#ctl00_ContentPlaceHolder1_ASPxGridView1_LPV'):
            # Wait for the table to be updated
            ...

    page = session.at_xpath('//td[@class="dxpPageNumber"]')
    page and page.click()    # Take us back to the 1st page
    while session.at_css('#ctl00_ContentPlaceHolder1_ASPxGridView1_LPV'):
        ...


def main():
    session = dryscrape.Session(base_url='http://www.cm.gov.nc.tr/')
    session.set_attribute('auto_load_images', False)
    session.visit('Secimler.aspx')

    with sqlite3.connect('data.sqlite') as c:
        c.execute('''\
CREATE TABLE IF NOT EXISTS data
    (first_name, last_name, party, election_year, area,
     UNIQUE (first_name, last_name, party, election_year, area))''')
        while True:
            c.executemany('INSERT OR REPLACE INTO data VALUES (?, ?, ?, ?, ?)',
                          it.chain.from_iterable(parse_pages(session)))
            year = session.at_xpath('//select[@name="ctl00$ContentPlaceHolder1$DropDownList1"]'
                                    '/option[@selected="selected"]/following-sibling::option')
            if not year:
                return
            year.select_option()

if __name__ == '__main__':
    main()
