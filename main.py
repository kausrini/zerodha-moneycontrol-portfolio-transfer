import argparse
import logging
from pathlib import Path
from collections import defaultdict
import csv
import xml.etree.ElementTree as ElementTree
from model import ZerodhaContractNote
from const import ISIN_LOOKUP, STOCK_NAME_LOOKUP

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')
logger = logging.getLogger()


# Shameless copy and paste from StackOverflow
def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


def get_zerodha_contract_xml_filename():
    parser = argparse.ArgumentParser("Argument Parser")
    parser.add_argument("input_filename", help="File name of the zerodha xml contract")
    parser.add_argument("input_file_path", help="File path of the zerodha xml contract")
    args = parser.parse_args()
    return args.input_file_path, args.input_filename + '.xml'


def parse_zerodha_contracts_xml_file(xml_filename):
    contract_note_list = []

    try:
        tree = ElementTree.parse(xml_filename.resolve())
    except ElementTree.ParseError:
        logger.error(f'Unable to parse the file {xml_filename.resolve()}')
        raise IOError

    root = tree.getroot()
    contracts = etree_to_dict(root[0])['contracts']['contract']

    for contract in contracts:
        contract_note_list.append(ZerodhaContractNote(contract))

    return contract_note_list


def initialize_csv_row():
    row = {
        'ISIN Code': '',
        'Enter Full/Partial Stock Name': 'Mandatory',
        'Date': 'Mandatory',
        'Transaction Type (Enter Either Buy or Sell)': 'Mandatory',
        'Exchange': 'Mandatory',
        'Qty': 'Mandatory',
        'Purchase/Sell price per share': 'Mandatory',
        'Total Amount': 'Optional',
        'Total Charges (Brokerage +Other charges)': 'Optional',
        'Net Amount': 'Optional',
        'Note': 'Optional',
        'Order Number': 'Optional',
        'Transaction Number': 'Optional',
        'Contract Note Number': 'Optional',
        'Brokerage': 'Optional',
        'Other Charges (All Charges other than brokerage charges)': 'Optional',
        'Service Tax/GST': 'Optional',
        'STT': 'Optional',
        'Exchange Charges': 'Optional',
        'Stamp Duty': 'Optional',
        'SEBI Charges': 'Optional'
    }
    return row


def build_csv_dict_rows(contract_notes):
    csv_dict_rows = [initialize_csv_row()]

    for contract_note in contract_notes:
        for trade in contract_note.trades:
            row = {}

            try:
                row['ISIN Code'] = ISIN_LOOKUP[trade.security_ticker]
                row['Enter Full/Partial Stock Name'] = STOCK_NAME_LOOKUP[trade.security_ticker]
            except KeyError:
                raise KeyError(f'Unable to find the lookup value for the ticker {trade.security_ticker}')

            row['Date'] = contract_note.trade_date
            row['Transaction Type (Enter Either Buy or Sell)'] = trade.transaction_type
            row['Exchange'] = trade.exchange
            row['Qty'] = trade.quantity
            row['Purchase/Sell price per share'] = trade.gross_rate
            row['Total Amount'] = trade.net_total
            row['Total Charges (Brokerage +Other charges)'] = round(contract_note.total_charges*trade.trade_percentage_of_contract, 2)
            row['Net Amount'] = round(row['Total Amount'] + row['Total Charges (Brokerage +Other charges)'], 2)
            row['Order Number'] = trade.order_no
            row['Transaction Number'] = trade.trade_no
            row['Contract Note Number'] = contract_note.contract_note_no
            row['Brokerage'] = round(contract_note.brokerage*trade.trade_percentage_of_contract, 2)
            row['Other Charges (All Charges other than brokerage charges)'] = round(contract_note.non_brokerage_charges*trade.trade_percentage_of_contract, 2)
            row['Service Tax/GST'] = round((contract_note.central_gst + contract_note.state_gst + contract_note.integrated_gst)*trade.trade_percentage_of_contract, 2)
            row['STT'] = round(contract_note.securities_transaction_tax*trade.trade_percentage_of_contract, 2)
            row['Exchange Charges'] = round(contract_note.exchange_transaction_charges*trade.trade_percentage_of_contract, 2)
            row['Stamp Duty'] = round(contract_note.stamp_duty*trade.trade_percentage_of_contract, 2)
            row['SEBI Charges'] = round(contract_note.sebi_turnover_fees*trade.trade_percentage_of_contract, 2)

            csv_dict_rows.append(row)

    return csv_dict_rows


def write_to_moneycontrol_csv(contract_notes, output_file_path):
    headers = ['ISIN Code', 'Enter Full/Partial Stock Name', 'Date', 'Transaction Type (Enter Either Buy or Sell)',
               'Exchange', 'Qty', 'Purchase/Sell price per share', 'Total Amount',
               'Total Charges (Brokerage +Other charges)', 'Net Amount', 'Note', 'Order Number',
               'Transaction Number', 'Contract Note Number', 'Brokerage',
               'Other Charges (All Charges other than brokerage charges)', 'Service Tax/GST', 'STT', 'Exchange Charges',
               'Stamp Duty', 'SEBI Charges'
               ]

    # List of dictionary objects for output csv file rows
    csv_dict = build_csv_dict_rows(contract_notes)

    with open(output_file_path.resolve(), 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(csv_dict)


if __name__ == "__main__":
    input_file_path, input_filename = get_zerodha_contract_xml_filename()
    input_file = Path(input_file_path, input_filename)
    parsed_contract_notes = parse_zerodha_contracts_xml_file(input_file)
    output_filename = 'Moneycontrol-output.csv'
    output_file = Path(input_file_path, output_filename)
    write_to_moneycontrol_csv(parsed_contract_notes, output_file)
