import re
import csv
import json
import xlsxwriter


class Export:
    def __init__(self, output_format=None, data=None, file_path=None,
                 file_name=None):
        self.data = data
        self.output_format = output_format
        self.file_path = file_path
        self.file_name = file_name
        self.save = self.put()

    def _to_csv(self):
        """
        Save to file with csv format.
        :return: output file
        """
        try:
            keys = self.data[0].keys()
            with open('{}/{}.{}'.format(
                    self.file_path.rstrip('/'),
                    self.file_name,
                    self.output_format), 'wb') as output_file:
                dict_writer = csv.DictWriter(output_file, keys)
                dict_writer.writeheader()
                dict_writer.writerows(self.data)
        except Exception:
            raise

    def _to_json(self):
        """
        Save to file with json format.
        :return: output file
        """
        try:
            with open('{}/{}.{}'.format(
                    self.file_path.rstrip('/'),
                    self.file_name,
                    self.output_format), 'wb') as output_file:
                json.dump(self.data, output_file)
        except Exception:
            raise

    def _to_xls(self):
        """
        Save to file with xls format.
        :return: output file
        """
        try:
            workbook = xlsxwriter.Workbook('{}/{}.{}'.format(
                self.file_path.rstrip('/'),
                self.file_name,
                self.output_format))
            worksheet = workbook.add_worksheet()
            row = 0
            col = 0
            titles = self.data[0].keys()

            # Title
            for i, t in enumerate(titles):
                worksheet.write(row, col + i, t)

            # Items
            for item in self.data:
                row += 1
                for j, v in enumerate(item.values()):
                    worksheet.write(row, col + j, v)

            workbook.close()
        except Exception:
            raise

    def put(self):
        """
        Output file selection.
        :return: output file
        """
        try:
            if self.output_format == 'csv':
                return self._to_csv()
            elif self.output_format == 'json':
                return self._to_json()
            elif re.search(r'xls.?', self.output_format):
                return self._to_xls()
            else:
                raise Exception('Export failed, file type not allowed.')
        except Exception:
            raise
