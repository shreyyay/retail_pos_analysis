"""Send XML requests to Tally's HTTP server on localhost:9000."""
import logging
from datetime import date
import requests
import config as cfg

logger = logging.getLogger(__name__)
TIMEOUT = 60


def _post(xml_body: str) -> str:
    resp = requests.post(cfg.TALLY_URL, data=xml_body.encode("utf-8"),
                         headers={"Content-Type": "application/xml"}, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text


def _voucher_xml(vtype: str, from_date: date, to_date: date) -> str:
    return f"""<ENVELOPE>
 <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
 <BODY><EXPORTDATA><REQUESTDESC>
  <REPORTNAME>Voucher Register</REPORTNAME>
  <STATICVARIABLES>
   <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   <SVFROMDATE>{from_date.strftime('%Y%m%d')}</SVFROMDATE>
   <SVTODATE>{to_date.strftime('%Y%m%d')}</SVTODATE>
   <VOUCHERTYPENAME>{vtype}</VOUCHERTYPENAME>
  </STATICVARIABLES>
 </REQUESTDESC></EXPORTDATA></BODY>
</ENVELOPE>"""


def fetch_sales_vouchers(from_date: date, to_date: date) -> str:
    return _post(_voucher_xml("Sales", from_date, to_date))


def fetch_purchase_vouchers(from_date: date, to_date: date) -> str:
    return _post(_voucher_xml("Purchase", from_date, to_date))


def fetch_payment_vouchers(from_date: date, to_date: date) -> str:
    return _post(_voucher_xml("Payment", from_date, to_date))


def fetch_receipt_vouchers(from_date: date, to_date: date) -> str:
    return _post(_voucher_xml("Receipt", from_date, to_date))


def fetch_stock_summary(as_of_date: date) -> str:
    xml = f"""<ENVELOPE>
 <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
 <BODY><EXPORTDATA><REQUESTDESC>
  <REPORTNAME>Stock Summary</REPORTNAME>
  <STATICVARIABLES>
   <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   <SVTODATE>{as_of_date.strftime('%Y%m%d')}</SVTODATE>
  </STATICVARIABLES>
 </REQUESTDESC></EXPORTDATA></BODY>
</ENVELOPE>"""
    return _post(xml)


def fetch_ledger_balances(as_of_date: date) -> str:
    xml = f"""<ENVELOPE>
 <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
 <BODY><EXPORTDATA><REQUESTDESC>
  <REPORTNAME>Group Summary</REPORTNAME>
  <STATICVARIABLES>
   <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   <SVTODATE>{as_of_date.strftime('%Y%m%d')}</SVTODATE>
  </STATICVARIABLES>
 </REQUESTDESC></EXPORTDATA></BODY>
</ENVELOPE>"""
    return _post(xml)
