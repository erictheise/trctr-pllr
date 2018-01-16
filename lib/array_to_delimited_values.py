import io, csv
from flask import make_response

def array_to_delimited_values(array, delimiter):
    si = io.StringIO()
    writer = csv.writer(si, delimiter=delimiter, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerows(array)
    output = make_response(si.getvalue())
    # output.headers["Content-Disposition"] = "attachment; filename=trctr-pllr.csv"
    # output.headers["Content-type"] = "text/csv"

    return output
