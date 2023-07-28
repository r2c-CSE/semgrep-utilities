# Steps:
# 1. Read the json file
# 2. Convert the json file to pandas dataframe
# 3. Get the list of all column names from headers  
# 4. list of columns of interest to include in the report
# 5. Create a new dataframe with the columns of interest
# 6. Write the dataframe to excel file
# 7. Create a HTML report from the dataframe

import getopt
import sys
import json
import pandas as pd
from pandas import json_normalize
import os
from datetime import datetime
import logging

def generate_html_sast(df_high: pd.DataFrame, df_med: pd.DataFrame, df_low: pd.DataFrame):
    # get the Overview table HTML from the dataframe
    # overview_table_html = df_overview.to_html(table_id="table")
    # get the Findings table HTML from the dataframe
    high_findings_table_html = df_high.to_html(index=False, table_id="tableHigh", render_links=True)
    med_findings_table_html = df_med.to_html(index=False, table_id="tableMedium", render_links=True)
    low_findings_table_html = df_low.to_html(index=False, table_id="tableLow", render_links=True)
    # construct the complete HTML with jQuery Data tables
    # You can disable paging or enable y scrolling on lines 20 and 21 respectively
    html = f"""
    <html>
    <header>
        <link href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css" rel="stylesheet">
    </header>
    <body>
    <div class="container">
    <h1> <p id="sast"> Semgrep SAST Scan Report </p> </h1>
    </div>

    <div class="topnav">
    <a class="active" href="#sast-high"> SAST Findings- High Severity  </a> 
    <a> &nbsp &nbsp &nbsp &nbsp &nbsp </a>
    <a href="#sast-med"> Findings- SAST Medium Severity  </a>
    <a> &nbsp &nbsp &nbsp &nbsp &nbsp </a>
    <a href="#sast-low"> Findings- SAST Low Severity  </a> 
    </div>

    <div class="heading">
    <h2> <p id="sast-high"> Findings Summary- HIGH Severity </p> </h2>
    </div>
    <div class="container">
    {high_findings_table_html}
    <script src="https://code.jquery.com/jquery-3.6.0.slim.min.js" integrity="sha256-u7e5khyithlIdTpu22PHhENmPcRdFiHRjhAuHcs05RI=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <script>
        $(document).ready( function () {{
            $('#tableHigh').DataTable({{
                order: [[4, 'asc']]
                // paging: false,    
                // scrollY: 400,
            }});
        }});
    </script>
    </div>

    <div class="heading">
    <h2> <p id="sast-med"> Findings Summary- MEDIUM Severity </p> </h2>
    </div>
    <div class="container">
    {med_findings_table_html}
    <script src="https://code.jquery.com/jquery-3.6.0.slim.min.js" integrity="sha256-u7e5khyithlIdTpu22PHhENmPcRdFiHRjhAuHcs05RI=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <script>
        $(document).ready( function () {{
            $('#tableMedium').DataTable({{
                order: [[4, 'asc']]
                // paging: false,    
                // scrollY: 400,
            }});
        }});
    </script>
    </div>

    <div class="heading">
    <h2> <p id="sast-low"> Findings Summary- LOW Severity </p> </h2>
    </div>
    <div class="container">
    {low_findings_table_html}
    <script src="https://code.jquery.com/jquery-3.6.0.slim.min.js" integrity="sha256-u7e5khyithlIdTpu22PHhENmPcRdFiHRjhAuHcs05RI=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <script>
        $(document).ready( function () {{
            $('#tableLow').DataTable({{
                order: [[4, 'asc']]
                // paging: false,    
                // scrollY: 400,
            }});
        }});
    </script>
    </div>


    </body>
    </html>
    """
    # return the html
    return html

def process_sast_findings(df: pd.DataFrame):
    # Create new DF with SAST findings only
    df_sast = df.loc[(df['check_id'].str.contains('ssc')==False)]

    # Get the list of all column names from headers
    column_headers = list(df.columns.values)
    logging.debug("The Column Header :", column_headers)

    # list of columns of interest to include in the report
    interesting_columns_sast = [
        'check_id',
        'extra.message',
        'path',
        # 'finding_hyperlink',
        'extra.severity',
        'extra.metadata.confidence', 
        'extra.metadata.semgrep.url',
        # 'extra.metadata.likelihood',
        # 'extra.metadata.impact',
        # 'extra.metadata.owasp',
        # 'extra.metadata.cwe', 
        # 'extra.metadata.cwe2021-top25', 
        # 'extra.metadata.cwe2022-top25', 
    ]

    START_ROW = 0
    df_red = df[interesting_columns_sast]

    # replace severity values ERROR = HIGH, WARNING = MEDIUM, INFO = LOW 
    df_red = df_red.replace('ERROR', 'HIGH', regex=True)
    df_red = df_red.replace('WARNING', 'MEDIUM', regex=True)
    df_red = df_red.replace('INFO', 'LOW', regex=True)

    # create filename for XLSX report
    dir_name = os.path.basename(os.getcwd())
    logging.debug(dir_name)
    current_time = datetime.now().strftime("%Y%m%d-%H%M")
    reportname = f"semgrep_sast_findings_{dir_name}_{current_time}"
    xlsx_filename = f"{reportname}.xlsx"

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(xlsx_filename, engine="xlsxwriter")

    # Write the dataframe data to XlsxWriter. Turn off the default header and
    # index and skip one row to allow us to insert a user defined header.
    df_red.to_excel(writer, sheet_name="findings", startrow=START_ROW, header=True, index=False)

    # Get the xlsxwriter workbook and worksheet objects.
    workbook = writer.book
    worksheet = writer.sheets["findings"]

    # Get the dimensions of the dataframe.
    (max_row, max_col) = df_red.shape

    # Create a list of column headers, to use in add_table().
    column_settings = [{"header": column.split(".")[-1]} for column in df_red.columns]

    # Add the Excel table structure. Pandas will add the data.
    # we start from row = 4 to allow us to insert a title and summary of findings
    worksheet.add_table(START_ROW, 0, max_row+START_ROW, max_col - 1, {"columns": column_settings})

    # Add a format.
    text_format = workbook.add_format({'text_wrap' : True})

    # Make the text columns width = 48 & add text wrap for clarity
    worksheet.set_column(0, max_col - 1, 48, text_format) 

    # Make the message columns width = 96 & add text wrap for clarity
    worksheet.set_column(1, 1, 96, text_format) 

    # Make the severity, confidence, likelyhood & impact columns width = 12 
    worksheet.set_column(4, 7, 12)

    #  create new df_high by filtering df_red for HIGH severity
    df_high = df_red.loc[(df_red['extra.severity'] == 'HIGH')]
    # Create a list of column headers, to use in add_table().
    column_settings = [{"header": column.split(".")[-1]} for column in df_high.columns]

    #  create new df_med by filtering df_red for MED severity
    df_med = df_red.loc[(df_red['extra.severity'] == 'MEDIUM')]
    # Create a list of column headers, to use in add_table().
    column_settings = [{"header": column.split(".")[-1]} for column in df_med.columns]

    #  create new df_low by filtering df_red for LOW severity
    df_low = df_red.loc[(df_red['extra.severity'] == 'LOW')]
    # Create a list of column headers, to use in add_table().
    column_settings = [{"header": column.split(".")[-1]} for column in df_low.columns]

    # Close the Pandas Excel writer and output the Excel file.
    writer.close()

    # generate the HTML from the dataframe
    html = generate_html_sast(df_high, df_med, df_low)
    
    # create filename for HTML report
    html_filename = f"{reportname}.html"

    # write the HTML content to an HTML file
    open(html_filename, "w").write(html)

if __name__=="__main__":
    logging.basicConfig(level=logging.DEBUG)

    user_inputs = sys.argv[1:]
    logging.debug(user_inputs)

    # get option and value pair from getopt
    try:
        opts, args = getopt.getopt(user_inputs, "f:h", ["findings=", "help"])
        #lets's check out how getopt parse the arguments
        logging.debug(opts)
        logging.debug(args)
    except getopt.GetoptError:
        logging.debug('pass the arguments like -f <findings JSON file> -h <help> or --findings <findings JSON file> and --help <help>')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            logging.info('pass the arguments like -f <findings JSON file> -h <help> or --findings <findings JSON file> and --help <help>')
            sys.exit()
        elif opt in ("-f", "--findings"):
            logging.debug(opt)
            logging.debug(arg)
            findings_json_filename = arg
            
            with open(findings_json_filename) as json_file:
                data = json.load(json_file)
                logging.debug(data['results'])

            # df = pd.DataFrame(data['results'])
            df = json_normalize(data['results'])

            process_sast_findings(df)
        else:
            logging.info('pass the arguments like -f <findings JSON file> -h <help> or --findings <findings JSON file> and --help <help>')
            sys.exit()
    
